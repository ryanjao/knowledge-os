# 工作流程 Workflow

## 週間（零門檻）
只做兩件事：
1. 寫 Daily（`01_Inbox/`，套用 `_templates/daily-note.md`）
2. 用 Callout 包住可整理的內容

> AI 不可用 / 沒空時，Daily 仍是可讀、可追溯的時間線日誌——不切分、不搬家。

## 週末（重構，Human-in-the-Loop）
1. **Pull**：拉出 `status: draft` 清單（Dataview 查詢，Phase 3 提供）
2. **昇級**：把有價值的 draft 補 Extended metadata → 設 `status: verified`
3. **投影**：跑同步工具（Phase 2 的 `km-sync`），可重跑、可覆寫、可報告

### 變更控制硬規定（提議 → 預覽 → 核准 → 寫入）
1. AI/腳本只能輸出**候選檔案**（draft output）
2. 必須提供 **Diff 預覽**（或新增/修改摘要）
3. 人類輸入 `Y` 才能寫入 SoT / 觸發同步

### 思維風格保護
含「主觀評斷/策略直覺/審美」的句子，AI 必須原文保留（引用區塊）＋分開標示其整理，禁止改成客觀定論。

## 失效模式對策
- **AI 不可用**：不切、不搬，Daily 仍可讀，等有空再整理。
- **Notion API 失敗**：同步停止但 SoT 不受影響，Mirror 隨時可重跑重建。
- **不小心寫入敏感**：同步前掃描阻擋（fail fast），逼你先 token 化。
