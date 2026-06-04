---
uid: 01KSESSIONWRAPLESSONS0001
status: verified
kind: note
title: "教訓集 Lessons（append-only）"
mirror: false
---

# 教訓集 Lessons

> Session Wrap 收尾捕捉、`/km-review` 核准後追加於此（append-only，不重排、不搬家）。
> 每筆對應一個 `[!lesson]`。彙整索引見 [[playbook]]。

<!-- /km-review 由此行下方往下 append [!lesson] callouts -->

> [!lesson] skill=test-driven-development stage=Build error=macos-bash3.2-multibyte
> what: reason 字串裡變數緊接中文（goal=$project。）在 macOS bash 3.2 觸發 unbound variable
> fix: 變數緊接非 ASCII 字元時用 ${project} 大括號界定
> rule: bash 腳本中變數後接中文/全形標點，一律用 ${var} 大括號

> [!lesson] skill=communication stage=Build error=language-drift
> what: 對話中途無故從繁體中文切成日文，使用者全程用繁中、repo 也是繁中
> fix: 改回繁體中文並承認無正當依據
> rule: 固定對齊使用者與 repo 的語言，勿無訊號漂移語言

> [!lesson] skill=writing-plans stage=Build error=dataview-callout-limitation
> what: 原設計 playbook=Dataview，但 Dataview 無法解析 callout 標頭屬性（> [!lesson] skill=... stage=...），無法 group-by
> fix: 改用 /km-review 維護的 append-only 索引檔（04_MOCs/playbook.md），貼合 spec §9 append-only 哲學
> rule: 規劃前先確認查詢層能否讀到資料形狀；callout 標頭屬性非 Dataview 可查

> [!lesson] skill=subagent-driven-development stage=Build error=tool-unavailable
> what: skill 假設可用 SendMessage 續派同一 subagent 修小問題，但本環境無此工具
> fix: 對 4 行測試這種瑣碎 review 修正，改由 controller 直接套用
> rule: 別假設 SendMessage 存在；瑣碎 review 修正 controller 直接做即可，不必為此另派 subagent

> [!lesson] skill=requesting-code-review stage=Build error=green-tests-false-confidence
> what: 驗證器 17 測試全綠，但 final review 仍抓到 parser 會把「相鄰、無空行分隔的第二個 callout」整個吞掉、完全不驗——等於死板鐵閘可被排版繞過
> fix: _parse_callouts body 迴圈遇到 CALLOUT_START_RE 即 break，並補回歸測試；最終 17 測試
> rule: 測試全綠≠無漏洞；對「宣稱死板的閘」一定要派獨立 review 找邊界繞過，別只信自己寫的測試覆蓋

> [!lesson] skill=mcp stage=Build error=mcp-needs-auth
> what: Claude Code 啟動時出現「⚠ 1 setup issue: MCP」警告，Supabase MCP server 已安裝但尚未完成 OAuth 授權，導致工具不可用。
> fix: 呼叫 `mcp__plugin_supabase_supabase__authenticate` 工具，取得 OAuth URL，使用者在瀏覽器完成授權後 MCP server 自動上線，所有 Supabase 工具變為可用。
> rule: 每次新 session 若看到 MCP setup 警告，優先觸發 authenticate 工具而非嘗試直接呼叫其他工具；/doctor 指令不一定會顯示 Connect 按鈕，需直接呼叫 authenticate。

> [!lesson] skill=system-design stage=Build error=sync-architecture
> what: 設計 PM 系統與 Notion 的同步時，初步想法是「PM 系統自動推送到 Notion」，但使用者指出中間的溝通是透過 Claude，懷疑無法自動推送。
> fix: 釐清 Notion REST API 是公開 API：Next.js API route 存 Notion token 後可直接呼叫，不需要 Claude 作為中介。只有「Notion 手動編輯→回寫 PM 系統」這條路需要 Claude 協助，其餘方向可全自動。
> rule: 設計雙向同步時先區分「哪些方向需要 AI 判斷」vs「哪些是純 API 呼叫」，後者不需要 Claude 介入，應設計為自動化。

> [!lesson] skill=data-modeling stage=Build error=missing-table
> what: 設計資料模型時，columns 表有 board_id 欄位但忘記定義 boards 表，造成 foreign key 懸空。
> fix: 自我審查時掃描所有外鍵，補上 boards 表並說明：project_id=null 表示全域看板（跨專案的主看板），有 project_id 表示專案專屬看板。
> rule: 寫資料模型後做外鍵完整性審查：每個 *_id 欄位都應對應一個已定義的表。

> [!lesson] skill=architecture stage=Build error=sqlite-on-cloud-sync
> what: v1 設計把活的 SQLite 單檔放 OneDrive/Google Drive 同步資料夾當多機同步方案；外部審查指出區塊級同步不懂 SQLite 交易/WAL 語意，會偶發靜默損毀並產生 `pm-suite (1).db` 衝突副本。
> fix: 活的 DB 改存本機 OS app-data（永不同步），WAL 留著（本機安全）；跨機改用 better-sqlite3 online backup 產單檔一致快照寫到備份資料夾（同步靜止快照才安全）；加 lockfile 擋多機/多進程同開。
> rule: 永遠不要把活的 SQLite/WAL 檔放雲端區塊級同步資料夾；要跨機就同步「靜止快照」或改用 sync-aware 後端（如 Turso），不要同步活檔。

> [!lesson] skill=architecture stage=Build error=llm-as-data-bus
> what: v1 讓 Claude 讀 Notion 頁面、比對差異後寫入 SQLite，等於把非確定性 LLM 當資料匯流排；結構化欄位（案號/金額/日期）可能因幻覺被錯誤覆寫，且每次同步耗 token、延遲高。
> fix: Claude 只在「文件→JSON draft」輸入端出現，永不寫 DB；Notion↔SQLite 同步全程式化欄對欄 upsert，以 notion_page_id/block_id 為穩定鍵，用 last_edited_time 做變更偵測（零 token）。
> rule: AI 只當一次性資料提取器（產 draft），不可當資料同步管道；所有結構化資料的 upsert 與差異比對一律走確定性程式碼 + 穩定外部 ID。

> [!lesson] skill=slash-command stage=Build error=wrong-skill-invocation
> what: 使用者輸入 "km-review"，Claude 誤呼叫 `init` skill（用於建立 CLAUDE.md），而非執行 `/km-review` slash command，導致短暫跑錯方向。
> fix: 發現 `/km-review` 是定義在 `.claude/commands/km-review.md` 的 slash command，非 skill；讀取該檔後直接依其步驟執行，不需透過 Skill 工具。
> rule: 使用者輸入形似 slash command（如 "km-review"、"km-sync"）時，先查 `.claude/commands/` 是否有對應 `.md`；有則直接讀取執行，無須呼叫 Skill 工具。
