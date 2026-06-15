---
uid: 01HZ3465792C94D9
status: verified
kind: dev_goal
project: 0000-anewday
stage: Build
method: [Next.js, Supabase, Tailwind, Vercel]
tags: [web, ecommerce, fragrance]
phase_done: 3
phase_total: 6
mirror: true
source_date: 2026-06-01
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

> [!progress] stage=Build date=2026-05-28 goal=01HZ3465792C94D9 seq=01
> did: 完成後台系統基礎建設 — ADMIN.md 設計規格（tokens、排版、10 種元件、頁面原型）；Supabase admin_users 資料表 + RLS + is_admin() function；proxy.ts 雙層 auth 守門（middleware + server component）；admin shell（layout、sidebar、topbar）；login 頁；dashboard placeholder
> result: /admin/* 路由全部上鎖，後台設計規格與 auth 架構定案
> next: 後台訂單列表頁 → 產品列表頁 → Dashboard KPI cards

> [!progress] stage=Build date=2026-05-31 goal=01HZ3465792C94D9 seq=01
> did: 前台 P1/P2/P3 細節打磨 — FeaturedSection 色彩修正、Hero shadow、Quiz scrim + 圖片優化、copy 對齊（移除「四分鐘」framing）、shipping/contact/journal 頁完稿
> result: 前台頁面視覺與 copy 達到設計規格，P1/P2/P3 可進 Phase 5 audit
> next: 後台訂單列表頁實作；或 Phase 5 雙層 audit

> [!progress] stage=Build date=2026-05-31 goal=01HZ3465792C94D9 seq=02
> did: ADMIN.md 規格依雙評論修訂（字級 12px floor、weight 600 錨點、amber 語意子角色、功能性 shadow、48px 間距、CRUD modal 例外、mobile 監控模式、WCAG AA 聲明、新增 4.11 品牌專屬元件 Ritual Timeline/Scent Performance/Daily Ritual Card）；定義後台 Admin Phase A0–A5 流程（對照前台 v4.0）；完成 A2 Dashboard 標準部分 — KpiCard + StatusBadge 元件、admin-globals.css token 同步、新 migration（admin RLS policies + products.stock/low_stock_threshold）、page.tsx 接真實 Supabase 資料（KPI row + 近期訂單表）
> result: ADMIN.md 平衡可用性與品牌辨識度；A2 Dashboard typecheck + lint clean；品牌元件（Daily Ritual Card）留位待 A1.5 客戶校準；KPI「Awaiting action」取代規格的「Items shipped」（操作價值更高）
> next: 跑 migration 20260531000000；A3 後台訂單列表頁（StatusBadge 共用、detail drawer）→ A4 產品列表（inline stock edit）→ A5 雙層 audit

> [!progress] stage=Build date=2026-05-31 goal=01HZ3465792C94D9 seq=03
> did: A2 Dashboard 瀏覽器驗收通過（指定帳號設為 super_admin 登入成功，KPI/badge/mono/空狀態/sidebar active 全部正確渲染）；修掉登入 42501 — admin_users 表建立時漏給 authenticated 的 table GRANT（RLS policy 只過濾 row 不授權表存取），補 migration 20260531010000_grant_admin_users_select；migration 20260531000000（admin RLS + products.stock）已 db push 套用
> result: 後台 Dashboard 端到端可用；admin auth 完整打通（client form + server layout + proxy 三層查詢都靠 authenticated 對 admin_users 的 SELECT）
> next: A3 訂單列表 — 先驗 authenticated 對 orders 的 UPDATE 權限（detail drawer 會改狀態，可能同樣缺 GRANT）；Status tabs + 可篩選 table + 右側 detail drawer。元件可重用 StatusBadge。檔案位置：app/admin/{page.tsx, components/, orders/}

> [!progress] stage=Build date=2026-05-31 goal=01HZ3465792C94D9 seq=04
> did: A3 後台訂單列表頁完成。先驗權限：orders/order_items 的 RLS policy 齊全（Admins view/update via is_admin()），但 authenticated 缺 table GRANT（只有 REFERENCES/TRIGGER/TRUNCATE）— 與 admin_users 同根因。storefront 沒踩到是因為下單走 create_order() SECURITY DEFINER RPC，從不直接讀寫這兩張表。補 migration 20260531130610（grant select,update on orders + select on order_items to authenticated），db push 套用（同時補套了 seq=03 漏進 migration history 的 20260531010000）。以 set local role authenticated + super_admin JWT 模擬驗證：is_admin()=true、orders/items SELECT 各可見 2 筆、UPDATE rows_updated=1（TEST 單改 shipped 後復原 pending）。實作 orders/page.tsx（server fetch + force-dynamic）+ OrdersClient（Status tabs 含每狀態計數 + client 端篩選 table，重用 StatusBadge，整列可點開 drawer）+ OrderDrawer（min(520px,92vw) 右側 slide-over：Customer/Line items/Shipping/Payment/Summary/Timeline 區塊、4.11 Ritual Timeline 單線 amber、情境式 amber primary「Mark as shipped→delivered」+ ghost destructive「Cancel order」、Esc/backdrop 關閉）；狀態變更走 server action updateOrderStatus（RLS 過濾零列時回精確錯誤、revalidatePath('/admin/orders' + '/admin')）。drawer 內容保留與 pending/error reset 提升到 OrdersClient 用事件驅動 state，避免 React Compiler lint 禁止的 setState-in-effect / ref-in-render。
> result: typecheck + lint + next build 全綠；orders 資料層端到端打通。連帶修復：Dashboard 先前 orders SELECT 其實一直因缺 GRANT 而 42501，被 page.tsx 的 `?? []` 吞掉誤render空狀態 — seq=03「空狀態正確」其實是假象，現已會顯示真實 2 筆 pending 單。GRANT 缺漏是真實 bug 非預期。
> next: A3 瀏覽器視覺驗收 —（指定 super_admin 帳號登入）驗 tabs 篩選 + 計數、drawer 開/合 520ms slide 動畫、Mark as shipped 後 badge 即時更新、Cancel order destructive。通過後 → A4 產品列表頁（inline stock edit，重用 products.stock/low_stock_threshold）→ A5 雙層 audit。

> [!progress] stage=Build date=2026-05-31 goal=01HZ3465792C94D9 seq=05
> did: A4 後台產品列表頁完成。同 A3 先驗權限：products 的 RLS policy 齊全（Admins view/insert/update via is_admin() + Products are publicly readable），但 authenticated 一樣缺 table GRANT（只有 postgres 有 DML）。確認 storefront 不受影響 — fetchProducts() 以 anon 查詢、出錯就 fallback 靜態 PRODUCTS（app/lib/products.server.ts:46），所以前台一直跑靜態資料；補 migration 20260531132152（grant select, update on products to authenticated，不給 anon，INSERT 待 add-product flow），db push 套用。SQL 模擬驗證（set local role authenticated + super_admin JWT）：3 筆產品 SELECT 可見（abundance/clearing/drowsiness，stock 40 / threshold 10 / active）、stock UPDATE rows=1（clearing 改 7 後復原 40）。實作 products/page.tsx（server fetch + force-dynamic）+ ProductsClient（縮圖 next/image 用 /images 本地路徑 · Name zh+en · Slug〔schema 無 sku 欄，用 slug 當唯一碼〕· Price · Stock · Status table）。Stock 欄即 4.11 Inventory Atmosphere：mono 數字（≤threshold 轉 amber）+ 單一位置刻度（非進度條、reference = max(50, threshold×5) 軟上限）；點數字 → inline 編輯（autoFocus input、Enter/blur commit、Esc 取消，走 server action updateStock + revalidatePath）。Status badge = Active/Inactive（sage / draft wash）。inline edit state 全用 local component state + autoFocus，避開 React Compiler lint 禁制。
> result: typecheck + lint + next build 全綠；/admin/products 為 dynamic route。連帶修復 Dashboard low-stock KPI（先前同樣因缺 products GRANT 而 SELECT 失敗被 ?? [] 吞掉，永遠顯示 all healthy）。略過 spec 的「Add product」amber 按鈕（同 A3「New」判斷 — 無建立流程不放假按鈕，待專門 flow）。
> next: A3 + A4 瀏覽器視覺驗收（super_admin 登入：A3 tabs/drawer/狀態變更；A4 inline stock edit 即時更新 + low-stock amber + Inventory Atmosphere 刻度）。通過後 → A5 雙層 audit（後台全頁對照 ADMIN.md 規格 + 可用性）。可選：補 add-product flow（需 INSERT GRANT + 產品編輯 drawer）。

> [!progress] stage=Build date=2026-06-01 goal=01HZ3465792C94D9 seq=01
> did: A3+A4 遠端瀏覽器驗收 + 一輪修正與新功能。遠端管道：起 cloudflared quick tunnel 讓另一台電腦連 localhost:3000；遠端登入失敗根因＝Next.js 16 預設擋非 localhost 的 dev 資源（/_next/webpack-hmr），HMR WebSocket 被擋導致 hydration 壞 → 加 allowedDevOrigins: ['*.trycloudflare.com'] 重啟解決。依使用者逐張截圖回饋修正：(1) 產品縮圖破圖 — seed（20260520121806）把 items 2/3 存成 /images/item2.png、item3.png 但實際檔案是 .jpg（item1 .jpg 正常、靜態 products.ts 也用 .jpg）→ migration 20260601000000 UPDATE 回 .jpg、db push。(2) A4 庫存欄「Inventory Atmosphere」位置刻度無實際語意 → 依要求改成「數字 + 上下箭頭 stepper」（覆寫 ADMIN.md 4.11；箭頭 ±1 即時走 updateStock 存檔、數字仍可點擊直接輸入）。(3) A3 detail drawer 把直式 Ritual Timeline 改成「完整橫向進度條」Placed→Confirmed→Shipped→Delivered（已達填 amber、當前加 glow ring；覆寫 ADMIN.md 4.11；cancelled 走專屬終止條 Placed→Cancelled）。(4) Orders 狀態 tabs 未選取字色太暗（fg-2→fg-1、計數 fg-4→fg-3、hover→amber）。(5) sidebar header 56px ≠ topbar 52px 致兩條底線錯位 → header 改用 var(--admin-topbar-h) 對齊成一直線。(6) 進度條時間字色太暗（fg-3/10px → fg-2/12px）。各階段時間戳：orders 原僅 created_at/updated_at，無法逐階段顯示時間 → migration 20260601010000 加 confirmed_at/shipped_at/delivered_at/cancelled_at（回填現有訂單「當前階段」=updated_at，更早階段無真實資料留 null）；updateOrderStatus 轉換時同步寫對應 *_at 欄；orders/page.tsx select + AdminOrder 型別 + OrderProgress 讀各階段時間。新功能（使用者要求）：(a) Admin 訂單搜尋框 — order_number+name+phone+email 即時 client 過濾、與 tab 疊加。(b) Admin 列印 — 每列 checkbox + 表頭全選（限當前可見列）+ 工具列 Print 按鈕（顯示選取數）+ app/admin/orders/print.ts 開新視窗產生可列印出貨單（收件人/地址/品項/金額），詳細版型待真實營運再定。(c) 客戶端 pending 訂單可編輯收件資訊（姓名/電話/縣市/區/地址）+ 取消訂單 — migration 20260601020000 新增 update_my_order / cancel_my_order 兩個 SECURITY DEFINER RPC（沿用 create_order 模式，函式內驗證 owner=auth.uid()+status='pending'、只改交付欄或設 cancelled，避開 row-level RLS 無法限制欄位導致客戶竄改金額/狀態的風險），grant execute to authenticated；MemberCenterPage 訂單記錄對 pending 單顯示「編輯收件資訊／取消訂單」，編輯展開內嵌表單（重用 tw-districts 行政區資料）走 rpc，取消有 window.confirm 二次確認。
> result: 全部 typecheck + eslint 乾淨；三個 migration（20260601000000 圖片路徑、010000 各階段時間戳、020000 客戶自助 RPC）皆 db push 套用；dev server 回 200。遠端 dev 驗收管道打通。安全：客戶自助走 SECURITY DEFINER RPC 而非客戶 UPDATE policy，金額/狀態不可被竄改。已知限制：既有 delivered 測試單（AND20260521BFJL85）只回填得到 delivered_at，confirmed/shipped 因追蹤上線前未記錄而留白，僅新轉換訂單才有完整各階段時間；主流程 pending→shipped 跳過 confirmed，故 Confirmed 階段時間目前永不會被寫。設計債：ADMIN.md 4.11 兩個品牌元件（Inventory Atmosphere、Ritual Timeline）被使用者要求覆寫為更實用形式，規格文件與 code 現已不一致。
> next: 回寫 ADMIN.md 4.11（Inventory Atmosphere → 數字 stepper、Ritual Timeline → 橫向進度條），使 git-repo 設計 SoT 與 code 一致〔ADMIN.md 屬 git 例外文件，不走 Obsidian pipeline〕。與客戶確認真實出貨單列印版型。可選：補 admin「Mark as confirmed」動作（補上 confirmed 階段時間來源）。其後 → A5 雙層 audit。

> [!progress] stage=Build date=2026-06-02 goal=01HZ3465792C94D9 seq=01
> did: 啟動首頁「多版型探索」迭代（目的：給客戶挑版型，雛形與功能已完成）。方法＝比較淘汰法，每輪產 3 個真實 HTML mockup + Playwright 截圖（hero + mid-scroll）讓使用者選 best/worst，產出存 design-iterations/round-NN/ 永不刪。已跑 7 輪：Loop 1（R1 三景並置B → R2 B3 → R3「時刻切割」C3 勝出）；Loop 2（R4 整頁重做但商品段重複版型被否決 → R5 E2 全頁沉浸序列 → R6 F2 文字中心 → R7 G2 勝出）。方法升級：研究 GitHub 設計 skill，讀 taste-skill 全文發現它把本品牌核心長相列為 AI-slop 前兩名（#1 襯線當預設、#2 暖奶油+陶土+近黑字 premium-consumer 色票）——但兩條禁令都附「品牌 brief 明文指名即豁免」，本案有 DESIGN.md + 品牌 PDF，故 Cormorant + terracotta/slate 合法（且 terracotta+slate 本就在 skill 核可替代名單）；真正 AI 感來源是「每段一個 eyebrow + 三段同版型 + 幾乎無動態」。隔離：開 git worktree `/Users/juiyujao/Projects/0000-anewday-design`（分支 design/homepage-iterations，從 main 1a766d8），7 輪 mockup 全搬入、圖片同步，main 工作區與 DESIGN.md/正式碼完全不動；本機預覽 server 改從 worktree 根跑 8081。重用方法封裝：14 個全域 skill stage 在 /private/tmp/_skills_install/（自寫 design-iteration orchestration + 官方 frontend-design + taste-skill/soft/minimalist + distinctive-frontend + 官方 gsap×8 含 scrolltrigger），待使用者跑一行 cp 裝進 ~/.claude/skills/（全域寫入需本人核准，agent 被安全分類器擋）。
> result: 迭代與正式碼實體隔離、零污染；目前淘汰賽候選＝C3（Loop 1）、G2（Loop 2）。跨專案可重用的「視覺設計迭代辦法」已封裝成 design-iteration skill（待安裝即生效）。使用者 2026-06 授權迭代期間可探索鎖定外字體，但僅活在拋棄式 mockup，不編輯 DESIGN.md 規則。記憶已記：project-design-iteration-setup、feedback-design-iteration（含反 slop 檢查表）。
> next: 使用者下次接續＝(1) 在輸入框跑安裝指令 `!mkdir -p ~/.claude/skills && cp -R /private/tmp/_skills_install/. ~/.claude/skills/`（若 /tmp 已清，clone 原始碼也在 /private/tmp 可重 stage）；(2) cd 進 worktree 起 server：`cd /Users/juiyujao/Projects/0000-anewday-design && python3 -m http.server 8081`；(3) 說「開始 Loop 3」→ 我用 design-iteration orchestration 產 Round 8 三個整頁全新方向（隨機 Taste 三轉鈕 DESIGN_VARIANCE/MOTION_INTENSITY/VISUAL_DENSITY + 1–2 craft lever + GSAP scroll 動態 + 出稿前過反-slop 檢查、本輪字體可放開）。設計債仍在：回寫 ADMIN.md 4.11（承上一條 next，本次未處理）。

> [!progress] stage=Build date=2026-06-02 goal=01HZ3465792C94D9 seq=02
> did: 首頁版型迭代續跑 Loop 3–5（Round 8–16，每輪 3 個整頁全新 HTML + Playwright 截圖選 best/worst）。Loop 3 暗底純版式：H1 字型建築勝 → I1 深淺切割/I3 時間軸縱剖（兩個都喜歡）→ J3 斜體收斂勝出（Cormorant 斜體標題 + terracotta 脊線）。Loop 4 換全新前提「離開暗底」：K1 日光書頁勝 → L1 雜誌跨頁/L2 目錄索引/L3 留白攝影集（三個都讚）→ M1 美術館陳列 + M3 上線級精修（兩個都收）。Loop 5 換「結構本身」前提：N1 色域分塊/N2 模組網格/N3 長文捲軸 → N3 勝（N1 也有趣）→ Round B 長文支線 O1 一封信/O2 註解版/O3 大字朗讀**三個全被否決**（使用者：太像讀書、轉換意圖弱、且圖片撐不起文意導致亂）→ 轉向 Round C 改強化 N1 色域分塊：P1 純色塊/P2 錯位對角/P3 色溫日弧 → P3「好點但不夠好」，未加冕。關鍵判斷：Loop 5 整輪在「冷結構」territory 打轉，而使用者情感反應一直集中在暖 cream 攝影/編輯感（Loop 4 的 L/M 全部「都很棒」）。素材瓶頸確認＝可用圖僅 pano×3 + 有浮水印的 moisture-dropper mockup，版型越依賴單張照片敘事越亂。產出圖片補拍 prompt：審視使用者既有 12-prompt（A1–F，已蓋滿 DESIGN.md §8 清單），補 4 條缺口 prompt（補1/補2 直幅 9:16 沉浸/手機 Hero、補3 留白疊字 Hero 16:9、補4 上油身體細節 macro 3:2，沿用同 style DNA + --no 區塊）。收檔：worktree design-iterations 原 untracked，先 commit 完整 16 輪軌跡（7ae17e8 可復原），再 prune 工作區到 8 候選並 commit（b9acb56）。
> result: 候選池定為 8 個＝C3（Loop1 時刻切割）· G2（Loop2 漸暗序列）· J3（Loop3 斜體脊線）· I1（Loop3 深淺切割）· L1（Loop4 雜誌跨頁）· M1（Loop4 美術館陳列）· M3（Loop4 色溫精修上線版）· N1（Loop5 色域分塊）。最強 territory 已收斂：暖 cream 攝影/編輯感（L/M 群）。Loop 5 冷結構（網格/長文/色塊）證實智性不同但情感弱，不再發明冷前提。記憶已更新 feedback-design-iteration（Loop1–5 方向偏好 + 素材瓶頸 + 判斷捷徑）。工作區清爽（132K，8 檔），完整淘汰軌跡留在 git 7ae17e8。
> next: 使用者尚未做最終淘汰賽。下次接續二選一：(A)「把候選拉出來比」→ 我並排截圖 C3/G2/J3/I1/L1/M1/M3/N1 選 1 個最終首頁方向進實作；(B)「回暖 cream territory 再精修」→ 在 L/M 群再跑 3 個更精的版。預覽 server 從 worktree 起：`cd /Users/juiyujao/Projects/0000-anewday-design && python3 -m http.server 8081`，候選在 design-iterations/round-{03,07,09,10,12,13,14}/。圖片補拍：4 條 prompt 待使用者用 Midjourney 跑（直幅 Hero + 留白疊字 + 上油 macro）。設計債續欠：回寫 ADMIN.md 4.11（Inventory stepper / Ritual 橫向進度條），本次仍未處理。

> [!progress] stage=Build date=2026-06-02
> did: feat: admin panel (A2–A4) + customer order edit + pano PNG refresh
> result:
> next:

> [!progress] stage=Design date=2026-06-04 goal=01HZ3465792C94D9 seq=01
> did: 首頁版型最終淘汰賽完成，8 個候選縮減為 3 個（C3 / J3 / M1，不分排名）；淘汰 G2 / I1 / L1 / M3 / N1，worktree 清檔
> result: 候選池剩 C3（round-03 時刻切割）· J3（round-10 斜體脊線）· M1（round-13 美術館陳列），完整淘汰軌跡可由 git 7ae17e8 回溯
> next: 從 C3 / J3 / M1 選定最終首頁方向，或以某個為基底精修後進 main 實作
