## Why

目前中共軍事動態情資分析系統仍為半手動流程：手動蒐集 X 貼文存入 `_daily_input`，手動觸發 Claude Code 進行分析。需要建立完整的自動化架構，實現從「資料蒐集 → 分析 → 報告產出 → 歸檔」的端到端自動化，並確保程式碼品質、安全性和可維護性。

## What Changes

- **新增** `analysis.py` 主分析腳本：讀取 `_daily_input/` 文件，透過 Claude API 產出結構化分析報告
- **新增** Gmail 自動讀取模組：自動從 Grok 排程郵件提取中共軍事動態內容
- **新增** 深度分析模組：對綜合報告中的每個議題自動產出深度研究報告
- **新增** URL 內容擷取模組：自動從 X 貼文連結、智庫報告 URL 擷取全文
- **新增** 環境變數管理：API 金鑰改用 `.env` 檔案管理，不寫死在程式碼中
- **BREAKING** 報告格式標準化：統一所有報告的 Markdown 結構和引用格式

## Capabilities

### New Capabilities

- `data-collection`: 自動化資料蒐集 — Grok 郵件解析、X 貼文擷取、智庫報告 URL 抓取
- `analysis-engine`: Claude API 分析引擎 — 綜合分析報告產出、每議題深度分析、中英對照摘要
- `report-generation`: 報告產出系統 — 標準化 Markdown 格式、資料夾自動建立與命名、引用文獻管理
- `archive-management`: 歸檔管理 — 已處理檔案自動歸檔、歷史資料索引
- `security-config`: 安全設定管理 — API 金鑰環境變數化、`.env` 檔案管理、敏感資料保護

### Modified Capabilities

（目前無現有規格需修改）

## Impact

- **程式碼**: 新增 `analysis.py` 主腳本、`gmail_reader.py` 郵件模組、`url_fetcher.py` 擷取模組
- **API 依賴**: Anthropic Claude API (claude-opus-4-1)、Gmail API (可選)
- **外部服務**: Grok 排程（每日 0500 蒐集）、OneDrive 雲端同步
- **安全性**: 需建立 `.env` 檔案管理 API 金鑰，`.gitignore` 排除敏感檔案
- **資料流**: `Grok → Gmail → _daily_input/ → analysis.py → _daily_output/ → _archive/`
