# Knowledge OS — 統一知識與進度管理系統

所有專案共用的知識與進度管理標準。基於「在地單一真理源（SoT）+ 資料契約 + 可觀測治理」的防禦性設計。

- **SoT（唯一真理源）** = 這個 Obsidian Vault（地端 Markdown）。**禁止**出現「只有 Notion 有、Obsidian 沒有」的資訊。
- **Mirror（反射鏡）** = Notion 雲端唯讀檢視，可丟、可重建，不承載唯一資訊。
- **Projection（投影）** = 從 SoT 萃取 → 去敏感 → idempotent upsert 至 Notion（Phase 2 的 `km-sync` 工具）。

## 資料夾結構
| 資料夾 | 用途 |
|--------|------|
| `01_Inbox/` | 週間原始輸入（Daily、碎片） |
| `02_Notes/` | 已成形筆記（draft/verified/deprecated） |
| `03_Projects/<專案名>/` | 專案筆記、CONTEXT.md、ADR、LOG.md（**不放程式碼**） |
| `04_MOCs/` | 日誌流 MOC（append-only） |
| `05_Secrets/` | **敏感資料專區（永不上雲、永不給 AI）** |
| `06_Exports/` | 投影輸出 / sync_state.json（可重建） |
| `99_Archive/` | 冷凍封存（排除索引） |
| `_templates/` | Daily / 目標卡 / 一般筆記 模板 |
| `_docs/` | 標準文件（慣例、Callout、流程） |

## 怎麼開始
1. 用 Obsidian 開啟本資料夾為 Vault。
2. 寫筆記：`01_Inbox/` 套用 `_templates/daily-note.md`。
3. 開新專案：複製 `03_Projects/_TEMPLATE/` 為 `03_Projects/<專案名>/`。
4. 設目標：用 `_templates/goal-note.md` 建目標卡（`kind: dev_goal`，預設會投影到 Notion）。

## 文件
- 規格書（系統設計正本）：[_docs/spec.md](_docs/spec.md)
- 撰寫慣例：[_docs/conventions.md](_docs/conventions.md)
- Callout 字典：[_docs/callouts.md](_docs/callouts.md)
- 工作流程：[_docs/workflow.md](_docs/workflow.md)
- 資料契約（機器規則）：[data-contract.yaml](data-contract.yaml)

## 設定（Phase 2 同步用）
複製 `notion.config.example.json` → `notion.config.local.json`，填入 Notion token 與 database id。
`notion.config.local.json` 與 `05_Secrets/` 已被 `.gitignore` / `.claudeignore` 封鎖。

## 路線圖
- **Phase 1（本階段，已完成）**：Vault 骨架、資料契約、模板、標準文件。
- **Phase 2**：`km-sync` CLI（掃描 → 去敏感 fail-fast → 兩階段 idempotent upsert → 報告）+ Notion 兩個 DB。
- **Phase 3**：健康檢查、Pull-based backlog、週末重構流程、可重建驗證。
