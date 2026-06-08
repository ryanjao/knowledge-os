---
uid: 01RYANPHOTO000001
status: verified
kind: dev_goal
project: ryan-photographer-site
stage: Build
method: [Astro, Tailwind-v4, GSAP, Playwright, Vercel]
tags: [web, photography, portfolio, lead-gen]
phase_done: 4
phase_total: 6
mirror: true
source_date: 2026-06-08
---

# Goal：Ryan 攝影師個人網站（導購＋接案）上線

## 方法 Method
- 調整版 KMOS 網頁開發流程（小型網站裁切版）
- Astro 6 + Tailwind v4 靜態站；subagent-driven 實作；先蓋骨架後做設計迭代
- 表單 Formspree、部署 Vercel、Playwright 煙霧測試

## DoD（六階段）
- Phase 1：規格 + 實作計畫 ✅
- Phase 2：基礎建設（Astro/Tailwind v4 token/共用元件/內容模組）✅
- Phase 3：作品集照片接入（219 張、6 分類）✅
- Phase 4：四頁開發 + 設計定案（米古銅 + Fraunces + GSAP；首頁 R2 Hero+磚牆瀑布、服務頁 S3 圖文雙欄）✅
- Phase 5：Impeccable 雙層 Audit ⬜
- Phase 6：部署 Vercel（Formspree endpoint + 自訂域名）⬜

## 相關文件
- 程式碼與規格/計畫：`/Users/juiyujao/Projects/ryan-photographer-site/`（獨立 git repo，branch `build/portfolio-site`，最後 commit `a36a3e0`）；規格/計畫在該 repo `docs/superpowers/`
- KMOS 流程：Notion「網頁開發流程」已升級 v4.1（新增小型網站裁切版 + 動效層 GSAP）

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
