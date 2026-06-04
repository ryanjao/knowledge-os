# PM Suite — 設計 Spec

- 日期：2026-06-04
- 專案代號：pm-suite
- 狀態：設計完成，待實作
- 作者：juiyujao + Claude Sonnet 4.6

---

## 1. 背景與目的

管理政府 IT 標案的 PM 工具。使用者（IT 承包商 PM）同時負責最多 8 個政府案件（調查局、刑事局、高檢署等），需要追蹤：文件交付時程、SLA 條款、定期月會、保固期、付款條件、問題處理。

現況以 Notion + Trello 手動管理，資訊分散、截止日靠記憶。本系統整合行事曆、看板、Notion 雙向同步、AI 文件解析，解決這個問題。

---

## 2. 核心設計原則

- **本機優先**：資料存在本機 SQLite，無需付費雲端 DB
- **Notion 為審閱介面**：AI 解析結果先進 Notion 由人工確認，確認後才寫入 PM DB
- **人工確認閘**：AI 只產生草稿，資料流每個關鍵節點都有人工審核
- **開源可安裝**：其他人 `git clone` + `npm install` + 設 `.env` 即可使用
- **桌面優先**：針對桌面瀏覽器設計，手機版 Phase 2+

---

## 3. 系統架構

### 3.1 技術棧

| 層次 | 技術 |
|------|------|
| 前端 | Next.js App Router（React）|
| 資料庫 | SQLite（`better-sqlite3`）|
| 文件儲存 | 本機資料夾（`/data/uploads/`）|
| AI 解析 | Claude API（`claude-sonnet-4-6`）|
| Notion 同步 | Notion REST API（直接呼叫）|
| Email 通知 | Nodemailer + SMTP（使用者自設）|
| 執行環境 | localhost（`npm run dev`）|

### 3.2 資料夾結構（使用者視角）

```
OneDrive 或 Google Drive（同步資料夾）
  └── pm-suite-data/
        ├── pm-suite.db          ← SQLite 資料庫
        └── uploads/             ← 上傳的標案文件

GitHub（開源 repo）
  └── pm-suite/
        ├── .env.local           ← API keys（gitignore）
        └── ...（程式碼）
```

App 首次啟動時選擇資料夾路徑，之後記住設定。支援 Windows 路徑（OneDrive）與 macOS 路徑（Google Drive）。

### 3.3 多機同步策略

- SQLite 單一檔案存在 OneDrive/Google Drive sync 資料夾
- 同一時間只在一台機器開 App（單用戶 PM，實際不會同時操作）
- App 啟動時顯示「上次開啟：[機器名] [時間]」，若非本機則提示確認
- 上傳的文件同樣在 sync 資料夾，跨機器可存取

---

## 4. 主要功能設計

### 4.1 主框架（Layout）

```
┌─────────────────────────────────────────────────────┐
│ Sidebar（200px）│ Main Content Area（flex: 1）       │
│                 │                                    │
│ Logo: PM Suite  │ [依當前路由顯示對應視圖]           │
│                 │                                    │
│ 🏠 首頁         │                                    │
│ 📅 行事曆       │                                    │
│ 🗂 看板          │                                    │
│ 📄 文件上傳     │                                    │
│ 📧 通知設定     │                                    │
│                 │                                    │
│ ── 專案清單 ──  │                                    │
│ ● 調查局-網路   │                                    │
│ ● 刑事局-幣流   │                                    │
│ ● 高檢署-維護   │                                    │
│ ● 高檢署-擴充   │                                    │
│ ● 高檢署-毒品DB │                                    │
│ …（最多 8 個）  │                                    │
└─────────────────────────────────────────────────────┘
```

側邊欄專案清單每個專案有顏色 dot（最多 8 種顏色），點擊可跳至該專案的篩選視圖。

### 4.2 首頁（Home View）

上方佔約 75% 高度：**Google Calendar 風格月曆**
- 月視圖為預設，支援切換週/日
- 事件直接顯示在格子內（不隱藏），以顏色標示所屬專案
- 事件類型：文件截止日、定期月會、SLA 到期日、付款節點
- 跨專案全部顯示，可按專案 filter

下方佔約 25% 高度：**告警橫條**
- 橫向排列 chip：逾期事項（紅）、即將到期 7 天內（黃）、SLA 狀態（綠/紅）
- 最右側：`SLA ✓ X/Y 正常` 總覽
- 點擊 chip 跳至對應事件或卡片

### 4.3 看板（Kanban）

設計原則：忠實還原使用者現有 Trello 習慣。

**欄位結構（預設）：**
- `待處理` — 尚未開始
- `處理中` — 正在進行
- `處理中 [專案名]`（可動態新增，用於專案衝刺期）
- `已完成未記錄` — 完成但尚未抄錄至 Redmine / 客戶監控平台
- `已完成` — 完全結束

**卡片設計：**
- 左上角彩色標籤：`[機關]-[案名]`（專案層級，非機關層級）
  - 例：`高檢署-六大緝毒維護`、`高檢署-六大緝毒擴充`（同機關不同案為不同顏色）
- 卡片標題：自由文字
- 可選：截止日、備註（`≡` icon 提示有備註）
- 無 SLA 倒數計時（實際工作不以此罰款）

**全板操作：**
- 右上角「↗ 同步至 Notion」：將所有卡片（含狀態）upsert 至 Notion 對應專案頁（依卡片 ID 比對，已存在則更新，不刪除 Notion 端手動新增的內容）
- 頂部 filter bar：按專案篩選
- 可手動新增欄位

**「已完成未記錄」欄位說明：**
- 用途：提醒 PM 這些完成事項還需要手動抄錄至 Redmine 或客戶端監控平台
- 與 Notion 同步無關
- 每張卡片顯示「待抄錄至 [平台名]」badge（可編輯平台名）

### 4.4 文件上傳與 AI 解析

**流程：**
```
PM 上傳 PDF 或 Word
  → 存至 uploads/ 資料夾
  → 呼叫 Claude API 解析
  → 結構化資料顯示於「解析預覽」頁面
  → PM 確認 / 修改後按「寫入 Notion」
  → 資料寫入 Notion 對應專案頁的子頁面
  → PM 在 Notion 確認無誤後按「確認回寫 PM 系統」
  → 資料正式寫入 SQLite（包含截止日自動建行事曆事件）
```

**AI 解析欄位（Claude API prompt 指定）：**

| 欄位 | 說明 |
|------|------|
| 專案名稱 | 標案名稱 |
| 案號 | 採購案號 |
| 機關名稱 | 主辦機關 |
| 採購金額 | 含幣別 |
| 付款條件 | 付款時程與方式 |
| 決標日期 | 計算相對截止日的基準 |
| 文件交付時程 | 每份文件名稱 + 截止日（決標後 N 天或絕對日期）|
| SLA 條款 | 各優先級處理時效（P1/P2/P3/P4）|
| 保固期 | 起訖日 |
| 資安檢測 | 相關時程與要求 |
| 定期會議 | 月會、維運會議等週期與規則 |

**解析後自動建立：**
- 行事曆事件：每個截止日、定期會議（依規則重複建立）
- 看板卡片：每份文件交付物自動建一張「待處理」卡片

### 4.5 Notion 雙向同步

```
方向一：文件解析 → Notion（首次，Claude 協助）
  AI 解析完 → 寫入 Notion 專案子頁面 → 人工確認

方向二：Notion → PM 系統（人工確認後，Claude 協助）
  PM 在 Notion 確認無誤 → 告知 Claude → Claude 讀 Notion → 寫入 SQLite

方向三：PM 系統 → Notion（日後更新，自動）
  PM 在 App 改資料 → Next.js API route 直接呼叫 Notion REST API

方向四：Notion 手動編輯 → PM 系統（Claude 協助）
  PM 在 Notion 改了 → 告知 Claude → Claude 讀 Notion 差異 → 更新 SQLite
```

**Notion 頁面結構（對應現有 Notion）：**
- 根頁面：`專案和任務`
- 每個專案：子頁面（現有的 `調查局 網路流量紀錄後端系統` 等）
- PM Suite 新增子頁面：`時程_驗收資訊`、`SLA`、`文件需求` 等（與現有結構一致）

### 4.6 Email / 通知

- 使用者在「通知設定」設定 SMTP（公司信箱或 Gmail SMTP）
- 觸發條件：文件截止 7 天前、3 天前、當天；月會前 1 天
- 通知內容：`[專案名] [文件名] 將於 [日期] 截止`
- **Phase 1 預設不啟用 Email**，僅首頁告警橫條提醒；使用者在「通知設定」填入 SMTP 後才啟用寄信

---

## 5. 資料模型（SQLite）

```sql
-- 專案
projects (id, name, client, case_number, color_tag, status, created_at)

-- 事件（行事曆）
events (id, project_id, title, event_type, due_date, recurrence_rule, is_completed)
-- event_type: document_delivery | meeting | sla_checkpoint | payment | security_audit
-- recurrence_rule: null（單次）或 JSON，例如 {"freq":"monthly","day":5}（每月5日）

-- 看板（每個專案一個看板，加上一個全域看板）
boards (id, project_id, title)
-- project_id: null 表示全域看板（首頁看板）

-- 看板欄位
columns (id, board_id, title, position)

-- 看板卡片
cards (id, project_id, column_id, title, notes, due_date, target_platform, created_at, updated_at)
-- target_platform: 「已完成未記錄」的目標平台名（Redmine 等）

-- 上傳文件
documents (id, project_id, file_path, file_name, parsed_at, notion_page_id)

-- 解析結果
parsed_fields (id, document_id, field_key, field_value, confirmed_at)

-- App 設定
settings (key, value)
-- 含：data_dir, last_opened_machine, notion_token, claude_api_key
```

---

## 6. 開源安裝流程

```bash
# 1. Clone
git clone https://github.com/<user>/pm-suite
cd pm-suite

# 2. 安裝依賴
npm install

# 3. 設定 API keys
cp .env.example .env.local
# 填入：CLAUDE_API_KEY, NOTION_TOKEN

# 4. 啟動
npm run dev
# → 瀏覽器開 http://localhost:3000
# → 首次啟動選擇資料資料夾（OneDrive/GDrive 下的資料夾）
```

**跨平台支援：**
- macOS：Google Drive 或 iCloud Drive
- Windows：OneDrive（公司電腦標配）
- 資料夾路徑存在 `settings` table，跨 OS 路徑格式自動處理

---

## 7. 分階段實作計畫（概要）

| Phase | 內容 |
|-------|------|
| Phase 1 | 基礎框架、SQLite 設定、側邊欄、首頁行事曆 + 告警條 |
| Phase 2 | 看板（拖曳、標籤、欄位管理）|
| Phase 3 | 文件上傳 + Claude API 解析 + Notion 寫入 |
| Phase 4 | Notion 雙向同步（PM→Notion 自動推）|
| Phase 5 | Email 通知、資安檢測提醒、定期會議自動建立 |
| Phase 6 | 登入系統（多用戶）|

---

## 8. 不在本次範圍

- 手機版 UI
- 多用戶登入（Phase 6）
- SLA 倒數計時與罰款計算
- Redmine 直接整合（「已完成未記錄」仍需手動抄錄）
- 離線 Claude API（需要網路）
