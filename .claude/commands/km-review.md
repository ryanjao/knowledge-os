---
description: 審核 Session Wrap 候選草稿，核准後併入 SoT
---

你是 knowledge-os 的 promotion 守門員。執行候選審核流程，嚴守「提議→預覽→核准→寫入」。

## 步驟
1. 列出 `01_Inbox/_candidates/` 內所有 `.md` 候選檔（忽略 `.gitkeep`）。若無 → 回報「無待審候選」並結束。
2. 逐一處理每個候選檔：
   a. **結構驗證（鐵閘）**：執行
      `python3 tools/km_review/validate_candidate.py <候選檔> --vault .`
      把輸出的白話「入庫審查單」原樣顯示給使用者。
   b. 完整顯示候選內容（[!progress] 與 [!lesson] 區塊）。
   c. 若審查單有 ❌ 攔截項 → 預設引導 `edit`（你提自動修法），但仍由使用者決定；
      無攔截 → 問使用者：approve / edit / reject。
   d. **approve：**
      - 對每個 `[!progress]`：找出其 `goal=` 對應的目標卡
        （依序解析 goal 值：
         1. 等於某 `03_Projects/<slug>/` 內 dev_goal 檔的 frontmatter `uid` → 用該卡；
         2. 否則等於某 `03_Projects/<slug>/` 且該目錄含 dev_goal 卡 → 自動用該卡，不再追問；
         3. 都對不到 → 回報並詢問要併入哪張目標卡）。
        把該 `[!progress]` callout 追加到目標卡的 `## Stage Log` 區段末尾。
      - 對每個 `[!lesson]`：
        - 把該 callout 追加到 `02_Notes/lessons.md` 末尾（append-only）。
        - 從其 header 取 `stage`/`skill`/`error`、body 取 `rule`，
          追加一行到 `04_MOCs/playbook.md` 的「## 索引」下方：
          `- <date> — stage=<stage> skill=<skill> error=<error> — <rule>`
          （date 取自同候選的 progress date，或今日）。
      - 全部併入成功後，刪除該候選檔。
   e. **edit：** 讓使用者口述修改，改完回到 a（重新驗證）。
   f. **reject：** 刪除候選檔，不寫入任何 SoT。
3. 結束時摘要：併入幾筆 progress、幾筆 lesson、刪幾個候選。

## 硬規定
- 候選檔（`01_Inbox/_candidates/`）是唯一允許「被刪」的對象；其餘只 append，不重排、不改舊內容。
- 未經使用者明確 approve，不得寫入 `03_Projects/`、`02_Notes/lessons.md`、`04_MOCs/playbook.md`。
