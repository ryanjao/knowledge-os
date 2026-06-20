> **Note for new users:** This is the author's personal Backbone SOP — a 5-phase execution framework for AI-assisted development. Copy to `~/.claude/CLAUDE.md` (global, applies to all projects) or keep in this repo root (project-scope only).
> Before use, customise: (1) §0.7 Registry URL → your own Notion skill registry; (2) §5 km-sync path → your actual km-sync install path.
> Pairs with: https://github.com/ryanjao/knowledge-os

---

# CLAUDE.md — 開發骨幹 SOP（Execution Backbone）

> **狀態：v2.0-beta（§0 新增 YAGNI 鐵則含升級觸發 + 不可簡化區擴充；§1 Phase 3/4 加入 ponytail；§2 風險定義澄清；§3 Lite Card 補 YAGNI 初判 + Micro-task 說明；§7 Phase 3/4 產物補 ponytail 確認；§8 ponytail 狀態修正）。前版 v1.5 §5 全自動 KMOS。** 安裝位置：**全域 `~/.claude/CLAUDE.md`**。
> **鐵則範圍：所有專案在開始執行前，一律遵照本骨幹。** 不分網頁或一般專案，共用同一套 5-Phase 骨幹；差別只在 Phase 1/3 綁定的 skill 不同。
> **職責邊界：** 本檔只管「執行層」（怎麼把東西做出來）。知識層（session 開場讀進度、收場 sync）由 `knowledge-os` 負責，本檔只在 Phase 0 與 Phase 4 引用它，不重複實作。

---

## 0. 鐵則（Non-negotiables）

1. **先偵察，後動工。** 任何任務在進 Phase 1 之前，必須先跑 Phase 0。禁止「直接開問然後猛做」。
2. **Phase 0 必須留下 Recon Card。** 低風險任務可用精簡版，高風險/需人工核准任務用完整版（見 §3）。沒有 Recon Card = 沒完成偵察，不得進 Phase 1。
3. **每階段有 gate。** 未通過離開條件，不得進入下一階段。
4. **gate 可人工核准，也可條件式自動前進。** 判定規則見 §2，禁止模糊帶過。
5. **嚴格變更管制（Change Control）。** 回頭改**上一階段**的產出 = 變更請求。退回前強制撰寫 `<Impact_Analysis>`：界定作廢的設計區塊、需捨棄的程式碼、受影響的 DoD；推出版號後，重跑該階段 gate。Phase 3 內的實作細節決策（不影響上一階段產出的 DESIGN.md / ADR）不在此限，可直接在實作紀錄中說明。
6. **skill 綁在階段上，不臨場叫。** 要用哪個 skill 由階段決定（見 §1 表）。
7. **新裝 skill 必須登錄。** 任何時候安裝新 skill，當次就要在 Notion「已安裝 Skill 清單」新增一列（名稱·版本·來源·狀態·目的），否則視為未安裝。若因技術限制無法當次完成 Notion 登錄，須在 §8 明確標注「待登錄」，並列為 Phase 4 收尾必辦項目；Phase 4 完成前視為暫定可用，完成後才視為正式安裝。
   - Registry: （請替換為你自己的 Notion skill registry 頁面 URL）
8. **Session 開場確認（可觀測性）。** 在專案內每個 session 的第一個回應，最上方先輸出一行確認標頭，讓使用者一眼確認本骨幹已生效、目前在哪個 Phase：
   - 格式：`[骨幹 SOP <版本> 已生效 ✓] 專案=<名稱> · 進入點 Phase 0 偵察 · 先查 Registry、填 Recon Card 再動工`
   - `<版本>` 取本檔狀態列版號；無法判斷專案時標 `專案=（一般／無 .km-project）`。
   - **此標頭未出現 ＝ SOP 未載入的警訊**，使用者應檢查 CLAUDE.md 是否被讀取。
9. **YAGNI 最小化（Ponytail 原則）。** 進入 Phase 3 實作任何功能前，先過六階梯：
   ① 這需要存在嗎？→ 不需要：不寫，一行說明理由（YAGNI）。
   ② stdlib 能做？→ 用它。
   ③ 原生平台功能能做？（CSS > JS、`<input type="date">` > picker lib、DB constraint > app code）→ 用它。
   ④ 已裝的依賴能做？→ 用它；不得為幾行能做到的事新增依賴。
   ⑤ 一行搞定？→ 一行。
   ⑥ 最後才：寫最少量程式碼。

   **`ponytail:` 標記格式：** 有意識的捷徑必須標注 `ponytail:`，且需含兩個部分：(a) 捷徑說明 + (b) 升級觸發條件。
   ```
   # ponytail: 現在先不抽象化，只有一個 caller
   # upgrade when: 出現第 2 個 caller，或邏輯超過 30 行
   ```

   **永遠不得省略（不可簡化區）：**
   - 信任邊界的輸入驗證
   - 防資料丟失的錯誤處理（含高風險操作的 transaction / rollback）
   - 安全措施
   - 無障礙基礎
   - 可觀測性：關鍵錯誤訊息、必要 log（靜默失敗 = 禁止）

---

## 1. 骨幹流程（5 個 Phase）

| Phase | 進入條件 | 動作 | 綁定 skill | 離開 gate |
|---|---|---|---|---|
| **0 偵察 Recon** | 接到任務 | ① 判斷任務領域與風險 ② 查 Registry「我有什麼」 ③ 缺關鍵 skill → 記入 §8、走發現流程 ④ 填 Recon Card（精簡或完整，依風險） | `context7`（查最新外部文件） | ✅ **工具已確認**：Recon Card 完成、skill 清單已列、gate mode 已初判 |
| **1 設計 Design** | 工具已確認 | 鎖定架構 / 資料模型 / 樣式決策，寫成設計文件 | 一般：`document-skills`<br>網頁：`taste-skill` → `ui-ux-pro-max`（先美學品味，再 UI/UX 規範）+ 詳見網頁 playbook | ✅ **設計凍結**：DESIGN.md / ADR 已寫，並依 §2 判定人工核准或自動前進 |
| **2 規劃 Plan** | 設計凍結 | 拆 phase / 任務 / 驗收條件、排序；**強制標註高風險節點並給出降級方案（Fallback）** | `superpowers`（寫計畫、TDD 規劃、subagent 拆分） | ✅ **計畫核准**：任務清單 + DoD 明確 + 高風險退路已定義，並依 §2 判定 |
| **3 開發 Develop** | 計畫核准 | 按計畫實作，逐任務交付；**實作前先過 ponytail 六階梯（§0.9）** | `superpowers`（TDD/除錯/子代理）、`context7`（即時文件）、**`MACE`（標準除錯 skill）**、**`ponytail`（full mode 常駐，程式碼最小化）**<br>網頁：`supabase`、`gsap-skills` + 詳見網頁 playbook | ✅ **驗收通過**：`code-review` 跑過，測試綠 |
| **4 收尾 Wrap** | 驗收通過 | ① `code-review` 最終審 ② `/ponytail-review` 檢查過度設計 ③ 重複錯誤 → `hookify` 立 hook ④ 交給 KMOS 做 session wrap / sync | `code-review`、**`ponytail`（`/ponytail-review` 掃過度設計）**、`hookify`、`claude-md-management`（維護本檔）、`km-review`（KMOS 收場，**自動執行**，見 §5） | ✅ **已紀錄**：`/ponytail-review` 無過度設計（或積欠已列入 `ponytail-debt`）；§8 待登錄項目已完成 Notion 登錄；KMOS 候選已自動併入 |

---

## 2. Gate approval policy

所有 gate 都必須留下可檢查紀錄，但**不一定每次都需要人工核准**。目標是避免兩種失敗：**流程過重**（小修正都卡人工核准）與**流程失真**（名義有 gate、實際沒留設計/計畫/風險/驗收依據）。

### 2.1 Human approval required（必須人工核准）

- 新專案初始化
- 重大架構決策
- 影響資料模型 / DB schema / API contract 的**結構性或破壞性**變更
  > 澄清：「影響」= 刪除欄位、改型別、新增必填欄、改 API 回傳格式等結構性變更。新增 DB index（不改 schema）、新增可選欄位、非破壞性 API 新增，不在此限，可走 Auto-advance。
- 影響權限 / 安全 / 隱私 / 金流 / 成本的變更
- 生產環境高風險變更
- 大型 UI/UX 方向確認
- 涉及跨系統整合、資料遷移、不可逆操作
- 需求不明確且假設錯誤會造成高返工成本

```md
Gate mode: Human approval required
Status: Pending / Approved / Rejected
Approver:
Decision notes:
```
未取得 `Approved` 前，不得進入下一 Phase。

### 2.2 Auto-advance allowed（可條件式自動前進）

- 小型 bug fix
- 既有規格內的功能實作
- 文件整理 / SOP 微調
- 測試補強
- refactor 但不改外部行為
- 已有明確需求、DoD、rollback 的低風險任務
- 不改整體方向的 UI 小調整
- 內部工具 / 實驗分支，不影響 production
- 非破壞性 DB 變更（新增 index、新增可選欄位）

自動前進**不是跳過 gate**。採 Auto-advance 時，Phase 1/2 文件必須明列下列欄位，缺一不可：

```md
Gate mode: Auto-advance allowed
Reason:
Assumptions:
Risks:
Rollback / fallback:
DoD:
Status: Passed
```

### 2.3 預設規則

無法判斷時，**預設 `Human approval required`**。禁止為趕進度把高風險任務降級成 Auto-advance。

---

## 3. Phase 0 Recon Card

**選用規則：** 命中 §2.1 任一條（影響 production / schema / 安全 / 金流 / 不可逆…）→ 用**完整版**；其餘低風險任務 → 可用**精簡版**。

### 3.1 精簡版 Recon Card（低風險 / Auto-advance）

```md
# Recon Card (Lite)
- 任務 / 類型：
- 風險：低（不影響 production / schema / 安全 / 金流，且可逆）
- Gate mode：Auto-advance
- 本案 skill（依 §1 綁定表）：Phase1 ___ / Phase3 ___
- Registry 已查：是 / 否　缺口：無 / 已記入 §8
- YAGNI 初判：□ 整體任務可跳過 □ 部分子功能可跳過（已標記）□ 全部需要
```
> **Micro-task 說明：** 若任務為 typo 修正、README 小改、單行 bug fix，且同時符合：不影響 production/schema/API/security、≤ 2 個檔案、可 git revert——則 Phase 0–2 可合併為單一 Recon Card 段落（精簡版），ponytail 六階梯可以一句話代替（如「直接修正即為最小解，無需額外評估」）。
> 任一風險旗標翻成「是」→ 立即升級為完整版 + Human approval。

### 3.2 完整版 Recon Card（高風險 / 需人工核准）

```md
# Recon Card (Full)

## 1. 任務分類
- 任務名稱：
- 任務類型：□一般開發 □網頁開發 □文件/SOP □除錯 □研究/評估 □測試/品質 □維運/部署 □其他___

## 2. 風險判斷（任一為「是」即需 Human approval）
- 影響 production：□是 □否
- 影響資料模型 / DB schema / API contract（結構性/破壞性）：□是 □否
- 涉及權限 / 安全 / 隱私 / 金流 / 成本：□是 □否
- 不可逆或高返工成本：□是 □否
- 初步 Gate mode：□Human approval required □Auto-advance allowed
- 判定理由：

## 3. 本任務需要的能力
（架構 / 文件 / UI-UX / 測試 / 除錯 / 外部文件 / DB-後端 / 動畫 / 專案管理 / 其他）

## 4. Registry 查核
- 已查核：□是 □否
- 本案綁定 skill（依 §1，僅列實際要用的）：
- 缺口：□無 □有 ___　是否記入 §8：□是 □否，原因：

## 5. YAGNI 初判
- □ 整體任務可跳過（說明理由）
- □ 部分子功能可跳過（列出跳過項目）
- □ 全部需要做
- 備註（哪些是 speculative need、哪些已確認必要）：

## 6. Phase 0 Gate
- □工具已確認 □skill 清單已列 □缺口已記錄/確認無 □gate mode 已初判 □YAGNI 已初判
- Status：□Passed □Blocked
- 備註：
```
> 註：skill 綁定以 §1 表為單一真實來源，本卡不重列各 Phase 預設清單，只列「本案實際要用的」。

---

## 4. Skill 偵察：兩種節奏（Recon cadence）

**把「找新 skill」從每任務移到週期性，避免偵察變成瓶頸。**

- **每任務（快，Phase 0 內）：** 只查 Registry，從已裝的挑，填 Recon Card。幾秒鐘完成。
- **週期性（慢，每月排程 + 缺口觸發）：**
  - 每月跑 `claude plugin marketplace update` → 各 plugin `claude plugin update` → 更新 Registry「版本檢查」日期。（已排程）
  - **缺口觸發：** Phase 0 發現某領域 Registry 無對應 skill，記入 §8 待補，於週期性時段上 GitHub/marketplace 評估、安裝、登錄。不在當次任務臨時 yak-shaving。

---

## 5. KMOS 收場：全自動（決策更新 2026-06-16）

- **決策：** `/km-review` 自動執行；**並改為「自動放行 + 自動同步」**——促進後不標 `verified=no`，由 SessionStart hook 接著自動跑 `km-sync sync --no-autolog` 推到 Notion。目的：先讓資料全自動累積，日後 review Obsidian 紀錄的可用性，再決定是否維持全自動。
- **仍保留的硬保護（非選用）：**
  1. promote.py 機器結構驗證 gate：不過 → 隔離，不併入。
  2. km-sync 推送前的**敏感掃描 fail-fast**：命中（如明文憑證）即中止、零外洩。
- **可一鍵切回安全網：** 設環境變數 `KM_HOLD=1` → 促進改標 `verified=no`、暫不同步，需 `promote.py --verify-all` 才放行。若 review 後發現自動紀錄品質差，用此還原。
- **取捨：** 全自動移除了「人工逐筆把關」，記錯可能先進 Notion 才被發現；換取零摩擦累積。憑證外洩仍由敏感掃描擋住。
- **實作狀態：已實作。** `promote.py`（HOLD 開關，預設放行）+ `km-auto-promote.sh`（促進 → 自動 sync）+ `km-sync sync`。

---

## 6. 階段詞彙對齊（Stage vocabulary）

所有編號一律以本骨幹 Phase 0–4 為準。

**對 KMOS `stage` enum：**

| 本檔 Phase | KMOS `stage` |
|---|---|
| 0 偵察 + 1 設計 | `Idea` |
| 2 規劃 + 3 開發 | `Build` |
| 3 開發（驗收） | `Validate` |
| 4 收尾（交付） | `Ship` |
| 上線後維運 | `Maintain` |

**對「網頁開發流程 v5.0」既有編號（該 playbook 自有 Phase 0–5，須對映回本骨幹）：**

| 網頁 playbook | 本骨幹 |
|---|---|
| Phase 0 Skill 偵察（v5.0 新增） | **0 偵察** |
| 審美校準 + 視覺迭代 + 1.5 Firecrawl + Stitch | **1 設計** |
| 頁面排序規劃 | **2 規劃** |
| 基礎建設 + 頁面開發 + GSAP 動效 | **3 開發** |
| 雙層 Audit | **4 收尾** |

> 寫 goal card 用 KMOS enum；口語與流程文件一律用本骨幹 Phase 名。

---

## 7. 各 Phase 產物最低要求

避免 gate 只停在口頭確認，每個 Phase 至少留下：

| Phase | 最低產物 | 備註 |
|---|---|---|
| **0 Recon** | Recon Card（精簡或完整） | 沒有就不得進 Phase 1 |
| **1 Design** | DESIGN.md 或 ADR | 小任務可精簡，但須含 assumptions / risks / rollback / DoD |
| **2 Plan** | PLAN.md 或任務清單 | 須含任務排序、驗收條件、測試策略、高風險 Fallback |
| **3 Develop** | 實作紀錄、測試結果、review 結果；六階梯已確認；複雜任務的 `ponytail:` 標記需含升級觸發條件 | 測試未綠不得進 Phase 4 |
| **4 Wrap** | code-review 結果；`/ponytail-review` 確認（無過度設計，或積欠已列入 `ponytail-debt`）；§8 待登錄項目已完成 Notion 登錄；KMOS 候選紀錄 | 重複錯誤評估是否 hookify |

---

## 8. 已知缺口（Known gaps）

| 領域 | 現況 | 動作 |
|---|---|---|
| 理財 / 投資分析 | ✅ 已補（2026-06-16） | 裝官方 `financial-analysis` + `equity-research`（user scope）；疊在 Investment Research OS pipeline 上（pipeline 供資料、skill 做 DCF/估值/論點分析）。已登錄 Registry。 |
| 專案管理 PM | 無第三方 skill（刻意） | 決議不裝通用 PM skill（PMP 本人 + `superpowers` 已涵蓋規劃）；改列**自建待辦：pm-suite → 包成 callable skill**。 |
| 極簡主義開發 / YAGNI | ✅ 已補（2026-06-17） | 裝 `ponytail` v4.7.0（DietrichGebert/ponytail）全域；六階梯強制最小程式碼；`ponytail:` 標記含升級觸發條件；`/ponytail-review` 於 Phase 4 掃過度設計。已登錄 Registry。 |

---

## 9. 版本紀錄

### v2.0（2026-06-17）
- **§0.9 新增 YAGNI 最小化鐵則（Ponytail 原則）：** 六階梯強制執行；`ponytail:` 標記需含升級觸發條件（升級 when）；不可簡化區擴充加入高風險操作的 transaction/rollback 與可觀測性（關鍵錯誤訊息、必要 log）。
- **§0.5 Change Control 澄清：** 明確說明「Phase 3 內的實作細節決策不觸發變更管制」，消除與敏捷迭代的表面衝突。
- **§0.7 Registry 登錄寬限說明：** 無法當次登錄時，§8 標「待登錄」，Phase 4 必辦，完成後才正式算已安裝。
- **§1 Phase 3：** 動作欄新增「實作前先過 ponytail 六階梯」；skill 欄加入 `ponytail`（full mode 常駐）。
- **§1 Phase 4：** 動作欄新增 `/ponytail-review`；skill 欄補 ponytail；離開 gate 補 ponytail-review 確認 + §8 待登錄項目清零。
- **§2.1 風險定義澄清：** 「影響資料模型」限定為結構性/破壞性變更（改型別、刪欄位、改 API 回傳格式）；新增 DB index、非破壞性新增不在此限，可走 Auto-advance。§2.2 補充「非破壞性 DB 變更」可 Auto-advance 例子。
- **§3.1 Lite Recon Card：** 新增 YAGNI 三選一欄位；新增 Micro-task 說明（typo/README/單行 bug 可合併 Phase 0–2 為單一段落，六階梯可一句帶過）。
- **§3.2 Full Recon Card：** 新增獨立「§5 YAGNI 初判」區塊；Gate checklist 補 YAGNI 已初判；風險欄位補「結構性/破壞性」修飾語。
- **§7 Phase 3：** 補六階梯已確認 + `ponytail:` 需含升級觸發條件要求。
- **§7 Phase 4：** 補 `/ponytail-review` 確認 + §8 待登錄清零。
- **§8：** 新增極簡主義 / YAGNI 一列，狀態區分「已安裝」與「待登錄（Phase 4 必辦）」。

### v1.5（2026-06-16）
- §5 改「全自動」：促進不再標 verified=no（自動放行），SessionStart hook 接著自動 `km-sync` 同步到 Notion。保留硬保護（結構驗證 + km-sync 敏感掃描 fail-fast）。`KM_HOLD=1` 可一鍵切回安全網。目的：先全自動累積資料，日後 review Obsidian 紀錄品質再定。

### v1.4（2026-06-16）
- 新增 §0.8「Session 開場確認」：每個 session 第一個回應須輸出 SOP 標頭，使用者可即時確認骨幹是否生效；標頭缺席即為警訊。由 SessionStart hook 同步注入提醒強化遵循。

### v1.3（2026-06-16）
- §8 缺口收尾：理財領域裝官方 `financial-analysis` + `equity-research`（疊在 Investment Research OS 上、已登錄 Registry）；PM 定調不裝第三方、改列自建 `pm-suite` skill 待辦。

### v1.2（2026-06-15）
- 合併 A/B 兩份建議。
- 收編 A：Recon Card、Gate 核准政策（human / auto-advance）、各 Phase 最低產物、章節重排序。
- 收編 B：§0 變更管制（回溯需 Impact Analysis）、Phase 2 高風險強制 Fallback。
- 新增：精簡版 Recon Card（剋制每任務摩擦，避免被跳過）。
- 修正：詞彙對映 `Ship` / `Maintain` 拆回兩列；Recon Card 與 §1 skill 綁定去重；網頁對映改指向 v5.0。

### v1.1
- Phase 0 Recon Card、Gate approval policy 初版。

### v1.0
- 全域骨幹初版。
