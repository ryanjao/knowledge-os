# Session 收尾自動捕捉 Session Wrap Capture — 設計 Spec

- 日期：2026-06-01
- 載體：Claude Code Stop hook（全域）+ Obsidian Vault（SoT）
- 狀態：方向已核准（使用者：「整體 OK」）；**兩個子決策待定**（見 §9），回來後定調即可轉寫實作計畫
- 服務需求：需求 1（做法知識層：階段→skill + 錯誤→教訓）、需求 3（每次結束保證記錄進度）

## 1. 目的與核心洞察
> 在每次 Claude Code 開發 session 結束時，自動產生一塊**候選草稿**（進度 + 用過的 skill + 錯誤→教訓），寫進 vault 暫存區待人工核准；核准後才進 SoT。

**核心洞察**：需求 1 與需求 3 是**同一個收尾事件**的兩面，只是欄位不同——
- 需求 3 → 進度（did / result / next）+ 整體規劃（phase）
- 需求 1 → 這階段用過哪些 skill、踩到什麼錯、怎麼解（累積成「錯誤→教訓」，playbook 由下而上長出）

故以**單一「session 收尾」機制**一次寫齊，不做兩套。

## 2. 範圍

### 2.1 這次做（in scope）
- 全域 Stop hook + `.km-project` 標記檔判定專案。
- 候選草稿產生（progress + lessons）寫入暫存區。
- 新增 `[!lesson]` callout 慣例。
- 由下而上的 playbook（Dataview 查詢）。
- 核准 / promotion 流程（輕量）。
- 更新 `_docs/spec.md`、`_docs/callouts.md`、`data-contract.yaml`、Notion Mirror。

### 2.2 這次不做（backlog，已歸位，不在本 spec）
- 外部評估的「同步韌性」另一軸：①記錄層隔離 + 系統級斷路器、②分層 DLP（risk scoring / exception registry / 語意分類）、③契約生命週期治理（owner / review gate / canary）。理由：屬另一條軸，且 km-sync 的 Notion 推送（Phase 2b）尚未建，目前是單人 vault，多為未來或過度工程。
- km-sync 把 `[!lesson]` 投影上 Notion「教訓 Lessons」DB（Phase 2b 之後）。
- 自寫 Obsidian 外掛做輸入自動化（若摩擦仍在，先用現成 Templater / QuickAdd）。
- 已撿入「未來右尺寸 backlog」的小片：存檔時 sensitive lint（②的一片）、km-sync golden test fixtures + 同步前關聯驗證（③/⑤的一片）。記錄於此但不在本 spec 實作。

## 3. 機制（核心流程）
1. **全域 Stop hook**（裝於 `~/.claude/settings.json` 的 `Stop` 事件）。session 結束觸發。
2. hook 檢查 cwd 是否有 **`.km-project`**（內容 = 專案 slug，如 `investment-research-os`）。
   - 無 → **no-op 放行**（不打擾其他 repo）。
   - 有 → 進入步驟 3。
3. hook 回傳 `block` + 指示，讓**仍在執行的 Claude 用自身完整 context** 產出候選草稿（推薦做法，見 §9 決策一）。
   - **防迴圈**：候選寫完後放 sentinel（或檢查候選檔已存在）；第二次 Stop 即放行，避免 block 無限循環。
4. 候選寫入暫存區：`01_Inbox/_candidates/YYYY-MM-DD--<project>--<session>.md`。
   - **不直接寫目標卡**（目標卡是 SoT，受 §8.1 人工核准閘約束）。

## 4. 資料慣例（沿用既有 + 新增 `[!lesson]`）
候選內容由兩種 callout 組成：

### 4.1 `[!progress]`（既有）— 服務需求 3
```markdown
> [!progress] stage=Build date=2026-06-01 goal=<該專案目標卡 uid> seq=01
> did: ...
> result: ...
> next: ...
```
- `goal=` 由 hook/Claude 從 `03_Projects/<project>/` 的目標卡 frontmatter `uid` 自動填入。

### 4.2 `[!lesson]`（新增）— 服務需求 1
```markdown
> [!lesson] skill=test-driven-development stage=Build error=flaky-test
> what: 測試偶發失敗，誤判是程式 bug
> fix: 改用固定 seed，隔離時間依賴
> rule: Build 階段寫測試先釘死隨機源
```
- header 屬性：`skill`（這次用到/相關的 skill）/ `stage` / `error`（錯誤類型短標籤）。
- body 鍵：`what`（發生什麼）/ `fix`（怎麼解）/ `rule`（萃取出的可復用規則）。
- **不新增 `kind: lesson`**：純靠 callout，與 `[!progress]` 同套抽取哲學，未來可比照投影成 Notion「教訓 Lessons」DB。

## 5. 由下而上的 playbook（需求 1 產出面）
- **不手寫**「階段×skill」對照表。
- playbook = 一條 **Dataview**：掃所有 `[!lesson]`，依 `stage` / `skill` / `error` 分組彙整 →「哪個階段反覆踩哪種錯、該配哪個 skill」自然浮現，隨日誌累積自動長大。
- 位置：`04_MOCs/playbook.md`（或 `02_Notes/`）。

## 6. 核准 / promotion 流程
- 下次 session 開場或週末，檢視 `01_Inbox/_candidates/`。
- 輕量 `/km-review`（見 §9 決策二）或純手動貼上：
  - **approve** → `[!progress]` 併入該目標卡 Stage Log；`[!lesson]` 併入 lessons 集合。
  - **reject** → 刪除候選。
- 守住規格 §8.1「提議 → 預覽 → Y → 寫入」。

## 7. 對既有檔案的變更
- `_docs/spec.md`（+ Notion Mirror）：§3.1 callout 字典加 `[!lesson]`；§6 加「session 收尾候選」流程；§8.1 註明 auto-candidate 是合規的「提議」（非繞過寫入閘）。
- `data-contract.yaml`：登記 `[!lesson]` 抽取規則（為未來 Notion 投影預留），維持「契約即真相」。
- `_docs/callouts.md`：補 `[!lesson]` 用法。

## 8. 為什麼這個設計成立（與系統原則的相容性）
- **守 §8.1 寫入閘**：hook 只產「候選」，不直接寫 SoT。
- **守 §1.1 SoT 原則**：候選進 `01_Inbox`（Obsidian），Notion 不承載唯一資訊。
- **沿用既有抽取哲學**：`[!lesson]` 比照 `[!progress]`，機器可解析、可投影、可重建。
- **零摩擦**：Stop hook 自動觸發，達成需求 3 的「保證每次都記」，又不靠紀律。

## 9. 待定子決策（回來後定調，其餘已核准）
**決策一 — §3 收尾的產出做法**：
- (A) 讓**仍在跑的 Claude** 自己寫候選（推薦）：零額外 LLM 成本、品質高、不怕 transcript 格式變。
- (B) 純腳本 `jq/grep` 機械萃取：只列 skill / 失敗測試，prose 要人補；較省但較笨。

**決策二 — §6 promotion**：
- (A) 這次一併做 `/km-review` 指令。
- (B) 先純手動貼，指令列 backlog。

## 10. 下一步
1. 回來定調 §9 兩個決策。
2. 轉 `writing-plans` skill 寫實作計畫（brainstorming 的終點）。
3. 依計畫實作：Stop hook 腳本 → `.km-project` 約定 → 候選模板 → `[!lesson]` 慣例 → spec/契約/Mirror 更新 → playbook Dataview。
</content>
</invoke>
