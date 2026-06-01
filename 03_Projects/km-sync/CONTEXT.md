---
uid: 01HZP3K8M9X2KMSYNCCTX
status: verified
kind: note
project: km-sync
---

# 📌 PROJECT CONTEXT — km-sync

> Obsidian（SoT）→ Notion（Mirror）的同步 CLI。靜態長週期內容；高頻進度寫進目標卡 Stage Log。
> 程式碼 repo 在 `/Users/juiyujao/Projects/km-sync`（本筆記只放知識，不放程式碼）。

## Scope
- One-line：掃描 Vault → 去敏感 fail-fast → 兩階段 idempotent upsert 至 Notion → 報告。
- Constraints：純函式引擎 + TDD；敏感命中即整批 fail（Zero Leak）；契約為 `data-contract.yaml`（`dev-notion-mirror@1.1`）。

## ADR Index（只列索引，不寫動態狀態）
- 兩階段同步（先 dev_goals 後 dev_stage_log），確保 relation 可對應。
- Fingerprint 雙存：本地 `06_Exports/sync_state.json` + Notion `內容指紋` 欄位。

## Environment（敏感一律 token）
- Notion token / database_id：`notion.config.local.json`（已 gitignore，不入庫）。

## 狀態
- 動態進度見目標卡 [[goal-phase2]] 的 Stage Log。Phase 2a 純引擎已完成；2b Notion 推送待做。
