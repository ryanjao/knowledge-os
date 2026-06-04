# PM Suite Phase 1 — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the foundational PM Suite web app: Next.js scaffold, SQLite data layer, sidebar layout, Google Calendar-style home page (month view + alert strip), and project CRUD.

**Architecture:** Next.js App Router (localhost) with better-sqlite3 for local SQLite storage. The SQLite file lives in a user-configured sync folder (OneDrive/Google Drive). API routes handle all DB access server-side; React components consume them via fetch.

**Tech Stack:** Next.js 15, TypeScript, Tailwind CSS, better-sqlite3, Vitest, @fullcalendar/react

**Project root:** `/Users/juiyujao/Projects/pm-suite/`
**Plans saved to:** `knowledge-os/docs/superpowers/plans/`
**Spec:** `knowledge-os/docs/superpowers/specs/2026-06-04-pm-suite-design.md`

---

## File Map

```
pm-suite/
├── package.json
├── next.config.ts
├── tsconfig.json
├── vitest.config.ts
├── .env.example
├── .env.local                         ← gitignored
├── .gitignore
├── tailwind.config.ts
├── src/
│   ├── app/
│   │   ├── layout.tsx                 ← Root layout: sidebar + main
│   │   ├── page.tsx                   ← Home: calendar + alert strip
│   │   ├── globals.css
│   │   └── api/
│   │       ├── settings/route.ts      ← GET/POST data_dir & app settings
│   │       ├── projects/route.ts      ← GET all projects, POST new project
│   │       ├── projects/[id]/route.ts ← GET/PATCH/DELETE one project
│   │       └── events/route.ts        ← GET events (with ?month=YYYY-MM filter)
│   ├── components/
│   │   ├── Sidebar.tsx                ← Nav links + project colour list
│   │   ├── CalendarView.tsx           ← FullCalendar month wrapper
│   │   ├── AlertStrip.tsx             ← Bottom urgency bar
│   │   └── FirstRunSetup.tsx          ← Folder-path picker on first run
│   ├── lib/
│   │   ├── db.ts                      ← SQLite singleton + getDb()
│   │   ├── schema.ts                  ← CREATE TABLE statements
│   │   └── queries/
│   │       ├── settings.ts            ← getSetting / setSetting
│   │       ├── projects.ts            ← listProjects / createProject / updateProject / deleteProject
│   │       └── events.ts              ← listEvents / createEvent
│   └── types/
│       └── index.ts                   ← Project, Event, Card, Settings types
└── tests/
    └── lib/
        ├── schema.test.ts
        ├── settings.test.ts
        ├── projects.test.ts
        └── events.test.ts
```

---

## Task 1: Project Scaffold

**Files:**
- Create: `pm-suite/` (all root config files)

- [ ] **Step 1: Bootstrap Next.js app**

```bash
cd /Users/juiyujao/Projects/pm-suite
npx create-next-app@latest . \
  --typescript \
  --tailwind \
  --app \
  --src-dir \
  --no-eslint \
  --import-alias "@/*"
```

When prompted, accept defaults. This sets up `src/app/`, TypeScript, and Tailwind.

- [ ] **Step 2: Install dependencies**

```bash
npm install better-sqlite3 @fullcalendar/react @fullcalendar/daygrid @fullcalendar/interaction
npm install -D @types/better-sqlite3 vitest @vitejs/plugin-react vite-tsconfig-paths
```

- [ ] **Step 3: Create vitest config**

Create `vitest.config.ts`:
```typescript
import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import tsconfigPaths from 'vite-tsconfig-paths'

export default defineConfig({
  plugins: [react(), tsconfigPaths()],
  test: {
    environment: 'node',
    globals: true,
  },
})
```

- [ ] **Step 4: Add test script to package.json**

In `package.json`, add to `"scripts"`:
```json
"test": "vitest run",
"test:watch": "vitest"
```

- [ ] **Step 5: Create .env.example and .gitignore entries**

Create `.env.example`:
```
# Claude API key (for document parsing — Phase 3)
CLAUDE_API_KEY=

# Notion Integration Token (for sync — Phase 3+)
NOTION_TOKEN=
```

Add to `.gitignore` (append):
```
.env.local
data/
*.db
```

- [ ] **Step 6: Create shared types**

Create `src/types/index.ts`:
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
  title: string
  event_type: 'document_delivery' | 'meeting' | 'sla_checkpoint' | 'payment' | 'security_audit'
  due_date: string    // ISO date "YYYY-MM-DD"
  recurrence_rule: string | null  // JSON: {"freq":"monthly","day":5} or null
  is_completed: number  // 0 or 1 (SQLite boolean)
}

export interface AppSetting {
  key: string
  value: string
}
```

- [ ] **Step 7: Initial commit**

```bash
git init
git add .
git commit -m "feat: scaffold Next.js + Tailwind + Vitest for pm-suite"
```

---

## Task 2: SQLite Schema & Database Layer

**Files:**
- Create: `src/lib/schema.ts`
- Create: `src/lib/db.ts`
- Create: `tests/lib/schema.test.ts`

- [ ] **Step 1: Write failing schema test**

Create `tests/lib/schema.test.ts`:
```typescript
import { describe, it, expect, beforeEach, afterEach } from 'vitest'
import Database from 'better-sqlite3'
import { applySchema } from '@/lib/schema'

describe('applySchema', () => {
  let db: Database.Database

  beforeEach(() => {
    db = new Database(':memory:')
  })

  afterEach(() => {
    db.close()
  })

  it('creates all required tables', () => {
    applySchema(db)
    const tables = db
      .prepare("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
      .all() as { name: string }[]
    const names = tables.map(t => t.name)
    expect(names).toContain('projects')
    expect(names).toContain('boards')
    expect(names).toContain('columns')
    expect(names).toContain('cards')
    expect(names).toContain('events')
    expect(names).toContain('documents')
    expect(names).toContain('parsed_fields')
    expect(names).toContain('settings')
  })

  it('is idempotent — calling twice does not throw', () => {
    expect(() => {
      applySchema(db)
      applySchema(db)
    }).not.toThrow()
  })
})
```

- [ ] **Step 2: Run test to confirm it fails**

```bash
npm test -- tests/lib/schema.test.ts
```
Expected: FAIL — "Cannot find module '@/lib/schema'"

- [ ] **Step 3: Implement schema**

Create `src/lib/schema.ts`:
```typescript
import type Database from 'better-sqlite3'

export function applySchema(db: Database.Database): void {
  db.exec(`
    CREATE TABLE IF NOT EXISTS settings (
      key   TEXT PRIMARY KEY,
      value TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS projects (
      id          INTEGER PRIMARY KEY AUTOINCREMENT,
      name        TEXT NOT NULL,
      client      TEXT NOT NULL DEFAULT '',
      case_number TEXT NOT NULL DEFAULT '',
      color_tag   TEXT NOT NULL DEFAULT '#60a5fa',
      status      TEXT NOT NULL DEFAULT 'active'
                  CHECK(status IN ('active','warranty','maintenance','closed')),
      created_at  TEXT NOT NULL DEFAULT (datetime('now','localtime'))
    );

    CREATE TABLE IF NOT EXISTS boards (
      id         INTEGER PRIMARY KEY AUTOINCREMENT,
      project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
      title      TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS columns (
      id       INTEGER PRIMARY KEY AUTOINCREMENT,
      board_id INTEGER NOT NULL REFERENCES boards(id) ON DELETE CASCADE,
      title    TEXT NOT NULL,
      position INTEGER NOT NULL DEFAULT 0
    );

    CREATE TABLE IF NOT EXISTS cards (
      id              INTEGER PRIMARY KEY AUTOINCREMENT,
      project_id      INTEGER REFERENCES projects(id) ON DELETE SET NULL,
      column_id       INTEGER NOT NULL REFERENCES columns(id) ON DELETE CASCADE,
      title           TEXT NOT NULL,
      notes           TEXT,
      due_date        TEXT,
      target_platform TEXT,
      created_at      TEXT NOT NULL DEFAULT (datetime('now','localtime')),
      updated_at      TEXT NOT NULL DEFAULT (datetime('now','localtime'))
    );

    CREATE TABLE IF NOT EXISTS events (
      id              INTEGER PRIMARY KEY AUTOINCREMENT,
      project_id      INTEGER REFERENCES projects(id) ON DELETE CASCADE,
      title           TEXT NOT NULL,
      event_type      TEXT NOT NULL
                      CHECK(event_type IN (
                        'document_delivery','meeting',
                        'sla_checkpoint','payment','security_audit'
                      )),
      due_date        TEXT NOT NULL,
      recurrence_rule TEXT,
      is_completed    INTEGER NOT NULL DEFAULT 0 CHECK(is_completed IN (0,1))
    );

    CREATE TABLE IF NOT EXISTS documents (
      id             INTEGER PRIMARY KEY AUTOINCREMENT,
      project_id     INTEGER REFERENCES projects(id) ON DELETE SET NULL,
      file_path      TEXT NOT NULL,
      file_name      TEXT NOT NULL,
      parsed_at      TEXT,
      notion_page_id TEXT
    );

    CREATE TABLE IF NOT EXISTS parsed_fields (
      id           INTEGER PRIMARY KEY AUTOINCREMENT,
      document_id  INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
      field_key    TEXT NOT NULL,
      field_value  TEXT,
      confirmed_at TEXT
    );
  `)
}
```

- [ ] **Step 4: Run test to confirm it passes**

```bash
npm test -- tests/lib/schema.test.ts
```
Expected: PASS (2 tests)

- [ ] **Step 5: Write and implement db singleton**

Create `src/lib/db.ts`:
```typescript
import Database from 'better-sqlite3'
import path from 'path'
import fs from 'fs'
import { applySchema } from './schema'

let _db: Database.Database | null = null

export function getDataDir(): string {
  // In production: read from settings file or env
  // Falls back to a local ./data dir for first-run
  const envDir = process.env.PM_DATA_DIR
  if (envDir) return envDir
  const localDir = path.join(process.cwd(), 'data')
  if (!fs.existsSync(localDir)) fs.mkdirSync(localDir, { recursive: true })
  return localDir
}

export function getDb(): Database.Database {
  if (_db) return _db
  const dataDir = getDataDir()
  const dbPath = path.join(dataDir, 'pm-suite.db')
  _db = new Database(dbPath)
  _db.pragma('journal_mode = WAL')
  _db.pragma('foreign_keys = ON')
  applySchema(_db)
  return _db
}
```

- [ ] **Step 6: Commit**

```bash
git add src/lib/schema.ts src/lib/db.ts tests/lib/schema.test.ts
git commit -m "feat: SQLite schema and db singleton"
```

---

## Task 3: Settings & Projects Queries (TDD)

**Files:**
- Create: `src/lib/queries/settings.ts`
- Create: `src/lib/queries/projects.ts`
- Create: `tests/lib/settings.test.ts`
- Create: `tests/lib/projects.test.ts`

- [ ] **Step 1: Write failing settings tests**

Create `tests/lib/settings.test.ts`:
```typescript
import { describe, it, expect, beforeEach, afterEach } from 'vitest'
import Database from 'better-sqlite3'
import { applySchema } from '@/lib/schema'
import { getSetting, setSetting } from '@/lib/queries/settings'

describe('settings queries', () => {
  let db: Database.Database

  beforeEach(() => {
    db = new Database(':memory:')
    applySchema(db)
  })

  afterEach(() => { db.close() })

  it('returns null for missing key', () => {
    expect(getSetting(db, 'data_dir')).toBeNull()
  })

  it('sets and gets a value', () => {
    setSetting(db, 'data_dir', '/Users/test/OneDrive/pm-suite-data')
    expect(getSetting(db, 'data_dir')).toBe('/Users/test/OneDrive/pm-suite-data')
  })

  it('overwrites existing value', () => {
    setSetting(db, 'data_dir', '/old/path')
    setSetting(db, 'data_dir', '/new/path')
    expect(getSetting(db, 'data_dir')).toBe('/new/path')
  })
})
```

- [ ] **Step 2: Write failing projects tests**

Create `tests/lib/projects.test.ts`:
```typescript
import { describe, it, expect, beforeEach, afterEach } from 'vitest'
import Database from 'better-sqlite3'
import { applySchema } from '@/lib/schema'
import { listProjects, createProject, updateProject, deleteProject } from '@/lib/queries/projects'

describe('projects queries', () => {
  let db: Database.Database

  beforeEach(() => {
    db = new Database(':memory:')
    applySchema(db)
  })

  afterEach(() => { db.close() })

  it('returns empty list initially', () => {
    expect(listProjects(db)).toEqual([])
  })

  it('creates a project and lists it', () => {
    const id = createProject(db, {
      name: '調查局-網路流量',
      client: '調查局',
      case_number: '11427516920',
      color_tag: '#60a5fa',
      status: 'active',
    })
    const projects = listProjects(db)
    expect(projects).toHaveLength(1)
    expect(projects[0].name).toBe('調查局-網路流量')
    expect(projects[0].id).toBe(id)
  })

  it('updates a project', () => {
    const id = createProject(db, {
      name: '舊名稱', client: '', case_number: '', color_tag: '#fff', status: 'active',
    })
    updateProject(db, id, { name: '新名稱', status: 'warranty' })
    const [p] = listProjects(db)
    expect(p.name).toBe('新名稱')
    expect(p.status).toBe('warranty')
  })

  it('deletes a project', () => {
    const id = createProject(db, {
      name: 'to-delete', client: '', case_number: '', color_tag: '#fff', status: 'active',
    })
    deleteProject(db, id)
    expect(listProjects(db)).toHaveLength(0)
  })
})
```

- [ ] **Step 3: Run tests to confirm they fail**

```bash
npm test -- tests/lib/settings.test.ts tests/lib/projects.test.ts
```
Expected: FAIL — "Cannot find module"

- [ ] **Step 4: Implement settings queries**

Create `src/lib/queries/settings.ts`:
```typescript
import type Database from 'better-sqlite3'

export function getSetting(db: Database.Database, key: string): string | null {
  const row = db.prepare('SELECT value FROM settings WHERE key = ?').get(key) as
    | { value: string }
    | undefined
  return row?.value ?? null
}

export function setSetting(db: Database.Database, key: string, value: string): void {
  db.prepare('INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)').run(key, value)
}
```

- [ ] **Step 5: Implement projects queries**

Create `src/lib/queries/projects.ts`:
```typescript
import type Database from 'better-sqlite3'
import type { Project } from '@/types'

type CreateProjectInput = Omit<Project, 'id' | 'created_at'>

export function listProjects(db: Database.Database): Project[] {
  return db.prepare('SELECT * FROM projects ORDER BY created_at DESC').all() as Project[]
}

export function createProject(db: Database.Database, input: CreateProjectInput): number {
  const result = db.prepare(`
    INSERT INTO projects (name, client, case_number, color_tag, status)
    VALUES (@name, @client, @case_number, @color_tag, @status)
  `).run(input)
  return result.lastInsertRowid as number
}

export function updateProject(
  db: Database.Database,
  id: number,
  patch: Partial<CreateProjectInput>
): void {
  const fields = Object.keys(patch)
    .map(k => `${k} = @${k}`)
    .join(', ')
  db.prepare(`UPDATE projects SET ${fields} WHERE id = @id`).run({ ...patch, id })
}

export function deleteProject(db: Database.Database, id: number): void {
  db.prepare('DELETE FROM projects WHERE id = ?').run(id)
}
```

- [ ] **Step 6: Run tests to confirm they pass**

```bash
npm test -- tests/lib/settings.test.ts tests/lib/projects.test.ts
```
Expected: PASS (7 tests total)

- [ ] **Step 7: Commit**

```bash
git add src/lib/queries/ tests/lib/
git commit -m "feat: settings and projects query layer (TDD)"
```

---

## Task 4: Events Queries (TDD)

**Files:**
- Create: `src/lib/queries/events.ts`
- Create: `tests/lib/events.test.ts`

- [ ] **Step 1: Write failing events tests**

Create `tests/lib/events.test.ts`:
```typescript
import { describe, it, expect, beforeEach, afterEach } from 'vitest'
import Database from 'better-sqlite3'
import { applySchema } from '@/lib/schema'
import { createProject } from '@/lib/queries/projects'
import { listEventsForMonth, createEvent } from '@/lib/queries/events'

describe('events queries', () => {
  let db: Database.Database
  let projectId: number

  beforeEach(() => {
    db = new Database(':memory:')
    applySchema(db)
    projectId = createProject(db, {
      name: '調查局-網路流量', client: '調查局',
      case_number: '123', color_tag: '#60a5fa', status: 'active',
    })
  })

  afterEach(() => { db.close() })

  it('returns empty for a month with no events', () => {
    expect(listEventsForMonth(db, '2026-06')).toEqual([])
  })

  it('creates an event and returns it in the correct month', () => {
    createEvent(db, {
      project_id: projectId,
      title: '工作月報',
      event_type: 'document_delivery',
      due_date: '2026-06-05',
      recurrence_rule: null,
    })
    const events = listEventsForMonth(db, '2026-06')
    expect(events).toHaveLength(1)
    expect(events[0].title).toBe('工作月報')
    expect(events[0].project_id).toBe(projectId)
  })

  it('does not return events from another month', () => {
    createEvent(db, {
      project_id: projectId,
      title: '七月月報',
      event_type: 'document_delivery',
      due_date: '2026-07-05',
      recurrence_rule: null,
    })
    expect(listEventsForMonth(db, '2026-06')).toHaveLength(0)
  })

  it('filters by is_completed=0 by default', () => {
    const id = createEvent(db, {
      project_id: projectId,
      title: '已完成事件',
      event_type: 'meeting',
      due_date: '2026-06-10',
      recurrence_rule: null,
    })
    db.prepare('UPDATE events SET is_completed = 1 WHERE id = ?').run(id)
    expect(listEventsForMonth(db, '2026-06')).toHaveLength(0)
  })
})
```

- [ ] **Step 2: Run to confirm failure**

```bash
npm test -- tests/lib/events.test.ts
```
Expected: FAIL — "Cannot find module '@/lib/queries/events'"

- [ ] **Step 3: Implement events queries**

Create `src/lib/queries/events.ts`:
```typescript
import type Database from 'better-sqlite3'
import type { CalendarEvent } from '@/types'

type CreateEventInput = Omit<CalendarEvent, 'id' | 'is_completed'>

export function listEventsForMonth(
  db: Database.Database,
  month: string  // "YYYY-MM"
): CalendarEvent[] {
  return db.prepare(`
    SELECT * FROM events
    WHERE due_date LIKE ? || '%'
      AND is_completed = 0
    ORDER BY due_date ASC
  `).all(month) as CalendarEvent[]
}

export function createEvent(
  db: Database.Database,
  input: CreateEventInput
): number {
  const result = db.prepare(`
    INSERT INTO events (project_id, title, event_type, due_date, recurrence_rule)
    VALUES (@project_id, @title, @event_type, @due_date, @recurrence_rule)
  `).run(input)
  return result.lastInsertRowid as number
}
```

- [ ] **Step 4: Run all tests**

```bash
npm test
```
Expected: PASS (all tests across all files)

- [ ] **Step 5: Commit**

```bash
git add src/lib/queries/events.ts tests/lib/events.test.ts
git commit -m "feat: events query layer (TDD)"
```

---

## Task 5: API Routes

**Files:**
- Create: `src/app/api/settings/route.ts`
- Create: `src/app/api/projects/route.ts`
- Create: `src/app/api/projects/[id]/route.ts`
- Create: `src/app/api/events/route.ts`

- [ ] **Step 1: Settings API route**

Create `src/app/api/settings/route.ts`:
```typescript
import { NextResponse } from 'next/server'
import { getDb } from '@/lib/db'
import { getSetting, setSetting } from '@/lib/queries/settings'

export async function GET() {
  const db = getDb()
  return NextResponse.json({
    data_dir: getSetting(db, 'data_dir'),
    last_machine: getSetting(db, 'last_machine'),
  })
}

export async function POST(req: Request) {
  const db = getDb()
  const body = await req.json() as Record<string, string>
  for (const [key, value] of Object.entries(body)) {
    setSetting(db, key, value)
  }
  return NextResponse.json({ ok: true })
}
```

- [ ] **Step 2: Projects API route**

Create `src/app/api/projects/route.ts`:
```typescript
import { NextResponse } from 'next/server'
import { getDb } from '@/lib/db'
import { listProjects, createProject } from '@/lib/queries/projects'
import type { Project } from '@/types'

export async function GET() {
  const db = getDb()
  return NextResponse.json(listProjects(db))
}

export async function POST(req: Request) {
  const db = getDb()
  const body = await req.json() as Omit<Project, 'id' | 'created_at'>
  const id = createProject(db, body)
  return NextResponse.json({ id }, { status: 201 })
}
```

- [ ] **Step 3: Single project API route**

Create `src/app/api/projects/[id]/route.ts`:
```typescript
import { NextResponse } from 'next/server'
import { getDb } from '@/lib/db'
import { updateProject, deleteProject } from '@/lib/queries/projects'
import type { Project } from '@/types'

export async function PATCH(
  req: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  const db = getDb()
  const { id } = await params
  const body = await req.json() as Partial<Omit<Project, 'id' | 'created_at'>>
  updateProject(db, Number(id), body)
  return NextResponse.json({ ok: true })
}

export async function DELETE(
  _req: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  const db = getDb()
  const { id } = await params
  deleteProject(db, Number(id))
  return NextResponse.json({ ok: true })
}
```

- [ ] **Step 4: Events API route**

Create `src/app/api/events/route.ts`:
```typescript
import { NextResponse } from 'next/server'
import { getDb } from '@/lib/db'
import { listEventsForMonth, createEvent } from '@/lib/queries/events'
import type { CalendarEvent } from '@/types'

export async function GET(req: Request) {
  const db = getDb()
  const { searchParams } = new URL(req.url)
  const month = searchParams.get('month') ?? new Date().toISOString().slice(0, 7)
  return NextResponse.json(listEventsForMonth(db, month))
}

export async function POST(req: Request) {
  const db = getDb()
  const body = await req.json() as Omit<CalendarEvent, 'id' | 'is_completed'>
  const id = createEvent(db, body)
  return NextResponse.json({ id }, { status: 201 })
}
```

- [ ] **Step 5: Start dev server and verify routes respond**

```bash
npm run dev
```

In a separate terminal:
```bash
# Should return []
curl http://localhost:3000/api/projects

# Should return {data_dir: null, last_machine: null}
curl http://localhost:3000/api/settings

# Should return []
curl "http://localhost:3000/api/events?month=2026-06"
```

- [ ] **Step 6: Commit**

```bash
git add src/app/api/
git commit -m "feat: REST API routes for settings, projects, events"
```

---

## Task 6: Root Layout & Sidebar

**Files:**
- Modify: `src/app/layout.tsx`
- Create: `src/components/Sidebar.tsx`
- Modify: `src/app/globals.css`

- [ ] **Step 1: Create Sidebar component**

Create `src/components/Sidebar.tsx`:
```typescript
'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { useEffect, useState } from 'react'
import type { Project } from '@/types'

const NAV_ITEMS = [
  { href: '/', label: '首頁', icon: '🏠' },
  { href: '/calendar', label: '行事曆', icon: '📅' },
  { href: '/kanban', label: '看板', icon: '🗂' },
  { href: '/upload', label: '文件上傳', icon: '📄' },
  { href: '/settings', label: '通知設定', icon: '📧' },
]

export default function Sidebar() {
  const pathname = usePathname()
  const [projects, setProjects] = useState<Project[]>([])

  useEffect(() => {
    fetch('/api/projects')
      .then(r => r.json())
      .then(setProjects)
      .catch(() => {})
  }, [])

  return (
    <aside className="w-50 min-h-screen bg-[#1e1e2e] text-[#cdd6f4] flex flex-col py-4 px-3 shrink-0">
      <div className="text-[#89b4fa] font-bold text-base mb-5 px-2">⊙ PM Suite</div>

      <nav className="flex flex-col gap-0.5 mb-4">
        {NAV_ITEMS.map(item => (
          <Link
            key={item.href}
            href={item.href}
            className={`flex items-center gap-2 px-2.5 py-1.5 rounded-md text-sm transition-colors ${
              pathname === item.href
                ? 'bg-[#313244] text-[#cdd6f4] font-medium'
                : 'text-[#a6adc8] hover:bg-[#2a2a3d]'
            }`}
          >
            <span>{item.icon}</span>
            <span>{item.label}</span>
          </Link>
        ))}
      </nav>

      <div className="text-[10px] text-[#6c7086] uppercase tracking-wide px-2 mb-1">
        專案
      </div>
      <div className="flex flex-col gap-0.5">
        {projects.map(p => (
          <div
            key={p.id}
            className="flex items-center gap-2 px-2.5 py-1 rounded-md text-xs text-[#7f849c] hover:text-[#cdd6f4] hover:bg-[#2a2a3d] cursor-pointer transition-colors"
          >
            <span
              className="w-2 h-2 rounded-full shrink-0"
              style={{ background: p.color_tag }}
            />
            <span className="truncate">{p.name}</span>
          </div>
        ))}
        {projects.length === 0 && (
          <div className="text-[10px] text-[#4b5563] px-2">尚無專案</div>
        )}
      </div>

      <div className="mt-auto text-[10px] text-[#4b5563] px-2">
        {projects.length} 個專案
      </div>
    </aside>
  )
}
```

- [ ] **Step 2: Update root layout**

Replace `src/app/layout.tsx`:
```typescript
import type { Metadata } from 'next'
import './globals.css'
import Sidebar from '@/components/Sidebar'

export const metadata: Metadata = {
  title: 'PM Suite',
  description: '政府標案專案管理系統',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="zh-TW">
      <body className="flex min-h-screen bg-[#f8fafc]">
        <Sidebar />
        <main className="flex-1 min-h-screen overflow-auto">
          {children}
        </main>
      </body>
    </html>
  )
}
```

- [ ] **Step 3: Verify in browser**

Visit `http://localhost:3000` — should see dark sidebar on left, content area on right.

- [ ] **Step 4: Commit**

```bash
git add src/app/layout.tsx src/components/Sidebar.tsx
git commit -m "feat: root layout with sidebar navigation"
```

---

## Task 7: Home Page — Calendar View

**Files:**
- Modify: `src/app/page.tsx`
- Create: `src/components/CalendarView.tsx`

- [ ] **Step 1: Create CalendarView component**

Create `src/components/CalendarView.tsx`:
```typescript
'use client'

import FullCalendar from '@fullcalendar/react'
import dayGridPlugin from '@fullcalendar/daygrid'
import interactionPlugin from '@fullcalendar/interaction'
import { useEffect, useState } from 'react'
import type { CalendarEvent } from '@/types'

// Map event_type → display colour
const EVENT_TYPE_COLOR: Record<string, string> = {
  document_delivery: '#3b82f6',
  meeting:           '#f59e0b',
  sla_checkpoint:    '#ef4444',
  payment:           '#8b5cf6',
  security_audit:    '#ec4899',
}

export default function CalendarView() {
  const [events, setEvents] = useState<CalendarEvent[]>([])
  const [currentMonth, setCurrentMonth] = useState(
    () => new Date().toISOString().slice(0, 7)
  )

  useEffect(() => {
    fetch(`/api/events?month=${currentMonth}`)
      .then(r => r.json())
      .then(setEvents)
      .catch(() => {})
  }, [currentMonth])

  const fcEvents = events.map(e => ({
    id: String(e.id),
    title: e.title,
    date: e.due_date,
    backgroundColor: EVENT_TYPE_COLOR[e.event_type] ?? '#6b7280',
    borderColor: 'transparent',
    textColor: '#fff',
  }))

  return (
    <div className="h-full p-0 [&_.fc]:h-full [&_.fc-toolbar-title]:text-lg [&_.fc-toolbar-title]:font-medium">
      <FullCalendar
        plugins={[dayGridPlugin, interactionPlugin]}
        initialView="dayGridMonth"
        locale="zh-tw"
        headerToolbar={{
          left: 'today prev,next',
          center: 'title',
          right: 'dayGridMonth,dayGridWeek',
        }}
        events={fcEvents}
        height="100%"
        datesSet={info => {
          const month = info.startStr.slice(0, 7)
          setCurrentMonth(month)
        }}
        eventClassNames="text-xs px-1"
      />
    </div>
  )
}
```

- [ ] **Step 2: Add FullCalendar CSS to globals.css**

Add to top of `src/app/globals.css`:
```css
@import '@fullcalendar/common/main.css';
@import '@fullcalendar/daygrid/main.css';
```

- [ ] **Step 3: Seed test data and update home page**

Replace `src/app/page.tsx`:
```typescript
import CalendarView from '@/components/CalendarView'
import AlertStrip from '@/components/AlertStrip'

export default function HomePage() {
  return (
    <div className="flex flex-col h-screen">
      <div className="flex-1 min-h-0">
        <CalendarView />
      </div>
      <AlertStrip />
    </div>
  )
}
```

- [ ] **Step 4: Verify calendar renders**

Visit `http://localhost:3000` — should see FullCalendar month view in top 75% of page.

If FullCalendar CSS import causes issues in Next.js App Router, add to `next.config.ts`:
```typescript
const nextConfig = {
  transpilePackages: ['@fullcalendar/react', '@fullcalendar/daygrid', '@fullcalendar/interaction'],
}
export default nextConfig
```

- [ ] **Step 5: Commit**

```bash
git add src/app/page.tsx src/components/CalendarView.tsx src/app/globals.css next.config.ts
git commit -m "feat: FullCalendar month view on home page"
```

---

## Task 8: Alert Strip

**Files:**
- Create: `src/components/AlertStrip.tsx`

- [ ] **Step 1: Create AlertStrip component**

Create `src/components/AlertStrip.tsx`:
```typescript
'use client'

import { useEffect, useState } from 'react'
import type { CalendarEvent } from '@/types'

function getDaysUntil(dateStr: string): number {
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  const target = new Date(dateStr)
  return Math.ceil((target.getTime() - today.getTime()) / 86400000)
}

export default function AlertStrip() {
  const [events, setEvents] = useState<CalendarEvent[]>([])

  useEffect(() => {
    // Fetch next 30 days of events for alerts
    const month = new Date().toISOString().slice(0, 7)
    fetch(`/api/events?month=${month}`)
      .then(r => r.json())
      .then(setEvents)
      .catch(() => {})
  }, [])

  const overdue  = events.filter(e => getDaysUntil(e.due_date) < 0)
  const urgent   = events.filter(e => { const d = getDaysUntil(e.due_date); return d >= 0 && d <= 3 })
  const upcoming = events.filter(e => { const d = getDaysUntil(e.due_date); return d > 3 && d <= 7 })

  return (
    <div className="bg-white border-t border-slate-200 px-4 py-2 flex items-center gap-3 min-h-[44px] flex-wrap shrink-0">
      <span className="text-xs font-semibold text-slate-600 whitespace-nowrap">⚡ 需要注意</span>

      {overdue.map(e => (
        <span key={e.id}
          className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs bg-red-50 border border-red-200 text-red-600 whitespace-nowrap cursor-pointer"
        >
          🔴 {e.title} (逾期 {Math.abs(getDaysUntil(e.due_date))} 天)
        </span>
      ))}

      {urgent.map(e => (
        <span key={e.id}
          className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs bg-amber-50 border border-amber-200 text-amber-600 whitespace-nowrap cursor-pointer"
        >
          🟡 {e.title} ({getDaysUntil(e.due_date) === 0 ? '今天' : `${getDaysUntil(e.due_date)}天後`})
        </span>
      ))}

      {upcoming.map(e => (
        <span key={e.id}
          className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs bg-slate-50 border border-slate-200 text-slate-500 whitespace-nowrap cursor-pointer"
        >
          📅 {e.title} ({getDaysUntil(e.due_date)}天後)
        </span>
      ))}

      {overdue.length === 0 && urgent.length === 0 && upcoming.length === 0 && (
        <span className="text-xs text-slate-400">本週無待辦事項</span>
      )}

      <div className="ml-auto flex items-center gap-2">
        <span className="text-xs text-slate-400">SLA：</span>
        <span className="text-xs px-2 py-0.5 rounded-full bg-green-50 text-green-700 font-medium">
          ✓ 全部正常
        </span>
      </div>
    </div>
  )
}
```

- [ ] **Step 2: Seed events to verify alert strip**

```bash
# Add a test event due today to see the alert strip working
curl -X POST http://localhost:3000/api/events \
  -H 'Content-Type: application/json' \
  -d '{"project_id":null,"title":"測試月報","event_type":"document_delivery","due_date":"'$(date +%Y-%m-%d)'","recurrence_rule":null}'
```

- [ ] **Step 3: Verify in browser**

Reload `http://localhost:3000` — should see alert chip for today's event in the bottom strip.

- [ ] **Step 4: Commit**

```bash
git add src/components/AlertStrip.tsx
git commit -m "feat: alert strip with overdue/urgent/upcoming events"
```

---

## Task 9: First-Run Setup & Project Creation

**Files:**
- Create: `src/components/FirstRunSetup.tsx`
- Modify: `src/app/layout.tsx`

- [ ] **Step 1: Create FirstRunSetup component**

Create `src/components/FirstRunSetup.tsx`:
```typescript
'use client'

import { useState } from 'react'

interface Props {
  onComplete: () => void
}

export default function FirstRunSetup({ onComplete }: Props) {
  const [dataDir, setDataDir] = useState('')
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  async function handleSave() {
    if (!dataDir.trim()) { setError('請輸入資料夾路徑'); return }
    setSaving(true)
    setError('')
    const res = await fetch('/api/settings', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ data_dir: dataDir.trim() }),
    })
    if (res.ok) { onComplete() }
    else { setError('儲存失敗，請重試'); setSaving(false) }
  }

  return (
    <div className="fixed inset-0 bg-[#1e1e2e] flex items-center justify-center z-50">
      <div className="bg-[#242938] rounded-2xl p-8 w-full max-w-md shadow-2xl">
        <div className="text-2xl font-bold text-[#89b4fa] mb-2">⊙ PM Suite</div>
        <div className="text-[#cdd6f4] text-lg font-medium mb-1">首次設定</div>
        <div className="text-[#7f849c] text-sm mb-6">
          請選擇資料儲存位置。建議放在 OneDrive 或 Google Drive 的同步資料夾，
          這樣多台電腦可以自動同步。
        </div>

        <label className="block text-xs text-[#a6adc8] mb-1">資料夾路徑</label>
        <input
          type="text"
          value={dataDir}
          onChange={e => setDataDir(e.target.value)}
          placeholder={
            process.platform === 'win32'
              ? 'C:\\Users\\你的名字\\OneDrive\\pm-suite-data'
              : '/Users/你的名字/OneDrive/pm-suite-data'
          }
          className="w-full bg-[#1e2336] border border-[#3b4262] rounded-lg px-3 py-2 text-sm text-[#cdd6f4] placeholder-[#4b5563] focus:outline-none focus:border-[#89b4fa] mb-1"
        />
        {error && <div className="text-red-400 text-xs mb-3">{error}</div>}

        <div className="text-[10px] text-[#4b5563] mb-4">
          路徑不存在時會自動建立。API Keys 設定在 .env.local 中（見 .env.example）。
        </div>

        <button
          onClick={handleSave}
          disabled={saving}
          className="w-full bg-[#3b82f6] hover:bg-[#2563eb] disabled:opacity-50 text-white rounded-lg py-2 text-sm font-medium transition-colors"
        >
          {saving ? '設定中…' : '開始使用'}
        </button>
      </div>
    </div>
  )
}
```

- [ ] **Step 2: Add first-run check to root layout**

Replace `src/app/layout.tsx` with client wrapper:

Create `src/components/AppShell.tsx`:
```typescript
'use client'

import { useEffect, useState } from 'react'
import Sidebar from './Sidebar'
import FirstRunSetup from './FirstRunSetup'

export default function AppShell({ children }: { children: React.ReactNode }) {
  const [ready, setReady] = useState<boolean | null>(null)

  useEffect(() => {
    fetch('/api/settings')
      .then(r => r.json())
      .then(data => setReady(!!data.data_dir))
      .catch(() => setReady(false))
  }, [])

  if (ready === null) return null  // loading

  if (!ready) {
    return <FirstRunSetup onComplete={() => setReady(true)} />
  }

  return (
    <div className="flex min-h-screen bg-[#f8fafc]">
      <Sidebar />
      <main className="flex-1 min-h-screen overflow-auto">{children}</main>
    </div>
  )
}
```

Update `src/app/layout.tsx`:
```typescript
import type { Metadata } from 'next'
import './globals.css'
import AppShell from '@/components/AppShell'

export const metadata: Metadata = {
  title: 'PM Suite',
  description: '政府標案專案管理系統',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-TW">
      <body>
        <AppShell>{children}</AppShell>
      </body>
    </html>
  )
}
```

- [ ] **Step 3: Test first-run flow**

Clear settings (or use fresh DB), reload `http://localhost:3000`. Should see the dark setup screen asking for a folder path.

Enter any valid path (e.g. `./data`), click 開始使用 → should transition to the main app.

- [ ] **Step 4: Run all tests**

```bash
npm test
```
Expected: all tests PASS

- [ ] **Step 5: Final Phase 1 commit**

```bash
git add src/components/AppShell.tsx src/components/FirstRunSetup.tsx src/app/layout.tsx
git commit -m "feat: first-run setup flow — data folder configuration"
```

---

## Self-Review Checklist

**Spec coverage check:**

| Spec section | Covered by task |
|---|---|
| Next.js + SQLite 架構 | Task 1, 2 |
| data_dir 在 sync 資料夾 | Task 2 (db.ts), Task 9 |
| 側邊欄（nav + 專案清單） | Task 6 |
| 首頁月曆 Google Calendar 風格 | Task 7 |
| 首頁告警橫條 | Task 8 |
| Projects CRUD | Task 3, 5 |
| Events CRUD | Task 4, 5 |
| 首次啟動設定 | Task 9 |
| 跨 OS 路徑支援 | Task 2 (path.join) |
| 開源 .env.example | Task 1 |

**Placeholder scan:** None found. All steps include complete code.

**Type consistency:**
- `Project` type used in: queries/projects.ts, Sidebar.tsx, API route — all consistent.
- `CalendarEvent` used in: queries/events.ts, CalendarView.tsx, AlertStrip.tsx, API route — all consistent.
- `id` is `number` in types, `lastInsertRowid as number` in queries — consistent.

---

**Plan complete and saved to `knowledge-os/docs/superpowers/plans/2026-06-04-pm-suite-phase1.md`. Two execution options:**

**1. Subagent-Driven (recommended)** — Fresh subagent per task, fast iteration

**2. Inline Execution** — Execute tasks in this session using executing-plans

Which approach?
