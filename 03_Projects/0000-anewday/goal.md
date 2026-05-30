---
uid: 01HZ3465792C94D9
status: verified
kind: dev_goal
project: 0000-anewday
stage: Ship
method: [Next.js, Supabase, Tailwind, Vercel]
tags: [web, ecommerce, fragrance]
phase_done: 3
phase_total: 3
mirror: true
source_date: 2026-05-24
---

# Goal：00:00 A NEW DAY 品牌官網上線與打磨

## 方法 Method
- Next.js 16 App Router + Supabase（SSR）+ Tailwind 4 設計系統
- 設計 token 化（DESIGN.md 為 SoT，禁止 raw hex）
- Resend 處理聯絡表單寄信，Supabase 存 contact_messages
- 部署於 Vercel，逐頁（P1/P2/P3）打磨

## DoD（完成定義 Definition of Done）
- 全站頁面（products / journal / quiz / about / stockists / contact / shipping）上線且符合設計規範
- 聯絡表單可寄信並寫入 Supabase
- 首頁與 quiz 的 UX 經視覺審查通過

## Stage Log
> [!progress] stage=Build date=2026-05-19 goal=01HZ3465792C94D9 seq=01
> did: 設計系統定稿（DESIGN.md approved）— 色票、字體、間距 token 化
> result: 設計進入 production-ready
> next: 實作 P1/P2/P3 頁面

> [!progress] stage=Build date=2026-05-23 goal=01HZ3465792C94D9 seq=01
> did: 實作 P1/P2/P3 — shipping / returns / series / contact / journal 頁；新增 contact_messages migration
> result: 主要頁面到位
> next: 首頁與 quiz 打磨

> [!progress] stage=Ship date=2026-05-24 goal=01HZ3465792C94D9 seq=01
> did: 首頁 P1+P2 polish、quiz 文案統一、Layer 2 audit（padding/圖片優化/contact spinner）
> result: 部署 Vercel，視覺審查通過
> next: 持續維運與內容更新
