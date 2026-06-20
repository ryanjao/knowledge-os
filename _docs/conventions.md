# 慣例 Conventions（front-matter / 命名 / uid）

這份文件是所有專案共用的撰寫標準。詳細的機器規則見根目錄 `data-contract.yaml`。

## 1) Front-matter：Core vs Extended

### Core（任何時候都能寫，最低標準）
```yaml
---
uid: 01HZP3K8M9X2   # 全庫唯一、永不改（ULID/UUID）
status: draft       # draft | verified | deprecated
---
```
> 週間只寫這個也完全合規。`uid` 與 `status` 是唯二必填欄位。

### Extended（週末整理成可復用資產時再補）
```yaml
title, domain, kind, tags, project, stage, method, mirror, source_date
```
- `project` **永遠可空**，不逼人亂塞，避免拓樸污染。
- `mirror`：**`kind: dev_goal` 預設 `true`（opt-out）**；其餘筆記預設 `false`（opt-in）。含敏感風險時同步前自動降為 `false`。
- 不用數字信心值、不用 deadline，避免警示疲勞。

## 2) uid 規則
- 全系統主鍵：檔名可變、標題可變、資料夾可搬；**uid 不變**。
- 建議 ULID（可排序）或 UUID。每篇非 Daily 筆記都應有 uid。

## 3) 檔名 / Slug 規則
- 路徑模板（通用筆記）：`YYYY/MM/YYYY-MM-DD--<slug>--<uid>.md`
- Slug：全小寫、僅 `a-z 0-9 -`、最長 48 字。
- 中文標題建議用自動 hash slug（`note-k3f9z1`）或手動短英別名（`nextjs-cors-403-middleware`）。

## 4) 階段枚舉 Stage
`Idea`（探索）→ `Build`（建置）→ `Validate`（驗證）→ `Ship`（交付）→ `Maintain`（維運）

## 5) 敏感資料
- 真實值只存 `05_Secrets/secrets.env`（永不上雲、永不給 AI）。
- 筆記中一律以 `{{SECRET_XXX}}` token 引用，`XXX` 需語義明確（如 `{{SECRET_NTPC_NETPROXY_IP}}`）。
- 兩道 fail-fast 敏感掃描（規則單一真實來源＝`data-contract.yaml` §6）：
  - **促進前**（寫入 SoT 前）：`promote.py` 掃候選，命中 hard_block 即隔離到 `_candidates/_quarantine/`，**不污染本地 SoT**。
  - **同步前**（推上 Notion 前）：`km-sync` 再掃一次，命中即整批失敗。
  - 報告只記檔案與規則 ID，不輸出命中內容。

### 金鑰治理（Key Governance）
靜態隔離只防「不該外洩」，治理層補「外洩後怎麼辦、平時怎麼降風險」。

- **最小權限**：Notion integration token、同步工具憑證一律只給「該做的事」所需的最小範圍——不要用 workspace 管理員 token，integration 只連接需投影的那幾個 database。
- **定期輪替**：`05_Secrets/secrets.env` 內的 token / API key / database id 設輪替週期（建議每季一次，或團隊成員異動時）。輪替後更新 `secrets.env`，不必改任何筆記（筆記只存 `{{SECRET_XXX}}` token）。
- **疑似外洩即撤銷**：一旦懷疑憑證外流（誤 commit、誤貼、掃描命中），**先撤銷再補救**——到該服務後台 revoke 舊憑證並重新產生，不要只是刪除檔案（git 歷史仍留存）。
- **example 檔不留真值**：`secrets.env.example` 只保留欄位名與格式註解，永不放真實範例值。
- **誤 commit 處理**：若敏感檔已被 git 追蹤（SessionStart Pre-flight 會警告），用 `git rm --cached <檔>` 解除追蹤；若已 push，視為已外洩，走上面的撤銷流程。

## 6) 知識來源 Provenance（`source=`）
AI 記憶最大的風險不是遺失，而是「三個月後不知道這條知識是真是假」。每筆 `[!lesson]` / `[!progress]` 可標 `source=` 標明出處，提升知識庫可信度。

- **語法**：callout 標頭加 `source=<type>` 屬性（與 `skill=` / `stage=` 同列）。
- **type 枚舉**：
  - `human` — 你本人的判斷 / 決策 / 直覺。
  - `ai` — Claude 推論產出（未經你驗證）。
  - `experiment` — 你本人實測 / 跑過驗證過的結論（可信度最高）。
  - `external` — 外部來源（官方文件、論壇、文章）。
- **`source_ref=`（可選）**：補出處細節——`external` 放 URL、`ai` 放模型名、`experiment` 放專案代號。含空白時用引號。
- **省略時**：視為 `ai`（候選多由 session wrap 自動生成，預設未經人工驗證）。
- **用途**：日後可 `grep 'source=experiment' 02_Notes/lessons.md` 只看自己驗證過的知識。

```md
> [!lesson] skill=bash stage=Build error=var-scope source=experiment
> what: ...
> fix: ...
> rule: ...

> [!lesson] skill=nextjs stage=Build error=cors source=external source_ref=https://nextjs.org/docs/...
```
> `source=` 為可選屬性，不影響結構驗證（缺漏不擋促進）；但建議週末整理成可復用資產時補上。
