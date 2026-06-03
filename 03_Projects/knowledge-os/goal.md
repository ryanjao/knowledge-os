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
