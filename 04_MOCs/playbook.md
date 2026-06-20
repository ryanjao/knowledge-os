---
uid: 01KSESSIONWRAPPLAYBOOK001
status: verified
kind: note
title: "做法 Playbook（階段 × skill × 錯誤，append-only 索引）"
mirror: false
---

# 做法 Playbook

> 由下而上長出來：每次 `/km-review` 核准一筆教訓，就追加一行索引（append-only）。
> 用 Obsidian 搜尋 `stage=Build` 或 `skill=` 即可拉出某階段/某 skill 的歷史教訓。
> （備註：採 append-only 索引而非 Dataview，因 Dataview 無法解析 callout 標頭屬性。）

格式：`- {date} — stage={stage} skill={skill} error={error} — {rule}`

## 索引
<!-- /km-review 由此行下方往下 append 一行索引 -->
- 2026-06-01 — stage=Build skill=test-driven-development error=macos-bash3.2-multibyte — bash 腳本中變數後接中文/全形標點，一律用 ${var} 大括號
- 2026-06-01 — stage=Build skill=communication error=language-drift — 固定對齊使用者與 repo 的語言，勿無訊號漂移語言
- 2026-06-01 — stage=Build skill=writing-plans error=dataview-callout-limitation — 規劃前先確認查詢層能否讀到資料形狀；callout 標頭屬性非 Dataview 可查
- 2026-06-01 — stage=Build skill=subagent-driven-development error=tool-unavailable — 別假設 SendMessage 存在；瑣碎 review 修正 controller 直接做即可，不必為此另派 subagent
- 2026-06-03 — stage=Build skill=requesting-code-review error=green-tests-false-confidence — 測試全綠≠無漏洞；對「宣稱死板的閘」一定要派獨立 review 找邊界繞過，別只信自己寫的測試覆蓋
- 2026-06-04 — stage=Build skill=mcp error=mcp-needs-auth — 看到 MCP setup 警告時優先呼叫 authenticate 工具，勿直接呼叫其他 MCP 工具
- 2026-06-04 — stage=Build skill=system-design error=sync-architecture — 雙向同步設計先分「需 AI 判斷」vs「純 API 呼叫」，後者設計為自動化不需 Claude 介入
- 2026-06-04 — stage=Build skill=data-modeling error=missing-table — 資料模型完成後掃描所有外鍵，確認每個 *_id 都對應已定義的表
- 2026-06-04 — stage=Build skill=architecture error=sqlite-on-cloud-sync — 永不把活的 SQLite/WAL 放雲端區塊級同步資料夾；跨機同步「靜止快照」或用 sync-aware 後端，勿同步活檔
- 2026-06-04 — stage=Build skill=architecture error=llm-as-data-bus — AI 只當一次性資料提取器（產 draft），不可當資料同步管道；結構化 upsert/diff 一律走確定性程式碼 + 穩定外部 ID
- 2026-06-04 — stage=Build skill=slash-command error=wrong-skill-invocation — 輸入形似 slash command（km-review/km-sync）先查 .claude/commands/ 有無對應 .md，有則直接讀取執行，勿呼叫 Skill 工具
- 2026-06-04 — stage=Build skill=writing-plans error=goal-card-missing-stagelog — 建立 dev_goal 目標卡時就內建 ## Stage Log 區塊與 km-review marker，讓後續 progress 有固定落點
- 2026-06-04 — stage=Build skill=system-design error=stale-context-note — 判斷工具能力以程式碼為準，CONTEXT/README 路線圖可能落後實作；回報「做不到」前先驗證實際程式與設定檔狀態
- 2026-06-05 — stage=Build skill=architecture error=lock-blocks-same-machine-workers — Web 框架跑多 worker，檔案鎖粒度要是「機器/實例」而非「進程」，否則同機並發自我死鎖
- 2026-06-05 — stage=Build skill=typescript error=spread-default-duplicate-key — 提供預設值用 spread 在前覆寫在後，或預設欄位設 optional；build 型檢比 vitest 嚴，完工前一定跑 next build
- 2026-06-05 — stage=Build skill=systematic-debugging error=silent-filter-drop — 「該出現的東西沒出現」且工具無錯，先懷疑不符 filter 被靜默丟棄；對照已知正常樣本的 frontmatter 是最快定位法
- 2026-06-05 — stage=Build skill=systematic-debugging error=non-code-symptom-misattributed — 診斷前先確認符號由誰維護，別把靜態文字當動態狀態指標
- 2026-06-08 — stage=Build skill=writing-plans error=scaffold-version-drift — 計畫不硬寫框架版本；scaffold 後先驗證實際版本再適配，視為正常偏差
- 2026-06-08 — stage=Build skill=subagent-driven-development error=git-add-removed-path-aborts — git add 只列確實存在的路徑；commit 後 --stat 驗證實際內容，別假設成功
- 2026-06-08 — stage=Build skill=test-driven-development error=playwright-strict-multiple-match — 斷言可能重複出現的文字時預先 scope 或 .first()，避免 strict-mode 報錯
- 2026-06-08 — stage=Build skill=frontend-design error=force-crop-mismatched-aspect — 混合比例圖庫預設以原比例呈現；要統一裁切前先確認來源比例分佈
- 2026-06-08 — stage=Build skill=brainstorming error=vague-visual-feedback-loop — 主觀視覺回饋要並排實際渲染、隔離單一變項來收斂，而非靠文字描述猜測
- 2026-06-20 — stage=Build skill=security error=pipeline-scan-gap — 敏感掃描必須在每一個「寫入 SoT 前」的節點觸發，不只在「同步外部服務前」。
- 2026-06-20 — stage=Build skill=security error=classification-design — 敏感程度分級先從最小可行開始（confidential boolean），待實際使用再評估是否需要更細粒度。
