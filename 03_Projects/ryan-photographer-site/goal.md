---
uid: 01RYANPHOTO000001
status: verified
kind: dev_goal
project: ryan-photographer-site
stage: Ship
method: [Astro, Tailwind-v4, GSAP, Playwright, Vercel]
tags: [web, photography, portfolio, lead-gen]
phase_done: 6
phase_total: 6
mirror: true
source_date: 2026-06-08
---

# Goal：Ryan 攝影師個人網站（導購＋接案）上線

## 方法 Method
- 調整版 KMOS 網頁開發流程（小型網站裁切版）
- Astro 6 + Tailwind v4 靜態站；subagent-driven 實作；先蓋骨架後做設計迭代
- 詢問頁採前端「填表→產生文字→複製貼 IG」產生器（零後端，取代 Formspree）；部署 Cloudflare Pages；Playwright 煙霧測試

## DoD（六階段）
- Phase 1：規格 + 實作計畫 ✅
- Phase 2：基礎建設（Astro/Tailwind v4 token/共用元件/內容模組）✅
- Phase 3：作品集照片接入（219 張、6 分類）✅
- Phase 4：四頁開發 + 設計定案（米古銅 + Fraunces + GSAP；首頁 R2 Hero+磚牆瀑布、服務頁 S3 圖文雙欄）✅
- Phase 5：Impeccable 雙層 Audit ✅（第一層 high-effort code-review 8 面向 → 修復 3 項：①resize 跨 640px 作品格卡 opacity:0 ②表單 endpoint 缺失靜默丟資料 ③hero CSV 守門；第二層 simplify/過度設計檢查 → 程式碼已最小、無修改）
- Phase 6：部署 Cloudflare Pages ✅（`ryan-photo-ab.pages.dev` production 已上線最新版，`--branch=main`；詢問頁改前端 IG 產生器，Formspree 不再需要）

## 相關文件
- 程式碼與規格/計畫：`/Users/juiyujao/Projects/ryan-photographer-site/`（獨立 git repo，branch `build/portfolio-site`，最後 commit `2b52dad`）；規格/計畫在該 repo `docs/superpowers/`
- KMOS 流程：Notion「網頁開發流程」已升級 v4.1（新增小型網站裁切版 + 動效層 GSAP）

## 待辦 Todo
- 買網域 → 啟用 Cloudflare 原生寄信（詢問表單 → Gmail，$0/月；僅網域 ~US$10/年）
- 補孕婦寫真照片（maternity 目前僅 1 張，牆面偏薄）
- 刪掉已合併的 build/portfolio-site 分支（repo 收尾）

## Stage Log
<!-- /km-review 由此 append [!progress] -->

> [!progress] stage=Build date=2026-06-08 goal=01RYANPHOTO000001 seq=01
> did: 完成設計規格與實作計畫（brainstorming→writing-plans），以 subagent-driven 執行 Phase 3–5 計畫的 Task 1–9：Astro 6 scaffold、Tailwind v4 @theme design token、共用元件、內容模組（8 服務真實定價/FAQ/評價）、四頁、Playwright。把 219 張 IG 作品移入 src/assets/portfolio 的 6 分類並接上首頁 gallery。
> result: 4 頁建置成功、測試全綠。關於頁下線、詢問頁加參考圖上傳。發現並修正環境雷區：Avast 誤刪含 shell 指令的 .md 計畫檔。
> next: 進行整體視覺設計迭代（使用者不滿意暫定樣式）。

> [!progress] stage=Build date=2026-06-08 goal=01RYANPHOTO000001 seq=02
> did: 用 /preview 多輪迭代讓使用者選定設計：字體 Fraunces+Noto Serif TC、配色米·古銅、首頁 R2 Hero（左字右拼貼）+磚牆瀑布作品牆、服務頁 S3 圖文雙欄；導入 GSAP 滾動動效（scripts/motion.ts，含 prefers-reduced-motion）。並依「IG 圖多為 4:3/4:5」修正全站不硬裁。查出 GSAP 之前漏掉的根因並把「動效層」補進 KMOS v4.1。
> result: 設計定案、首頁+服務頁完成、6 測試綠。最後 commit a36a3e0。共用模組 lib/portfolio.ts、components/BookingFaq.astro。
> next: ①詢問頁版面選版 ②Phase 5 Impeccable Audit ③部署 Vercel（建 Formspree 帳號填 endpoint）。

> [!progress] stage=Validate date=2026-06-19 goal=01RYANPHOTO000001 seq=03
> did: 首頁定案收尾（每週自動輪播 HERO 組合池 + 種子洗牌「全部」磚牆、CSV 控制檔、HERO↔牆每週去重、行動版 hero 修正）。跑 high-effort code-review（8 面向）對整個 build/portfolio-site 分支做 Phase 5 第一層 audit。
> result: 修復 3 項並實測綠：①resize 跨 640px 作品格卡 opacity:0（applyAll(reveal) 強制顯示）②PUBLIC_FORM_ENDPOINT 缺失→表單靜默送回自己頁，改 IG 後備 + build 警告 ③新增 build 守門：HERO_POOL 每張須 CSV hero=Y（py 9 反向測試擋下）。commit 71c02ae。確認線上版為 Cloudflare Pages ryan-photo-ab.pages.dev（非原訂 Vercel）。
> next: ①`wrangler pages deploy dist` 推最新版上線（手機驗證）②設 Formspree PUBLIC_FORM_ENDPOINT ③跑 /ponytail-review 補 Phase 5 第二層 ④完成即進 Ship。

> [!progress] stage=Ship date=2026-06-19 goal=01RYANPHOTO000001 seq=04
> did: 詢問頁砍掉 Formspree 表單，改成純前端「填表→自動產生 IG 詢問訊息→複製貼 IG」產生器（服務下拉附參考價、期望日期自由文字、風格、採購衣服+1000/造型老師+5000 加購勾選即顯示、即時預估總額、複製鈕含 execCommand 後備）。零後端＝靜默丟資料問題一併消除。Phase 5 第二層 simplify/過度設計檢查 → 程式碼已最小、無修改。
> result: 6 Playwright 測試全綠（含改寫的 contact 產生器測試）。commit 2b52dad。`wrangler pages deploy --branch=main` 上線 production，已驗證 `ryan-photo-ab.pages.dev/contact` 即新版產生器。專案進 Ship。
> next: ①買網域 + Cloudflare 原生 Email Sending（form→Gmail，$0/月，待網域）為後續加值 ②repo 收尾：build/portfolio-site 併回 main。
