---
uid: 01KSS7QEMGVS23YM2Q05G0RSZ3
status: verified
kind: dev_goal
project: investment-research-os
stage: Validate
method: [Python, yfinance, FMP, SQLite, Jinja2]
tags: [finance, research, capital-cycle]
mirror: true
source_date: 2026-05-29
---

# Goal：每週自動產出美股決策報告（Capital Cycle 評分）

## 方法 Method
- 週期管線：抓價格/技術（yfinance）+ 基本面（FMP/yfinance）→ AlphaEngine 絕對門檻評分
- watchlist.yaml 驅動主題；SQLite 儲存、同日去重
- Jinja2 產離線 HTML 報告（watchlist + portfolio 兩區）
- Human-in-the-Loop：只 surface 訊號，不自動下單

## DoD（完成定義 Definition of Done）
- 一條指令能跑完管線並產出當週 HTML 決策報告
- 報告含跨主題 overview、決策理由、資料新鮮度標示
- 交易帳本（transactions ledger）可記錄並反映在 portfolio 區

## Stage Log
> [!progress] stage=Build date=2026-05-28 goal=01KSS7QEMGVS23YM2Q05G0RSZ3 seq=01
> did: Phase 1 完成 — 管線 + AlphaEngine 評分 + Jinja2 HTML 報告，凍結依賴
> result: 可離線產出週報；FMP+yfinance 混合基本面、429 規避到位
> next: 交易帳本與 portfolio 區

> [!progress] stage=Validate date=2026-05-29 goal=01KSS7QEMGVS23YM2Q05G0RSZ3 seq=01
> did: 交易帳本 + portfolio/watchlist 兩區報告、跨主題 overview、資料新鮮度標示
> result: 報告升級為決策簡報，watchlist 用真實主題（AI_Platforms / Nuclear_Energy 等）
> next: 以真實交易驗證訊號品質

> [!progress] stage=Validate date=2026-05-29 goal=01KSS7QEMGVS23YM2Q05G0RSZ3 seq=02
> did: 定義 Phase 2 backlog（position sizing / rebalance / ranking 訊號，皆 surface-only）
> result: 範圍明確，維持 HITL；Phase 3 風險引擎留待 6 個月真實交易後
> next: 累積真實交易紀錄，再評估 Phase 2
