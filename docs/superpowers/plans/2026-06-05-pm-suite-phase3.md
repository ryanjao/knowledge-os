# PM Suite Phase 3 — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. When implementing the Claude API task, also consult the `claude-api` skill for current SDK/caching best practice.

**Goal:** Upload a tender document (PDF/Word) → extract text → Claude parses it into a structured JSON draft → review/edit in an in-app page → on approval, deterministically create the project's tasks, calendar events, and kanban cards in SQLite.

**Architecture:** Claude is used ONLY as a one-shot extractor that returns a structured draft via tool-use (decision D2 — it never writes the DB). All writes are deterministic code in a single transaction that reuses the Phase 2 tasks/events/cards/boards layer. The parse adapter takes an injectable client so the logic is testable without an API key.

**Tech Stack:** Next.js 16, React 19, TypeScript, better-sqlite3, Vitest, `@anthropic-ai/sdk` (claude-sonnet-4-6, tool-use + prompt caching), `pdf-parse` (PDF text), `mammoth` (.docx text).

**Project root:** `/Users/juiyujao/Projects/pm-suite/`
**Spec:** `knowledge-os/docs/superpowers/specs/2026-06-04-pm-suite-design.md` (v2 — §4.4, §4.5, D2, D5)

## Scope decisions (confirmed with user 2026-06-05)
- **No Notion in Phase 3.** Flow ends at writing SQLite. Programmatic Notion write is deferred to Phase 4.
- **Review interface is an in-app preview page** (not Notion).
- Extraction: `pdf-parse` (PDF), `mammoth` (.docx). Scanned/image PDFs (OCR) are out of scope — a PDF that yields no text returns a clear error.
- Claude: `@anthropic-ai/sdk`, model `claude-sonnet-4-6`, forced tool-use for structured output, `cache_control` on the system block. The parse adapter is client-injectable for tests.
- Minimal disclosure (spec §6): only extracted text is sent (never the raw binary), capped at a max length. Full PII masking is a documented future item, not built here.

---

## Context for the implementer (read first)

Phases 1–2 are committed on `pm-suite` `main`. Reuse these:
- `src/lib/db.ts` `getDb()` (local app-data SQLite, WAL, FK ON, runs migrations).
- `src/lib/migrations.ts` — `MIGRATIONS` array + `runMigrations`. You ADD a `version: 2` entry; do NOT edit version 1. `addColumn(db, table, column, ddl)` helper exists (guarded ADD COLUMN).
- Query modules take `db` as the first arg. Existing: `projects`, `events` (`createEvent` — `task_id` optional), `tasks` (`createTask`, `setTaskStatus`), `boards` (`getOrCreateBoard`, `ensureDefaultColumns`), `columns` (`listColumns`), `cards` (`createCard`), `audit` (`appendAudit`).
- Tests open `new Database(':memory:')`, then `applySchema(db); runMigrations(db)` in `beforeEach`. `foreign_keys` is enforced — child rows need real parents.
- `documents` table already exists (Phase 1 baseline + v1 migration columns): `id, project_id, file_path, file_name, parsed_at, notion_page_id, status, source_last_edited_time, last_synced_at`. Phase 3 migration adds `parsed_json` and `imported_at`.
- Env: `CLAUDE_API_KEY` lives in `.env.local` (already in `.env.example`). The data dir comes from `getDataDir()`; uploads go in `<dataDir>/uploads/`.
- Single test file: `npm test -- tests/lib/<name>.test.ts`. All: `npm test`. Build: `npm run build`.

---

## File Map

```
package.json                              ← MODIFY: add deps
src/types/pdf-parse.d.ts                  ← CREATE: module declaration (no @types)
src/types/index.ts                        ← MODIFY: add Deliverable, ParsedTender, PmDocument, ImportResult
src/lib/migrations.ts                     ← MODIFY: add MIGRATIONS version 2 (documents.parsed_json, imported_at)
src/lib/extract.ts                        ← CREATE: extractText(buffer, filename) dispatch by extension
src/lib/claude.ts                         ← CREATE: parseTenderText(text, client?) + normalizeTender + tool schema
src/lib/queries/documents.ts             ← CREATE: createDocument/getDocument/listDocuments/setParsedDraft/setImported
src/lib/queries/import.ts                ← CREATE: importTenderDraft (deterministic tx: project?/tasks/events/cards)
src/app/api/upload/route.ts              ← CREATE: POST multipart → save file + documents row
src/app/api/documents/route.ts          ← CREATE: GET list
src/app/api/documents/[id]/route.ts     ← CREATE: GET one (incl. parsed draft)
src/app/api/documents/[id]/parse/route.ts  ← CREATE: POST → extract + Claude → store draft
src/app/api/documents/[id]/import/route.ts ← CREATE: POST confirmed draft → import to SQLite
src/components/DocumentReview.tsx        ← CREATE: editable draft form
src/app/upload/page.tsx                  ← CREATE: upload → parse → review → import UI

tests/lib/migrations-v2.test.ts          ← CREATE
tests/lib/documents.test.ts              ← CREATE
tests/lib/extract.test.ts                ← CREATE
tests/lib/claude.test.ts                 ← CREATE (stubbed client)
tests/lib/import.test.ts                 ← CREATE (the core — no Claude needed)
```

---

## Task 1: Dependencies, Types, Migration v2

**Files:** `package.json`, `src/types/pdf-parse.d.ts`, `src/types/index.ts`, `src/lib/migrations.ts`, `tests/lib/migrations-v2.test.ts`

- [ ] **Step 1: Install dependencies**

```bash
cd /Users/juiyujao/Projects/pm-suite
npm install @anthropic-ai/sdk pdf-parse mammoth
```
(`mammoth` ships its own types; `pdf-parse` does not — handled by the declaration in Step 2.)

- [ ] **Step 2: Add the pdf-parse type declaration**

Create `src/types/pdf-parse.d.ts`:
```typescript
declare module 'pdf-parse' {
  interface PdfParseResult {
    text: string
    numpages: number
    info: unknown
  }
  function pdfParse(data: Buffer): Promise<PdfParseResult>
  export = pdfParse
}
```

- [ ] **Step 3: Add the new shared types**

Append to `src/types/index.ts`:
```typescript
export interface Deliverable {
  name: string
  due_date: string | null   // ISO "YYYY-MM-DD" or null
}

export interface ParsedTender {
  project_name: string | null
  case_number: string | null
  agency: string | null
  amount: string | null
  payment_terms: string | null
  award_date: string | null
  deliverables: Deliverable[]
  sla_terms: string | null
  warranty: string | null
  security_audit: string | null
  meetings: string | null
}

export interface PmDocument {
  id: number
  project_id: number | null
  file_path: string
  file_name: string
  parsed_at: string | null
  notion_page_id: string | null
  status: string
  source_last_edited_time: string | null
  last_synced_at: string | null
  parsed_json: string | null
  imported_at: string | null
}

export interface ImportResult {
  project_id: number
  created_tasks: number
  created_events: number
  created_cards: number
}
```

- [ ] **Step 4: Write the failing migration-v2 test**

Create `tests/lib/migrations-v2.test.ts`:
```typescript
import { describe, it, expect, beforeEach, afterEach } from 'vitest'
import Database from 'better-sqlite3'
import { applySchema } from '@/lib/schema'
import { runMigrations } from '@/lib/migrations'

function columnNames(db: Database.Database, table: string): string[] {
  return (db.prepare(`PRAGMA table_info(${table})`).all() as { name: string }[]).map(r => r.name)
}

describe('migration v2 (documents draft columns)', () => {
  let db: Database.Database
  beforeEach(() => { db = new Database(':memory:'); applySchema(db) })
  afterEach(() => { db.close() })

  it('adds parsed_json and imported_at to documents', () => {
    runMigrations(db)
    expect(columnNames(db, 'documents')).toContain('parsed_json')
    expect(columnNames(db, 'documents')).toContain('imported_at')
  })

  it('bumps user_version to 2 and stays idempotent', () => {
    runMigrations(db)
    expect(db.pragma('user_version', { simple: true })).toBe(2)
    expect(() => runMigrations(db)).not.toThrow()
    expect(db.pragma('user_version', { simple: true })).toBe(2)
  })
})
```

- [ ] **Step 5: Run it to confirm failure**

Run: `npm test -- tests/lib/migrations-v2.test.ts`
Expected: FAIL — `expect(user_version).toBe(2)` gets 1, and `parsed_json` missing.

- [ ] **Step 6: Add migration version 2**

In `src/lib/migrations.ts`, add a second entry to the `MIGRATIONS` array (after the `version: 1` object, do not modify version 1):
```typescript
  {
    version: 2,
    up(db) {
      addColumn(db, 'documents', 'parsed_json', `parsed_json TEXT`)
      addColumn(db, 'documents', 'imported_at', `imported_at TEXT`)
    },
  },
```

- [ ] **Step 7: Run to confirm pass + full suite**

Run: `npm test -- tests/lib/migrations-v2.test.ts` → PASS (2)
Run: `npm test` → all green (the existing migration test still expects version 1 behaviour only for its own assertions, which remain true; note the existing `migrations.test.ts` asserts `toBe(1)` — update it in the next step).

- [ ] **Step 8: Update the existing migrations test for the new latest version**

In `tests/lib/migrations.test.ts`, the two assertions `expect(db.pragma('user_version', { simple: true })).toBe(1)` are now wrong (latest is 2). Change both occurrences to `.toBe(2)`.

Run: `npm test -- tests/lib/migrations.test.ts` → PASS.

- [ ] **Step 9: Commit**

```bash
git add package.json package-lock.json src/types/ src/lib/migrations.ts tests/lib/migrations-v2.test.ts tests/lib/migrations.test.ts
git commit -m "feat: Phase 3 deps + types + migration v2 (documents.parsed_json/imported_at)"
```

---

## Task 2: Documents Queries

**Files:** `src/lib/queries/documents.ts`, `tests/lib/documents.test.ts`

- [ ] **Step 1: Write the failing test**

Create `tests/lib/documents.test.ts`:
```typescript
import { describe, it, expect, beforeEach, afterEach } from 'vitest'
import Database from 'better-sqlite3'
import { applySchema } from '@/lib/schema'
import { runMigrations } from '@/lib/migrations'
import {
  createDocument, getDocument, listDocuments, setParsedDraft, setImported,
} from '@/lib/queries/documents'

describe('documents queries', () => {
  let db: Database.Database
  beforeEach(() => { db = new Database(':memory:'); applySchema(db); runMigrations(db) })
  afterEach(() => { db.close() })

  it('creates a document with status uploaded', () => {
    const id = createDocument(db, { file_path: '/d/x.pdf', file_name: 'x.pdf' })
    const doc = getDocument(db, id)!
    expect(doc.file_name).toBe('x.pdf')
    expect(doc.status).toBe('uploaded')
    expect(doc.parsed_json).toBeNull()
  })

  it('lists documents newest-first', () => {
    createDocument(db, { file_path: '/d/a.pdf', file_name: 'a.pdf' })
    createDocument(db, { file_path: '/d/b.pdf', file_name: 'b.pdf' })
    expect(listDocuments(db).map(d => d.file_name)).toEqual(['b.pdf', 'a.pdf'])
  })

  it('stores a parsed draft and flips status to parsed_draft', () => {
    const id = createDocument(db, { file_path: '/d/x.pdf', file_name: 'x.pdf' })
    setParsedDraft(db, id, '{"project_name":"高檢署案"}')
    const doc = getDocument(db, id)!
    expect(doc.status).toBe('parsed_draft')
    expect(doc.parsed_json).toBe('{"project_name":"高檢署案"}')
    expect(doc.parsed_at).not.toBeNull()
  })

  it('marks a document imported with its project', () => {
    const id = createDocument(db, { file_path: '/d/x.pdf', file_name: 'x.pdf' })
    setImported(db, id, 42)
    const doc = getDocument(db, id)!
    expect(doc.status).toBe('imported_to_sqlite')
    expect(doc.project_id).toBe(42)
    expect(doc.imported_at).not.toBeNull()
  })
})
```

- [ ] **Step 2: Run to confirm failure**

Run: `npm test -- tests/lib/documents.test.ts`
Expected: FAIL — "Cannot find package '@/lib/queries/documents'"

- [ ] **Step 3: Implement documents.ts**

Create `src/lib/queries/documents.ts`:
```typescript
import type Database from 'better-sqlite3'
import type { PmDocument } from '@/types'

interface CreateDocumentInput {
  file_path: string
  file_name: string
  project_id?: number | null
}

export function createDocument(db: Database.Database, input: CreateDocumentInput): number {
  const result = db.prepare(`
    INSERT INTO documents (project_id, file_path, file_name, status)
    VALUES (@project_id, @file_path, @file_name, 'uploaded')
  `).run({ project_id: null, ...input })
  return result.lastInsertRowid as number
}

export function getDocument(db: Database.Database, id: number): PmDocument | null {
  return (db.prepare('SELECT * FROM documents WHERE id = ?').get(id) as PmDocument | undefined) ?? null
}

export function listDocuments(db: Database.Database): PmDocument[] {
  return db.prepare('SELECT * FROM documents ORDER BY id DESC').all() as PmDocument[]
}

export function setParsedDraft(db: Database.Database, id: number, parsedJson: string): void {
  db.prepare(`
    UPDATE documents
    SET parsed_json = ?, status = 'parsed_draft', parsed_at = datetime('now','localtime')
    WHERE id = ?
  `).run(parsedJson, id)
}

export function setImported(db: Database.Database, id: number, projectId: number): void {
  db.prepare(`
    UPDATE documents
    SET project_id = ?, status = 'imported_to_sqlite', imported_at = datetime('now','localtime')
    WHERE id = ?
  `).run(projectId, id)
}
```

- [ ] **Step 4: Run to confirm pass**

Run: `npm test -- tests/lib/documents.test.ts` → PASS (4)

- [ ] **Step 5: Commit**

```bash
git add src/lib/queries/documents.ts tests/lib/documents.test.ts
git commit -m "feat: documents query layer (upload → parsed_draft → imported states)"
```

---

## Task 3: Text Extraction

**Files:** `src/lib/extract.ts`, `tests/lib/extract.test.ts`

- [ ] **Step 1: Write the failing test**

The dispatch logic is what we test (choosing an extractor by extension + error handling). The real pdf/docx extractors are injected so the test needs no binary fixtures.

Create `tests/lib/extract.test.ts`:
```typescript
import { describe, it, expect } from 'vitest'
import { extractText, pickExtractor } from '@/lib/extract'

describe('text extraction dispatch', () => {
  it('picks pdf extractor for .pdf', () => {
    expect(pickExtractor('a/b/report.PDF')).toBe('pdf')
  })

  it('picks docx extractor for .docx', () => {
    expect(pickExtractor('report.docx')).toBe('docx')
  })

  it('throws a clear error for unsupported extensions', () => {
    expect(() => pickExtractor('notes.txt')).toThrow(/不支援/)
  })

  it('extractText uses the injected extractors and trims the result', async () => {
    const text = await extractText(Buffer.from('x'), 'r.pdf', {
      pdf: async () => '  hello pdf  ',
      docx: async () => 'unused',
    })
    expect(text).toBe('hello pdf')
  })

  it('extractText throws when extraction yields empty text (e.g. scanned PDF)', async () => {
    await expect(
      extractText(Buffer.from('x'), 'r.pdf', { pdf: async () => '   ', docx: async () => '' })
    ).rejects.toThrow(/未能擷取/)
  })
})
```

- [ ] **Step 2: Run to confirm failure**

Run: `npm test -- tests/lib/extract.test.ts`
Expected: FAIL — "Cannot find package '@/lib/extract'"

- [ ] **Step 3: Implement extract.ts**

Create `src/lib/extract.ts`:
```typescript
import path from 'path'

export type ExtractorKind = 'pdf' | 'docx'

export interface Extractors {
  pdf: (buf: Buffer) => Promise<string>
  docx: (buf: Buffer) => Promise<string>
}

export function pickExtractor(fileName: string): ExtractorKind {
  const ext = path.extname(fileName).toLowerCase()
  if (ext === '.pdf') return 'pdf'
  if (ext === '.docx') return 'docx'
  throw new Error(`不支援的檔案格式：${ext || '(無副檔名)'}（僅支援 .pdf / .docx）`)
}

// Default real extractors. Imported lazily so tests can inject fakes without
// loading the native/parsing libs.
async function defaultExtractors(): Promise<Extractors> {
  const pdfParse = (await import('pdf-parse')).default
  const mammoth = await import('mammoth')
  return {
    pdf: async buf => (await pdfParse(buf)).text,
    docx: async buf => (await mammoth.extractRawText({ buffer: buf })).value,
  }
}

export async function extractText(
  buffer: Buffer,
  fileName: string,
  extractors?: Extractors
): Promise<string> {
  const kind = pickExtractor(fileName)
  const ex = extractors ?? (await defaultExtractors())
  const raw = await ex[kind](buffer)
  const text = (raw ?? '').trim()
  if (!text) {
    throw new Error('未能擷取出文字（可能是掃描影像 PDF，Phase 3 不支援 OCR）')
  }
  return text
}
```

- [ ] **Step 4: Run to confirm pass**

Run: `npm test -- tests/lib/extract.test.ts` → PASS (5)

- [ ] **Step 5: Commit**

```bash
git add src/lib/extract.ts tests/lib/extract.test.ts
git commit -m "feat: document text extraction (pdf-parse / mammoth) with dispatch + empty guard"
```

---

## Task 4: Claude Parse Adapter

**Files:** `src/lib/claude.ts`, `tests/lib/claude.test.ts`

Claude is invoked through a tiny adapter with an injectable client, so the mapping logic is unit-tested without an API key. The real call uses forced tool-use for reliable structured output and caches the system prompt.

- [ ] **Step 1: Write the failing test**

Create `tests/lib/claude.test.ts`:
```typescript
import { describe, it, expect } from 'vitest'
import { parseTenderText, normalizeTender, type AnthropicLike } from '@/lib/claude'

describe('normalizeTender', () => {
  it('fills missing scalars with null and defaults deliverables to []', () => {
    const t = normalizeTender({ project_name: '高檢署案' })
    expect(t.project_name).toBe('高檢署案')
    expect(t.case_number).toBeNull()
    expect(t.deliverables).toEqual([])
  })

  it('coerces deliverables and drops entries without a name', () => {
    const t = normalizeTender({
      deliverables: [
        { name: '期初報告', due_date: '2026-07-01' },
        { name: '', due_date: '2026-08-01' },
        { due_date: '2026-09-01' } as never,
      ],
    })
    expect(t.deliverables).toEqual([{ name: '期初報告', due_date: '2026-07-01' }])
  })
})

describe('parseTenderText', () => {
  it('returns the tool_use input, normalized', async () => {
    const fakeClient: AnthropicLike = {
      messages: {
        create: async () => ({
          content: [
            { type: 'text', text: 'ignored' },
            { type: 'tool_use', name: 'record_tender', input: {
              project_name: '高檢署 緝毒系統維護',
              case_number: 'A-123',
              deliverables: [{ name: '期末報告', due_date: '2026-12-31' }],
            } },
          ],
        }),
      },
    }
    const out = await parseTenderText('某標案文字…', fakeClient)
    expect(out.project_name).toBe('高檢署 緝毒系統維護')
    expect(out.case_number).toBe('A-123')
    expect(out.deliverables).toHaveLength(1)
    expect(out.agency).toBeNull()
  })

  it('throws when Claude returns no tool_use block', async () => {
    const fakeClient: AnthropicLike = {
      messages: { create: async () => ({ content: [{ type: 'text', text: 'no tool' }] }) },
    }
    await expect(parseTenderText('x', fakeClient)).rejects.toThrow(/結構化/)
  })
})
```

- [ ] **Step 2: Run to confirm failure**

Run: `npm test -- tests/lib/claude.test.ts`
Expected: FAIL — "Cannot find package '@/lib/claude'"

- [ ] **Step 3: Implement claude.ts**

Create `src/lib/claude.ts`:
```typescript
import Anthropic from '@anthropic-ai/sdk'
import type { ParsedTender, Deliverable } from '@/types'

// Minimal shape we depend on, so tests can inject a fake client.
export interface AnthropicLike {
  messages: {
    create: (args: unknown) => Promise<{ content: Array<{ type: string; name?: string; input?: unknown }> }>
  }
}

const MODEL = 'claude-sonnet-4-6'
const MAX_INPUT_CHARS = 60_000 // minimal-disclosure guard: cap what we send

const SYSTEM_PROMPT =
  '你是政府 IT 標案文件的結構化抽取助手。只根據文件內容抽取欄位，找不到的欄位填 null。' +
  '日期一律輸出 ISO 格式 YYYY-MM-DD。deliverables 是每份交付文件的名稱與截止日。' +
  '務必呼叫 record_tender 工具回傳結果，不要用純文字回答。'

const TENDER_TOOL = {
  name: 'record_tender',
  description: '回傳從標案文件抽取的結構化欄位',
  input_schema: {
    type: 'object',
    properties: {
      project_name: { type: ['string', 'null'] },
      case_number: { type: ['string', 'null'] },
      agency: { type: ['string', 'null'] },
      amount: { type: ['string', 'null'] },
      payment_terms: { type: ['string', 'null'] },
      award_date: { type: ['string', 'null'] },
      deliverables: {
        type: 'array',
        items: {
          type: 'object',
          properties: {
            name: { type: 'string' },
            due_date: { type: ['string', 'null'] },
          },
          required: ['name'],
        },
      },
      sla_terms: { type: ['string', 'null'] },
      warranty: { type: ['string', 'null'] },
      security_audit: { type: ['string', 'null'] },
      meetings: { type: ['string', 'null'] },
    },
    required: ['deliverables'],
  },
} as const

export function normalizeTender(raw: Partial<ParsedTender>): ParsedTender {
  const deliverables: Deliverable[] = Array.isArray(raw.deliverables)
    ? raw.deliverables
        .filter((d): d is Deliverable => !!d && typeof d.name === 'string' && d.name.trim() !== '')
        .map(d => ({ name: d.name.trim(), due_date: d.due_date ?? null }))
    : []
  const s = (v: unknown): string | null => (typeof v === 'string' && v.trim() !== '' ? v : null)
  return {
    project_name: s(raw.project_name),
    case_number: s(raw.case_number),
    agency: s(raw.agency),
    amount: s(raw.amount),
    payment_terms: s(raw.payment_terms),
    award_date: s(raw.award_date),
    deliverables,
    sla_terms: s(raw.sla_terms),
    warranty: s(raw.warranty),
    security_audit: s(raw.security_audit),
    meetings: s(raw.meetings),
  }
}

function defaultClient(): AnthropicLike {
  return new Anthropic({ apiKey: process.env.CLAUDE_API_KEY }) as unknown as AnthropicLike
}

export async function parseTenderText(
  text: string,
  client: AnthropicLike = defaultClient()
): Promise<ParsedTender> {
  const msg = await client.messages.create({
    model: MODEL,
    max_tokens: 4096,
    system: [{ type: 'text', text: SYSTEM_PROMPT, cache_control: { type: 'ephemeral' } }],
    tools: [TENDER_TOOL],
    tool_choice: { type: 'tool', name: 'record_tender' },
    messages: [{ role: 'user', content: `標案文件內容：\n${text.slice(0, MAX_INPUT_CHARS)}` }],
  })
  const block = msg.content.find(b => b.type === 'tool_use')
  if (!block || block.input == null) {
    throw new Error('Claude 未回傳結構化結果（無 tool_use）')
  }
  return normalizeTender(block.input as Partial<ParsedTender>)
}
```

- [ ] **Step 4: Run to confirm pass**

Run: `npm test -- tests/lib/claude.test.ts` → PASS (4)

- [ ] **Step 5: Commit**

```bash
git add src/lib/claude.ts tests/lib/claude.test.ts
git commit -m "feat: Claude tender parser — forced tool-use, injectable client, normalize"
```

---

## Task 5: Import Logic (the deterministic core, D2)

**Files:** `src/lib/queries/import.ts`, `tests/lib/import.test.ts`

This is where the approved draft becomes real rows. No Claude here — pure, transactional, testable. Reuses Phase 2 boards/tasks/events/cards.

Behaviour of `importTenderDraft(db, documentId, draft)`:
1. Resolve the project: if the document already has `project_id`, use it; else if a project with the same non-empty `case_number` exists, use it; else create a new project from the draft.
2. Get/create that project's board and find its first non-done column (待處理).
3. For each deliverable with a name: create a `task` (kind `deliverable`), an `event` (`document_delivery`, only if `due_date` present), linked to the task, and a `card` linked to the task in the 待處理 column.
4. Mark the document imported (status, project_id, imported_at) and store the final `parsed_json`.
5. Write one `audit_log` row.
6. Return counts.

- [ ] **Step 1: Write the failing test**

Create `tests/lib/import.test.ts`:
```typescript
import { describe, it, expect, beforeEach, afterEach } from 'vitest'
import Database from 'better-sqlite3'
import { applySchema } from '@/lib/schema'
import { runMigrations } from '@/lib/migrations'
import { listProjects } from '@/lib/queries/projects'
import { listTasksForProject } from '@/lib/queries/tasks'
import { listEventsForMonth } from '@/lib/queries/events'
import { getOrCreateBoard } from '@/lib/queries/boards'
import { listColumns } from '@/lib/queries/columns'
import { listCardsForBoard } from '@/lib/queries/cards'
import { listAudit } from '@/lib/queries/audit'
import { createDocument, getDocument } from '@/lib/queries/documents'
import { importTenderDraft } from '@/lib/queries/import'
import type { ParsedTender } from '@/types'

function draft(over: Partial<ParsedTender> = {}): ParsedTender {
  return {
    project_name: '高檢署 緝毒系統維護', case_number: 'A-123', agency: '高檢署',
    amount: '500萬', payment_terms: '分期', award_date: '2026-06-01',
    deliverables: [
      { name: '期初報告', due_date: '2026-07-01' },
      { name: '期末報告', due_date: '2026-12-31' },
      { name: '無日期交付物', due_date: null },
    ],
    sla_terms: 'P1 4小時', warranty: '一年', security_audit: '上線前', meetings: '每月',
    ...over,
  }
}

describe('importTenderDraft', () => {
  let db: Database.Database
  beforeEach(() => { db = new Database(':memory:'); applySchema(db); runMigrations(db) })
  afterEach(() => { db.close() })

  it('creates a new project, tasks, events, and cards from a draft', () => {
    const docId = createDocument(db, { file_path: '/d/t.pdf', file_name: 't.pdf' })
    const res = importTenderDraft(db, docId, draft())

    const projects = listProjects(db)
    expect(projects).toHaveLength(1)
    expect(projects[0].name).toBe('高檢署 緝毒系統維護')
    expect(projects[0].case_number).toBe('A-123')

    expect(res.created_tasks).toBe(3)   // all three deliverables
    expect(res.created_events).toBe(2)  // only the two with due_date
    expect(res.created_cards).toBe(3)

    expect(listTasksForProject(db, res.project_id)).toHaveLength(3)
    expect(listEventsForMonth(db, '2026-07')).toHaveLength(1)
    expect(listEventsForMonth(db, '2026-12')).toHaveLength(1)

    const board = getOrCreateBoard(db, res.project_id)
    const todo = listColumns(db, board.id).find(c => c.is_done_column === 0)!
    const cards = listCardsForBoard(db, board.id)
    expect(cards).toHaveLength(3)
    expect(cards.every(c => c.column_id === todo.id)).toBe(true)
    expect(cards.every(c => c.task_id !== null)).toBe(true)
  })

  it('marks the document imported and writes audit', () => {
    const docId = createDocument(db, { file_path: '/d/t.pdf', file_name: 't.pdf' })
    const res = importTenderDraft(db, docId, draft())
    const doc = getDocument(db, docId)!
    expect(doc.status).toBe('imported_to_sqlite')
    expect(doc.project_id).toBe(res.project_id)
    expect(doc.imported_at).not.toBeNull()
    expect(doc.parsed_json).toContain('高檢署')
    expect(listAudit(db).some(a => a.action === 'document_imported')).toBe(true)
  })

  it('reuses an existing project with the same case_number instead of duplicating', () => {
    const d1 = createDocument(db, { file_path: '/d/1.pdf', file_name: '1.pdf' })
    const r1 = importTenderDraft(db, d1, draft({ deliverables: [{ name: 'A', due_date: null }] }))
    const d2 = createDocument(db, { file_path: '/d/2.pdf', file_name: '2.pdf' })
    const r2 = importTenderDraft(db, d2, draft({ deliverables: [{ name: 'B', due_date: null }] }))
    expect(r2.project_id).toBe(r1.project_id)
    expect(listProjects(db)).toHaveLength(1)
    expect(listTasksForProject(db, r1.project_id)).toHaveLength(2) // A + B
  })

  it('uses the document existing project_id when set', () => {
    const docId = createDocument(db, { file_path: '/d/t.pdf', file_name: 't.pdf' })
    db.prepare('UPDATE documents SET project_id = (SELECT id FROM projects WHERE 1=0)').run() // no-op safety
    // create a project and attach the document to it
    const pid = (db.prepare(
      `INSERT INTO projects (name, client, case_number, color_tag, status)
       VALUES ('既有專案','機關','OLD','#888','active')`
    ).run().lastInsertRowid) as number
    db.prepare('UPDATE documents SET project_id = ? WHERE id = ?').run(pid, docId)

    const res = importTenderDraft(db, docId, draft({ case_number: 'A-123' }))
    expect(res.project_id).toBe(pid)            // honoured the document's project
    expect(listProjects(db)).toHaveLength(1)    // no new project created
  })
})
```

- [ ] **Step 2: Run to confirm failure**

Run: `npm test -- tests/lib/import.test.ts`
Expected: FAIL — "Cannot find package '@/lib/queries/import'"

- [ ] **Step 3: Implement import.ts**

Create `src/lib/queries/import.ts`:
```typescript
import type Database from 'better-sqlite3'
import type { ParsedTender, ImportResult } from '@/types'
import { createProject } from './projects'
import { createTask } from './tasks'
import { createEvent } from './events'
import { getOrCreateBoard } from './boards'
import { listColumns } from './columns'
import { createCard } from './cards'
import { appendAudit } from './audit'
import { setImported, getDocument } from './documents'

function resolveProjectId(db: Database.Database, documentId: number, draft: ParsedTender): number {
  const doc = getDocument(db, documentId)
  if (doc?.project_id) return doc.project_id

  const caseNo = draft.case_number?.trim()
  if (caseNo) {
    const existing = db.prepare('SELECT id FROM projects WHERE case_number = ?')
      .get(caseNo) as { id: number } | undefined
    if (existing) return existing.id
  }

  return createProject(db, {
    name: draft.project_name?.trim() || doc?.file_name || '未命名專案',
    client: draft.agency?.trim() || '',
    case_number: caseNo || '',
    color_tag: '#60a5fa',
    status: 'active',
  })
}

export function importTenderDraft(
  db: Database.Database,
  documentId: number,
  draft: ParsedTender
): ImportResult {
  const run = db.transaction((): ImportResult => {
    const projectId = resolveProjectId(db, documentId, draft)

    const board = getOrCreateBoard(db, projectId)
    const todo = listColumns(db, board.id).find(c => c.is_done_column === 0)
    if (!todo) throw new Error('看板缺少「待處理」欄位')

    let createdTasks = 0
    let createdEvents = 0
    let createdCards = 0

    for (const d of draft.deliverables) {
      const taskId = createTask(db, {
        project_id: projectId, title: d.name, kind: 'deliverable', due_date: d.due_date,
      })
      createdTasks++

      if (d.due_date) {
        createEvent(db, {
          project_id: projectId, task_id: taskId, title: d.name,
          event_type: 'document_delivery', due_date: d.due_date, recurrence_rule: null,
        })
        createdEvents++
      }

      createCard(db, {
        project_id: projectId, task_id: taskId, column_id: todo.id,
        title: d.name, notes: null, due_date: d.due_date, target_platform: null,
      })
      createdCards++
    }

    setImported(db, documentId, projectId)
    db.prepare('UPDATE documents SET parsed_json = ? WHERE id = ?')
      .run(JSON.stringify(draft), documentId)

    appendAudit(db, {
      actor: 'user', action: 'document_imported', entity_type: 'document',
      entity_id: documentId,
      detail: `project ${projectId}: ${createdTasks} tasks / ${createdEvents} events / ${createdCards} cards`,
    })

    return { project_id: projectId, created_tasks: createdTasks, created_events: createdEvents, created_cards: createdCards }
  })
  return run()
}
```

- [ ] **Step 4: Run to confirm pass + full suite**

Run: `npm test -- tests/lib/import.test.ts` → PASS (4)
Run: `npm test` → all green.

- [ ] **Step 5: Commit**

```bash
git add src/lib/queries/import.ts tests/lib/import.test.ts
git commit -m "feat: deterministic tender import — draft → project/tasks/events/cards (D2)"
```

---

## Task 6: API Routes

**Files:** `src/app/api/upload/route.ts`, `src/app/api/documents/route.ts`, `src/app/api/documents/[id]/route.ts`, `src/app/api/documents/[id]/parse/route.ts`, `src/app/api/documents/[id]/import/route.ts`

- [ ] **Step 1: Upload route (multipart → save file + documents row)**

Create `src/app/api/upload/route.ts`:
```typescript
import { NextResponse } from 'next/server'
import path from 'path'
import fs from 'fs/promises'
import { getDb, getDataDir } from '@/lib/db'
import { createDocument } from '@/lib/queries/documents'

export async function POST(req: Request) {
  const form = await req.formData()
  const file = form.get('file')
  if (!(file instanceof File)) {
    return NextResponse.json({ error: '缺少檔案' }, { status: 400 })
  }
  const uploadsDir = path.join(getDataDir(), 'uploads')
  await fs.mkdir(uploadsDir, { recursive: true })

  const safeName = file.name.replace(/[/\\]/g, '_')
  const filePath = path.join(uploadsDir, `${Date.now()}-${safeName}`)
  await fs.writeFile(filePath, Buffer.from(await file.arrayBuffer()))

  const db = getDb()
  const id = createDocument(db, { file_path: filePath, file_name: safeName })
  return NextResponse.json({ id }, { status: 201 })
}
```

- [ ] **Step 2: Documents list + single routes**

Create `src/app/api/documents/route.ts`:
```typescript
import { NextResponse } from 'next/server'
import { getDb } from '@/lib/db'
import { listDocuments } from '@/lib/queries/documents'

export async function GET() {
  return NextResponse.json(listDocuments(getDb()))
}
```

Create `src/app/api/documents/[id]/route.ts`:
```typescript
import { NextResponse } from 'next/server'
import { getDb } from '@/lib/db'
import { getDocument } from '@/lib/queries/documents'

export async function GET(_req: Request, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params
  const doc = getDocument(getDb(), Number(id))
  if (!doc) return NextResponse.json({ error: 'not found' }, { status: 404 })
  return NextResponse.json(doc)
}
```

- [ ] **Step 3: Parse route (extract + Claude → draft)**

Create `src/app/api/documents/[id]/parse/route.ts`:
```typescript
import { NextResponse } from 'next/server'
import fs from 'fs/promises'
import { getDb } from '@/lib/db'
import { getDocument, setParsedDraft } from '@/lib/queries/documents'
import { extractText } from '@/lib/extract'
import { parseTenderText } from '@/lib/claude'

export async function POST(_req: Request, { params }: { params: Promise<{ id: string }> }) {
  const db = getDb()
  const { id } = await params
  const doc = getDocument(db, Number(id))
  if (!doc) return NextResponse.json({ error: 'not found' }, { status: 404 })
  if (!process.env.CLAUDE_API_KEY) {
    return NextResponse.json({ error: '未設定 CLAUDE_API_KEY（見 .env.example）' }, { status: 400 })
  }

  try {
    const buffer = await fs.readFile(doc.file_path)
    const text = await extractText(buffer, doc.file_name)
    const draft = await parseTenderText(text)
    setParsedDraft(db, doc.id, JSON.stringify(draft))
    return NextResponse.json({ draft })
  } catch (e) {
    return NextResponse.json({ error: (e as Error).message }, { status: 422 })
  }
}
```

- [ ] **Step 4: Import route (confirmed draft → SQLite)**

Create `src/app/api/documents/[id]/import/route.ts`:
```typescript
import { NextResponse } from 'next/server'
import { getDb } from '@/lib/db'
import { getDocument } from '@/lib/queries/documents'
import { importTenderDraft } from '@/lib/queries/import'
import type { ParsedTender } from '@/types'

export async function POST(req: Request, { params }: { params: Promise<{ id: string }> }) {
  const db = getDb()
  const { id } = await params
  const doc = getDocument(db, Number(id))
  if (!doc) return NextResponse.json({ error: 'not found' }, { status: 404 })

  const draft = await req.json() as ParsedTender
  const result = importTenderDraft(db, doc.id, draft)
  return NextResponse.json(result, { status: 201 })
}
```

- [ ] **Step 5: Verify the non-Claude routes against a running server**

```bash
npm run dev
```
In another terminal (upload needs a real file; use any small .pdf or .docx you have):
```bash
# upload
curl -s -F "file=@/path/to/some.pdf" http://localhost:3000/api/upload
# list
curl -s http://localhost:3000/api/documents
# import a hand-made draft (no Claude needed) — replace 1 with the returned id
curl -s -X POST http://localhost:3000/api/documents/1/import -H 'Content-Type: application/json' \
  -d '{"project_name":"測試標案","case_number":"T-1","agency":"測試機關","amount":null,"payment_terms":null,"award_date":null,"deliverables":[{"name":"期末報告","due_date":"2026-12-31"}],"sla_terms":null,"warranty":null,"security_audit":null,"meetings":null}'
# confirm the deliverable became an event
curl -s "http://localhost:3000/api/events?month=2026-12"
```
Expected: upload returns `{id}`; import returns `{project_id, created_tasks:1, created_events:1, created_cards:1}`; the event query shows 期末報告.

- [ ] **Step 6: Commit**

```bash
git add src/app/api/upload src/app/api/documents
git commit -m "feat: API routes for upload, documents, parse (Claude), import"
```

---

## Task 7: Upload & Review UI

**Files:** `src/components/DocumentReview.tsx`, `src/app/upload/page.tsx`

- [ ] **Step 1: Create the review form component**

Create `src/components/DocumentReview.tsx`:
```typescript
'use client'

import { useState } from 'react'
import type { ParsedTender, Deliverable } from '@/types'

interface Props {
  initial: ParsedTender
  onImport: (draft: ParsedTender) => void
  importing: boolean
}

const SCALAR_FIELDS: { key: keyof ParsedTender; label: string }[] = [
  { key: 'project_name', label: '專案名稱' },
  { key: 'case_number', label: '案號' },
  { key: 'agency', label: '機關' },
  { key: 'amount', label: '採購金額' },
  { key: 'payment_terms', label: '付款條件' },
  { key: 'award_date', label: '決標日期' },
  { key: 'sla_terms', label: 'SLA 條款' },
  { key: 'warranty', label: '保固期' },
  { key: 'security_audit', label: '資安檢測' },
  { key: 'meetings', label: '定期會議' },
]

export default function DocumentReview({ initial, onImport, importing }: Props) {
  const [draft, setDraft] = useState<ParsedTender>(initial)

  const setScalar = (key: keyof ParsedTender, value: string) =>
    setDraft(d => ({ ...d, [key]: value === '' ? null : value }))

  const setDeliverable = (i: number, patch: Partial<Deliverable>) =>
    setDraft(d => ({ ...d, deliverables: d.deliverables.map((x, j) => j === i ? { ...x, ...patch } : x) }))

  const addDeliverable = () =>
    setDraft(d => ({ ...d, deliverables: [...d.deliverables, { name: '', due_date: null }] }))

  const removeDeliverable = (i: number) =>
    setDraft(d => ({ ...d, deliverables: d.deliverables.filter((_, j) => j !== i) }))

  return (
    <div className="max-w-2xl space-y-4">
      <div className="grid grid-cols-2 gap-3">
        {SCALAR_FIELDS.map(f => (
          <label key={f.key} className="text-xs text-slate-600">
            {f.label}
            <input
              value={(draft[f.key] as string | null) ?? ''}
              onChange={e => setScalar(f.key, e.target.value)}
              className="mt-1 w-full border border-slate-300 rounded px-2 py-1 text-sm text-slate-800"
            />
          </label>
        ))}
      </div>

      <div>
        <div className="flex items-center justify-between mb-1">
          <span className="text-sm font-medium text-slate-700">交付項目（將建立卡片 / 行事曆）</span>
          <button onClick={addDeliverable} className="text-xs text-blue-600">+ 新增</button>
        </div>
        <div className="space-y-2">
          {draft.deliverables.map((d, i) => (
            <div key={i} className="flex gap-2 items-center">
              <input
                value={d.name}
                placeholder="交付物名稱"
                onChange={e => setDeliverable(i, { name: e.target.value })}
                className="flex-1 border border-slate-300 rounded px-2 py-1 text-sm"
              />
              <input
                type="date"
                value={d.due_date ?? ''}
                onChange={e => setDeliverable(i, { due_date: e.target.value || null })}
                className="border border-slate-300 rounded px-2 py-1 text-sm"
              />
              <button onClick={() => removeDeliverable(i)} className="text-xs text-red-500">刪</button>
            </div>
          ))}
        </div>
      </div>

      <button
        onClick={() => onImport(draft)}
        disabled={importing}
        className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white rounded px-4 py-2 text-sm font-medium"
      >
        {importing ? '匯入中…' : '確認匯入（建立任務 / 行事曆 / 卡片）'}
      </button>
    </div>
  )
}
```

- [ ] **Step 2: Create the upload page**

Create `src/app/upload/page.tsx`:
```typescript
'use client'

import { useState } from 'react'
import DocumentReview from '@/components/DocumentReview'
import type { ParsedTender, ImportResult } from '@/types'

type Stage = 'idle' | 'uploading' | 'parsing' | 'review' | 'importing' | 'done' | 'error'

export default function UploadPage() {
  const [stage, setStage] = useState<Stage>('idle')
  const [docId, setDocId] = useState<number | null>(null)
  const [draft, setDraft] = useState<ParsedTender | null>(null)
  const [result, setResult] = useState<ImportResult | null>(null)
  const [error, setError] = useState('')

  async function onUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (!file) return
    setStage('uploading'); setError('')
    const fd = new FormData()
    fd.append('file', file)
    const up = await fetch('/api/upload', { method: 'POST', body: fd })
    if (!up.ok) { setError('上傳失敗'); setStage('error'); return }
    const { id } = await up.json()
    setDocId(id)

    setStage('parsing')
    const pr = await fetch(`/api/documents/${id}/parse`, { method: 'POST' })
    const body = await pr.json()
    if (!pr.ok) { setError(body.error ?? '解析失敗'); setStage('error'); return }
    setDraft(body.draft); setStage('review')
  }

  async function onImport(confirmed: ParsedTender) {
    if (docId === null) return
    setStage('importing')
    const r = await fetch(`/api/documents/${docId}/import`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(confirmed),
    })
    const body = await r.json()
    if (!r.ok) { setError('匯入失敗'); setStage('error'); return }
    setResult(body); setStage('done')
  }

  return (
    <div className="p-6">
      <h1 className="text-lg font-semibold text-slate-800 mb-4">文件上傳與解析</h1>

      {(stage === 'idle' || stage === 'uploading' || stage === 'parsing') && (
        <div>
          <input type="file" accept=".pdf,.docx" onChange={onUpload}
            className="text-sm" disabled={stage !== 'idle'} />
          {stage === 'uploading' && <p className="text-sm text-slate-500 mt-2">上傳中…</p>}
          {stage === 'parsing' && <p className="text-sm text-slate-500 mt-2">Claude 解析中…</p>}
        </div>
      )}

      {stage === 'review' && draft && (
        <DocumentReview initial={draft} onImport={onImport} importing={false} />
      )}
      {stage === 'importing' && <p className="text-sm text-slate-500">匯入中…</p>}

      {stage === 'done' && result && (
        <div className="text-sm text-green-700">
          ✓ 匯入完成：建立 {result.created_tasks} 個任務、{result.created_events} 個行事曆事件、
          {result.created_cards} 張看板卡片。
          <a href="/kanban" className="text-blue-600 ml-2">前往看板</a>
        </div>
      )}
      {stage === 'error' && <p className="text-sm text-red-600">⚠ {error}</p>}
    </div>
  )
}
```

- [ ] **Step 3: Verify in the browser**

With `npm run dev`, visit `http://localhost:3000/upload`. The sidebar already links here (📄 文件上傳). Without `CLAUDE_API_KEY` set, uploading shows the parse error clearly (expected). With the key set, upload a real tender PDF/Word → see the review form → edit → 確認匯入 → success message → /kanban shows the new cards.

- [ ] **Step 4: Commit**

```bash
git add src/components/DocumentReview.tsx src/app/upload/page.tsx
git commit -m "feat: upload + Claude parse + in-app review/edit + import UI"
```

---

## Task 8: End-to-End Verification + Phase 3 Wrap

**Files:** none (verification + final commit)

- [ ] **Step 1: Full test suite**

Run: `npm test`
Expected: all PASS (migrations-v2, documents, extract, claude, import + all prior).

- [ ] **Step 2: Import path e2e without Claude (proves the deterministic core)**

With `npm run dev` running, run the curl block from Task 6 Step 5 (upload a file, POST a hand-made draft to `/import`). Confirm the deliverable becomes a task + event + card, and that `/api/events?month=...` then `/kanban` reflect it. This verifies the whole write path independent of the API key.

- [ ] **Step 3: (Optional, needs key) Live Claude parse**

If `CLAUDE_API_KEY` is set in `.env.local`, upload a real tender PDF on `/upload` and confirm the review form is populated by Claude, then import. If no key, note that this step is skipped — the deterministic import path is already verified in Step 2.

- [ ] **Step 4: Production build**

Run: `npm run build`
Expected: compiles; route list includes `/upload`, `/api/upload`, `/api/documents`, `/api/documents/[id]`, `/api/documents/[id]/parse`, `/api/documents/[id]/import`.

- [ ] **Step 5: Final Phase 3 commit**

```bash
git add -A
git commit -m "test: Phase 3 e2e verification; upload → parse → review → import complete"
```

---

## Self-Review Checklist

**Spec coverage (spec v2 §4.4 + scope decisions):**

| Requirement | Covered by task |
|---|---|
| 上傳 PDF/Word → uploads/ | Task 6 (upload route) |
| 文字抽取（PDF/Word） | Task 3 (extract) |
| Claude 解析成結構化（僅 draft，D2） | Task 4 (claude, tool-use) |
| AI 不寫 DB；匯入為確定性程式碼 | Task 5 (import.ts, no Claude) |
| App 內預覽/修改（使用者選擇） | Task 7 (DocumentReview, upload page) |
| 確認後建立 tasks/events/cards | Task 5, verified Task 8 |
| 解析欄位（案號/金額/SLA/交付物…） | Task 4 (tool schema), Task 7 (form) |
| 最小揭露（只送文字 + 長度上限） | Task 4 (MAX_INPUT_CHARS, text only) |
| documents 狀態機（uploaded→parsed_draft→imported） | Task 1 (migration), Task 2 (queries) |
| Notion 寫入 | DEFERRED to Phase 4 (per user decision) |

**Placeholder scan:** none — every code step has complete code; verification steps give exact commands and expected output. OCR/scanned PDF and PII masking are explicitly scoped out with clear runtime errors/notes, not placeholders.

**Type consistency:**
- `ParsedTender` / `Deliverable` defined Task 1; produced by `normalizeTender`/`parseTenderText` (Task 4); consumed by `importTenderDraft` (Task 5), import route (Task 6), `DocumentReview`/upload page (Task 7). All use the same field names.
- `PmDocument` (incl. `parsed_json`, `imported_at`) defined Task 1; returned by documents queries (Task 2) and routes (Task 6).
- `ImportResult` defined Task 1; returned by `importTenderDraft` (Task 5) and import route (Task 6); rendered in upload page (Task 7).
- `createEvent` is called with `task_id` (Task 5) — matches the optional-`task_id` signature from Phase 2.
- `getOrCreateBoard` + `listColumns` + `createCard` + `createTask` + `appendAudit` signatures match Phase 2 definitions.

No gaps or naming mismatches found.

---

**Plan complete and saved to `knowledge-os/docs/superpowers/plans/2026-06-05-pm-suite-phase3.md`. Two execution options:**

**1. Subagent-Driven (recommended)** — Fresh subagent per task, two-stage review between tasks.

**2. Inline Execution** — Execute tasks in this session using executing-plans, with checkpoints.

Which approach?
