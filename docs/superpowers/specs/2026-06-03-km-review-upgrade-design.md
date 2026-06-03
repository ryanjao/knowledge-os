# km-review 升級：結構驗證器 + 自我目標卡 + 雙保險待審提醒 — 設計 Spec

- 日期：2026-06-03
- 載體：Python 驗證器（`tools/km_review/`）+ `/km-review` slash command + Stop hook + Obsidian Vault（SoT）
- 狀態：**設計已核准（雙保險提醒已定）**，可轉寫實作計畫
- 啟發來源：Trellis（mindfold-ai）的 Verify-before-promote 與「把自己也當專案管」
- 相關前作：[2026-06-01-session-wrap-capture-design.md](2026-06-01-session-wrap-capture-design.md)

## 1. 目的與核心洞察

> 在候選草稿 promote 進 SoT 之前，加一道**死板、每次都一樣的結構鐵閘**（機器把關），並把生硬的語法錯誤**翻成白話「入庫審查單」**（人類秒懂）；同時給 knowledge-os 系統本身一張目標卡，並用雙保險提醒治「手動 /km-review 會忘記按」。

**核心洞察（審查盲區 Reviewer Blindspot）**：human-in-the-loop 系統最大的工程痛點是——若驗證器只吐 `Regex mismatch at line 4` 這種火星文，審查者看不懂，審查就退化成「閉眼點核准」，品質防線崩潰。解法是**分層**：

- **機器負責「嚴」**：死板的結構驗證，不靠 agent 那次有沒有認真看。
- **agent 負責「懂」**：把驗證結果渲染成白話審查單（症狀 / 規定 / 建議修法）。

## 2. 範圍

### 2.1 這次做（in scope）
- A. Python 結構驗證器 `tools/km_review/validate_candidate.py`（TDD）
- B. `/km-review` 接線：先驗證 → 渲染白話審查單 → 再核准
- C. knowledge-os 自我 `dev_goal` 目標卡 + km-review 認得 `goal=knowledge-os` slug
- D. 雙保險待審提醒（Stop hook 收尾尾巴 + session 開始）

### 2.2 這次不做（backlog，不在本 spec）
- 語意 / 內容完整度判斷（見 §4 範圍切割，留給審查時的 agent + 人）
- 清掉 `_candidates/` 既有 backlog（驗證器做好後另跑一次 /km-review dogfood）
- knowledge-os 對外介紹文（另一獨立工作）

## 3. 核心範圍切割：結構 vs 語意

| 檢查類型 | 例子 | 誰來檢查 |
|---|---|---|
| **結構**（死板、可機器判定） | 缺 `seq=`、忘了雙鏈中括號、callout 框框破掉、檔名格式錯、`goal=` 解不到卡 | ✅ 驗證器（機器，確定性） |
| **語意**（需判斷力） | 「漏掉前因後果、三個月後看不懂」 | 🧠 agent + 人（審查時） |

**理由**：把「看不看得懂」這種語意塞進機器驗證器，會做出一個假裝懂、其實亂判的東西。驗證器只當結構鐵閘，這樣才能死板、可單元測試、每次一致。

## 4. A — 結構驗證器

### 4.1 介面（單一用途、可獨立測試）
- 檔案：`tools/km_review/validate_candidate.py`
- 輸入：一個候選檔路徑（`01_Inbox/_candidates/*.md`）
- 輸出：**結構化 findings 清單**（純事實，不含 UI 文案）：`{rule_id, level, location, raw}`
  - `level`：`block`（攔截）/ `warn`（可放行但提示）
- Exit code：`0` = 無 block / 非 `0` = 有 block
- 同時提供可被 import 的函式 `validate(path) -> list[Finding]`，CLI 是薄包裝（方便 /km-review 與測試各自呼叫）

### 4.2 檢查規則（依 spec §6.3 / §6.6 / §8）
- **檔名**：符合 `YYYY-MM-DD--<slug>--<hash>.md`
- **`[!progress]`**：header 必含 `stage` `date` `goal` `seq`；body 必含 `did` `result` `next` 三行鍵
- **`[!lesson]`**：header 必含 `skill` `stage` `error`；body 必含 `what` `fix` `rule` 三行鍵
- **`goal=` 解析**：值需能對應到某 `dev_goal` 目標卡的 `uid`，或等於某 `03_Projects/<slug>/` 的專案 slug（見 C）；都對不到 → `block`
- **callout 完整性**：`> [!progress]` / `> [!lesson]` 區塊每行以 `>` 起頭、區塊未破

### 4.3 規則→白話對照表
- 一張 ~15 行的 dict：`rule_id → {症狀, 規定, 建議修法}`（即建議裡「Error Dictionary」拆掉包裝後的本體）
- 渲染端（B）查這張表把 `rule_id` 翻成白話。驗證器本身**不**輸出白話 UI（保持純結構，UI 與規則解耦）

### 4.4 測試（TDD，一條規則一個測試）
- 合格候選 → findings 空、exit 0
- 每個必填欄位各缺一次 → 觸發對應 `rule_id`、`level=block`
- 檔名錯、callout 破框、`goal=` 解不到 → 各對應 `rule_id`
- 既有兩個真候選（6/01、6/02）當 fixture：應全數通過（驗證驗證器本身沒亂攔）

## 5. B — `/km-review` 接線

改 `.claude/commands/km-review.md` 步驟 2，每個候選：

1. **先跑驗證器** `validate_candidate.py <候選檔>`
2. agent 把 findings 查 §4.3 對照表，**渲染成白話「入庫審查單」**：來源檔、目的地、逐項「症狀 / 規定 / 建議修法」條列
3. 有 `block` → 預設引導 `edit`（agent 提自動修法），但**最終仍由人輸入 Y/R/白話指令**
4. 無 block → 照舊顯示內容 + 問 approve/edit/reject

**不動的硬規定**：§8.1 人工核准閘（人輸入 Y 才寫 SoT）、append-only、候選檔是唯一可刪對象。

## 6. C — knowledge-os 自我目標卡

- 新檔 `03_Projects/knowledge-os/goal.md`：
  - frontmatter：`kind: dev_goal`、`uid: 01KKMOSSELFGOAL0001`、`project: knowledge-os`、`stage`、`mirror: true`、含 `## Stage Log`
- **km-review slug 解析**：`.claude/commands/km-review.md` 步驟 2c 既有「goal 非 uid 而是 slug 就詢問」改為——若 `03_Projects/<slug>/` 存在含該 slug 的 `dev_goal` 卡，**自動解析併入該卡**，不再追問。
- 效果：`goal=knowledge-os` 從此有家；兩個躺著的候選下次 promote 進這張卡的 Stage Log，不再是孤兒。

## 7. D — 雙保險待審提醒

治「手動 `/km-review` 會忘記按」（根因見 candidate-backlog 發現）。**雙保險**：

- **收尾端**：Stop hook 收尾腳本（`tools/hooks/km-session-wrap.sh`）尾巴，數 `_candidates/` 非 `.gitkeep` 檔數 `N`，`N>0` 時輸出 `📋 目前有 N 筆候選待審，跑 /km-review`。
- **開場端**：session 開始時同樣數一次並提示（雙保險，剛生完候選的當下 + 下次開工都會看到）。
- 純提醒，不自動 promote（守人工閘）。

## 8. 對既有檔案的變更

| 檔案 | 變更 |
|---|---|
| `tools/km_review/validate_candidate.py` | 新增（驗證器 + 對照表） |
| `tools/km_review/test_validate_candidate.py` | 新增（TDD 測試） |
| `.claude/commands/km-review.md` | 改步驟 2（接驗證器 + 白話審查單）、步驟 2c（slug 自動解析） |
| `03_Projects/knowledge-os/goal.md` | 新增（自我目標卡） |
| `tools/hooks/km-session-wrap.sh` | 尾巴加待審計數提醒 |
| session 開場提醒 | 新增（位置實作計畫時定：SessionStart hook 或既有開場機制） |

## 9. 為什麼這個設計成立

- **不違背人工閘（§8.1）**：驗證器只攔結構、只提建議，寫入 SoT 仍要人輸入 Y。機器把關是**加強**人工閘，不是取代。
- **append-only 哲學不變**：驗證器唯讀候選；promotion 仍只 append、刪候選。
- **比照既有方法**：Python + TDD 沿用 km-sync 的 method；不用 bash（callout 解析 bash 做不到，已有教訓）。
- **UI 與規則解耦**：驗證器吐 `rule_id`，白話文案在對照表/渲染端，日後改文案不動驗證邏輯。

## 10. 子決策（已定案）
- 待審提醒：**雙保險**（收尾 + 開場）。
- 驗證器語言：**Python**。
- 範圍：只驗**結構**，語意留給人。
- 自我目標卡 uid：`01KKMOSSELFGOAL0001`（實作時若衝突再調）。

## 11. 下一步
- 轉 writing-plans 寫實作計畫（TDD 順序：驗證器測試 → 驗證器 → km-review 接線 → 目標卡 → 提醒）。
- 實作完 dogfood：跑 `/km-review` 清 6/01、6/02 backlog，順便驗證白話審查單。
