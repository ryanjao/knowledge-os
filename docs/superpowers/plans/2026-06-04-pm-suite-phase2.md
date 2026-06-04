# PM Suite Phase 2 — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a `tasks` master table (single source of truth) plus a Trello-style kanban board whose card moves propagate completion to the linked calendar events (decision D3).

**Architecture:** A versioned SQLite migration runner (`PRAGMA user_version`) evolves the Phase 1 schema in place — adding `tasks`, `audit_log`, sync-metadata columns, and `task_id` links on `cards`/`events`. Query modules wrap all DB access; moving a card into a "done" column runs one transaction that flips the linked task to `done` and sets its events' `is_completed = 1`. A client-side kanban page uses native HTML5 drag-and-drop and calls REST routes.

**Tech Stack:** Next.js 16, React 19, TypeScript, Tailwind v4, better-sqlite3, Vitest. No new dependencies (native HTML5 DnD).

**Project root:** `/Users/juiyujao/Projects/pm-suite/`
**Plans saved to:** `knowledge-os/docs/superpowers/plans/`
**Spec:** `knowledge-os/docs/superpowers/specs/2026-06-04-pm-suite-design.md` (v2, see §0 decisions + §5 data model)

---

## Context for the implementer (read first)

Phase 1 already shipped and is committed on `pm-suite` `main`. Relevant existing code:

- `src/lib/schema.ts` — `applySchema(db)`: idempotent `CREATE TABLE IF NOT EXISTS` for `settings, projects, boards, columns, cards, events, documents, parsed_fields`.
- `src/lib/db.ts` — `getDb()`: opens the local app-data SQLite (WAL, `foreign_keys = ON`), acquires a lock, calls `applySchema`. **You will add `runMigrations` here.**
- `src/lib/queries/{settings,projects,events}.ts` — query modules taking `db` as first arg.
- Tests live in `tests/lib/*.test.ts`; each opens `new Database(':memory:')` and calls `applySchema(db)` in `beforeEach`.
- Run a single test file: `npm test -- tests/lib/<name>.test.ts`. Run all: `npm test`.
- `foreign_keys` is ON in production (`getDb`) but **OFF by default** for raw `new Database(':memory:')` in tests. Where a test relies on `ON DELETE` behaviour, it must call `db.pragma('foreign_keys = ON')`. The propagation logic in this plan does NOT rely on FK cascades, so tests don't need it unless noted.

Phase 2 adds a migration layer on top of the Phase 1 baseline:
- A fresh DB: `applySchema` creates the baseline (user_version stays 0), then `runMigrations` applies version 1.
- An existing Phase 1 DB: baseline tables already present (`IF NOT EXISTS` no-ops), `runMigrations` applies version 1.

---

## File Map

```
src/types/index.ts                 ← MODIFY: add Task, Board, Column, Card, AuditEntry; add task_id to CalendarEvent
src/lib/migrations.ts              ← CREATE: runMigrations + column helpers + MIGRATIONS array
src/lib/db.ts                      ← MODIFY: call runMigrations(_db) after applySchema
src/lib/queries/tasks.ts           ← CREATE: createTask/getTask/listTasksForProject/setTaskStatus (propagation)
src/lib/queries/events.ts          ← MODIFY: createEvent inserts task_id (default null)
src/lib/queries/audit.ts           ← CREATE: appendAudit/listAudit
src/lib/queries/boards.ts          ← CREATE: getOrCreateBoard/ensureDefaultColumns
src/lib/queries/columns.ts         ← CREATE: list/create/rename/setDone/reorder/delete
src/lib/queries/cards.ts           ← CREATE: list/get/create/update/moveCard(propagation+audit)/delete
src/app/api/boards/route.ts        ← CREATE: GET board+columns+cards for a project (or global)
src/app/api/columns/route.ts       ← CREATE: POST create column
src/app/api/columns/[id]/route.ts  ← CREATE: PATCH rename/done/reorder, DELETE
src/app/api/cards/route.ts         ← CREATE: POST create card
src/app/api/cards/[id]/route.ts    ← CREATE: PATCH (move or edit), DELETE
src/app/api/tasks/route.ts         ← CREATE: GET ?project_id, POST create
src/components/KanbanBoard.tsx     ← CREATE: client board (columns, cards, DnD, filter, column mgmt)
src/app/kanban/page.tsx            ← CREATE: route page mounting KanbanBoard

tests/lib/migrations.test.ts       ← CREATE
tests/lib/tasks.test.ts            ← CREATE
tests/lib/audit.test.ts            ← CREATE
tests/lib/boards.test.ts           ← CREATE
tests/lib/columns.test.ts          ← CREATE
tests/lib/cards.test.ts            ← CREATE
tests/lib/events.test.ts           ← MODIFY: runMigrations in beforeEach + a task_id test
```

---

## Task 1: Types + Schema Migration

**Files:**
- Modify: `src/types/index.ts`
- Create: `src/lib/migrations.ts`
- Modify: `src/lib/db.ts`
- Create: `tests/lib/migrations.test.ts`

- [ ] **Step 1: Add the new types**

Replace the contents of `src/types/index.ts` with (keeps existing types, adds new ones + `task_id` on `CalendarEvent`):

```typescript
export interface Project {
  id: number
  name: string        // e.g. "高檢署-六大緝毒維護"
  client: string      // e.g. "高檢署"
  case_number: string
  color_tag: string   // hex color, e.g. "#34d399"
  status: 'active' | 'warranty' | 'maintenance' | 'closed'
  created_at: string
}

export interface CalendarEvent {
  id: number
  project_id: number | null
  task_id: number | null
  title: string
  event_type: 'document_delivery' | 'meeting' | 'sla_checkpoint' | 'payment' | 'security_audit'
  due_date: string    // ISO date "YYYY-MM-DD"
  recurrence_rule: string | null
  is_completed: number  // 0 or 1
}

export interface AppSetting {
  key: string
  value: string
}

export interface Task {
  id: number
  project_id: number | null
  title: string
  kind: 'deliverable' | 'issue' | 'meeting' | 'misc'
  status: 'open' | 'in_progress' | 'done'
  due_date: string | null
  completed_at: string | null
  created_at: string
}

export interface Board {
  id: number
  project_id: number | null  // null = global board
  title: string
}

export interface Column {
  id: number
  board_id: number
  title: string
  position: number
  is_done_column: number  // 0 or 1
}

export interface Card {
  id: number
  project_id: number | null
  task_id: number | null
  column_id: number
  title: string
  notes: string | null
  due_date: string | null
  target_platform: string | null
  created_at: string
  updated_at: string
}

export interface AuditEntry {
  id: number
  ts: string
  actor: string
  action: string
  entity_type: string
  entity_id: number | null
  detail: string | null
}
```

- [ ] **Step 2: Write the failing migration test**

Create `tests/lib/migrations.test.ts`:
```typescript
import { describe, it, expect, beforeEach, afterEach } from 'vitest'
import Database from 'better-sqlite3'
import { applySchema } from '@/lib/schema'
import { runMigrations } from '@/lib/migrations'

function tableNames(db: Database.Database): string[] {
  return (db.prepare("SELECT name FROM sqlite_master WHERE type='table'").all() as { name: string }[])
    .map(t => t.name)
}
function columnNames(db: Database.Database, table: string): string[] {
  return (db.prepare(`PRAGMA table_info(${table})`).all() as { name: string }[]).map(r => r.name)
}

describe('runMigrations', () => {
  let db: Database.Database

  beforeEach(() => {
    db = new Database(':memory:')
    applySchema(db)
  })

  afterEach(() => { db.close() })

  it('creates the tasks and audit_log tables', () => {
    runMigrations(db)
    const names = tableNames(db)
    expect(names).toContain('tasks')
    expect(names).toContain('audit_log')
  })

  it('adds the new columns to existing tables', () => {
    runMigrations(db)
    expect(columnNames(db, 'columns')).toContain('is_done_column')
    expect(columnNames(db, 'cards')).toContain('task_id')
    expect(columnNames(db, 'events')).toContain('task_id')
    expect(columnNames(db, 'projects')).toContain('notion_page_id')
    expect(columnNames(db, 'projects')).toContain('sync_status')
    expect(columnNames(db, 'documents')).toContain('status')
  })

  it('bumps user_version to the latest migration', () => {
    runMigrations(db)
    expect(db.pragma('user_version', { simple: true })).toBe(1)
  })

  it('is idempotent — running twice does not throw and stays at latest', () => {
    runMigrations(db)
    expect(() => runMigrations(db)).not.toThrow()
    expect(db.pragma('user_version', { simple: true })).toBe(1)
  })
})
```

- [ ] **Step 3: Run it to confirm failure**

Run: `npm test -- tests/lib/migrations.test.ts`
Expected: FAIL — "Cannot find package '@/lib/migrations'"

- [ ] **Step 4: Implement the migration runner**

Create `src/lib/migrations.ts`:
```typescript
import type Database from 'better-sqlite3'

export interface Migration {
  version: number
  up: (db: Database.Database) => void
}

function hasColumn(db: Database.Database, table: string, column: string): boolean {
  const rows = db.prepare(`PRAGMA table_info(${table})`).all() as { name: string }[]
  return rows.some(r => r.name === column)
}

// Guarded ADD COLUMN — safe to call even if the column already exists.
function addColumn(db: Database.Database, table: string, column: string, ddl: string): void {
  if (!hasColumn(db, table, column)) {
    db.exec(`ALTER TABLE ${table} ADD COLUMN ${ddl}`)
  }
}

export const MIGRATIONS: Migration[] = [
  {
    version: 1,
    up(db) {
      db.exec(`
        CREATE TABLE IF NOT EXISTS tasks (
          id           INTEGER PRIMARY KEY AUTOINCREMENT,
          project_id   INTEGER REFERENCES projects(id) ON DELETE CASCADE,
          title        TEXT NOT NULL,
          kind         TEXT NOT NULL DEFAULT 'misc'
                       CHECK(kind IN ('deliverable','issue','meeting','misc')),
          status       TEXT NOT NULL DEFAULT 'open'
                       CHECK(status IN ('open','in_progress','done')),
          due_date     TEXT,
          completed_at TEXT,
          created_at   TEXT NOT NULL DEFAULT (datetime('now','localtime'))
        );

        CREATE TABLE IF NOT EXISTS audit_log (
          id          INTEGER PRIMARY KEY AUTOINCREMENT,
          ts          TEXT NOT NULL DEFAULT (datetime('now','localtime')),
          actor       TEXT NOT NULL DEFAULT 'system',
          action      TEXT NOT NULL,
          entity_type TEXT NOT NULL,
          entity_id   INTEGER,
          detail      TEXT
        );
      `)

      // Kanban: mark which columns mean "done" so card moves can propagate.
      addColumn(db, 'columns', 'is_done_column',
        `is_done_column INTEGER NOT NULL DEFAULT 0 CHECK(is_done_column IN (0,1))`)

      // D3 links: a card and an event can both point at the same task.
      // (SQLite allows a foreign-key column in ADD COLUMN only with a NULL default.)
      addColumn(db, 'cards', 'task_id', `task_id INTEGER REFERENCES tasks(id) ON DELETE SET NULL`)
      addColumn(db, 'events', 'task_id', `task_id INTEGER REFERENCES tasks(id) ON DELETE SET NULL`)

      // D2 sync metadata (populated in later phases; schema-forward here).
      addColumn(db, 'projects', 'notion_page_id', `notion_page_id TEXT`)
      addColumn(db, 'projects', 'source_last_edited_time', `source_last_edited_time TEXT`)
      addColumn(db, 'projects', 'last_synced_at', `last_synced_at TEXT`)
      addColumn(db, 'projects', 'content_hash', `content_hash TEXT`)
      addColumn(db, 'projects', 'sync_status', `sync_status TEXT`)

      addColumn(db, 'documents', 'status', `status TEXT NOT NULL DEFAULT 'uploaded'`)
      addColumn(db, 'documents', 'source_last_edited_time', `source_last_edited_time TEXT`)
      addColumn(db, 'documents', 'last_synced_at', `last_synced_at TEXT`)
    },
  },
]

export function runMigrations(db: Database.Database): void {
  const current = db.pragma('user_version', { simple: true }) as number
  const pending = MIGRATIONS
    .filter(m => m.version > current)
    .sort((a, b) => a.version - b.version)

  for (const m of pending) {
    const tx = db.transaction(() => {
      m.up(db)
      db.pragma(`user_version = ${m.version}`)
    })
    tx()
  }
}
```

- [ ] **Step 5: Run the migration test to confirm it passes**

Run: `npm test -- tests/lib/migrations.test.ts`
Expected: PASS (4 tests)

- [ ] **Step 6: Wire migrations into getDb**

In `src/lib/db.ts`, add the import at the top alongside the schema import:
```typescript
import { applySchema } from './schema'
import { runMigrations } from './migrations'
```

Then, in `getDb()`, immediately after the existing `applySchema(_db)` line, add `runMigrations(_db)`:
```typescript
  _db.pragma('journal_mode = WAL')
  _db.pragma('foreign_keys = ON')
  applySchema(_db)
  runMigrations(_db)
  return _db
```

- [ ] **Step 7: Run the full suite (nothing else should break)**

Run: `npm test`
Expected: all existing tests still PASS plus the 4 new migration tests.

- [ ] **Step 8: Commit**

```bash
git add src/types/index.ts src/lib/migrations.ts src/lib/db.ts tests/lib/migrations.test.ts
git commit -m "feat: versioned schema migration — tasks, audit_log, task links, sync metadata"
```

---

## Task 2: Tasks Queries + Event Completion Propagation

**Files:**
- Create: `src/lib/queries/tasks.ts`
- Modify: `src/lib/queries/events.ts`
- Modify: `tests/lib/events.test.ts`
- Create: `tests/lib/tasks.test.ts`

- [ ] **Step 1: Update events.ts to store task_id**

In `src/lib/queries/events.ts`, replace the `createEvent` function (the `CreateEventInput` type now includes `task_id` because it's part of `CalendarEvent`):
```typescript
type CreateEventInput = Omit<CalendarEvent, 'id' | 'is_completed'>

export function createEvent(
  db: Database.Database,
  input: CreateEventInput
): number {
  const result = db.prepare(`
    INSERT INTO events (project_id, task_id, title, event_type, due_date, recurrence_rule)
    VALUES (@project_id, @task_id, @title, @event_type, @due_date, @recurrence_rule)
  `).run({ task_id: null, ...input })
  return result.lastInsertRowid as number
}
```
The `{ task_id: null, ...input }` default keeps existing callers that omit `task_id` working.

- [ ] **Step 2: Update the events test to run migrations**

In `tests/lib/events.test.ts`, add the migrations import and call it in `beforeEach` (the `task_id` column lives in the migration, not the baseline):
```typescript
import { runMigrations } from '@/lib/migrations'
```
Change the `beforeEach` body from:
```typescript
    db = new Database(':memory:')
    applySchema(db)
    projectId = createProject(db, {
```
to:
```typescript
    db = new Database(':memory:')
    applySchema(db)
    runMigrations(db)
    projectId = createProject(db, {
```

- [ ] **Step 3: Write the failing tasks test**

Create `tests/lib/tasks.test.ts`:
```typescript
import { describe, it, expect, beforeEach, afterEach } from 'vitest'
import Database from 'better-sqlite3'
import { applySchema } from '@/lib/schema'
import { runMigrations } from '@/lib/migrations'
import { createProject } from '@/lib/queries/projects'
import { createEvent, listEventsForMonth } from '@/lib/queries/events'
import { createTask, getTask, listTasksForProject, setTaskStatus } from '@/lib/queries/tasks'

describe('tasks queries + completion propagation', () => {
  let db: Database.Database
  let projectId: number

  beforeEach(() => {
    db = new Database(':memory:')
    applySchema(db)
    runMigrations(db)
    projectId = createProject(db, {
      name: '高檢署-維護', client: '高檢署',
      case_number: '1', color_tag: '#34d399', status: 'active',
    })
  })

  afterEach(() => { db.close() })

  it('creates a task with default status open and lists it', () => {
    const id = createTask(db, {
      project_id: projectId, title: '期末報告', kind: 'deliverable', due_date: '2026-06-30',
    })
    const tasks = listTasksForProject(db, projectId)
    expect(tasks).toHaveLength(1)
    expect(tasks[0].id).toBe(id)
    expect(tasks[0].status).toBe('open')
  })

  it('marking a task done completes its linked events', () => {
    const taskId = createTask(db, {
      project_id: projectId, title: '期末報告', kind: 'deliverable', due_date: '2026-06-30',
    })
    createEvent(db, {
      project_id: projectId, task_id: taskId, title: '期末報告截止',
      event_type: 'document_delivery', due_date: '2026-06-30', recurrence_rule: null,
    })
    expect(listEventsForMonth(db, '2026-06')).toHaveLength(1)

    setTaskStatus(db, taskId, 'done')

    expect(listEventsForMonth(db, '2026-06')).toHaveLength(0) // filtered by is_completed=0
    const t = getTask(db, taskId)!
    expect(t.status).toBe('done')
    expect(t.completed_at).not.toBeNull()
  })

  it('reverting a task to in_progress re-opens its events', () => {
    const taskId = createTask(db, {
      project_id: projectId, title: 'x', kind: 'deliverable', due_date: '2026-06-30',
    })
    createEvent(db, {
      project_id: projectId, task_id: taskId, title: 'x截止',
      event_type: 'document_delivery', due_date: '2026-06-30', recurrence_rule: null,
    })
    setTaskStatus(db, taskId, 'done')
    setTaskStatus(db, taskId, 'in_progress')

    expect(listEventsForMonth(db, '2026-06')).toHaveLength(1)
    expect(getTask(db, taskId)!.completed_at).toBeNull()
  })
})
```

- [ ] **Step 4: Run to confirm failure**

Run: `npm test -- tests/lib/tasks.test.ts`
Expected: FAIL — "Cannot find package '@/lib/queries/tasks'"

- [ ] **Step 5: Implement tasks.ts**

Create `src/lib/queries/tasks.ts`:
```typescript
import type Database from 'better-sqlite3'
import type { Task } from '@/types'

interface CreateTaskInput {
  project_id: number | null
  title: string
  kind: Task['kind']
  due_date: string | null
  status?: Task['status']
}

export function createTask(db: Database.Database, input: CreateTaskInput): number {
  const result = db.prepare(`
    INSERT INTO tasks (project_id, title, kind, status, due_date)
    VALUES (@project_id, @title, @kind, @status, @due_date)
  `).run({ status: 'open', ...input })
  return result.lastInsertRowid as number
}

export function getTask(db: Database.Database, id: number): Task | null {
  return (db.prepare('SELECT * FROM tasks WHERE id = ?').get(id) as Task | undefined) ?? null
}

export function listTasksForProject(db: Database.Database, projectId: number): Task[] {
  return db.prepare('SELECT * FROM tasks WHERE project_id = ? ORDER BY created_at DESC')
    .all(projectId) as Task[]
}

// Sets the task status and propagates completion to all linked events.
// Wrapped in a transaction; better-sqlite3 nests this safely (savepoint) when
// called from within another transaction (e.g. moveCard).
export function setTaskStatus(
  db: Database.Database,
  taskId: number,
  status: Task['status']
): void {
  const tx = db.transaction(() => {
    if (status === 'done') {
      db.prepare(`UPDATE tasks SET status = 'done', completed_at = datetime('now','localtime') WHERE id = ?`)
        .run(taskId)
      db.prepare('UPDATE events SET is_completed = 1 WHERE task_id = ?').run(taskId)
    } else {
      db.prepare('UPDATE tasks SET status = ?, completed_at = NULL WHERE id = ?')
        .run(status, taskId)
      db.prepare('UPDATE events SET is_completed = 0 WHERE task_id = ?').run(taskId)
    }
  })
  tx()
}
```

- [ ] **Step 6: Run tasks + events tests to confirm they pass**

Run: `npm test -- tests/lib/tasks.test.ts tests/lib/events.test.ts`
Expected: PASS (tasks: 3, events: original tests + still green)

- [ ] **Step 7: Commit**

```bash
git add src/lib/queries/tasks.ts src/lib/queries/events.ts tests/lib/tasks.test.ts tests/lib/events.test.ts
git commit -m "feat: tasks query layer with event completion propagation (D3)"
```

---

## Task 3: Audit Log Query Helper

**Files:**
- Create: `src/lib/queries/audit.ts`
- Create: `tests/lib/audit.test.ts`

- [ ] **Step 1: Write the failing audit test**

Create `tests/lib/audit.test.ts`:
```typescript
import { describe, it, expect, beforeEach, afterEach } from 'vitest'
import Database from 'better-sqlite3'
import { applySchema } from '@/lib/schema'
import { runMigrations } from '@/lib/migrations'
import { appendAudit, listAudit } from '@/lib/queries/audit'

describe('audit log', () => {
  let db: Database.Database

  beforeEach(() => {
    db = new Database(':memory:')
    applySchema(db)
    runMigrations(db)
  })

  afterEach(() => { db.close() })

  it('appends an entry with defaults and lists it newest-first', () => {
    appendAudit(db, { actor: 'user', action: 'task_done', entity_type: 'task', entity_id: 7, detail: 'x' })
    appendAudit(db, { actor: 'user', action: 'card_created', entity_type: 'card' })
    const entries = listAudit(db)
    expect(entries).toHaveLength(2)
    expect(entries[0].action).toBe('card_created')
    expect(entries[0].entity_id).toBeNull()   // default
    expect(entries[0].detail).toBeNull()      // default
    expect(entries[1].action).toBe('task_done')
    expect(entries[1].entity_id).toBe(7)
  })
})
```

- [ ] **Step 2: Run to confirm failure**

Run: `npm test -- tests/lib/audit.test.ts`
Expected: FAIL — "Cannot find package '@/lib/queries/audit'"

- [ ] **Step 3: Implement audit.ts**

Create `src/lib/queries/audit.ts`:
```typescript
import type Database from 'better-sqlite3'
import type { AuditEntry } from '@/types'

interface AppendAuditInput {
  actor: string
  action: string
  entity_type: string
  entity_id?: number | null
  detail?: string | null
}

export function appendAudit(db: Database.Database, entry: AppendAuditInput): number {
  const result = db.prepare(`
    INSERT INTO audit_log (actor, action, entity_type, entity_id, detail)
    VALUES (@actor, @action, @entity_type, @entity_id, @detail)
  `).run({ entity_id: null, detail: null, ...entry })
  return result.lastInsertRowid as number
}

export function listAudit(db: Database.Database, limit = 100): AuditEntry[] {
  return db.prepare('SELECT * FROM audit_log ORDER BY id DESC LIMIT ?').all(limit) as AuditEntry[]
}
```

- [ ] **Step 4: Run to confirm it passes**

Run: `npm test -- tests/lib/audit.test.ts`
Expected: PASS (1 test)

- [ ] **Step 5: Commit**

```bash
git add src/lib/queries/audit.ts tests/lib/audit.test.ts
git commit -m "feat: audit_log query helper"
```

---

## Task 4: Boards & Columns Queries

**Files:**
- Create: `src/lib/queries/boards.ts`
- Create: `src/lib/queries/columns.ts`
- Create: `tests/lib/boards.test.ts`
- Create: `tests/lib/columns.test.ts`

- [ ] **Step 1: Write the failing boards test**

Create `tests/lib/boards.test.ts`:
```typescript
import { describe, it, expect, beforeEach, afterEach } from 'vitest'
import Database from 'better-sqlite3'
import { applySchema } from '@/lib/schema'
import { runMigrations } from '@/lib/migrations'
import { getOrCreateBoard } from '@/lib/queries/boards'
import { listColumns } from '@/lib/queries/columns'

describe('boards queries', () => {
  let db: Database.Database

  beforeEach(() => {
    db = new Database(':memory:')
    applySchema(db)
    runMigrations(db)
  })

  afterEach(() => { db.close() })

  it('creates the global board once and seeds default columns', () => {
    const a = getOrCreateBoard(db, null)
    const b = getOrCreateBoard(db, null)
    expect(a.id).toBe(b.id)             // not duplicated
    expect(a.project_id).toBeNull()
    const cols = listColumns(db, a.id)
    expect(cols.map(c => c.title)).toEqual(['待處理', '處理中', '已完成未記錄', '已完成'])
    expect(cols.find(c => c.title === '已完成')!.is_done_column).toBe(1)
    expect(cols.find(c => c.title === '待處理')!.is_done_column).toBe(0)
  })

  it('creates a separate board per project', () => {
    const global = getOrCreateBoard(db, null)
    const proj = getOrCreateBoard(db, 5)
    expect(proj.id).not.toBe(global.id)
    expect(proj.project_id).toBe(5)
  })
})
```

- [ ] **Step 2: Write the failing columns test**

Create `tests/lib/columns.test.ts`:
```typescript
import { describe, it, expect, beforeEach, afterEach } from 'vitest'
import Database from 'better-sqlite3'
import { applySchema } from '@/lib/schema'
import { runMigrations } from '@/lib/migrations'
import { getOrCreateBoard } from '@/lib/queries/boards'
import {
  listColumns, createColumn, renameColumn, setColumnDone, reorderColumn, deleteColumn,
} from '@/lib/queries/columns'

describe('columns queries', () => {
  let db: Database.Database
  let boardId: number

  beforeEach(() => {
    db = new Database(':memory:')
    applySchema(db)
    runMigrations(db)
    boardId = getOrCreateBoard(db, null).id  // seeds 4 default columns
  })

  afterEach(() => { db.close() })

  it('appends a new column at the end', () => {
    const id = createColumn(db, boardId, '處理中 緝毒')
    const cols = listColumns(db, boardId)
    expect(cols).toHaveLength(5)
    expect(cols[cols.length - 1].id).toBe(id)
    expect(cols[cols.length - 1].position).toBe(4)
  })

  it('renames a column', () => {
    const [first] = listColumns(db, boardId)
    renameColumn(db, first.id, '收件匣')
    expect(listColumns(db, boardId)[0].title).toBe('收件匣')
  })

  it('toggles is_done_column', () => {
    const [first] = listColumns(db, boardId)
    setColumnDone(db, first.id, 1)
    expect(listColumns(db, boardId)[0].is_done_column).toBe(1)
  })

  it('reorders a column by position', () => {
    const cols = listColumns(db, boardId)
    const last = cols[cols.length - 1]
    reorderColumn(db, last.id, 0)
    expect(listColumns(db, boardId)[0].id).toBe(last.id)
  })

  it('deletes a column', () => {
    const id = createColumn(db, boardId, 'temp')
    deleteColumn(db, id)
    expect(listColumns(db, boardId).some(c => c.id === id)).toBe(false)
  })
})
```

- [ ] **Step 3: Run both to confirm failure**

Run: `npm test -- tests/lib/boards.test.ts tests/lib/columns.test.ts`
Expected: FAIL — "Cannot find package '@/lib/queries/boards'"

- [ ] **Step 4: Implement columns.ts**

Create `src/lib/queries/columns.ts`:
```typescript
import type Database from 'better-sqlite3'
import type { Column } from '@/types'

export function listColumns(db: Database.Database, boardId: number): Column[] {
  return db.prepare('SELECT * FROM columns WHERE board_id = ? ORDER BY position ASC, id ASC')
    .all(boardId) as Column[]
}

export function createColumn(
  db: Database.Database,
  boardId: number,
  title: string,
  isDone: 0 | 1 = 0
): number {
  const row = db.prepare('SELECT COALESCE(MAX(position), -1) AS m FROM columns WHERE board_id = ?')
    .get(boardId) as { m: number }
  const result = db.prepare(
    'INSERT INTO columns (board_id, title, position, is_done_column) VALUES (?, ?, ?, ?)'
  ).run(boardId, title, row.m + 1, isDone)
  return result.lastInsertRowid as number
}

export function renameColumn(db: Database.Database, id: number, title: string): void {
  db.prepare('UPDATE columns SET title = ? WHERE id = ?').run(title, id)
}

export function setColumnDone(db: Database.Database, id: number, isDone: 0 | 1): void {
  db.prepare('UPDATE columns SET is_done_column = ? WHERE id = ?').run(isDone, id)
}

export function reorderColumn(db: Database.Database, id: number, position: number): void {
  db.prepare('UPDATE columns SET position = ? WHERE id = ?').run(position, id)
}

export function deleteColumn(db: Database.Database, id: number): void {
  db.prepare('DELETE FROM columns WHERE id = ?').run(id)
}
```

- [ ] **Step 5: Implement boards.ts**

Create `src/lib/queries/boards.ts`:
```typescript
import type Database from 'better-sqlite3'
import type { Board } from '@/types'

const DEFAULT_COLUMNS: { title: string; isDone: 0 | 1 }[] = [
  { title: '待處理', isDone: 0 },
  { title: '處理中', isDone: 0 },
  { title: '已完成未記錄', isDone: 0 },
  { title: '已完成', isDone: 1 },
]

export function ensureDefaultColumns(db: Database.Database, boardId: number): void {
  const { n } = db.prepare('SELECT COUNT(*) AS n FROM columns WHERE board_id = ?')
    .get(boardId) as { n: number }
  if (n > 0) return
  const insert = db.prepare(
    'INSERT INTO columns (board_id, title, position, is_done_column) VALUES (?, ?, ?, ?)'
  )
  DEFAULT_COLUMNS.forEach((c, i) => insert.run(boardId, c.title, i, c.isDone))
}

export function getOrCreateBoard(db: Database.Database, projectId: number | null): Board {
  const existing = projectId === null
    ? db.prepare('SELECT * FROM boards WHERE project_id IS NULL').get()
    : db.prepare('SELECT * FROM boards WHERE project_id = ?').get(projectId)
  if (existing) return existing as Board

  const title = projectId === null ? '全部' : '專案看板'
  const result = db.prepare('INSERT INTO boards (project_id, title) VALUES (?, ?)')
    .run(projectId, title)
  const id = result.lastInsertRowid as number
  ensureDefaultColumns(db, id)
  return { id, project_id: projectId, title }
}
```

- [ ] **Step 6: Run both to confirm they pass**

Run: `npm test -- tests/lib/boards.test.ts tests/lib/columns.test.ts`
Expected: PASS (boards: 2, columns: 5)

- [ ] **Step 7: Commit**

```bash
git add src/lib/queries/boards.ts src/lib/queries/columns.ts tests/lib/boards.test.ts tests/lib/columns.test.ts
git commit -m "feat: boards and columns query layer with default kanban columns"
```

---

## Task 5: Cards Queries (move + propagation + audit)

**Files:**
- Create: `src/lib/queries/cards.ts`
- Create: `tests/lib/cards.test.ts`

- [ ] **Step 1: Write the failing cards test**

Create `tests/lib/cards.test.ts`:
```typescript
import { describe, it, expect, beforeEach, afterEach } from 'vitest'
import Database from 'better-sqlite3'
import { applySchema } from '@/lib/schema'
import { runMigrations } from '@/lib/migrations'
import { createProject } from '@/lib/queries/projects'
import { createTask, getTask } from '@/lib/queries/tasks'
import { createEvent, listEventsForMonth } from '@/lib/queries/events'
import { getOrCreateBoard } from '@/lib/queries/boards'
import { listColumns } from '@/lib/queries/columns'
import { listAudit } from '@/lib/queries/audit'
import {
  listCardsForBoard, createCard, getCard, updateCard, moveCard, deleteCard,
} from '@/lib/queries/cards'

describe('cards queries', () => {
  let db: Database.Database
  let projectId: number
  let boardId: number
  let todoColId: number
  let doneColId: number

  beforeEach(() => {
    db = new Database(':memory:')
    applySchema(db)
    runMigrations(db)
    projectId = createProject(db, {
      name: '高檢署-維護', client: '高檢署',
      case_number: '1', color_tag: '#34d399', status: 'active',
    })
    boardId = getOrCreateBoard(db, null).id
    const cols = listColumns(db, boardId)
    todoColId = cols.find(c => c.title === '待處理')!.id
    doneColId = cols.find(c => c.title === '已完成')!.id
  })

  afterEach(() => { db.close() })

  it('creates and lists a card on the board', () => {
    const id = createCard(db, {
      project_id: projectId, task_id: null, column_id: todoColId,
      title: '撰寫期末報告', notes: null, due_date: null, target_platform: null,
    })
    const cards = listCardsForBoard(db, boardId)
    expect(cards).toHaveLength(1)
    expect(cards[0].id).toBe(id)
    expect(cards[0].title).toBe('撰寫期末報告')
  })

  it('updates a card title and notes', () => {
    const id = createCard(db, {
      project_id: projectId, task_id: null, column_id: todoColId,
      title: 'a', notes: null, due_date: null, target_platform: null,
    })
    updateCard(db, id, { title: 'b', notes: '記得附簽核單' })
    const c = getCard(db, id)!
    expect(c.title).toBe('b')
    expect(c.notes).toBe('記得附簽核單')
  })

  it('moving a card into the done column completes its task and events + writes audit', () => {
    const taskId = createTask(db, {
      project_id: projectId, title: '期末報告', kind: 'deliverable', due_date: '2026-06-30',
    })
    createEvent(db, {
      project_id: projectId, task_id: taskId, title: '期末報告截止',
      event_type: 'document_delivery', due_date: '2026-06-30', recurrence_rule: null,
    })
    const cardId = createCard(db, {
      project_id: projectId, task_id: taskId, column_id: todoColId,
      title: '撰寫期末報告', notes: null, due_date: null, target_platform: null,
    })

    moveCard(db, cardId, doneColId)

    expect(getCard(db, cardId)!.column_id).toBe(doneColId)
    expect(getTask(db, taskId)!.status).toBe('done')
    expect(listEventsForMonth(db, '2026-06')).toHaveLength(0)
    expect(listAudit(db).some(a => a.action === 'task_done' && a.entity_id === taskId)).toBe(true)
  })

  it('moving a card out of done re-opens its task and events', () => {
    const taskId = createTask(db, {
      project_id: projectId, title: 'x', kind: 'deliverable', due_date: '2026-06-30',
    })
    createEvent(db, {
      project_id: projectId, task_id: taskId, title: 'x截止',
      event_type: 'document_delivery', due_date: '2026-06-30', recurrence_rule: null,
    })
    const cardId = createCard(db, {
      project_id: projectId, task_id: taskId, column_id: doneColId,
      title: 'x', notes: null, due_date: null, target_platform: null,
    })
    moveCard(db, cardId, doneColId) // ensure done first
    moveCard(db, cardId, todoColId) // move back out

    expect(getTask(db, taskId)!.status).toBe('in_progress')
    expect(listEventsForMonth(db, '2026-06')).toHaveLength(1)
  })

  it('a card without a task can still be moved (no propagation)', () => {
    const cardId = createCard(db, {
      project_id: projectId, task_id: null, column_id: todoColId,
      title: '雜項', notes: null, due_date: null, target_platform: null,
    })
    expect(() => moveCard(db, cardId, doneColId)).not.toThrow()
    expect(getCard(db, cardId)!.column_id).toBe(doneColId)
  })

  it('deletes a card', () => {
    const id = createCard(db, {
      project_id: projectId, task_id: null, column_id: todoColId,
      title: 'temp', notes: null, due_date: null, target_platform: null,
    })
    deleteCard(db, id)
    expect(getCard(db, id)).toBeNull()
  })
})
```

- [ ] **Step 2: Run to confirm failure**

Run: `npm test -- tests/lib/cards.test.ts`
Expected: FAIL — "Cannot find package '@/lib/queries/cards'"

- [ ] **Step 3: Implement cards.ts**

Create `src/lib/queries/cards.ts`:
```typescript
import type Database from 'better-sqlite3'
import type { Card } from '@/types'
import { setTaskStatus } from './tasks'
import { appendAudit } from './audit'

interface CreateCardInput {
  project_id: number | null
  task_id: number | null
  column_id: number
  title: string
  notes: string | null
  due_date: string | null
  target_platform: string | null
}

type UpdateCardPatch = Partial<Pick<Card, 'title' | 'notes' | 'due_date' | 'target_platform' | 'project_id' | 'task_id'>>

export function listCardsForBoard(db: Database.Database, boardId: number): Card[] {
  return db.prepare(`
    SELECT c.* FROM cards c
    JOIN columns col ON col.id = c.column_id
    WHERE col.board_id = ?
    ORDER BY c.column_id ASC, c.updated_at DESC
  `).all(boardId) as Card[]
}

export function getCard(db: Database.Database, id: number): Card | null {
  return (db.prepare('SELECT * FROM cards WHERE id = ?').get(id) as Card | undefined) ?? null
}

export function createCard(db: Database.Database, input: CreateCardInput): number {
  const result = db.prepare(`
    INSERT INTO cards (project_id, task_id, column_id, title, notes, due_date, target_platform)
    VALUES (@project_id, @task_id, @column_id, @title, @notes, @due_date, @target_platform)
  `).run(input)
  return result.lastInsertRowid as number
}

export function updateCard(db: Database.Database, id: number, patch: UpdateCardPatch): void {
  const keys = Object.keys(patch)
  if (keys.length === 0) return
  const fields = keys.map(k => `${k} = @${k}`).join(', ')
  db.prepare(`UPDATE cards SET ${fields}, updated_at = datetime('now','localtime') WHERE id = @id`)
    .run({ ...patch, id })
}

// Move a card to another column. If the card is linked to a task, propagate:
// landing in a done column marks the task done (→ events completed); landing
// elsewhere re-opens it. The whole thing is one transaction.
export function moveCard(db: Database.Database, cardId: number, toColumnId: number): void {
  const tx = db.transaction(() => {
    db.prepare(`UPDATE cards SET column_id = ?, updated_at = datetime('now','localtime') WHERE id = ?`)
      .run(toColumnId, cardId)

    const card = getCard(db, cardId)
    const col = db.prepare('SELECT is_done_column FROM columns WHERE id = ?')
      .get(toColumnId) as { is_done_column: number } | undefined

    if (card?.task_id && col) {
      const newStatus = col.is_done_column ? 'done' : 'in_progress'
      setTaskStatus(db, card.task_id, newStatus)
      appendAudit(db, {
        actor: 'user',
        action: `task_${newStatus}`,
        entity_type: 'task',
        entity_id: card.task_id,
        detail: `card ${cardId} → column ${toColumnId}`,
      })
    }
  })
  tx()
}

export function deleteCard(db: Database.Database, id: number): void {
  db.prepare('DELETE FROM cards WHERE id = ?').run(id)
}
```

- [ ] **Step 4: Run to confirm it passes**

Run: `npm test -- tests/lib/cards.test.ts`
Expected: PASS (6 tests)

- [ ] **Step 5: Run the whole suite**

Run: `npm test`
Expected: all PASS.

- [ ] **Step 6: Commit**

```bash
git add src/lib/queries/cards.ts tests/lib/cards.test.ts
git commit -m "feat: cards query layer — move propagates task/event completion + audit (D3)"
```

---

## Task 6: API Routes

**Files:**
- Create: `src/app/api/boards/route.ts`
- Create: `src/app/api/tasks/route.ts`
- Create: `src/app/api/columns/route.ts`
- Create: `src/app/api/columns/[id]/route.ts`
- Create: `src/app/api/cards/route.ts`
- Create: `src/app/api/cards/[id]/route.ts`

- [ ] **Step 1: Boards route (board + columns + cards in one payload)**

Create `src/app/api/boards/route.ts`:
```typescript
import { NextResponse } from 'next/server'
import { getDb } from '@/lib/db'
import { getOrCreateBoard } from '@/lib/queries/boards'
import { listColumns } from '@/lib/queries/columns'
import { listCardsForBoard } from '@/lib/queries/cards'

// GET /api/boards            → global board (all projects)
// GET /api/boards?project_id=5 → that project's board
export async function GET(req: Request) {
  const db = getDb()
  const { searchParams } = new URL(req.url)
  const raw = searchParams.get('project_id')
  const projectId = raw === null || raw === '' ? null : Number(raw)

  const board = getOrCreateBoard(db, projectId)
  return NextResponse.json({
    board,
    columns: listColumns(db, board.id),
    cards: listCardsForBoard(db, board.id),
  })
}
```

- [ ] **Step 2: Tasks route**

Create `src/app/api/tasks/route.ts`:
```typescript
import { NextResponse } from 'next/server'
import { getDb } from '@/lib/db'
import { createTask, listTasksForProject } from '@/lib/queries/tasks'
import type { Task } from '@/types'

export async function GET(req: Request) {
  const db = getDb()
  const { searchParams } = new URL(req.url)
  const projectId = Number(searchParams.get('project_id'))
  if (!projectId) return NextResponse.json([])
  return NextResponse.json(listTasksForProject(db, projectId))
}

export async function POST(req: Request) {
  const db = getDb()
  const body = await req.json() as {
    project_id: number | null
    title: string
    kind: Task['kind']
    due_date: string | null
  }
  const id = createTask(db, body)
  return NextResponse.json({ id }, { status: 201 })
}
```

- [ ] **Step 3: Columns routes**

Create `src/app/api/columns/route.ts`:
```typescript
import { NextResponse } from 'next/server'
import { getDb } from '@/lib/db'
import { createColumn } from '@/lib/queries/columns'

export async function POST(req: Request) {
  const db = getDb()
  const body = await req.json() as { board_id: number; title: string; is_done_column?: 0 | 1 }
  const id = createColumn(db, body.board_id, body.title, body.is_done_column ?? 0)
  return NextResponse.json({ id }, { status: 201 })
}
```

Create `src/app/api/columns/[id]/route.ts`:
```typescript
import { NextResponse } from 'next/server'
import { getDb } from '@/lib/db'
import { renameColumn, setColumnDone, reorderColumn, deleteColumn } from '@/lib/queries/columns'

export async function PATCH(
  req: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  const db = getDb()
  const { id } = await params
  const colId = Number(id)
  const body = await req.json() as {
    title?: string
    is_done_column?: 0 | 1
    position?: number
  }
  if (body.title !== undefined) renameColumn(db, colId, body.title)
  if (body.is_done_column !== undefined) setColumnDone(db, colId, body.is_done_column)
  if (body.position !== undefined) reorderColumn(db, colId, body.position)
  return NextResponse.json({ ok: true })
}

export async function DELETE(
  _req: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  const db = getDb()
  const { id } = await params
  deleteColumn(db, Number(id))
  return NextResponse.json({ ok: true })
}
```

- [ ] **Step 4: Cards routes**

Create `src/app/api/cards/route.ts`:
```typescript
import { NextResponse } from 'next/server'
import { getDb } from '@/lib/db'
import { createCard } from '@/lib/queries/cards'

export async function POST(req: Request) {
  const db = getDb()
  const body = await req.json() as {
    project_id: number | null
    task_id: number | null
    column_id: number
    title: string
    notes: string | null
    due_date: string | null
    target_platform: string | null
  }
  const id = createCard(db, body)
  return NextResponse.json({ id }, { status: 201 })
}
```

Create `src/app/api/cards/[id]/route.ts`:
```typescript
import { NextResponse } from 'next/server'
import { getDb } from '@/lib/db'
import { moveCard, updateCard, deleteCard } from '@/lib/queries/cards'

// PATCH with { column_id } moves the card (triggers completion propagation);
// any other fields are treated as an edit.
export async function PATCH(
  req: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  const db = getDb()
  const { id } = await params
  const cardId = Number(id)
  const body = await req.json() as Record<string, unknown>

  if (typeof body.column_id === 'number') {
    moveCard(db, cardId, body.column_id)
  }
  const { column_id, ...edit } = body
  if (Object.keys(edit).length > 0) {
    updateCard(db, cardId, edit)
  }
  return NextResponse.json({ ok: true })
}

export async function DELETE(
  _req: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  const db = getDb()
  const { id } = await params
  deleteCard(db, Number(id))
  return NextResponse.json({ ok: true })
}
```

- [ ] **Step 5: Verify routes against a running server**

Start the dev server (uses the real local app-data DB):
```bash
npm run dev
```
In another terminal:
```bash
# create a project to attach cards to
curl -s -X POST http://localhost:3000/api/projects -H 'Content-Type: application/json' \
  -d '{"name":"高檢署-緝毒維護","client":"高檢署","case_number":"P2-1","color_tag":"#34d399","status":"active"}'

# global board with default columns
curl -s http://localhost:3000/api/boards

# create a card in the first column (use a column id from the previous response)
curl -s -X POST http://localhost:3000/api/cards -H 'Content-Type: application/json' \
  -d '{"project_id":1,"task_id":null,"column_id":1,"title":"撰寫期末報告","notes":null,"due_date":null,"target_platform":null}'

# move the card to another column id
curl -s -X PATCH http://localhost:3000/api/cards/1 -H 'Content-Type: application/json' \
  -d '{"column_id":4}'
```
Expected: board returns `{board, columns:[4 default], cards:[...]}`; card create returns `{id}`; move returns `{ok:true}`.

- [ ] **Step 6: Commit**

```bash
git add src/app/api/boards src/app/api/tasks src/app/api/columns src/app/api/cards
git commit -m "feat: REST API routes for boards, columns, cards, tasks"
```

---

## Task 7: Kanban Board UI

**Files:**
- Create: `src/components/KanbanBoard.tsx`
- Create: `src/app/kanban/page.tsx`

- [ ] **Step 1: Create the KanbanBoard component**

Create `src/components/KanbanBoard.tsx`:
```typescript
'use client'

import { useCallback, useEffect, useState } from 'react'
import type { Board, Column, Card, Project } from '@/types'

interface BoardPayload {
  board: Board
  columns: Column[]
  cards: Card[]
}

export default function KanbanBoard() {
  const [data, setData] = useState<BoardPayload | null>(null)
  const [projects, setProjects] = useState<Project[]>([])
  const [filterProject, setFilterProject] = useState<number | null>(null)
  const [dragCardId, setDragCardId] = useState<number | null>(null)

  const reload = useCallback(() => {
    fetch('/api/boards')
      .then(r => r.json())
      .then(setData)
      .catch(() => {})
  }, [])

  useEffect(() => { reload() }, [reload])
  useEffect(() => {
    fetch('/api/projects').then(r => r.json()).then(setProjects).catch(() => {})
  }, [])

  const projectById = (id: number | null) =>
    projects.find(p => p.id === id) ?? null

  async function addCard(columnId: number) {
    const title = window.prompt('卡片標題？')
    if (!title) return
    await fetch('/api/cards', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        project_id: filterProject,
        task_id: null,
        column_id: columnId,
        title,
        notes: null,
        due_date: null,
        target_platform: null,
      }),
    })
    reload()
  }

  async function addColumn() {
    if (!data) return
    const title = window.prompt('新欄位名稱？')
    if (!title) return
    await fetch('/api/columns', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ board_id: data.board.id, title }),
    })
    reload()
  }

  async function dropOnColumn(columnId: number) {
    if (dragCardId === null) return
    await fetch(`/api/cards/${dragCardId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ column_id: columnId }),
    })
    setDragCardId(null)
    reload()
  }

  if (!data) return <div className="p-6 text-slate-400 text-sm">載入中…</div>

  const visibleCards = (columnId: number) =>
    data.cards
      .filter(c => c.column_id === columnId)
      .filter(c => filterProject === null || c.project_id === filterProject)

  return (
    <div className="flex flex-col h-screen">
      {/* Filter bar */}
      <div className="flex items-center gap-2 px-4 py-2 border-b border-slate-200 bg-white flex-wrap shrink-0">
        <span className="text-xs font-semibold text-slate-600">看板</span>
        <button
          onClick={() => setFilterProject(null)}
          className={`text-xs px-2.5 py-1 rounded-full border ${
            filterProject === null
              ? 'bg-slate-800 text-white border-slate-800'
              : 'bg-white text-slate-600 border-slate-200'
          }`}
        >
          全部
        </button>
        {projects.map(p => (
          <button
            key={p.id}
            onClick={() => setFilterProject(p.id)}
            className={`text-xs px-2.5 py-1 rounded-full border flex items-center gap-1.5 ${
              filterProject === p.id
                ? 'text-white border-transparent'
                : 'bg-white text-slate-600 border-slate-200'
            }`}
            style={filterProject === p.id ? { background: p.color_tag } : undefined}
          >
            <span className="w-2 h-2 rounded-full" style={{ background: p.color_tag }} />
            {p.name}
          </button>
        ))}
        <button
          onClick={addColumn}
          className="ml-auto text-xs px-2.5 py-1 rounded-md border border-slate-200 text-slate-600 hover:bg-slate-50"
        >
          + 欄位
        </button>
      </div>

      {/* Columns */}
      <div className="flex-1 min-h-0 overflow-x-auto p-3 flex gap-3 items-start">
        {data.columns.map(col => (
          <div
            key={col.id}
            onDragOver={e => e.preventDefault()}
            onDrop={() => dropOnColumn(col.id)}
            className="w-64 shrink-0 bg-slate-100 rounded-lg flex flex-col max-h-full"
          >
            <div className="px-3 py-2 flex items-center justify-between">
              <span className="text-sm font-medium text-slate-700 flex items-center gap-1.5">
                {col.title}
                {col.is_done_column === 1 && <span title="完成欄">✓</span>}
              </span>
              <span className="text-xs text-slate-400">{visibleCards(col.id).length}</span>
            </div>

            <div className="flex-1 overflow-y-auto px-2 pb-2 flex flex-col gap-2">
              {visibleCards(col.id).map(card => {
                const proj = projectById(card.project_id)
                return (
                  <div
                    key={card.id}
                    draggable
                    onDragStart={() => setDragCardId(card.id)}
                    className="bg-white rounded-md shadow-sm border border-slate-200 p-2 cursor-grab active:cursor-grabbing"
                  >
                    {proj && (
                      <span
                        className="inline-block text-[10px] text-white px-1.5 py-0.5 rounded mb-1"
                        style={{ background: proj.color_tag }}
                      >
                        {proj.name}
                      </span>
                    )}
                    <div className="text-sm text-slate-800">{card.title}</div>
                    {card.due_date && (
                      <div className="text-[10px] text-slate-400 mt-1">截止 {card.due_date}</div>
                    )}
                  </div>
                )
              })}
            </div>

            <button
              onClick={() => addCard(col.id)}
              className="text-xs text-slate-500 hover:text-slate-700 px-3 py-2 text-left"
            >
              + 新增卡片
            </button>
          </div>
        ))}
      </div>
    </div>
  )
}
```

- [ ] **Step 2: Create the kanban page**

Create `src/app/kanban/page.tsx`:
```typescript
import KanbanBoard from '@/components/KanbanBoard'

export default function KanbanPage() {
  return <KanbanBoard />
}
```

- [ ] **Step 3: Verify in the browser**

With `npm run dev` running, visit `http://localhost:3000/kanban`. You should see four default columns (待處理 / 處理中 / 已完成未記錄 / 已完成 ✓). Add a card with "+ 新增卡片", drag it between columns, and confirm it sticks after the move (the list reloads from the server).

- [ ] **Step 4: Commit**

```bash
git add src/components/KanbanBoard.tsx src/app/kanban/page.tsx
git commit -m "feat: kanban board UI — columns, cards, native drag-and-drop, project filter"
```

---

## Task 8: End-to-End Completion Propagation Check + Phase 2 Wrap

**Files:** none (verification + final commit)

- [ ] **Step 1: Seed a linked task + event + card via API**

With `npm run dev` running (note the column ids from `GET /api/boards`; the done column is the one titled 已完成):
```bash
# create task
curl -s -X POST http://localhost:3000/api/tasks -H 'Content-Type: application/json' \
  -d '{"project_id":1,"title":"期末報告","kind":"deliverable","due_date":"2026-06-30"}'
# create the linked calendar event (use the task id returned above)
curl -s -X POST http://localhost:3000/api/events -H 'Content-Type: application/json' \
  -d '{"project_id":1,"task_id":1,"title":"期末報告截止","event_type":"document_delivery","due_date":"2026-06-30","recurrence_rule":null}'
# create the linked card in the 待處理 column (use its id)
curl -s -X POST http://localhost:3000/api/cards -H 'Content-Type: application/json' \
  -d '{"project_id":1,"task_id":1,"column_id":1,"title":"撰寫期末報告","notes":null,"due_date":null,"target_platform":null}'
```

- [ ] **Step 2: Confirm the event shows, then move the card to done, then confirm it disappears**

```bash
# before: event present
curl -s "http://localhost:3000/api/events?month=2026-06"
# move card (id 1) to the done column (use the 已完成 column id, e.g. 4)
curl -s -X PATCH http://localhost:3000/api/cards/1 -H 'Content-Type: application/json' -d '{"column_id":4}'
# after: event filtered out because its task is done
curl -s "http://localhost:3000/api/events?month=2026-06"
```
Expected: first call returns the event; after the move it returns `[]`. This proves D3 end-to-end: completing a kanban card clears the matching calendar deadline (and the home alert strip).

- [ ] **Step 3: Run the full test suite**

Run: `npm test`
Expected: all PASS.

- [ ] **Step 4: Production build**

Run: `npm run build`
Expected: compiles successfully; the route list includes `/kanban`, `/api/boards`, `/api/cards`, `/api/cards/[id]`, `/api/columns`, `/api/columns/[id]`, `/api/tasks`.

- [ ] **Step 5: Final Phase 2 commit**

```bash
git add -A
git commit -m "test: end-to-end D3 verification; Phase 2 complete"
```

---

## Self-Review Checklist

**Spec coverage (spec v2 §8 Phase 2 = schema migration + kanban):**

| Spec requirement | Covered by task |
|---|---|
| `tasks` master table (D3 single source of truth) | Task 1 (migration), Task 2 (queries) |
| sync metadata columns on projects/documents (D2, schema-forward) | Task 1 |
| `audit_log` table (D5) | Task 1 (schema), Task 3 (helper), Task 5 (first consumer) |
| `task_id` link on cards + events | Task 1 (columns), Task 2/5 (usage) |
| events/cards completion propagation (D3) | Task 2 (setTaskStatus), Task 5 (moveCard), Task 8 (e2e) |
| kanban default columns incl. 已完成未記錄 + 已完成 | Task 4 (ensureDefaultColumns) |
| kanban drag, project colour labels, filter, column mgmt | Task 6 (API), Task 7 (UI) |
| migration runs in place on existing Phase 1 DB | Task 1 (user_version, guarded ADD COLUMN), Task 1 Step 6 (getDb) |

**Placeholder scan:** none — every code step contains complete code; every verification step gives exact commands and expected output.

**Type consistency:**
- `Task` (project_id, title, kind, status, due_date, completed_at, created_at) — defined Task 1, used identically in tasks.ts (Task 2), cards.ts (Task 5), tasks route (Task 6).
- `Column.is_done_column: number` — defined Task 1; written by `setColumnDone`/`createColumn` (Task 4); read in `moveCard` (Task 5) and UI (Task 7).
- `Card` (incl. task_id, column_id) — defined Task 1; `createCard`/`moveCard`/`updateCard` signatures consistent (Task 5); UI uses `column_id`, `project_id`, `task_id`, `title`, `due_date` (Task 7).
- `CalendarEvent.task_id` added Task 1; `createEvent` updated to insert it Task 2; tests pass `task_id` consistently.
- `getOrCreateBoard(db, projectId|null)` returns `Board` — used by boards route (Task 6) and tests (Task 4). The global board is `project_id IS NULL`; the UI uses the global board (`GET /api/boards` with no param).
- `setTaskStatus(db, taskId, status)` — single definition (Task 2); called by `moveCard` (Task 5). Nested transaction note documented.

No gaps or naming mismatches found.

---

**Plan complete and saved to `knowledge-os/docs/superpowers/plans/2026-06-04-pm-suite-phase2.md`. Two execution options:**

**1. Subagent-Driven (recommended)** — Fresh subagent per task, two-stage review between tasks.

**2. Inline Execution** — Execute tasks in this session using executing-plans, with checkpoints.

Which approach?
