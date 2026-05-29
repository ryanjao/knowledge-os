---
uid: 01HZ3465792C94CTX
status: verified
kind: note
project: 0000-anewday
---

# 📌 PROJECT CONTEXT — 00:00 A NEW DAY

> 台北香氛品牌電商網站。靜態長週期內容；高頻進度寫進 LOG.md / 目標卡的 Stage Log。
> 程式碼 repo 在 `/Users/juiyujao/Projects/0000-anewday`（本筆記只放知識，不放程式碼）。

## Scope
- One-line：00:00 A NEW DAY（一個新的開始）品牌官網與電商，含 products / journal / quiz / about / stockists / contact / shipping / admin。
- Stack：Next.js 16（App Router）、React 19、Supabase（@supabase/ssr）、Tailwind CSS 4、Resend（寄信）、Zustand、Framer Motion。
- 部署：Vercel（0000-anewday-vercel-app）。

## Constraints
- **設計定稿不可重定義**：所有色票/字體 token 以 `DESIGN.md` + `colors_and_type.css` 為唯一真理源，引用 CSS 變數，**禁止用 raw hex**。
- 一個畫面只放一個主要 CTA（`--terracotta`）。
- 背景用 `--cream`、內文用 `--navy`，不用純白/純黑。

## ADR / 重要文件索引
- DESIGN.md（設計 SoT，2026-05-19 approved）
- ADMIN.md / AGENTS.md / CLAUDE.md
- docs/（P1/P2/P3 設計與實作計畫）

## Environment（敏感一律 token，真實值只存 05_Secrets/，永不上雲）
- Supabase URL: {{SECRET_ANEWDAY_SUPABASE_URL}}
- Supabase anon key: {{SECRET_ANEWDAY_SUPABASE_ANON_KEY}}
- Supabase service role: {{SECRET_ANEWDAY_SUPABASE_SERVICE_ROLE}}
- Resend API key: {{SECRET_ANEWDAY_RESEND_API_KEY}}
