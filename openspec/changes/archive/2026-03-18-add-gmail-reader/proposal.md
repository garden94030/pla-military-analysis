## Why

目前 Grok 排程郵件（每日 0500）寄到 Gmail 後，使用者需要手動開啟郵件、複製內容、貼上到 `_daily_input/` 資料夾。這個手動步驟是整個自動化流程中唯一的瓶頸。新增 Gmail 自動讀取功能可以實現從「Grok 蒐集 → 分析 → 報告」的全自動化。

## What Changes

- **新增** `gmail_reader.py` 模組：使用 Gmail API 自動讀取 Grok 排程郵件
- **新增** Gmail API OAuth2 認證設定流程
- **新增** 郵件內容解析器：將 HTML 郵件轉為純文字
- **修改** `analysis.py`：整合 Gmail 讀取作為資料來源之一
- **新增** 排程觸發機制：每日 0530 自動執行（在 Grok 0500 之後）

## Capabilities

### New Capabilities

- `gmail-integration`: Gmail API 整合 — OAuth2 認證、郵件搜尋、HTML 解析、自動存檔至 `_daily_input/`

### Modified Capabilities

- `data-collection`: 新增 Gmail 作為自動化資料來源，擴展現有手動輸入流程

## Impact

- **新增依賴**: `google-auth`, `google-api-python-client`, `beautifulsoup4`
- **認證**: 需要 Google Cloud Console 建立 OAuth2 credentials（一次性設定）
- **安全**: OAuth2 token 存放在 `.env` 同級目錄，需加入 `.gitignore`
- **排程**: 可搭配 Windows Task Scheduler 或 Claude Code 排程任務
- **現有流程**: 不影響手動輸入流程，Gmail 讀取為額外自動化來源
