---
uid: 01KSESSIONWRAPLESSONS0001
status: verified
kind: note
title: "教訓集 Lessons（append-only）"
mirror: false
---

# 教訓集 Lessons

> Session Wrap 收尾捕捉、`/km-review` 核准後追加於此（append-only，不重排、不搬家）。
> 每筆對應一個 `[!lesson]`。彙整索引見 [[playbook]]。

<!-- /km-review 由此行下方往下 append [!lesson] callouts -->

> [!lesson] skill=test-driven-development stage=Build error=macos-bash3.2-multibyte
> what: reason 字串裡變數緊接中文（goal=$project。）在 macOS bash 3.2 觸發 unbound variable
> fix: 變數緊接非 ASCII 字元時用 ${project} 大括號界定
> rule: bash 腳本中變數後接中文/全形標點，一律用 ${var} 大括號

> [!lesson] skill=communication stage=Build error=language-drift
> what: 對話中途無故從繁體中文切成日文，使用者全程用繁中、repo 也是繁中
> fix: 改回繁體中文並承認無正當依據
> rule: 固定對齊使用者與 repo 的語言，勿無訊號漂移語言

> [!lesson] skill=writing-plans stage=Build error=dataview-callout-limitation
> what: 原設計 playbook=Dataview，但 Dataview 無法解析 callout 標頭屬性（> [!lesson] skill=... stage=...），無法 group-by
> fix: 改用 /km-review 維護的 append-only 索引檔（04_MOCs/playbook.md），貼合 spec §9 append-only 哲學
> rule: 規劃前先確認查詢層能否讀到資料形狀；callout 標頭屬性非 Dataview 可查

> [!lesson] skill=subagent-driven-development stage=Build error=tool-unavailable
> what: skill 假設可用 SendMessage 續派同一 subagent 修小問題，但本環境無此工具
> fix: 對 4 行測試這種瑣碎 review 修正，改由 controller 直接套用
> rule: 別假設 SendMessage 存在；瑣碎 review 修正 controller 直接做即可，不必為此另派 subagent

> [!lesson] skill=requesting-code-review stage=Build error=green-tests-false-confidence
> what: 驗證器 17 測試全綠，但 final review 仍抓到 parser 會把「相鄰、無空行分隔的第二個 callout」整個吞掉、完全不驗——等於死板鐵閘可被排版繞過
> fix: _parse_callouts body 迴圈遇到 CALLOUT_START_RE 即 break，並補回歸測試；最終 17 測試
> rule: 測試全綠≠無漏洞；對「宣稱死板的閘」一定要派獨立 review 找邊界繞過，別只信自己寫的測試覆蓋
