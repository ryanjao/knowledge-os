---
uid: 01PMSUITE00000001
status: verified
kind: dev_goal
project: pm-suite
stage: Build
method: [Next.js, SQLite, Claude-API, Notion-API, TDD]
phase_done: 4
phase_total: 6
mirror: true
source_date: 2026-06-15
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

> [!progress] stage=Build date=2026-06-09 goal=01PMSUITE00000001 seq=04
> did: （Phase 2 Task6-8 + Phase 3 文件上傳/Claude解析/匯入已於先前 session 完成，commits 在 pm-suite repo；故 phase_done 由 1 修正為 3，反映 Phase 1-3 實際完成。）本趟工作三批，全在分支 feat/card-deadline-calendar：①修使用者功能測試發現的 4 個 bug（/calendar 與 /settings 缺頁 404、側邊欄專案是死 div、上傳裸 input）。②Feature A 卡片 Deadline×行事曆（完成、最終全功能審查 ready-to-merge）：行事曆合併「事件層 + 卡片層」，靠 task_id IS NULL 去重（匯入交付物走事件層、手動壓日期卡片走卡片層，不重複；維持 D2/D3 完成連動）；點日快速新增卡片；Trello 式卡片詳情 modal（編輯 deadline/專案/備註、刪除）。③Feature B 專案詳情抽屜 phase A（進行中 B1-B3/8）：migration v3 給 projects 加 10 資訊欄、解析器補聯絡人(name/email/phone)、getProject + applyProjectInfo（匯入時把過去被丟掉的解析資訊落地進專案）。執行法：superpowers subagent-driven（每任務 implementer→規格審查→程式碼品質審查，opus 做最終全功能審查）。
> result: commits 81ae143（bug fix）、e3213b6..f076463（Feature A，68 tests 綠）、0307c44..1957633（Feature B B1-B3，74 tests 綠）；tsc 全乾淨；尚未合併 main。Spec/plan 在 pm-suite repo docs/superpowers/（card-deadline-calendar、project-detail-drawer）。
> next: 完成 Feature B B4-B8（import 落地呼叫 applyProjectInfo、GET /api/projects/[id]、DocumentReview 聯絡人三欄、ProjectDetailDrawer 元件、Kanban ℹ詳情 鈕）→ 合併分支 → 再開 Feature B-phaseB（結構化付款/分期/請款里程碑，需改 AI 解析 schema）。

> [!progress] stage=Build date=2026-06-10 goal=01PMSUITE00000001 seq=05
> did: 完成 Feature B 剩餘（B4–B8，B7/B8 改為 ProjectInfoBar 常駐看板頂端而非抽屜）：applyProjectInfo 在 importTenderDraft 落地（B4）、GET /api/projects/[id]（B5）、DocumentReview 聯絡人三欄（B6）、ProjectInfoBar 可內聯編輯含得標日 date-input 與里程碑欄位（B7/B8）。卡片附件上傳/下載/刪除（migration v4 card_attachments）；行事曆改 4 週滾動視圖（前1週+後3週）＋/api/calendar 改 date range 查詢（listEventsForRange + listDatedCardsForRange）；AlertStrip 改呼叫 /api/alerts 同時涵蓋 events+cards 7 天到期；migration v5 加 milestone 欄位。feat/card-deadline-calendar（26 commits）fast-forward 合併 main（HEAD 33057f3），分支刪除。Notion Stage Log 同步寫入（UID 01PMSUITE00000001#2026-06-10#01）。
> result: pm-suite main HEAD 33057f3；migration v3–v5 落地；tsc 乾淨；_candidates/ 本次未產生。
> next: Phase 4：Notion 雙向同步（PM Suite 任務完成狀態推送至 Notion）；或先補 Phase 3 剩餘（Notion 寫入：匯入後把解析資料/任務推至 Notion）。

> [!progress] stage=Build date=2026-06-10 goal=01PMSUITE00000001 seq=06
> did: 完成 Phase 3 剩餘 — Notion 寫入（匯入後自動推送 + 手動重推 + sync badge）。新增 @notionhq/client；notion-sync.ts（buildPageProperties、buildPageBody、pushProjectToNotion，dependency-injected client 供測試，不用 module mock）；generateProjectSummary（Claude Haiku，無 key 時 fallback）；POST /api/projects/[id]/notion-push；import route 加 void pushProjectToNotion non-blocking；settings 頁加 Notion token 欄位；ProjectInfoBar 加 sync badge（synced/error/skipped/未推送）+ 推送 Notion 按鈕。Project type 補 notion_page_id/sync_status/last_synced_at/content_hash。migration version assertions 修正（v3→v5）。
> result: pm-suite main HEAD ea4e2a5；86 tests 綠；tsc 乾淨。Phase 3 全完成。
> next: Phase 4 Notion 雙向同步；或 Phase 3 補充（付款/分期/請款里程碑，需改 AI 解析 schema）。

> [!progress] stage=Build date=2026-06-12 goal=01PMSUITE00000001 seq=07
> did: UI/UX 全面升級（Lucide icons 取代 emoji、Tailwind v4 @theme 語義色票、可存取 Modal 元件 focus trap/Esc/aria-modal/動畫、告警條真實狀態計算 lib/alerts.ts、KanbanBoard 內聯表單取代 window.prompt、拖曳視覺回饋 dragOverColumnId）；結構化付款里程碑（AI 解析 schema 擴展 TENDER_TOOL、DB migration v7 TEXT JSON 欄位、parseProject 邊界反序列化、ProjectInfoBar read-only 表格）；多文件支援（ImportTarget auto/new/number、import API backward-compatible 雙格式、DocumentReview 匯入目標選單）；手動新增專案（NewProjectModal＋8 色色票、側欄 + 按鈕）。
> result: pm-suite main HEAD db9837a；commits 86d8f77→9361cec→db9837a；111 tests 綠；tsc 乾淨。KMOS+Notion 同步：補建缺漏 stage log #2026-06-09#01、#2026-06-10#02，goal phase_done 升至 3.9。
> next: Phase 4 Notion 雙向同步（任務完成狀態推 Notion）；或 SLA 到期追蹤（sla_terms 結構化）。

> [!progress] stage=Build date=2026-06-15 goal=01PMSUITE00000001 seq=08
> did: 用 taste-skill 對整個 pm-suite 前端做全面設計審查（讀遍 globals.css、layout、AppShell、Sidebar、Modal、KanbanBoard、CardDetail、ProjectInfoBar、AlertStrip、CalendarView、DocumentReview、FirstRunSetup、NewProjectModal 及四個 page），並用 grep 驗證跨檔一致性宣稱。
> result: 整體判定「品質高、非 AI-slop」，問題集中在跨畫面一致性漂移。確認 8 項問題（依嚴重度）：①FirstRunSetup 暗色與全站亮色不一致 ②儲存鍵雙色 ③focus:outline-none/無 focus-visible（WCAG 2.4.7）④emoji 與 Lucide 並存 ⑤--color-primary 被 blue-500 硬寫繞過 ⑥h-screen 應改 dvh ⑦CardDetail 仍用 window.confirm ⑧input 圓角漂移。
> next: 開分支實作 #1–#8 設計一致性修正。

> [!progress] stage=Build date=2026-06-15 goal=01PMSUITE00000001 seq=09
> did: 設計一致性收尾：taste-skill 審查抓出的 8 項，分兩批 #1–#4、#5–#8 各開分支實作驗證後合併 main（merge 87b1396、08f28a1）。啟動 Phase 4：brainstorm 釐清「雙向同步」實為「強化單向手動推送」，再因使用者貼真實標案資料改為「先修抽取再推送」。產出 spec（commit e576dec）+ 兩個 plan（commit 896a964），用 subagent-driven 執行 Plan 1（Part A+B 抽取強化）完成。
> result: main HEAD 08f28a1（含設計修正全部）。分支 feat/phase4-extraction-push Plan 1 完成：commits ccfc889→8de889d—TW假日表+loader、due-date resolver、claude TENDER_TOOL/prompt/normalize、parseProject/import 串接、summarizePayments。130 tests 綠、tsc/build 過。
> next: 同分支執行 Plan 2（Part C 推送）：付款里程碑入 Notion 內文+emoji→文字、一覽表加欄位、版本化 schema。

> [!progress] stage=Build date=2026-06-15 goal=01PMSUITE00000001 seq=10
> did: 完成 Phase 4 Plan 2（Notion 推送強化）— 4 tasks：付款里程碑 5 欄表格入 buildPageBody + emoji→文字；buildPageProperties 加 金額/得標日/里程碑/付款期數（summarizePayments）；DATA_SOURCE_PROPERTIES 拆成 BASE_PROPERTIES（非 select 可重送，版本 gate notion_projects_schema_version='2'）+ SELECT_PROPERTIES（建立時一次送）；stale comment 修正。
> result: 137 tests 全綠，tsc 乾淨，build 成功。commits 529cf15→41e4fe4（feat/phase4-extraction-push）。Phase 4 全完成，branch 待 push/PR。
> next: 建立 GitHub remote 並推 PR；tw-holidays.json 缺年度假日需每年補；Phase 5（Email 通知、資安提醒）或 SLA 追蹤。

> [!progress] stage=Build date=2026-06-05 goal=01PMSUITE00000001 seq=01
> did: inline 執行完成 Phase 2 Task 6-8：6 個 REST API routes（boards/tasks/columns/cards + [id]）、Kanban UI（KanbanBoard.tsx + /kanban，原生 HTML5 拖曳 + 專案彩色標籤 + 篩選 + 欄位管理）、端對端 D3 驗證。再寫好 Phase 3 計畫（8 task，upload + Claude 解析 + App 內審閱 + 確定性匯入；經使用者確認 scope：不含 Notion、留 Phase 4，審閱用 App 內預覽頁）。
> result: Phase 2 完成，commits 至 854c06a，44 tests 綠、build 綠；D3 端對端驗證通過（拖 task-linked 卡片到「已完成」→ task done → events.is_completed=1 → 首頁月曆/告警對應截止日消失）。Phase 3 計畫 commit bf743a3。
> next: 執行 Phase 3（inline 或 subagent）；Task 8 的 live Claude 解析需在 .env.local 設 CLAUDE_API_KEY，未設則 import 確定性路徑仍可完整驗證。

> [!progress] stage=Build date=2026-06-15 goal=01PMSUITE00000001 seq=11
> did: 執行 km-review（手動）：讀 knowledge-os 規則，整合本日 pm-suite candidates 寫入 SoT（phase_done 3.9→4，seq=08-10，+6 lessons）。建立 GitHub remote（ryanjao/pm-suite），推 feat/phase4-extraction-push，開 PR #1 並 merge，分支刪除。
> result: knowledge-os SoT 更新完畢（Phase 4 全記錄在案）。pm-suite GitHub repo 建立，main + Phase 4 commits 已在 GitHub。
> next: Phase 5（Email 通知、資安提醒）或 SLA 到期追蹤（sla_terms 結構化）；tw-holidays.json 每年需補官方假日。
