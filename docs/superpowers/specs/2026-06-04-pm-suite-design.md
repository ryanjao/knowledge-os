# PM Suite — 設計 Spec（v2）

- 日期：2026-06-04（v1）／2026-06-04 修訂（v2）
- 專案代號：pm-suite
- 狀態：設計 v2，Phase 1 已實作（含 v2 止血修正）
- 作者：juiyujao + Claude（v1: Sonnet 4.6；v2: Opus 4.8）

---

## 0. 架構決策紀錄（v2 修訂）

v1 設計經兩輪外部審查後，定案以下五項決策。本文件其餘章節已依此更新。

| # | 決策 | 取代 v1 的什麼 | 狀態 |
|---|------|----------------|------|
| D1 | **活的 SQLite 永不放雲端同步資料夾**；存本機 OS app-data，跨機改用「快照備份/還原」 | v1「SQLite 單檔放 OneDrive/GDrive 同步」 | ✅ 已實作（止血） |
| D2 | **Claude 永不寫入 SQLite**；只在「文件上傳→抽 JSON draft」出現。所有 Notion↔SQLite 同步走程式化欄對欄 upsert + 穩定 ID | v1「Claude 讀 Notion 差異寫入 SQLite」 | 待 Phase 3/4 |
| D3 | 新增 **`tasks` 主表**為單一事實來源；`events`/`cards` 連結之並連動完成狀態 | v1「events 與 cards 完全獨立」 | 待 Phase 2 |
| D4 | 桌面化（Tauri/Electron）列為**對外發佈**目標，非 Phase 1 blocker；現 Next.js（Node 後端）架構正確、可重用 | v1 未界定發佈形態 | 待未來 |
| D5 | **API key 不入 DB**（放 `.env.local`／OS credential store）；加 `audit_log`；資料處理指引寫進 README；at-rest 加密與 PII 遮罩標註延後 | v1「settings 表存 notion_token/claude_api_key」 | 部分已做 |

**被否決但記錄備查的選項：** Turso/LibSQL embedded replica 能根治多機同步，但引入雲端帳號、對「開源讓人下載」造成摩擦，故列為「未來若需無縫多機」的選項，非現階段解法。

---

## 1. 背景與目的

管理政府 IT 標案的 PM 工具。使用者（IT 承包商 PM）同時負責最多 8 個政府案件（調查局、刑事局、高檢署等），需要追蹤：文件交付時程、SLA 條款、定期月會、保固期、付款條件、問題處理。

現況以 Notion + Trello 手動管理，資訊分散、截止日靠記憶。本系統整合行事曆、看板、Notion 同步、AI 文件解析，解決這個問題。

---

## 2. 核心設計原則

- **本機優先且本機安全**：活的資料庫存在本機 OS app-data 的 SQLite，**不放雲端同步資料夾**；跨機透過快照備份/還原（D1）
- **Notion 為審閱介面**：AI 解析結果先進 Notion 由人工確認，確認後才寫入 PM DB
- **AI 只在輸入端**：Claude 只產 draft，永不直接寫入正式資料庫（D2）
- **人工確認閘**：資料流每個關鍵節點都有人工審核
- **開源可安裝**：其他人 `git clone` + `npm install` + 設 `.env.local` 即可使用
- **桌面優先**：針對桌面瀏覽器設計；未來以 Tauri/Electron 封裝為單鍵桌面 App（D4）

---

## 3. 系統架構

### 3.1 技術棧

| 層次 | 技術 |
|------|------|
| 前端 | Next.js App Router（React 19）|
| 後端 | Next.js API routes（**Node.js runtime**，非瀏覽器沙箱）|
| 資料庫 | SQLite（`better-sqlite3`），存本機 OS app-data |
| 文件儲存 | 本機資料夾（app-data 下 `/uploads/`）|
| AI 解析 | Claude API（`claude-sonnet-4-6`），僅文件→JSON |
| Notion 同步 | Notion REST API（程式化，直接呼叫）|
| Email 通知 | Nodemailer + SMTP（使用者自設）|
| 憑證儲存 | `.env.local`（API key）；不落地到 SQLite（D5）|
| 執行環境（現） | localhost（`npm run dev`）|
| 執行環境（未來） | Tauri/Electron 桌面封裝（D4）|

> **架構澄清（回應審查 D4）：** better-sqlite3 與所有檔案操作都在 Next.js 的 server-side（Node.js）執行，瀏覽器只是 UI。因此「選資料夾」只是存一個字串路徑、由 Node 讀寫，**不受瀏覽器沙箱限制**。現架構正確；桌面化僅為改善發佈與啟動體驗。

### 3.2 資料落點（v2）

```
本機 OS app-data（自動，不同步）
  macOS:   ~/Library/Application Support/pm-suite/
  Windows: %APPDATA%\pm-suite\
  Linux:   $XDG_DATA_HOME/pm-suite/
    ├── pm-suite.db          ← 活的 SQLite（WAL 模式，本機安全）
    ├── pm-suite.db-wal/-shm
    ├── pm-suite.lock        ← 機器鎖（machine/pid/opened_at）
    └── uploads/             ← 上傳的標案文件

備份資料夾（選填，可放 OneDrive/Google Drive）
  └── pm-suite-backups/
        └── pm-suite-backup-<timestamp>.db   ← 單檔快照（可安全同步）

GitHub（開源 repo）
  └── pm-suite/   ← 程式碼；.env.local（gitignore）放 API key
```

可用 `PM_DATA_DIR` 環境變數覆寫活的 DB 位置（測試/進階用）。

### 3.3 多機策略（v2，降級為備援）

v1 的「同步單一活檔」會因雲端區塊級同步損毀 SQLite/WAL 並產生衝突副本，已廢除。改為：

- **單主機操作**：同一時間僅一台機器寫入；`pm-suite.lock` 阻擋多機/多進程同時開啟（偵測 stale：同機看 pid 是否存活、跨機看時間戳逾 12h）
- **快照備份/還原**：以 better-sqlite3 online backup 產生**單檔一致快照**寫到備份資料夾（可放雲端網盤——同步靜止快照是安全的）
- **切換機器**：在 A 機備份 → 等雲端同步完成 → 在 B 機還原。非即時協作，是備援/搬機
- 未來若需無縫多機：評估 Turso embedded replica（見 §0 備查）

---

## 4. 主要功能設計

### 4.1 主框架（Layout）

```
┌─────────────────────────────────────────────────────┐
│ Sidebar（200px）│ Main Content Area（flex: 1）       │
│ Logo: PM Suite  │ [依當前路由顯示對應視圖]           │
│ 🏠 首頁         │                                    │
│ 📅 行事曆       │                                    │
│ 🗂 看板          │                                    │
│ 📄 文件上傳     │                                    │
│ 📧 通知設定     │                                    │
│ ── 專案清單 ──  │                                    │
│ ● 調查局-網路   │   （每專案彩色 dot，最多 8 個）   │
└─────────────────────────────────────────────────────┘
```

### 4.2 首頁（Home View）

- 上方約 75%：**Google Calendar 風格月曆**（事件直接顯示於格內、以顏色標所屬專案，類型：文件截止/月會/SLA/付款；可按專案 filter）
- 下方約 25%：**告警橫條**（逾期=紅、7 天內=黃、即將=灰；右側 SLA 總覽）

### 4.3 看板（Kanban）

忠實還原使用者現有 Trello 習慣。

- 預設欄位：`待處理`／`處理中`／`處理中 [專案名]`（可動態增）／`已完成未記錄`／`已完成`
- 卡片：左上彩色標籤 `[機關]-[案名]`（專案層級）；標題自由文字；可選截止日、備註；無 SLA 倒數
- 全板「↗ 同步至 Notion」：所有卡片依 ID upsert 至 Notion 對應頁（程式化，不刪 Notion 端手動內容）
- 「已完成未記錄」：提醒待手動抄錄至 Redmine/客戶監控平台，與 Notion 同步無關，每卡顯示「待抄錄至 [平台]」badge
- **完成狀態連動（D3）**：卡片拖到「已完成」欄時，後端事務同步將關聯 `tasks` 與其 `events.is_completed` 設為 1（見 §5）

### 4.4 文件上傳與 AI 解析

```
PM 上傳 PDF/Word
  → 存 uploads/
  → 呼叫 Claude API 解析成「結構化 JSON draft」（doc 狀態: parsed_draft）
  → 解析預覽頁；PM 確認/修改
  → 寫入 Notion 對應專案子頁（reviewed_in_notion）
  → PM 在 Notion 確認 → 按「匯入確認」（approved_for_import）
  → 程式化寫入 SQLite（imported_to_sqlite；自動建 tasks/events/cards）
```

**AI 解析欄位**：專案名稱、案號、機關、採購金額、付款條件、決標日期、文件交付時程（名稱+相對/絕對截止日）、SLA 條款、保固期、資安檢測、定期會議。

**重要（D2）**：Claude 的輸出一律是 draft JSON，**永不直接寫 DB**。「匯入確認」由 PM Suite 程式化寫入。

### 4.5 Notion 同步（v2，程式化 + 縮小範圍）

```
方向一：文件解析 → Notion（Claude 產 draft → 程式寫入 Notion → 人工確認）
方向二：Notion 確認 → PM 系統（PM 按「匯入確認」→ 程式讀 Notion → 寫 SQLite）
方向三：PM 系統 → Notion（PM 改資料 → API route 程式化 upsert Notion）
方向四：Notion 手動編輯 → PM 系統  ❌ Phase 1~3 不做（高風險，延後）
```

- **所有同步皆程式化**，以 `notion_page_id`/`block_id` 為穩定鍵做欄對欄 upsert
- 以 Notion API 的 `last_edited_time` 做變更偵測，只同步改過的頁（零 token 成本、低延遲）
- 同步物件帶中繼欄位：`notion_page_id`、`source_last_edited_time`、`last_synced_at`、`content_hash`、`sync_status`
- 文件解析流程為狀態機：`uploaded → parsed_draft → reviewed_in_notion → approved_for_import → imported_to_sqlite → synced_to_notion`（外加 `conflict_detected`）

**Notion 頁面結構**：根頁 `專案和任務`；每專案一子頁（沿用現有）；PM Suite 新增 `時程_驗收資訊`／`SLA`／`文件需求` 等子頁。

### 4.6 Email / 通知

- 「通知設定」設定 SMTP；觸發：文件截止 7/3/0 天前、月會前 1 天
- **Phase 1 預設不啟用 Email**，僅首頁告警橫條；填入 SMTP 後才啟用

---

## 5. 資料模型（SQLite，v2）

```sql
-- App 設定（不存任何 API key）
settings (key, value)
-- 含：setup_done, backup_dir, last_machine, data_dir(歷史保留)
-- 不含：notion_token / claude_api_key（改放 .env.local）

-- 專案
projects (id, name, client, case_number, color_tag, status, created_at,
          notion_page_id, source_last_edited_time, last_synced_at,
          content_hash, sync_status)

-- 任務主表（D3：單一事實來源）
tasks (id, project_id, title, kind, status, due_date, completed_at, created_at)
-- kind: deliverable | issue | meeting | misc
-- status: open | in_progress | done
-- events 與 cards 皆指向 task；完成狀態以此為準

-- 看板（每專案一看板 + 全域看板）
boards  (id, project_id, title)
columns (id, board_id, title, position, is_done_column)
cards   (id, project_id, task_id, column_id, title, notes, due_date,
         target_platform, created_at, updated_at)
-- task_id: 連結主表；拖到 is_done_column=1 的欄 → 事務更新 task.status='done'

-- 事件（行事曆）
events (id, project_id, task_id, title, event_type, due_date,
        recurrence_rule, is_completed)
-- task_id: 連結主表；task 完成時連動 is_completed=1

-- 上傳文件（狀態機）
documents (id, project_id, file_path, file_name, status, parsed_at,
           notion_page_id, source_last_edited_time, last_synced_at)
-- status: uploaded|parsed_draft|reviewed_in_notion|approved_for_import|
--         imported_to_sqlite|synced_to_notion|conflict_detected

-- 解析結果（人工修正可追蹤）
parsed_fields (id, document_id, field_key, field_value, confirmed_at, edited_by_human)

-- 稽核軌跡（D5）
audit_log (id, ts, actor, action, entity_type, entity_id, detail)
-- 記錄：送 AI、核准解析、寫 Notion、回寫 SQLite、人工改欄位
```

> Phase 1 已實作 `settings/projects/boards/columns/cards/events/documents/parsed_fields`。`tasks`、各表的 sync 中繼欄位、`audit_log`、`is_done_column`、`task_id` 連結為 **v2 新增，於 Phase 2 schema migration 加入**。

---

## 6. 安全與資料治理（v2 新增，D5）

- **API key 不落地 DB**：`.env.local`（gitignore）或 OS credential store；DB 僅記「是否已設定」
- **稽核軌跡**：所有外部同步與回寫保留 `audit_log`
- **資料處理指引（README）**：建議於公司受控裝置使用、同步至受控企業雲端、勿放機敏正本
- **AI 最小揭露**（Phase 3）：上傳可選頁面、敏感欄位遮罩後再送 Claude
- **at-rest 加密**（延後）：評估 SQLCipher 與備份加密；Phase 1~2 先以指引替代

---

## 7. 開源安裝流程

```bash
git clone https://github.com/<user>/pm-suite
cd pm-suite
npm install
cp .env.example .env.local   # 填 CLAUDE_API_KEY, NOTION_TOKEN
npm run dev                  # http://localhost:3000
# 首次啟動：資料自動存本機 app-data；可選填備份資料夾（OneDrive/GDrive）
```

跨平台：macOS（Google Drive/iCloud 當備份）、Windows（OneDrive）；活的 DB 一律在本機 app-data。

---

## 8. 分階段實作計畫

| Phase | 內容 | 狀態 |
|-------|------|------|
| Phase 1 | 框架、SQLite（本機）、側邊欄、首頁月曆 + 告警條；**+ v2 止血**（app-data/lock/快照備份） | ✅ 完成 |
| Phase 2 | schema migration（`tasks`/sync 中繼欄位/`audit_log`）+ 看板（拖曳、標籤、完成連動 D3） | 待做 |
| Phase 3 | 文件上傳 + Claude 解析（僅 JSON draft）+ 程式化寫 Notion；AI 最小揭露 | 待做 |
| Phase 4 | Notion 程式化同步（方向一二三）+ 衝突偵測；方向四仍不做 | 待做 |
| Phase 5 | Email 通知、資安提醒、定期月會自動建立 | 待做 |
| Phase 6 | 登入系統（多用戶）；評估 Tauri/Electron 桌面封裝（D4） | 待做 |

---

## 9. 不在本次範圍

- 手機版 UI
- 多用戶登入（Phase 6）
- SLA 倒數計時與罰款計算
- Redmine 直接整合（「已完成未記錄」仍手動抄錄）
- Notion 手動編輯自動回寫 PM（方向四，高風險，延後）
- 離線 Claude API（需網路）
