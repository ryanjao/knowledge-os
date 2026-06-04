---
uid: 01PMSUITE00000001
status: active
kind: dev_goal
project: pm-suite
stage: Build
method: [Next.js, SQLite, Claude-API, Notion-API, TDD]
phase_done: 1
phase_total: 6
mirror: true
source_date: 2026-06-04
---
# Goal：PM Suite — 政府標案專案管理系統

## 方法 Method
- Brainstorm → spec → writing-plans → TDD 實作（每 phase 一個 plan）
- Next.js + SQLite 本機，資料存 OneDrive/GDrive sync 資料夾
- Notion 為審閱介面（AI 解析草稿確認後才入庫）

## DoD
- Phase 1：基礎框架可跑（側邊欄 + 首頁月曆 + 告警條 + SQLite）
- Phase 2：看板（拖曳、標籤、欄位管理）
- Phase 3：文件上傳 + Claude API 解析 + Notion 寫入
- Phase 4：Notion 雙向同步（PM→Notion 自動推）
- Phase 5：Email 通知、資安提醒、定期月會自動建立
- Phase 6：多用戶登入

## 相關文件
- Spec（v2，含 ADR §0 五決策）：`docs/superpowers/specs/2026-06-04-pm-suite-design.md`
- Phase 1 計畫：`docs/superpowers/plans/2026-06-04-pm-suite-phase1.md`
- Phase 2 計畫：`docs/superpowers/plans/2026-06-04-pm-suite-phase2.md`
- 程式碼：`/Users/juiyujao/Projects/pm-suite/`（獨立 git repo，main）

## Stage Log
<!-- /km-review 由此 append [!progress] -->

> [!progress] stage=Build date=2026-06-04 goal=01PMSUITE00000001 seq=01
> did: 完成 Phase 1 全 9 task（TDD）：create-next-app（Next 16 + React 19 + Tailwind v4）、SQLite schema、settings/projects/events 查詢層、REST API、側邊欄、首頁 FullCalendar v6 月曆 + 告警橫條、首次設定流程。實際技術版本比設計新（Next 16 非 15、Tailwind v4 無 config 檔、FullCalendar v6 CSS 自動注入），已逐一適配。
> result: pm-suite repo（獨立 git，main）commits 6185859→58c2c5f；22 tests 綠、next build 綠。
> next: 依外部審查修正設計再進 Phase 2。

> [!progress] stage=Build date=2026-06-04 goal=01PMSUITE00000001 seq=02
> did: 兩輪外部審查後做 v2 止血 + 設計固化。止血：活的 SQLite 從雲端同步資料夾移到本機 OS app-data、加 lockfile 機器鎖、加 backup.ts + /api/backup 單檔快照、first-run 改「資料本機+選填備份資料夾」。spec 升 v2 寫入 ADR §0 鎖住五決策（D1 本機DB+快照、D2 Claude不寫DB、D3 tasks主表連動、D4 桌面化未來、D5 key不入DB+audit）。
> result: pm-suite commit ca47bdf（止血，22 tests 綠）；knowledge-os spec v2 commit 6f3cc18。修正審查 D4 誤判（better-sqlite3 跑 Node 後端，非瀏覽器沙箱）。
> next: 寫 Phase 2 計畫（schema migration + 看板）。

> [!progress] stage=Build date=2026-06-04 goal=01PMSUITE00000001 seq=03
> did: 寫 Phase 2 計畫（8 task，commit 18b4cb8）並 inline 執行至 Task 5。完成：版本化 migration runner（user_version + guarded ADD COLUMN，加 tasks/audit_log/task_id 連結/sync 中繼欄位）、tasks 查詢含事件完成連動（D3）、audit helper、boards/columns 查詢、cards 查詢（moveCard 拖到完成欄→task done→events is_completed=1 + 寫 audit）。
> result: pm-suite commits fda01d1→e529453；43 tests 綠。資料層 + D3 核心邏輯全部完成。Task 6-8（API routes、Kanban UI、端對端驗證）待做。
> next: 接 Phase 2 Task 6（建 boards/tasks/columns/cards API routes）→ Task 7 Kanban UI → Task 8 e2e。
