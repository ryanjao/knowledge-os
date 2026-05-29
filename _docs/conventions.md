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
- 同步前敏感掃描 fail-fast：內網 IP / 金鑰 / 私鑰命中即整批失敗（見 `data-contract.yaml` §6）。
