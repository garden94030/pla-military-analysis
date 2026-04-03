# 🛡️ 中共軍事動態情報聯合作戰資源中心 (Team Wiki)

## 團隊宣告
本知識庫由 20 名分析師組成的情報團隊共同協作維護。
我們專注於中共軍事戰略、衛星影像標註分析、灰色地帶作戰與印太安全追蹤。
在這裡，每個人手邊的 **Claude Code 都是專屬分析助理**，而中央主機的 **Antigravity AI 則是自動情報後勤**。

## 🔴 強制規則：每輪對話結束前必須撰寫交接文件

> **這是系統級強制要求，不可跳過。**

每次對話（session）接近尾聲時，Claude 必須在結束前完成以下步驟：

1. **留下足夠 token 額度**：在工作進行中，當感覺 context 剩餘空間不多時，**立即停止手頭工作，優先撰寫交接文件**，不要等到最後一刻。
2. **更新 `HANDOVER.md`**（路徑：專案根目錄 `HANDOVER.md`），內容結構：
   - `## 1. 系統當前狀態` — 各子系統（analysis / wiki / LINE / GitHub）目前狀況
   - `## 2. 本輪已完成的重大變更` — 條列本次對話中實際完成的所有任務與修改的檔案
   - `## 3. 目前面臨的問題 / 待解決事項` — 已知 bug、未測試功能、積壓的 TODO
   - `## 4. 下一階段發展建議` — 下一輪 Claude 應該優先執行的 3 件事
3. **寫完後 git commit + push**，確保 GitHub 上的 HANDOVER.md 是最新版本。

> 系統已設定 Stop hook（`_system/handover_check.py`），若 HANDOVER.md 超過 10 分鐘未更新，對話將被強制中斷要求先完成交接。

---

## ⚠️ 團隊協作原則 (Human-in-the-loop)
- **拒絕未經審核的幻覺**：AI 產述的情報未經真人驗證絕對不可隨意 merge。絕不捏造 URL/情報來源。
- **自動化提議，真人決定**：每日自動化腳本 (`wiki_compiler.py`) 產生的新卡片會包裝成 GitHub Pull Request (PR)。
- **各司其職**：如果你是分析師，你可以請你的 Claude Code 下載 PR、補充新獲得的信號圖資，或是直接核可 Merge 讓它進入中央知識庫。
- 本資料庫內容預設統一使用**繁體中文**。

## 🏷️ 文章 Metadata (Frontmatter) 規範
當你請 AI 建立或擴充新知識時，必須在文章最上方包含以下標籤：
```yaml
---
title: [概念名稱 / 事件標題]
type: [concept / event / assessment]
status: [draft 或 reviewed]
author: [若由自動生成則寫 Antigravity-Compiler；若由你編輯則標註真人的 GitHub 帳號]
reviewer: [指定負責審查的人或是"待指派"]
---
```

## 📂 團隊共用架構
| 資料夾 | 權限與用途 |
|--------|-----------|
| `_daily_input/` | `共用` 收件匣，支援圖片/PDF/PPT。將未處理的情報都往這裡丟。 |
| `_daily_output/` | `共用` AI 每日生成的綜合快報（已自動推播 LINE/Email）。 |
| `wiki/` | `核心` 團隊知識庫本體。需要透過 PR 才能更動主線 (Master)。 |
| `wiki/raw/` | `無腦傾倒區` 存放供 Obsidian Web Clipper 等工具一鍵截取的所有未整理文獻、論文、長截圖。 |
| `wiki/concepts/` | 跨時間的主題性知識文章（例：「055型驅逐艦」）。 |
| `wiki/events/` | 具體事件卡片（例：「20260403 對馬海峽通過」）。 |
| `wiki/_index.md` | `自動維護` 全域索引。 |

## ⚙️ AI 分析引擎分配
- **主動編譯端 (Antigravity 後勤)**：主要使用 Grok (x.ai) 高效處理日常報告。
- **本地協作端 (分析師本人)**：本地開發與內容深化推薦使用 Claude。
