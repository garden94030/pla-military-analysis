# 🤖 AI 協作交接文件 (交接給 Claude Code)

> **給接手的 Claude Code：** 
> 你好！我是負責後端系統升級的 Antigravity。這是我與 User 稍早針對「中共軍事情報知識庫 (20人團隊協作版)」升級的完整進度紀錄。請基於此文件協助 User 繼續測試與擴建。

---

## 1. 系統當前狀態 (System Status)
本專案已成功從「單機單人版」升級至 **「支援多人的 Git/GitHub PR 審查系統」**。
主要包含以下核心功能與目錄：
*   `_daily_input/`：供 20 人團隊隨時傾倒當日情報資料的收件匣。
*   `wiki/`：Obsidian 知識庫。所有 AI 生成的知識都會存在這裡 (`concepts/`, `events/`)，且所有檔案都已注入 YAML Frontmatter (例如：`author: ai-agent`, `status: draft`)。
*   `wiki/raw/`：**【最新建立】** 給 Obsidian Web Clipper 或人類分析師使用的「原始資源圖書館」。這邊存放未經 AI 加工的原始網頁截圖或論文。

## 2. 剛完成的重大變更 (Recent Changes)
*   **自動 Pull Request (PR) 機制**：
    `wiki_compiler.py` 已加入自動使用 Git 分支與 `gh` (GitHub CLI) 發送 PR 的功能。
*   **修復 Windows cp950 編碼地雷**：
    這是一個重大的 Bug。稍早 `subprocess.run(["git", "commit", "-m", msg], text=True)` 在讀取含有中文的輸出時會觸發 `UnicodeDecodeError`。我已在 `wiki_compiler.py` 的 Git 相關指令中加入了 `encoding="utf-8"` 強制轉碼，成功解決了該崩潰問題。
*   **GitHub CLI 授權登入**：
    User 已經在電腦上完成了 `gh auth login`，現在背景的自動化腳本具備了完整的發 Pull Request 權限。

## 3. 目前面臨的問題 / 待解決事項 (Pending Fixes)
1. **Obsidian Web Clipper 檔名非法字元**：
   稍早 User 在擷取「(2) 首頁 / X」這篇網頁時，因為標題含有 `/` (Windows 下為非法檔名字元)，導致外掛無法成功將文章存進 `wiki/raw/`。
   *👉 **給 Claude Code 的下一步指令**：請陪伴 User 測試將無斜線的標題網頁存入 `wiki/raw/`，確保 Web Clipper 運作正常。*

2. **驗證自動 PR 流程**：
   由於 `wiki/` 內容皆無變動，剛剛的測試沒有觸發 Git commit。 
   *👉 **給 Claude Code 的下一步指令**：請帶領 User 在隨意一篇 `wiki/concepts/*.md` 裡面加上一行測試字眼，然後執行 `python wiki_compiler.py --team-sync`，並去 GitHub 網頁查看是否成功送出了第一張由 AI 自動生成的 Pull Request 表單！*

## 4. 下一階段發展建議 (Phase 5 Roadmap)
如果以上測試都順利通過，你們可以開始著手開發以下進階功能：
*   **編寫 `wiki_health.py`**：定時掃描系統裡還有多少個 PR 處於未審核 (`Draft`) 階段，或是針對太久沒更新的 `concepts/` 卡片發出預警。
*   **導入 Mermaid 戰略地圖**：在知識卡的生成 Prompt 中，要求它自動加入 `mermaid` 語法來串接實體關係。
*   **向量資料庫 (RAG) 強化**：隨著資料量暴增，未來的 `wiki_query.py` 可能需要導入 ChromaDB 向量檢索。

---
交接完畢！Claude Code，接下來這套情報基地就交給你與 User 繼續守護了！🚀
