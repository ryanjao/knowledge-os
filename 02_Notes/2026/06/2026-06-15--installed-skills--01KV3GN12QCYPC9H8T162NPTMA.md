---
uid: 01KV3GN12QCYPC9H8T162NPTMA
title: 已安裝 Skill 清單與版本檢查
status: verified
kind: reference
domain: tooling
tags: [skills, claude-code, plugins, inventory, maintenance]
source_date: 2026-06-15
mirror: false
---

# 已安裝 Skill 清單與版本檢查

> Claude Code 環境中安裝與自製的所有頂層 skill（不含子 skill）。
> Notion 對應頁：知識管理 ▸ 已安裝 Skill 清單 Installed Skills。

## 版本檢查紀錄

- **2026-06-15**：全部最新、無重複。移除重複的舊 `superpowers@superpowers-marketplace`（5.0.7），保留官方 `superpowers@claude-plugins-official`（5.1.0）。supabase 0.1.11 / context7 / hookify / code-review 經 `claude plugin update` 確認皆為最新。

## 安裝的 Skill（10 個）

| Skill | 版本 | 來源 | 目的 |
| --- | --- | --- | --- |
| superpowers | 5.1.0 | anthropics-official | TDD、系統化除錯、寫計畫、平行子代理、程式碼審查等開發工作流方法論 |
| document-skills | rolling | anthropics/skills | Word/PDF/Excel/PPT 文件讀寫生成，含前端設計、品牌、MCP 開發、網頁測試 |
| ui-ux-pro-max | 2.5.0 | nextlevelbuilder | UI/UX 設計智庫：50+ 風格、161 配色、字體配對、UX 準則 |
| context7 | rolling | anthropics-official | 即時抓取函式庫/框架/API 最新官方文件 |
| supabase | 0.1.11 | anthropics-official | Supabase DB/Auth/Edge Functions/RLS 與 Postgres 效能最佳化 |
| code-review | rolling | anthropics-official | 審查分支或 PR 差異，找正確性錯誤與簡化/重用/效能改進 |
| claude-md-management | 1.0.0 | anthropics-official | 稽核並改善各 repo 的 CLAUDE.md 專案記憶檔 |
| hookify | rolling | anthropics-official | 依不想要的行為產生 hook 規則，攔截並預防重複犯錯 |
| taste-skill | 1.0.0 | Leonxlnx/taste-skill | 前端設計品味包：極簡/粗獷/柔和/重設計/圖轉碼等美學風格 |
| gsap-skills | 1.0.0 | greensock/gsap-skills | 官方 GSAP 動畫包：tween/timeline/ScrollTrigger/React/效能 |

## 自行開發的 Skill（2 個）

| Skill | 位置 | 目的 |
| --- | --- | --- |
| gmail-organizer | `~/.claude/skills/`（全域）| 依規則自動標籤/封存/丟垃圾 Gmail，遇未知寄件者暫停詢問並同步規則到 Notion |
| km-review | `knowledge-os/.claude/commands/`（專案）| Session Wrap 候選審核守門員，「提議→預覽→核准→寫入」併入 SoT |

## 每月 Skill 更新檢查 SOP

1. `claude plugin marketplace update` — 刷新所有 marketplace 來源。
2. 對每個 plugin 跑 `claude plugin update <plugin>@<marketplace>`（已最新則 no-op）。
3. `claude plugin list` 確認版本、檢查是否有重複安裝。
4. 更新本筆與 Notion 頁面的「版本檢查紀錄」日期。
5. 已排程每月自動提醒執行此檢查。
