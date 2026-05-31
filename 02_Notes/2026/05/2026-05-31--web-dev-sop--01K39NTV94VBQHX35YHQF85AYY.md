---
uid: 01K39NTV94VBQHX35YHQF85AYY
title: 香氛電商網站開發流程 v3.1
status: draft
kind: runbook
domain: web
tags: [web, sop, ecommerce, nextjs, supabase, tailwind, workflow]
source_date: 2026-05-31
mirror: false
---

# 香氛電商網站開發流程 v3.1

vibe coding 開發實戰流程 — 從需求到上線的完整 SOP。

> [!note] 來源
> 由 Notion「vibe coding 專案開發 / 網頁開發流程」忠實整理回 SoT（2026-05-31）。Notion 為 Mirror，本檔為唯一真理源。

> [!idea] 適用範圍
> 本流程基於 **00:00 A NEW DAY 品牌官網**實戰提煉，適用 Next.js + Supabase + Tailwind 技術棧的中小型電商／品牌網站。

## 階段總覽
| 階段 | 名稱 | 產出 | 把關 |
|------|------|------|------|
| 0 | 需求釐清 | PRD、線框圖 | 需求凍結 |
| 1 | 設計系統 | DESIGN.md、token | 設計審查 |
| 2 | 骨架搭建 | 路由、layout | 結構審查 |
| 3 | 頁面實作 | P1/P2/P3 頁面 | 逐頁驗收 |
| 4 | 整合測試 | 表單、金流、SEO | 功能驗收 |
| 5 | 上線部署 | Vercel production | 上線檢查 |

## 階段 0：需求釐清
- 用一句話定義網站目標與目標客群
- 列出必要頁面清單（products / about / contact 等）
- 確認品牌素材：logo、色票、字體、產品圖
- 產出 PRD 與低保真線框圖
- **把關**：需求凍結，避免開發中反覆變更

## 階段 1：設計系統
- 建立 DESIGN.md 作為設計唯一真理源
- 色彩、字體、間距、圓角全部 token 化（禁止 raw hex）
- 定義元件規格：button、card、input、nav
- **把關**：設計審查通過才進入實作

## 階段 2：骨架搭建
- Next.js App Router 路由結構
- 共用 layout、Header、Footer
- Tailwind config 接上設計 token
- Supabase 專案建立、環境變數設定
- **把關**：結構審查，確認可擴展

## 階段 3：頁面實作（P1/P2/P3 分級）
- **P1（必要）**：首頁、產品列表、產品詳情、聯絡
- **P2（重要）**：關於、購物車、結帳、quiz/互動
- **P3（加分）**：journal/部落格、stockists、動效打磨
- 每頁三輪：骨架 → 內容 → polish
- **把關**：逐頁驗收，符合設計規範

## 階段 4：整合測試
- 聯絡表單：Resend 寄信 + Supabase 寫入 contact_messages
- 金流串接（若需要）：測試環境先行
- SEO：meta、OG image、sitemap、robots
- RWD：mobile / tablet / desktop 三斷點
- **把關**：功能驗收清單全過

## 階段 5：上線部署
- Vercel production 部署
- 自訂網域 + SSL
- 環境變數 production 設定
- Lighthouse 效能檢查（目標 > 90）
- **上線檢查清單**：
    - [ ] 所有頁面 RWD 正常
    - [ ] 表單可寄信並寫入 DB
    - [ ] SEO meta 完整
    - [ ] 404 / 錯誤頁
    - [ ] 密鑰不入版控

## 常見雷區
> [!risk] 常見雷區
> - **CORS / middleware 403**：檢查 Next.js middleware matcher 設定
> - **Supabase SSR**：使用 `@supabase/ssr`，勿用已棄用的 auth-helpers
> - **圖片優化**：用 `next/image` 並設定 `sizes` 屬性，避免 CLS

## 關聯
- 實例：`03_Projects/0000-anewday/`（00:00 A NEW DAY 品牌官網即依此 SOP 開發）
