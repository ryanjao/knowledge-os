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
