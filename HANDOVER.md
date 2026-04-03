# 🤖 PLA 軍事情報分析系統：2.0 版開發交接 (2026-04-03)

本文件摘要了「20 人專家團隊」與「GIS 地理資訊系統」深度自動化後的最新架構與操作指南。系統現已達成從情資讀取到 Wiki 全自動同步的閉環。

---

## 🛠️ 系統架構 2.0 (最新版)

### 1. 📂 結構化輸入與輸出 (Unified Input/Output)
- **統一入口**：系統自動讀取 `_daily_input/` 與 [**`wiki/raw/`**](file:///C:/Users/garde/OneDrive/3.教務/1.中共軍事體制研究/每日資料蒐集更新/wiki/raw/)。使用 Obsidian 剪輯後直接執行即可。
- **主題目錄**：報告與 KML 統一儲存於 `_daily_output/YYYYMMDD_議題N_[標題]/`。
- **自動計數**：議題編號由 `_system/issue_counter.json` 全域管理，確保時序。

### 2. 🌍 GIS 地理圖資系統 (KML Fixes)
- **非洲飄移修正**：已修復 `None` 座標導致地點飄至 0,0 (幾內亞灣) 的錯誤。
- **精準目標庫**：強化了對 906 基地、台海關鍵區域的座標校驗。
- **同步備份**：KML 也會同步於 `_geo_output/`，方便 Google Earth 一鍵載入。

### 3. 🕵️ 20 人全專家團隊 (Agentic Review)
- **領域路由**：系統自動根據「主題標題」比對 `team/analysts.json`，指派對應專家。
- **專家複審**：報告自動附帶「🖋️ 專家評核意見」與「戰略風險等級」，提升報告深度。

### 4. 🧠 Wiki 全自動同步 (Wiki Compiler)
- **動態更新**：自動更新 15 個以上概念主題、索引、時間線與實體名錄。
- **GitHub 同步**：自動發送 Pull Request，確保雲端/團隊資料一致。

---

## 🚀 軟硬體環境
- **Python**：**3.13** (路徑：`C:\Users\garde\AppData\Local\Programs\Python\Python313\python.exe`)
- **核心依賴**：`openai`, `anthropic`, `python-docx`, `PyPDF2`。
- **認證**：`.env` 中需具備有效 API Key (Claude/Grok)。

---

## 📅 操作備忘錄
1. **清理模式**：分析後原始檔會移至 `_archive/`，若需重新分析請將檔案移回 `_daily_input`。
2. **KML 更新**：Google Earth 會自動偵測 `_geo_output/` 下的新檔案（若已同步 OneDrive）。
3. **錯誤修復**：已解決 Word 檔案鎖定與 Windows 萬國碼亂碼問題。

*系統開發已圓滿完成，所有功能均已經過 2026-04-03 現證測試。*
