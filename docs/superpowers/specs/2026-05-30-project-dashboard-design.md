# 專案儀表板 Project Dashboard — 設計 Spec

- 日期：2026-05-30
- 載體：Notion（Mirror）
- 資料來源：Obsidian `kind: dev_goal` 目標卡（SoT）
- 相關 DB：`開發目標 Dev Goals`、`階段記錄 Dev Stage Log`

## 1. 目的
把 `開發目標 Dev Goals` 的資訊整理成一個視覺化儀表板，用**進度條**呈現每個專案的進度，並附近期進展與接下來作業。

## 2. SoT 原則（不可違反）
- Obsidian 是唯一真理源；Notion 是可丟、可重建的 Mirror。
- 儀表板的所有數字都是**投影/推導**，不得出現「只存在 Notion」的權威資訊。
- 進度推導規則的 SoT 在本 spec 與 `data-contract.yaml`；Notion formula 只是規則的可執行鏡像。

## 3. 進度模型：Stage 區間 × Phase 內插
進度 % 由兩個結構化來源推導：
1. `stage`（已存在於目標卡 frontmatter）決定**區間**。
2. `phase_done / phase_total`（**本次新增**的結構化 frontmatter 欄位）在區間內線性內插。

### Stage 區間
| Stage | 下界 low | 上界 high | 寬度 |
|-------|---------|----------|------|
| Idea | 0 | 15 | 15 |
| Build | 15 | 50 | 35 |
| Validate | 50 | 80 | 30 |
| Ship | 80 | 95 | 15 |
| Maintain | 95 | 100 | 5 |

### 公式
```
progress = low(stage) + (phase_done / phase_total) * width(stage)
```
覆寫規則：
- `狀態 Status == Done` → `progress = 100`
- `狀態 Status == Dropped` → `progress = 0`（灰階）
- `phase_total == 0` → phase 項視為 0（只取區間下界）

進度四捨五入為整數。

### 套用現況（已確認）
| 專案 | Stage | phase_done / total | 進度 |
|------|-------|--------------------|------|
| km-sync | Build | 1 / 2（2a 完成、2b 待做） | 33% |
| investment-research-os | Validate | 1 / 2（Phase 1 完成、Phase 2 backlog 待做；Phase 3 不計入當前範圍） | 65% |
| 0000-anewday | Ship | 3 / 3（P1/P2/P3 打磨完成） | 95% |

## 4. SoT 變更：目標卡 frontmatter 新增欄位
在 3 張 `dev_goal` 目標卡的 frontmatter 加入：
```yaml
phase_done: <int>   # 已完成的 phase 數
phase_total: <int>  # 規劃的 phase 總數
```
- `03_Projects/km-sync/goal-phase2.md` → `phase_done: 1`, `phase_total: 2`
- `03_Projects/investment-research-os/goal.md` → `phase_done: 1`, `phase_total: 2`
- `03_Projects/0000-anewday/goal.md` → `phase_done: 3`, `phase_total: 3`

## 5. 資料契約變更：`data-contract.yaml`
在 `notion.databases.dev_goals` 加入新欄位與映射，使未來 km-sync 推送會帶上 phase，並記錄進度推導規則：
- 新增 frontmatter 欄位定義：`phase_done`、`phase_total`（type: number, optional）。
- 新增 Notion 屬性映射：
  - `已完成階段 Phase Done`（number）← `frontmatter.phase_done`
  - `規劃階段 Phase Total`（number）← `frontmatter.phase_total`
- 以註解記錄「進度 / 進度條為 Notion 端 formula，依 Stage 區間 × Phase 推導（規則見本 spec）」。

> 註：km-sync 的 Notion 推送（Phase 2b）尚未實作。本次由 MCP 直接把 `Phase Done / Phase Total` 寫入現有 Notion row（屬 frontmatter 投影）。契約先行記錄，待 Phase 2b 實作時納入。

## 6. Notion schema 變更：`開發目標 Dev Goals` DB
新增以下屬性：
- `已完成階段 Phase Done`（number）— 由 frontmatter 投影。
- `規劃階段 Phase Total`（number）— 由 frontmatter 投影。
- `進度 Progress`（formula，number，0–100，可排序、可切 Show as bar）— 依 §3 公式，自包含（內聯 Stage 區間與 phase 計算，不參照其他 formula 屬性）。
- `進度條 Progress Bar`（formula，text）— 以 `slice()` 切固定字串畫條，輸出如 `███░░░░░░░ 33%`，保證任何檢視都看得到視覺進度條。

進度條繪製（避免依賴 `repeat()`，用 `slice()` 兼容）：
```
filled = round(progress / 10)              # 0–10
bar = slice("██████████", 0, filled)
    + slice("░░░░░░░░░░", 0, 10 - filled)
    + " " + format(round(progress)) + "%"
```

## 7. 儀表板頁面 `專案儀表板 Project Dashboard`
版面（由上而下）：
1. **抬頭 callout** — 說明這是 Mirror（SoT 在 Obsidian）、進度推導規則一句話、最後更新日。
2. **總覽 Overview** — 專案數、平均進度、各階段分佈。
3. **各專案進度** — Dev Goals 連結 table 檢視：專案 / 階段 / phase（Phase Done/Total）/ 進度條 / 進度 / 狀態，依進度由高到低排序。
4. **管線看板 Pipeline** — Dev Goals board 檢視，依 `階段 Stage` 分組。
5. **近期進展 Recent Progress** — Dev Stage Log 連結檢視，依日期 desc（顯示 做了什麼 / 結果）。
6. **接下來作業 Next / Upcoming** — Dev Stage Log 連結檢視，顯示「下一步 Next」、依日期 desc、過濾掉 Next 為空者。

## 8. 建置方式與冪等
- 透過 Notion MCP：先加屬性 → 寫入 Phase Done/Total → 建儀表板頁 → 建檢視。
- **冪等**：屬性/頁面/檢視以名稱檢查，存在則更新，不重複建立。
- **保底順序**（若 API 對建檢視支援有限）：屬性（必成功，主 DB 立即有進度條）→ 頁面 + 總覽 → 盡量建檢視，其餘附一行手動步驟。

## 9. 不做（YAGNI）
- 不加每張卡手填進度數字。
- 不改 DoD 格式。
- 不改 km-sync 程式碼（僅更新 data-contract.yaml）。
- 不碰 `05_Secrets`。

## 10. 驗收
- 3 張目標卡有 `phase_done / phase_total`。
- `data-contract.yaml` 記錄新欄位與推導規則。
- Notion Dev Goals DB 有 4 個新屬性，3 個 row 顯示正確進度條（33% / 65% / 95%）。
- 儀表板頁含 §7 全部六區（檢視能建多少建多少，無法建者列出手動步驟）。
