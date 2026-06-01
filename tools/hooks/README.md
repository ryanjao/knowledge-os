# Session Wrap Capture — Hook

## 它做什麼
每次 Claude Code session 結束（Stop 事件），若當前 repo 根目錄有 `.km-project`，
hook 會讓 Claude 用自身 context 寫一塊候選草稿到
`<vault>/01_Inbox/_candidates/`，之後用 `/km-review` 核准併入 SoT。

## `.km-project` 慣例
在「要追蹤開發進度的 code repo」根目錄放一個 `.km-project`，
內容為對應的 vault 專案 slug（單行），例如：

    investment-research-os

沒有此檔的 repo，hook 一律 no-op，不打擾。

## 安裝（全域 settings.json）
在 `~/.claude/settings.json` 的 `hooks` 加入（與既有 hook 並存）：

    "Stop": [
      {
        "hooks": [
          { "type": "command",
            "command": "bash /Users/juiyujao/Projects/knowledge-os/tools/hooks/km-session-wrap.sh" }
        ]
      }
    ]

vault 路徑可用環境變數 `KM_VAULT` 覆寫（預設 /Users/juiyujao/Projects/knowledge-os）。

## 測試
    bash tools/hooks/test/run-tests.sh
