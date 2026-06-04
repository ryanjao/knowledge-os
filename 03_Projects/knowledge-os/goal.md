---
uid: 01KKMOSSELFGOAL0001
status: verified
kind: dev_goal
project: knowledge-os
stage: Build
method: [TDD, Python, Bash]
phase_done: 0
phase_total: 1
mirror: true
source_date: 2026-06-03
---
# Goal：knowledge-os 系統本身的開發

## 方法 Method
- spec → plan → TDD 實作 → dogfood
- 守 §8.1 人工核准閘；SoT append-only

## DoD
- Session Wrap + /km-review promotion 閉環可用
- 候選 promote 前有結構驗證鐵閘 + 白話審查單

## Stage Log
<!-- /km-review 由此 append [!progress] -->

> [!progress] stage=Research date=2026-06-02 goal=knowledge-os seq=01
> did: 閱讀 Trellis（mindfold-ai）AI coding agent 記憶框架，與 knowledge-os 做架構對照。Trellis 用 .trellis/（tasks PRD + workspace journal + 自動注入 spec），4 階段迴圈 Plan→Implement→Verify→Finish，Finish 把 learnings promote 回 spec。
> result: 確認其 Finish promotion ≈ 本專案 Session Wrap + /km-review；關鍵差異點：Trellis promotion 自動入 spec，knowledge-os 刻意保留人工 review gate。最值得借鏡：Trellis 的 Verify 階段在 promote 前先做 spec 符合性自動檢查（對應上次手動的 b208a92 規格符合性修正）。另查證：03_Projects/ 下無 knowledge-os 自身的 dev_goal 目標卡，故本則 goal= 回退為 knowledge-os。
> next: 評估把「spec 符合性檢查」做成 Session Wrap 流程的自動 gate（事前驗證取代事後修）；為 knowledge-os 系統本身建一張 dev_goal 目標卡，讓 progress 有歸屬 uid（延續 2026-06-01 候選的 next）。

> [!progress] stage=Design date=2026-06-03 goal=knowledge-os seq=01
> did: 把 km-review 三塊升級寫成設計 spec：docs/superpowers/specs/2026-06-03-km-review-upgrade-design.md。涵蓋 A 結構驗證器（Python+TDD，validate_candidate.py，吐 rule_id；UI 與規則解耦）、B /km-review 接驗證器後渲染白話「入庫審查單」、C knowledge-os 自我 dev_goal 目標卡 + slug 自動解析、D 雙保險待審提醒（收尾 hook 尾巴 + session 開場）。
> result: spec 完成並自我檢查（無 TBD、uid 一致、範圍單一）。關鍵範圍切割定案：驗證器只攔「結構」（缺欄位/破框/檔名/goal 解不到），語意完整度留給審查時的人。守 §8.1 人工 Y 閘不動。尚未 commit（等使用者過目）。
> next: 使用者 review spec → commit → 進 writing-plans 寫實作計畫（TDD 順序：驗證器測試→驗證器→km-review 接線→目標卡→提醒）→ 實作完跑 /km-review 清 6/01、6/02 backlog 順便 dogfood。

> [!progress] stage=Build date=2026-06-03 goal=01KKMOSSELFGOAL0001 seq=02
> did: 用 subagent-driven 執行 km-review 升級實作計畫（11 task + 1 review 修正，全 TDD）：結構驗證器 validate_candidate.py（Python stdlib，17 測試）、/km-review 接驗證器+白話審查單、knowledge-os 自我目標卡 01KKMOSSELFGOAL0001、雙保險待審提醒（Stop hook 尾段 + SessionStart hook）。最後跑出第一次真實 /km-review promotion。
> result: Python 17 + bash 16 測試全綠；三個真實候選結構通過；首次真 promotion 併入 2 progress（6/02/6/03）+ 3 lesson（6/01）+ playbook 4 行，並由人工閘擋下 6/01 一筆矛盾 progress。commits 4e12528..9097684 已在 main。SoT promotion 變更尚未 commit。
> next: commit 本次 promotion 的 3 個 SoT 檔；視需要修 review 留下的小限制（callout 內文空行截斷、hook hash 大小寫邊界）；之後可動手寫 knowledge-os 對外介紹文。

> [!progress] stage=Build date=2026-06-04 goal=01KKMOSSELFGOAL0001 seq=03
> did: 研究 knowledge-os 介紹文撰寫方向：對照三個 superpowers skill（subagent-driven-development、brainstorming、TDD）的寫作結構，分析其「痛點先行／流程圖／紅燈清單」模式；並以 README.md 作為素材基礎，提出三種介紹文切入角度。
> result: 產出三方案比較：A 痛點敘事文（dev.to/X）、B 系統設計概念文（GitHub/HN，Trellis 風）、C 一天流程 walkthrough（高轉換率但需截圖）。建議先做 B 打底 + A 社群傳播，C 留到有 demo 素材。使用者尚未選定方向，文章尚未生成。README 已用方式 B 更新並 commit（d146658）。
> next: 使用者確認撰寫方式後，生成對應介紹文；優先推薦先寫 B（GitHub 概念文）搭配 A（dev.to 敘事文）。

> [!progress] stage=Build date=2026-06-04 goal=01KKMOSSELFGOAL0001 seq=04
> did: 跑 /km-review 清空 _candidates/：核准並併入 2026-06-03 Build seq=02（km-review 升級實作）和 2026-06-04 Build seq=03（介紹文研究）兩筆 progress，及 requesting-code-review/green-tests-false-confidence 一筆 lesson。
> result: _candidates/ 清空；goal.md Stage Log 新增 seq=02/03；lessons.md 新增第 5 筆；playbook.md 新增第 5 行索引。SoT 變更尚未 commit。
> next: commit 本次 promotion 變更；推 GitHub 後可考慮在社群發布 README 介紹文（dev.to / X）。

> [!progress] stage=Build date=2026-06-04 goal=01KKMOSSELFGOAL0001 seq=01
> did: 完成 pm-suite 設計 brainstorming session。探索使用者現有 Notion 專案結構（政府 IT 標案：調查局、刑事局、高檢署），設計主框架（側邊欄 + Google Calendar 月視圖 + 告警橫條）、看板（混合式、專案層級顏色標籤、已完成未記錄欄）、AI 文件解析流程（PDF/Word → Claude API 抽取 → Notion 暫存 → 人工確認 → 回寫 SQLite）、Notion 多向同步策略。確定架構：Next.js + SQLite（本機，存 OneDrive/GDrive sync 資料夾）+ Notion REST API + Claude API。設計文件已 commit 至 knowledge-os/docs/superpowers/specs/2026-06-04-pm-suite-design.md（commit bd17c8a）。
> result: pm-suite 設計 spec 完整，覆蓋 8 大功能區塊、資料模型、多機同步策略、6 個 Phase 概要、開源安裝流程。Supabase MCP 同時完成授權。
> next: 在 knowledge-os/03_Projects/ 建立 pm-suite 目標卡（goal.md），然後切換 model 開始 Phase 1 實作（Next.js 基礎框架 + SQLite 設定 + 側邊欄 + 首頁行事曆）。

> [!progress] stage=Build date=2026-06-04 goal=01KKMOSSELFGOAL0001 seq=05
> did: 跑 /km-review 清空 _candidates/（2 筆）：候選 1（1090b430，km-review 自身執行記錄 seq=04）與候選 2（b7a92737，pm-suite 設計 session seq=01）均 approve，共併入 2 progress + 3 lesson（mcp-needs-auth、sync-architecture、missing-table），並追加 3 行 playbook 索引。SoT commit 979d54d。
> result: _candidates/ 清空；goal.md Stage Log 累計至 seq=05；lessons.md 新增 3 筆（共 8 筆）；playbook.md 新增 3 行。
> next: 切換 model，開始 pm-suite Phase 1 實作（計畫在 knowledge-os/docs/superpowers/plans/2026-06-04-pm-suite-phase1.md）。
