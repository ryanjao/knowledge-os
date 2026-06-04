---
uid: 01PMSUITE00000001
status: draft
kind: dev_goal
project: pm-suite
stage: Build
method: [Next.js, SQLite, Claude-API, Notion-API, TDD]
phase_done: 0
phase_total: 6
mirror: true
source_date: 2026-06-04
---
# Goal：PM Suite — 政府標案專案管理系統

## 方法 Method
- Brainstorm → spec → writing-plans → TDD 實作（每 phase 一個 plan）
- Next.js + SQLite 本機，資料存 OneDrive/GDrive sync 資料夾
- Notion 為審閱介面（AI 解析草稿確認後才入庫）

## DoD
- Phase 1：基礎框架可跑（側邊欄 + 首頁月曆 + 告警條 + SQLite）
- Phase 2：看板（拖曳、標籤、欄位管理）
- Phase 3：文件上傳 + Claude API 解析 + Notion 寫入
- Phase 4：Notion 雙向同步（PM→Notion 自動推）
- Phase 5：Email 通知、資安提醒、定期月會自動建立
- Phase 6：多用戶登入

## 相關文件
- Spec：`docs/superpowers/specs/2026-06-04-pm-suite-design.md`
- Phase 1 計畫：`docs/superpowers/plans/2026-06-04-pm-suite-phase1.md`
- 程式碼：`/Users/juiyujao/Projects/pm-suite/`
