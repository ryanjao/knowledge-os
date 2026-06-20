# knowledge-os：給 AI Coding Session 的知識留存系統

你解了個難題。Session 結束。隔天重開，AI 不記得，你也記得模糊。

knowledge-os 讓每次 session 留下可查的痕跡。

---

## 它怎麼運作

Session 結束時，Stop hook 自動在 `01_Inbox/_candidates/` 生一份草稿：

```
2026-06-04--my-project--abc123.md
```

裡面有這次的進度（`[!progress]`）和踩到的坑（`[!lesson]`）。

草稿不會自動入庫。下次開 session，你跑 `/km-review`：

1. 結構驗證器先過（格式、必要欄位、目標卡可解析）
2. 白話審查單顯示結果
3. 你決定：核准 / 編輯 / 拒絕

核准後，三件事自動發生：
- 進度追加到 `03_Projects/<專案>/goal.md` Stage Log
- 教訓追加到 `02_Notes/lessons.md`
- 一行索引追加到 `04_MOCs/playbook.md`

**還沒有**：下次 session 問 AI「上週那個 bash 變數問題怎麼解的」，AI 說不知道。  
**有了以後**：`grep 'skill=bash' 02_Notes/lessons.md`，答案在那裡。

---

## 三個設計原則

**SoT 在地端，Notion 是鏡子**
所有真實資訊住在這個 Obsidian Vault。Notion 是唯讀反射——可丟、可重建，不承載唯一資訊。

**人工閘不動**
機器做結構驗證，人做內容判斷。自動 promote 省事，但省掉了你唯一能擋掉「記錯的事」的機會。

**SoT 只 append，不改舊內容**
你知道每一行是什麼時候加進去的。

---

## 需要什麼

- Obsidian（或任何能讀 Markdown 的工具）
- Claude Code（Stop hook + `/km-review` slash command）
- Python 3（stdlib only，零 pip deps）

---

## 資料夾結構

| 資料夾 | 用途 |
|--------|------|
| `01_Inbox/` | 週間原始輸入（Daily、碎片、session 候選草稿） |
| `02_Notes/` | 已成形筆記（draft/verified/deprecated） |
| `03_Projects/<專案名>/` | 專案筆記、目標卡、Stage Log |
| `04_MOCs/` | 日誌流 MOC（append-only 索引） |
| `05_Secrets/` | **敏感資料專區（永不上雲、永不給 AI）** |
| `06_Exports/` | 投影輸出 / sync_state.json（可重建） |
| `99_Archive/` | 冷凍封存（排除索引） |
| `_templates/` | Daily / 目標卡 / 一般筆記 模板 |
| `_docs/` | 標準文件（慣例、Callout、流程） |

## 快速開始（5 分鐘）

### 1. 安裝前置工具

- [Obsidian](https://obsidian.md)（免費）
- [Claude Code](https://claude.ai/code)（CLI）
- Python 3（系統內建即可，零 pip 依賴）

### 2. Clone 並開啟 Vault

```bash
git clone https://github.com/ryanjao/knowledge-os.git
```

用 Obsidian 開啟 `knowledge-os/` 資料夾為 Vault。

### 3. 啟用自動化 Hook

`.claude/settings.json` 已包含兩個 hook，Claude Code 開此目錄時**自動生效**：

- **SessionStart**：自動促進待審候選草稿
- **Stop**：session 結束自動捕捉進度與教訓

> 若你想追蹤**其他專案**，在該專案根目錄建一個 `.km-project` 檔，內容填一行專案代號（如 `my-app`）。Stop hook 偵測到此檔案才會觸發。

### 4. 建立第一個專案

```bash
cp -r 03_Projects/_TEMPLATE 03_Projects/my-app
echo "my-app" > /path/to/my-app/.km-project
```

用 `_templates/goal-note.md` 在 `03_Projects/my-app/` 建目標卡（`kind: dev_goal`）。

### 5.（選用）安裝骨幹 SOP

`CLAUDE.md` 是配套的 5-Phase 開發方法論。複製到全域讓所有專案都套用：

```bash
cp CLAUDE.md ~/.claude/CLAUDE.md
```

記得把 `§0.7` 的 Registry URL 換成你自己的 Notion 頁面。

### 6.（選用）Notion 同步

```bash
cp notion.config.example.json notion.config.local.json
# 填入 Notion Integration Token 與 Database ID
```

不需要 Notion 也能用——知識只存在 Obsidian，Notion 是可選的雲端鏡子。

---

## 日常工作流程

1. 寫筆記：`01_Inbox/` 套用 `_templates/daily-note.md`
2. session 結束後，Claude Code 自動生成候選草稿到 `01_Inbox/_candidates/`
3. 下次開工時跑 `/km-review` 審查並併入知識庫

## 文件

- 規格書（系統設計正本）：[_docs/spec.md](_docs/spec.md)
- 撰寫慣例：[_docs/conventions.md](_docs/conventions.md)
- Callout 字典：[_docs/callouts.md](_docs/callouts.md)
- 工作流程：[_docs/workflow.md](_docs/workflow.md)
- 資料契約（機器規則）：[data-contract.yaml](data-contract.yaml)

## 設定（Notion 同步用）

複製 `notion.config.example.json` → `notion.config.local.json`，填入 Notion token 與 database id。
`notion.config.local.json` 與 `05_Secrets/` 已被 `.gitignore` / `.claudeignore` 封鎖。

## 路線圖

- **Phase 1（完成）**：Vault 骨架、資料契約、模板、標準文件。
- **Phase 2（進行中）**：Session Wrap + `/km-review` promotion 閉環、結構驗證器、知識留存完整跑通。
- **Phase 3**：`km-sync` CLI（掃描 → 去敏感 → idempotent upsert 至 Notion）。
- **Phase 4**：健康檢查、Pull-based backlog、週末重構流程。
