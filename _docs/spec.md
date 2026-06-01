---
uid: 01KSPEC0KMOSV11SPECDOC001
status: verified
kind: note
title: "規格書 Knowledge OS — 在地單一真理源 + 資料契約 + 可觀測治理"
mirror: true
source_date: 2026-06-01
---

# 規格書 Knowledge OS

> ── 基於「在地單一真理源（SoT）」+「資料契約（Data Contract）」+「可觀測治理」的防禦性系統

> [!note] 一句話
> Obsidian 是唯一真理源（SoT）；Notion 是可丟可重建的 Mirror；所有自動化都必須遵守「資料契約」與「可回滾（Rollback）」。

> [!note] 本文件的角色
> 本檔是規格書的**正本（SoT）**，位於 Obsidian。Notion 的「規格書」頁是它的**可重建 Mirror**。技術機器規則的權威來源是根目錄 [data-contract.yaml](../data-contract.yaml)（版本 `dev-notion-mirror@1.1`）；本檔不重複貼整份 YAML，只引用並說明，避免兩處不同步。實作現況見 [../README.md](../README.md) 路線圖。

---

## 0) 名詞與邊界（務必先讀）

- **SoT（Source of Truth）**：唯一真理源＝Obsidian 地端 Markdown。
- **Mirror（反射鏡）**：Notion 雲端唯讀檢視，可刪可重建，**不得承載唯一資訊**。
- **Projection（投影）**：從 SoT 萃取/聚合/表格化後推送至 Notion 的結果。
- **Sensitive（敏感）**：任何可識別的 IP/網域/帳號/金鑰/真實資產數字/政府或機關內部拓樸。
- **Automation Agent（自動化代理）**：Claude-code / 本地 LLM / Python 腳本都算，通通必須受規格約束。

---

## 1) 系統架構（Single SoT + Rebuildable Mirror）

```text
[任何輸入]
  └─> Obsidian Vault (SoT, CommonMark 純文字)
        ├─> 本地 AI / CLI：可讀寫（受 .claudeignore 限制）
        ├─> Python 工具鏈（km-sync）：掃描、萃取、投影、同步、報告
        └─> Notion Mirror：唯讀看板（可重建）
```

**落地模型（v1.1）**：單一 Vault + 每專案子資料夾（`03_Projects/<專案名>/`）+ 共用同步 CLI（`km-sync`）。Vault 只存知識/筆記，**不存程式碼**；Notion 以 `專案 Project` 欄位區分各專案。

### 1.1 絕對在地化 SoT（不拆域、不拆工具）
- 所有領域（網頁/理財/攝影/運維/隨筆）原始資料**全部留在 Obsidian**。
- **禁止**出現「只有 Notion 有、Obsidian 沒有」的資訊。本規格書本身也遵守此規則：正本在此檔，Notion 僅為投影。

### 1.2 Notion 的定位（可丟、可重建、不可當真理）
Notion 僅接受「投影後的結構化內容」。目前實際投影對象為**兩個開發治理 DB**（見 §6）：
- `開發目標 Dev Goals`（目標卡聚合）
- `階段記錄 Dev Stage Log`（progress 日誌聚合）

**Notion 不存：** 原始全文、敏感 token 對照、任何需要回寫到 SoT 的狀態。

---

## 2) 安全與隱私隔離（SecOps & Privacy Isolation）

### 2.1 目錄級隔離（物理邊界）
Vault 核心資料夾（語義固定）：

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
| `_docs/` | 標準文件（本規格書、慣例、Callout、流程） |

**必做規則**：`05_Secrets/` 必須同時存在於 `.gitignore` 與 `.claudeignore`。任何敏感內容只允許在 `05_Secrets/` 或以 Token 形式出現。

### 2.2 Token 化與去敏感（Sanitization Contract）
- Token 一律使用 `{{SECRET_XXX}}`，`XXX` 需語義明確（如 `{{SECRET_NTPC_NETPROXY_IP}}`、`{{SECRET_ECPAY_HASH_KEY}}`）。
- 禁止在 `01_Inbox / 02_Notes / 03_Projects / 04_MOCs / 06_Exports` 寫入真實 IP/網域/帳號/密碼/金鑰；真實資產數字改用區間/比例（例：股 60% / 債 40%）。
- 對照檔只在 Secrets：`05_Secrets/secrets.env`（真實值）、`05_Secrets/secrets.env.example`（只留欄位名，方便移機）。

> [!note] 設計目的
> 就算整個 Vault 外洩，文本也具有防禦性匿名；Mirror 更不可能帶出敏感。

### 2.3 自動化的「阻擋」優先於「提醒」
立場：**寧可同步失敗，也不要把敏感推上雲**。同步腳本在推送 Notion 前必做：
- Token 檢查：出現疑似 IP/金鑰 pattern 且未 token 化 → **直接 fail**（fail-fast）。
- Secrets 路徑檢查：任何 `05_Secrets/` 內容 → **絕不讀取、絕不處理**。
- 完整 pattern 清單與處置等級見 [data-contract.yaml](../data-contract.yaml) §6（`sensitive_scan`）。

---

## 3) 輸入規格（Progressive Ingestion + 語義區塊化）

### 3.1 週間輸入：Callout 區塊為最小單位（Block is the atom）
可被整理的內容用 Callout 包起來，避免上下文破碎、避免 Regex 切碎。Callout 字典見 [callouts.md](callouts.md)：

| 類型 | 用途 |
|------|------|
| `[!bug]` | 已發生問題 + 解法/線索 |
| `[!question]` | 尚未理解，需補課/查證 |
| `[!idea]` | 靈感、策略、假設 |
| `[!note]` | 一般紀錄（中性） |
| `[!decision]` | 決策（會導向 ADR 或專案筆記） |
| `[!risk]` | 風險/雷區（含避免路徑） |
| `[!progress]` | **階段日誌**：會被 km-sync 抽取成 Dev Stage Log（見 §6.3） |
| `[!lesson]` | **錯誤→教訓**：Session 收尾捕捉，`/km-review` 核准後存入 `02_Notes/lessons.md`（見 6.6） |

> 類型越少越好；多了只會變成新的分類地獄。

### 3.2 Daily Note 模板（週間零門檻）
模板見 [`_templates/daily-note.md`](../_templates/daily-note.md)。Daily front-matter：

```yaml
---
uid:
status: draft
type: daily
source_date: YYYY-MM-DD
---
```

> [!note] front-matter 主鍵是 `uid`
> 全系統主鍵為 `uid`（見 §4.4），**不使用** `id` 之類的雲端流水號。Daily 的 `uid` 可在週末整理升級時補上。

### 3.3 零行動降級（Zero-Action Fallback）
- 不做 Regex 切分、不生成 Conflict_Zone。
- Daily 就保持可讀、可追溯的時間線日誌——Callout 本身就是結構，降級時仍有價值。

---

## 4) 元數據（Front-matter）資料契約：Core vs Extended

機器規則的權威來源見 [data-contract.yaml](../data-contract.yaml) §1（`obsidian.frontmatter`）；撰寫慣例見 [conventions.md](conventions.md)。

### 4.1 Core（任何時候都能寫，最低標準）
```yaml
---
uid: 01HZP3K8M9X2   # 全庫唯一、永不改（ULID/UUID）
status: draft       # draft | verified | deprecated
---
```
> `uid` 與 `status` 是唯二必填欄位。週間只寫這個也完全合規。

### 4.2 Extended（週末重構/有空再補）
```yaml
title    # 可選；缺則用 H1 或檔名推導
kind     # dev_goal | dev_log | note | adr | runbook | snippet | review
project  # 永遠可空，不逼人亂塞，避免拓樸污染
stage    # Idea | Build | Validate | Ship | Maintain
method   # list
tags     # list
mirror   # 是否允許投影到 Notion（見 4.3）
phase_done / phase_total   # 進度推導用（見 §6.4）
source_date                # ISO 日期 YYYY-MM-DD
```

### 4.3 `mirror` 預設規則（v1.1：dev_goal opt-out，其餘 opt-in）
- **`kind: dev_goal` 預設 `mirror: true`（opt-out）**：目標類筆記預設投影。
- 其餘所有筆記預設 `mirror: false`（opt-in）：要投影才設 `true`。
- 任一情況含敏感風險時，同步前敏感掃描會**二次否決**，自動降為不投影。

### 4.4 uid 規則
- 全系統主鍵：檔名可變、標題可變、資料夾可搬；**uid 不變**。
- 建議 ULID（可排序）或 UUID。每篇非 Daily 筆記都應有 uid。

### 4.5 檔名 / Slug 規則
- 路徑模板（通用筆記）：`YYYY/MM/YYYY-MM-DD--<slug>--<uid>.md`。
- Slug：全小寫、僅 `a-z 0-9 -`、最長 48 字；連續 `-` 合併；去頭尾 `-`。
- 中文標題建議用自動 hash slug（`note-k3f9z1`）或手動短英別名（`nextjs-cors-403-middleware`）。

---

## 5) 專案上下文（CONTEXT.md）：靜態文件 + 事件日誌

### 5.1 CONTEXT.md 只放「長週期不易變」內容
Scope（One-line / Constraints）、ADR Index（只列索引，不寫動態狀態）、Environment（敏感一律 token）。

### 5.2 動態狀態用「事件日誌」而非「覆寫文字」
高頻變動（branch、進度、hot bug）不寫在 CONTEXT.md，改存 `03_Projects/<Project>/LOG.md`（append-only）或本地 `.gitignore` 檔。

> [!note] 好處
> 避免 merge conflict，也避免「過期狀態誤導」。

---

## 6) Notion Mirror（投影）規格：可重跑、可覆寫、可驗證

### 6.1 投影流程（Projection Pipeline）
1. **掃描**：只掃 `02_Notes / 03_Projects / 04_MOCs`（排除 Archive/Secrets）。
2. **過濾**：依各 DB 的 `source_filter` 篩選（見 6.2）。
3. **去敏感檢查**：命中 hard_block pattern → 整批 fail（寧可不同步）。
4. **轉換**：產出 `06_Exports/notion_payload.json`（可檢視、可版本化）。
5. **同步**：兩階段 idempotent upsert（先 Goals 後 Stage Log），同一筆筆記重跑不會變成重複卡片。
6. **報告**：輸出同步報告（成功/失敗/原因，只記類型不記敏感內容）。

### 6.2 投影對象 = 兩個開發治理 DB
v1.1 實際維護**兩個** DB（非早期草案的 Knowledge Cards / Finance Overview / Photo Reviews 三個）：

#### DB-1：`開發目標 Dev Goals`
- **過濾條件**（`source_filter.where_all`）：`kind == dev_goal` **且** `status ∈ {verified, draft}` **且** `mirror == true`。
  > 注意：**draft 的目標卡也會投影**（讓進行中的目標即時上看板）。這與「一般筆記只投影 verified」不同；目標卡是治理用途，故放寬到 draft+verified。
- **唯一鍵（idempotency）**：`來源UID Source UID == frontmatter.uid`。
- **Status 映射**：`draft → Active`、`verified → Active`、`deprecated → Dropped`。
- 欄位、映射、進度推導見 [data-contract.yaml](../data-contract.yaml) §4 `dev_goals` 與本檔 §6.4。

#### DB-2：`階段記錄 Dev Stage Log`
- **來源**：`02_Notes / 03_Projects / 04_MOCs` 中的 `[!progress]` callout（每個 callout 一筆）。
- **複合唯一鍵**：`{goal_uid}#{date}#{seq}`（同一天多筆用 `seq` 不互相覆蓋）。
- **關聯**：以 `goal` 屬性對應到 `開發目標` 的 `來源UID`；缺 `goal` → 視為未關聯日誌，仍可投影但不建 relation。

### 6.3 `[!progress]` 抽取格式
```markdown
> [!progress] stage=Build date=2026-05-29 goal=01HZP3K8M9X2 seq=01
> did: 串接綠界測試金流，修正 hash 計算
> result: 400 -> 200，但 WAF 還有阻擋
> next: 加入 retry/backoff + 調整 header
```
- header 屬性：`stage` / `date` / `goal`（對應 dev_goal 的 uid）/ `seq`（同日多筆序號，可省，缺則自動補 01/02/03）。
- body 鍵：`did` / `result` / `next`。

### 6.4 進度推導：Stage 區間 × Phase 內插（v1.1 新增）
目標卡 frontmatter 新增結構化欄位 `phase_done` / `phase_total`；Notion `開發目標` DB 對應新增 4 個屬性：
- `已完成階段 Phase Done`（number）← `frontmatter.phase_done`
- `規劃階段 Phase Total`（number）← `frontmatter.phase_total`
- `進度 Progress`（formula，0–100，可排序、可 Show as bar）
- `進度條 Progress Bar`（formula，text，如 `███░░░░░░░ 33%`）

**進度由 `stage`（決定區間）+ `phase_done/phase_total`（區間內線性內插）推導：**

| Stage | 下界 low | 上界 high | 區間寬度 |
|-------|---------|----------|---------|
| Idea | 0 | 15 | 15 |
| Build | 15 | 50 | 35 |
| Validate | 50 | 80 | 30 |
| Ship | 80 | 95 | 15 |
| Maintain | 95 | 100 | 5 |

```
progress = low(stage) + (phase_done / phase_total) * width(stage)
```
覆寫規則：`Status == Done → 100`；`Status == Dropped → 0`；`phase_total == 0 → 只取區間下界`。進度四捨五入為整數。

> [!note] 進度為 Notion 端 formula（derived）
> `進度` / `進度條` 不由 km-sync 投影，而是 Notion formula 依上表自包含計算。規則的 SoT 在本檔與 [data-contract.yaml](../data-contract.yaml)；完整設計見 [../docs/superpowers/specs/2026-05-30-project-dashboard-design.md](../docs/superpowers/specs/2026-05-30-project-dashboard-design.md)。儀表板頁 `專案儀表板 Project Dashboard` 即以這些欄位呈現。

### 6.5 同步成功定義（Definition of Done）
1. **Upsert 穩定**：相同 `Source UID` 不會新增重複頁面。
2. **No-op 避免**：`Content Fingerprint` 相同就不更新。
3. **Zero Leak**：hard_block 命中則同步必須失敗（或該筆記被排除）。
4. **可重建**：刪掉 Notion DB 後，從 `06_Exports/sync_state.json` 與 Vault 可完整重建。

### 6.6 Session 收尾自動捕捉（Session Wrap Capture）
- 全域 Claude Code Stop hook：cwd 有 `.km-project`（內容＝專案 slug）時，讓 Claude 用自身 context 寫候選草稿到 `01_Inbox/_candidates/`（非 SoT，gitignore）。`stop_hook_active` 防迴圈。
- 候選含 `[!progress]`（did/result/next，需求 3）與 `[!lesson]`（skill/stage/error → what/fix/rule，需求 1）。
- `/km-review` 做 promotion：`[!progress]`→目標卡 Stage Log、`[!lesson]`→`02_Notes/lessons.md`，並追加一行到 `04_MOCs/playbook.md` 索引（append-only；採索引而非 Dataview，因 Dataview 無法解析 callout 標頭屬性）。守 §8.1 人工核准閘。
- 設計與計畫：`docs/superpowers/specs/2026-06-01-session-wrap-capture-design.md`、`docs/superpowers/plans/2026-06-01-session-wrap-capture.md`。

---

## 7) 治理與可觀測（Governance & Observability）

### 7.1 Pull-based Backlog（拉取式待整理）
不需要 deadline 或紅燈，只需要「想整理時」能拉出來的清單（Dataview）：
```dataview
TABLE file.mday AS "更新日", kind, tags
FROM "02_Notes"
WHERE status = "draft"
SORT file.mday DESC
```

### 7.2 系統健康檢查（Health Check）
週末重構/同步前輸出可讀報告，至少包含：本週新增 draft 數、verified 增量、同步成功/失敗筆數與原因、被擋下的敏感風險（只記「類型」，不記內容）。

> [!note] 目的
> 你看到的是「系統是否健康」，不是「紅燈恐嚇」。

---

## 8) 週末重構流程（Human-in-the-Loop, 變更控制）

### 8.1 提議 → 預覽 → 核准 → 寫入（硬規定）
1. AI/腳本只能輸出**候選檔案**（draft output）。
2. 必須提供 **Diff 預覽**（或「新增/修改摘要」）。
3. 人類輸入 `Y` 才能寫入 SoT / 觸發同步。

### 8.2 思維風格保護條款（不讓 AI 稀釋你）
任何含「主觀評斷/策略直覺/審美取向」的句子，AI 必須：原文保留（引用區塊）＋分開標示其整理，禁止把語氣改成客觀定論。

---

## 9) 規模化（10k+）效能策略

- **物理排除 + 路徑限定**：Obsidian 排除 `.git/ node_modules/ 99_Archive/ 05_Secrets/`；Dataview 查詢永遠限定路徑。
- **MOC 改成 Append-only 日誌流**：`04_MOCs/<Domain>.md` AI 只准追加，不准重排/搬家/改舊分類。每條格式固定：
  `2026-05-29 — [[Nextjs-ServerActions-Serialization]]（verified）— 重點：RPC 序列化超時排查`

---

## 10) 失效模式（Failure Modes）與對策

| 模式 | 行為 | 結果 |
|------|------|------|
| **FM-1 AI 不可用 / 額度用盡** | 不切、不搬、不做垃圾回收場 | Daily 仍可讀；有空再拉 draft 清單整理 |
| **FM-2 Notion API 失敗 / 權限翻車** | 同步停止，但 SoT 不受影響 | Mirror 暫停更新，隨時可重跑重建 |
| **FM-3 不小心寫入敏感** | 同步前掃描阻擋（fail fast） | 被迫先 token 化再允許投影 |

---

## 附錄 A) v1.1 落地修正（相對早期 v4.0 草案）

本系統實作時相對最初的 v4.0 草案採納了以下修正，均已落地於 `knowledge-os/` Vault 與 [data-contract.yaml](../data-contract.yaml)（`dev-notion-mirror@1.1`）：

- **A. 工具/內容分離**：同步工具獨立成 `km-sync` CLI；Vault 只放資料，`data-contract.yaml` 置於 Vault 根目錄可被所有專案重用。
- **B. Secrets/設定分離**：Notion `database_id` 與 token 改放 `notion.config.local.json`（已 gitignore），契約改用 `notion_config_ref` / `database_id_ref` 指向。
- **C. `dev_goal` 預設 `mirror: true`（opt-out）**：目標類筆記預設投影；一般筆記維持 opt-in。
- **D. 兩階段同步**：`sync.order: [dev_goals, dev_stage_log]`，先目標後日誌，確保 Stage Log relation 能對應。
- **E. Fingerprint 雙存**：本地 `06_Exports/sync_state.json` 快取 + Notion `內容指紋` 欄位。
- **F. 內網 IP 升級為 Hard Block**：私有 IPv4（10 / 172.16–31 / 192.168）由 Soft Warn 升為 Hard Block。
- **G. 進度推導欄位（最新）**：目標卡新增 `phase_done` / `phase_total`，Notion 新增 `Phase Done` / `Phase Total` / `進度 Progress` / `進度條 Progress Bar`（見 §6.4）。

## 附錄 B) Phase 建置切分

- **Phase 1（已完成）**：Vault 骨架、`data-contract.yaml`、`.gitignore`/`.claudeignore`、Daily/目標卡/一般筆記模板、慣例/Callout/流程文件、本規格書。
- **Phase 2**：`km-sync` CLI（掃描 → 去敏感 fail-fast → 兩階段 idempotent upsert → 報告）+ Notion 兩個 DB。Phase 2a 純引擎已完成，2b Notion 推送待做。
- **Phase 3**：健康檢查報告、Pull-based backlog、週末重構流程、可重建驗證、思維風格保護。
</content>
</invoke>
