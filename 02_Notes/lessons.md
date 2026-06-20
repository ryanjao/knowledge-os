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

> [!lesson] skill=taste-skill stage=Build error=design-token-bypass
> what: 專案已在 globals.css `@theme` 定義 `--color-primary`（blue-600），但實際 UI 大量硬寫 `focus:border-blue-500`（13×）、`bg-slate-800` 當儲存鍵、`text-red-*`（~20×），導致「同一個動作不同顏色」的一致性破口——定義了 token 不等於用了 token。
> fix: 審查時用 grep 量化驗證（`grep -rohE "(text|bg|border)-(blue|red)-[0-9]+"` 統計頻率、`grep focus-visible | wc -l`），才抓出 primary 動作雙色與 focus ring 缺失。
> rule: review 設計一致性時，凡專案宣稱有 design token，一律 grep 原始色階 util 統計頻率對照 token 定義；token 存在 ≠ 一致，要量化證明而非目視。

> [!lesson] skill=taste-skill stage=Build error=zsh-glob-nomatch
> what: 在 Bash 工具跑 `grep -rn "x" --include=*.tsx .` 時 zsh 先把未加引號的 `*.tsx` 當 glob 展開，因 cwd 無相符檔而報 `no matches found`，整條指令未執行。
> fix: 把 glob 樣式加引號 `--include="*.tsx"`，交給 grep 自己解析而非 shell。
> rule: 在 zsh 下傳給工具（grep/find）的 glob 樣式一律加引號（`"*.tsx"`），避免 shell 搶先展開造成 no-match 中止。

> [!lesson] skill=subagent-driven-development stage=Build error=batch-must-end-green
> what: 原計畫把「型別變更」獨立成一個 task/batch，但改 PaymentMilestone/Deliverable 型別會立刻讓 claude.ts、projects.ts 與既有測試編譯失敗，直到後面 task 才修好——type-only 的 batch 無法收在綠燈。
> fix: 重新分批，讓每個 subagent batch 自成一個會綠的單元：型別變更要和它的所有 consumer 綁在同一 batch，結尾 tsc+vitest+build 全綠。
> rule: subagent-driven 分批時，每個 batch 必須能獨立收在綠燈；型別變更要和它的所有 consumer 綁在同一 batch，不可把 type 與用它的程式拆到不同 batch。

> [!lesson] skill=brainstorming stage=Build error=scope-word-ambiguity
> what: 目標卡寫「Phase 4 Notion 雙向同步」，但 Phase 3 其實已做完 PM→Notion 推送；直接照字面做會重工或誤做真雙向。使用者口頭「自動 vs 手動」也一度自相矛盾。
> fix: 先讀現有 notion-sync.ts 確認已實作範圍，再用單選逐題釐清；並請使用者貼真實資料，才發現真正缺口在「上游抽取（相對日期、保證金混入）」而非推送。
> rule: 接「下一階段」前先讀該領域既有程式確認實際完成度，別只信目標卡字面；範圍詞（雙向/同步/自動）一律向使用者單題確認，並盡量索取真實樣本資料驗證模型假設。

> [!lesson] skill=subagent-driven-development stage=Build error=schema-test-isolation
> what: 版本化 schema 的整合測試（Task 3）因卡片 path 也會呼叫 dataSources.update，若未提前 seed 卡片 schema settings，斷言「無 狀態 re-send」會被卡片 update call 污染。
> fix: 在 'existing install' test 手動 INSERT notion_cards_schema_ready='1' 與 notion_cards_view_grouped='1' 以隔離卡片路徑雜訊。
> rule: Notion 整合測試要斷言 dataSources.update 呼叫的 properties 內容時，必須把所有「其他路徑」的 schema update 也事先 gate 掉，否則斷言結果不可信。

> [!lesson] skill=subagent-driven-development stage=Build error=stale-comment
> what: Task 3 把 DATA_SOURCE_PROPERTIES 常數移除後，buildPageProperties 上方的 JSDoc 仍引用了已不存在的常數名稱，final reviewer 抓到。
> fix: 同 commit 修正 comment（chore: fix stale comment referencing removed DATA_SOURCE_PROPERTIES）。
> rule: 重命名或移除常數時，同步搜尋該名稱在 comment 中的出現，一併更新。

> [!lesson] skill=writing-plans stage=Build error=goal-card-missing-stagelog
> what: pm-suite 目標卡（writing-plans 階段建立）沒有 `## Stage Log` 區塊與 km-review marker，km-review approve 要把 [!progress] append 進去時無落點。
> fix: approve 時先 append 一個 `## Stage Log` 區塊 + `<!-- /km-review 由此 append [!progress] -->` marker 再寫 progress（屬 append，不違反只增不改的閘規）。
> rule: 建立 dev_goal 目標卡時就內建 `## Stage Log` 區塊與 km-review marker，讓後續 progress 有固定落點，避免 promotion 卡關。

> [!lesson] skill=system-design stage=Build error=stale-context-note
> what: km-sync 的 CONTEXT.md/README 路線圖寫「Phase 2b Notion 推送待做」，但實際 repo 已有 push.py / notion_api.py / cli.py 的 sync 指令；真正卡點是缺 notion.config.local.json（token + db id），不是缺程式碼。
> fix: 直接讀程式碼（cli.py、push.py）查證能力，而非信 CONTEXT 註記；確認阻塞點是設定檔而非實作後再回報。
> rule: 判斷工具能力以程式碼為準，CONTEXT/README 路線圖可能落後實作；在回報「做不到」前先驗證實際程式與設定檔狀態。

> [!lesson] skill=architecture stage=Build error=lock-blocks-same-machine-workers
> what: v2 止血加的 pm-suite.lock 機器鎖在 Next.js dev/prod 多 worker 進程下會互鎖——worker A 持有 live lock（其 pid 存活），worker B 的請求被擋下全 500。Task 8 端對端驗證才暴露（events/cards API 突然 500）。
> fix: acquireLock 改成「只擋來自不同機器的 live lock」；同機 holder 一律放行（同機並發由 SQLite WAL 安全處理；活的 DB 已在本機 app-data，跨機才是鎖要防的情境）。加回歸測試 multi-worker same-machine 必須可取得鎖。
> rule: 設計檔案鎖前先確認執行模型的進程數；Web 框架（Next.js）會跑多 worker，鎖的粒度要是「機器/實例」而非「進程」，否則同機並發會自我死鎖。

> [!lesson] skill=typescript stage=Build error=spread-default-duplicate-key
> what: 為 CalendarEvent 加上 task_id 後，createEvent 用 `{ task_id: null, ...input }` 提供預設值；因 input 型別現在必含 task_id，TS2783「specified more than once」在 next build 變成硬錯誤（vitest 不型檢所以測試沒抓到）。
> fix: 把欲覆寫的鍵放在 spread「之後」（`{ ...input, task_id: input.task_id ?? null }`），並把該欄位在輸入型別設為 optional。
> rule: 提供預設值別用「字面鍵在前、spread 在後」（會觸發 TS2783）；要嘛 spread 在前覆寫在後，要嘛預設欄位在輸入型別設 optional。build 的型檢比 vitest 嚴，完工前一定跑 next build。

> [!lesson] skill=systematic-debugging stage=Build error=silent-filter-drop
> what: goal 因 frontmatter 值不在白名單被靜默略過，sync report 的 blocked/dropped 都是 0，使用者與工具都無從察覺漏了哪個專案。
> fix: 從「症狀（dashboard 缺項）」往上游追資料流——比對正常專案與異常專案的 frontmatter（status: verified vs active），再讀 engine 的過濾常數 `GOAL_STATUSES` 確認 active 不在內。
> rule: 凡是「該出現的東西沒出現」且工具回報無錯，先懷疑「不符 filter 被靜默丟棄」而非「程式壞了」；對照一個已知正常的樣本的 frontmatter 是最快的定位法。

> [!lesson] skill=systematic-debugging stage=Build error=non-code-symptom-misattributed
> what: 使用者把頁首靜態日期「更新：2026-05-31」當成同步失效證據，容易誤導往「sync 壞了」方向查。
> fix: 讀 push.py 確認同步只 create/update 兩個 DB 的 properties，沒有任何程式碼觸碰頁首 callout → 該文字本就不會自動更新。
> rule: 報告的「最後更新」要區分「程式維護的欄位」與「人手打的裝飾文字」；診斷前先確認該符號到底由誰維護，別把靜態文字當動態狀態。

> [!lesson] skill=writing-plans stage=Build error=scaffold-version-drift
> what: 實作計畫假設 Astro 5 + @astrojs/tailwind + tailwind.config.mjs（Tailwind v3），但 `npm create astro` 實際給 Astro 6 + Tailwind v4（CSS 設定制，無 config 檔，token 在 @theme）。
> fix: 採用當前官方工具不降級，把計畫 Task 2/3 即時改寫為 v4 @theme 機制（語意 utility 名稱不變，只換定義方式），並記入 CLAUDE.md/memory。
> rule: 計畫不要硬寫死框架版本與設定檔假設；scaffold 後先驗證實際產出版本再適配，視為正常偏差而非錯誤。

> [!lesson] skill=subagent-driven-development stage=Build error=git-add-removed-path-aborts
> what: 用 `git add -A` 帶入一個已被 `git rm` 的路徑 → fatal pathspec，整個 staging 中止，結果 commit 只含那個刪除、其餘修改沒進去。
> fix: 改用 `git commit --amend` 補上明確存在的檔案路徑；事後以 `git show --stat HEAD` 驗證 commit 內容。
> rule: git add 只列確實存在的路徑（或用 `git commit -am`）；commit 後一律 --stat 檢查實際內容，別假設成功。

> [!lesson] skill=test-driven-development stage=Build error=playwright-strict-multiple-match
> what: Playwright `getByText`/`getByRole` 命中重複文字（nav 連結與 hero 按鈕同名「詢問檔期」、價格「8,000」在兩張卡都出現）→ strict-mode 多重匹配失敗。
> fix: 加 `.first()` 或縮小 locator 範圍（scope 到容器）。
> rule: 斷言可能在導覽列＋內文重複出現的文字時，預先用 scope 或 `.first()`，避免 strict-mode 報錯。

> [!lesson] skill=frontend-design stage=Build error=force-crop-mismatched-aspect
> what: 對來源比例不一（IG 多為 4:3 與 4:5）的照片硬套 `object-cover` + 固定 aspect 方框，裁切結果切到頭/身體很怪。
> fix: 改用原始比例（`h-auto w-full`）或瀑布流，不強制統一裁切。
> rule: 使用者提供的混合比例圖庫，預設以原比例呈現；要統一裁切前先確認來源比例分佈。

> [!lesson] skill=brainstorming stage=Build error=vague-visual-feedback-loop
> what: 面對「整個版面不滿意」這類主觀模糊回饋反覆用猜的，連續被否決、浪費回合。
> fix: 改用「在實際頁面渲染、一次只變動一個維度」的比較頁讓使用者選（純字體比較頁、即時配色切換器、只換版面結構的 /preview a–e）。
> rule: 主觀視覺回饋要用並排的實際渲染、隔離單一變項來收斂，而非靠文字描述猜測。

> [!lesson] skill=security stage=Build error=pipeline-scan-gap
> what: promote.py 只做 YAML 結構驗證，不做內容敏感掃描。敏感資料若寫進 candidate 並被 promote，會先寫入 SoT（lessons.md / goal.md），km-sync 同步時才被 hard_block 攔截。SoT 已污染但 Notion 無外洩。
> fix: 在 promote.py 寫入 SoT 前，重用 data-contract.yaml 的 hard_block pattern 跑一次掃描；命中則拒絕 promote 並輸出規則 ID。
> rule: 敏感掃描必須在每一個「寫入 SoT 前」的節點觸發，不只在「同步外部服務前」。

> [!lesson] skill=security stage=Build error=classification-design
> what: binary `mirror: true/false` 無法分類商業資訊（如併購計畫、客戶名稱）——這類資料不是密碼，regex 抓不到，但同樣不該同步。
> fix: 加單一 `confidential: true` flag（優先於 mirror 設定），凡帶此 flag 的筆記預設禁止同步，不需四層分級制度。
> rule: 敏感程度分級先從最小可行開始（confidential boolean），待實際使用再評估是否需要更細粒度。
