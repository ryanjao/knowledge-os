---
uid: 01KSS7QEMGVS23YM2Q05G0CTX
status: verified
kind: note
project: investment-research-os
---

# 📌 PROJECT CONTEXT — AI Investment Research OS

> 個人本地 Python 工具：每週跑資料管線，用資本週期理論（Capital Cycle）基本面為美股評分，產出離線 HTML 決策報告。
> 程式碼 repo 在 `/Users/juiyujao/Projects/investment-research-os`（本筆記只放知識，不放程式碼，也不放真實持倉/金額）。

## Scope
- One-line：每週 surface 美股訊號供人決策，不自動下單。
- Stack：Python、pandas/numpy、yfinance + FMP（基本面）、SQLite、Jinja2（HTML 報告）、PyYAML（watchlist）、pytest。
- 流程：`core_pipeline.py --theme <T>` 抓資料評分 → `generate_report.py` 產報告。

## Constraints
- **Human-in-the-Loop（鐵則）**：系統只 surface 訊號，買賣由人決定，任何階段都不自動執行下單。
- 基本面來源在 call time dispatch：有 `FMP_API_KEY` 用 FMP，否則 yfinance（`--free`）。
- yfinance 經 curl_cffi 模擬 Chrome TLS 規避 Yahoo Edge 429。
- 評分用絕對門檻（非百分位），含 200 SMA 趨勢過濾。

## 模組邊界（core_pipeline.py）
- DatabaseManager（SQLite、FK、同日去重）
- DataFetcher（yfinance 價格/技術 + FMP 基本面，每呼叫 try/except）
- AlphaEngine（絕對門檻評分）
- SystemOrchestrator（argparse CLI）

## ADR / 文件索引
- CLAUDE.md（架構與執行說明）
- docs/phase2-backlog.md（Phase 2/3 延後想法）

## Environment（敏感一律 token，真實值只存 05_Secrets/，永不上雲）
- FMP API key: {{SECRET_IROS_FMP_API_KEY}}
