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
