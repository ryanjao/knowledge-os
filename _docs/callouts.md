# Callout 字典

Callout 是「可被整理」內容的最小單位（atom）。類型越少越好，避免分類地獄。

## 一般類型
| 類型 | 用途 |
|------|------|
| `[!bug]` | 已發生問題 + 解法/線索 |
| `[!question]` | 尚未理解，需補課/查證 |
| `[!idea]` | 靈感、策略、假設 |
| `[!note]` | 一般紀錄（中性） |
| `[!decision]` | 決策（會導向 ADR 或專案筆記） |
| `[!risk]` | 風險/雷區（含避免路徑） |

## `[!progress]`：階段日誌（會被同步工具抽取）

固定格式，讓腳本可機器解析成 Dev Stage Log：

```markdown
> [!progress] stage=Build date=2026-05-29 goal=01HZP3K8M9X2
> did: 串接綠界測試金流，修正 hash 計算
> result: 400 -> 200，但 WAF 還有阻擋
> next: 加入 retry/backoff + 調整 header
```

- header 屬性：`stage` / `date` / `goal`(對應 dev_goal 的 uid) / `seq`(同日多筆序號，可省)。
- body 鍵：`did` / `result` / `next`。
- 缺 `goal` → 視為未關聯日誌，仍可投影但不建 relation。
- 同步唯一鍵：`{goal_uid}#{date}#{seq}`，同一天多筆用 seq 不互相覆蓋。
