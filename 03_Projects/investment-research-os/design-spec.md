---
uid: 01M80TKWY35YMB7BWSG1M7A43G
status: verified
kind: note
project: investment-research-os
tags: [finance, research, capital-cycle, design-spec]
mirror: false
source_date: 2026-05-31
---

# 設計規格書 — AI Investment Research OS

> 整合自 Notion：頭腦風暴 rev2 / 階段式開發規畫 / reports 報告生成 /
> Phase 1 實際執行狀態 / 使用說明（2026-05-31 整理）

## 1. 投資哲學（Philosophy）

### 核心 Thesis
基於**資本循環理論（Capital Cycle）**：Alpha 來源為資本供給 vs 基礎建設需求失衡，以及多年期投資週期錯配。

### 投資主題
- AI 基礎設施（AI Infrastructure）
- 電網現代化（Power Grid）
- 核能 / 能源轉型（Nuclear Energy）
- 資料中心（Digital Infrastructure）
- 工業電氣化

### 核心優勢（Edge）
大多數市場參與者看：價格、技術指標、短線故事。
本系統看：機構資金流、CapEx 擴張週期、盈餘修正動能、流動性結構。

---

## 2. 系統邊界（Constraints）

### Portfolio
- 規模：約 200 萬台幣
- 市場：美股；市值 ≥ 20 億 USD；成交量 ≥ 200 萬股/日

### Exposure 上限
- 單股 ≤ 15%；單產業 ≤ 35%
- 禁入：小型股、流動性陷阱、高價差資產

### Human-in-the-Loop（鐵則）
AI 只 surface 訊號與推導理由；100% 買賣決策由人執行，任何階段不自動下單。

---

## 3. 失效條件（Kill Switch）

任一條件成立 → 進入全面檢討模式（停止新部位，重新評估主題）。

| 面向 | 條件 |
|------|------|
| 績效 | 6M Alpha < 0 vs SPY；Sharpe 持續下降；連續 2 季輸 Benchmark |
| 風險 | Max Drawdown > 15%；勝率 < 35%（30 trades 樣本）；波動超標 |
| 結構 | AI CapEx 轉負；流動性反轉；主題全面崩潰 |

---

## 4. 風險哲學

### 非對稱框架（Antifragile）
- **Downside 有限且已知**：進場前即可計算硬停損 = 進場價 − 2 × ATR。
- **Upside 不設頂板**：趨勢持續則持有，直到跌破 200 SMA 或 Kill Switch 觸發。

### 停損邏輯
- 初始硬停損：`進場價 - 2 × ATR`（報告自動計算並顯示）
- 動態停利（Trailing Stop）：獲利超 2×ATR → 移停損至成本；後續每創新高 → 停損跟至 `最高價 - 3×ATR`

### 優先序
生存 → 控回撤 → 穩定複利 → 報酬

---

## 5. 系統架構（Architecture）

```
core_pipeline.py      — 資料管線 + 評分
generate_report.py    — 讀 SQLite → Jinja2 → 離線 HTML
portfolio.py          — 交易帳本 CLI（add / positions / txns）
watchlist.yaml        — 主題與股票清單（YAML 驅動，不動 code）
templates/            — report_template.html（embedded CSS）
reports/              — 輸出：YYYY-MM-DD_<theme>_Report.html
investment_os.db      — SQLite 資料庫
tests/                — pytest 6 個測試檔（86 tests 全綠）
```

### core_pipeline.py — 4 OOP Classes

| Class | 職責 |
|-------|------|
| `DatabaseManager` | SQLite init、FK 約束、同日去重防衛 |
| `DataFetcher` | yfinance（價格/技術）+ FMP（基本面）；try/except 全包，失敗回 0 |
| `AlphaEngine` | 絕對門檻評分、200 SMA 趨勢判斷 |
| `SystemOrchestrator` | argparse CLI，串接上述三個 class |

---

## 6. 資料庫設計（SQLite Schema）

**資料庫**：`investment_os.db`

### `stocks`
```sql
ticker TEXT UNIQUE
company_name TEXT
theme TEXT          -- e.g. "AI_Infrastructure"
```
由 `watchlist.yaml` 同步維護，不硬編碼。

### `metrics`
```sql
date TEXT, ticker TEXT         -- UNIQUE(date, ticker) ON CONFLICT REPLACE
price REAL, sma_200 REAL, atr REAL
trend_status TEXT              -- 'UPTREND' | 'DOWNTREND'
capex_growth REAL, eps_revision REAL, fcf_yield REAL
alpha_score REAL               -- 0–100
raw_data TEXT                  -- JSON 原始 API 數據（Debug 用）
```

### `transactions`（交易帳本）
```sql
ticker TEXT, action TEXT       -- 'BUY' | 'SELL'
shares REAL, price REAL, trade_date TEXT, notes TEXT
```
Ledger 設計：保留全部 BUY/SELL 歷史；持倉 = 動態彙總，avg_cost 加權平均法計算。

---

## 7. Alpha Score 演算法（絕對門檻法）

Phase 1 捨棄百分位排序，改用絕對門檻——樣本少時仍穩定，API 缺值給 0 分不 crash。

| 因子 | 權重 | 得分規則 |
|------|------|---------|
| CapEx Growth YoY | 50% | >20%→50；>10%→30；>0%→10 |
| EPS Revision (90d) | 30% | >10%→30；>0%→15 |
| FCF Yield | 20% | >5%→20；>0%→10 |

### 決策訊號路由

| 訊號 | 觸發條件 |
|------|---------|
| 🟢 強烈建議 | Alpha ≥ 85 **且** UPTREND |
| 🟠 可考慮 | Alpha 70–84 **且** UPTREND |
| ⚪ 觀望 | Alpha < 70 **或** DOWNTREND |

**風控覆寫**：即使 Alpha 100 分，跌破 200 SMA → 強制「觀望」。

---

## 8. 基本面資料來源

| 類型 | 來源 | 備注 |
|------|------|------|
| 股價 / SMA / ATR | yfinance | 技術面主力 |
| CapEx / EPS / FCF | FMP API | 付費；有 `FMP_API_KEY` 才走此路徑 |
| CapEx / FCF fallback | yfinance cashflow | `--free` 或無 key 時使用 |
| EPS Revision fallback | yfinance `eps_trend` | current vs 90daysAgo（屬性可能消失） |

**429 防禦**：`curl_cffi.requests.Session(impersonate="chrome")` 模擬 Chrome TLS 指紋；
yfinance 需 ≥ 1.0（0.2.x 忽略 injected session，仍會 429）。

---

## 9. 報告生成規格（Report Spec）

**技術堆疊**：Python + pandas + Jinja2 + SQLite → 離線 HTML

### 設計決策
- **Zero CDN**：CSS 全部嵌入 `<head>`，無網路環境下排版不崩壞。
- **兩段式版面**：
  - **持倉區（Portfolio）**：報酬率、未實現損益、停損距成本 %、Rationale
  - **觀察區（Watchlist）**：Alpha 分、趨勢、假設停損、Rationale 推導
- **Rationale 欄**：每筆顯示 CapEx / EPS Rev / FCF 各項得分，及風控覆寫是否觸發。

### 風控指標（報告自動算）
```
硬停損 = price - 2 × ATR
```

---

## 10. Spec vs 實作差異（Phase 1）

| 項目 | 原 Spec | 實際實作 |
|------|---------|---------|
| yfinance 版本 | 0.2.40 | 1.4.0（Yahoo Edge 升級，0.2.x 被 429 擋） |
| 基本面來源 | 僅 FMP | Hybrid FMP + yfinance fallback，`--free` 動態切換 |
| 股票清單 | 硬編碼 VRT/GEV/CEG | watchlist.yaml 驅動，含驗證 |
| 交易記錄 | 無 | Ledger 設計：transactions table |
| 報告格式 | 單一表格 | 兩段式（持倉 + 觀察），含 Rationale |
| macro_status | 寫死 "RISK ON" | 顯示 "未啟用 (Phase 2 Macro Engine)"，避免誤導 |
| EPS Revision 口徑 | 90 天上修 | FMP ≈ 9 個月偏移 vs yfinance ≈ 90 天（Phase 2 待統一） |

**不採納的外部建議**：
- `ScoreResult + __float__` 魔法方法 → 過度工程
- OpenBB Platform → Phase 1 依賴太重，Phase 2 再評估
- Web UI (FastAPI/Next.js) → 個人週用工具，CLI + 靜態 HTML 已足

---

## 11. 階段規劃（Phase Roadmap）

### Phase 1（完成）
本地管線：core_pipeline.py + generate_report.py + portfolio.py，pytest 86 tests 全綠。

### Phase 2（進行中）

| 功能 | 說明 |
|------|------|
| Macro Engine | VIX / Yield Curve / Net Liquidity → RISK ON/OFF，取代 macro_status 佔位 |
| EPS 口徑統一 | FMP 改為真 90 天 vs 90 天前預估，對齊 yfinance |
| 已實現損益 | SELL 完保留 "已售出" 記錄，顯示 realized P&L |
| 多主題擴充 | 電網 / 核能 / 資料中心加入 watchlist |

### Phase 3（6 個月真實交易後再評估）
- 完整 Risk Engine + Position Sizing（Kelly + 波動調整 + Regime Multiplier）
- Kill Switch 自動監控
- 回測系統（Backtesting）+ Walk Forward Analysis（防過度最佳化）

---

## 12. 日常使用指引

### 一週標準流程
```bash
cd /Users/juiyujao/Projects/investment-research-os

# 1. (可選) 編輯 watchlist.yaml 加減股票
# 2. 抓資料 + 算分
python3 core_pipeline.py --theme AI_Infrastructure --free
# （有 FMP key 時拿掉 --free）
# 3. (可選) 記帳
python3 portfolio.py add --ticker VRT --action BUY \
  --shares 100 --price 250.00 --date 2026-05-31
# 4. 生報告
python3 generate_report.py --theme AI_Infrastructure
open reports/*.html
```

### 關鍵規則
- **watchlist.yaml**：只改 yaml，不動 code；主題名只能用字母/數字/底線。
- **dedup guard**：同一天重跑會跳過；要強制重抓加 `--force`。
- **賣出上限**：不能賣超過持有股數（系統會擋）。
- **ticker 前提**：必須先在 watchlist.yaml，才能記交易。

### 常見錯誤
| 訊息 | 原因 | 處理 |
|------|------|------|
| `ticker 'XXX' not in stocks` | 未加入 watchlist | 先改 yaml 再跑管線 |
| `cannot SELL N: only M held` | 賣超過持有 | 查 `portfolio.py positions` |
| `Today's data already fetched` | 同日已跑 | 正常防呆；要重抓加 `--force` |
| `HTTP Error 429` | Yahoo 封 IP | 等 5–10 分鐘或換網路 |
| `Insufficient history` | 上市未滿 200 交易日 | 暫無趨勢，技術面給 0 |
