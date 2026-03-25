# 每日中共軍事動態分析專案

## 專案簡介

此專案每日自動蒐集 X（Twitter）上的中共軍事相關貼文，使用 Claude API 進行深度分析，產出繁體中文分析報告供國防與安全研究使用。

## 資料夾結構

```
_daily_input/   → 放置待分析的 .txt 貼文檔案
_daily_output/  → 輸出的 Markdown 分析報告
_archive/       → 已處理的輸入檔案歸檔
analysis.py     → 主程式
```

## 每日工作流程

1. 將 X 貼文內容存成 `.txt` 檔，放入 `_daily_input/`
2. 執行 `python analysis.py`
3. 在 `_daily_output/` 取得分析報告（Markdown 格式）
4. 輸入檔案自動移至 `_archive/`

## 分析報告內容

每份報告包含：
- **原始摘要**：中英對照表格
- **核心分析**：關鍵發現、對台灣防衛的影響、與過往發展的關聯
- **政策建議**：針對國防部門、民防規劃、國際協調
- **引用註釋**：Chicago 格式

## 執行環境需求

- Python 3.x
- `anthropic` 套件：`pip install anthropic`
- 環境變數 `ANTHROPIC_API_KEY` 必須設定

## Remote Control 使用說明

透過 Remote Control 連線後，你可以：

### 分析新貼文
```
請分析 _daily_input 資料夾中的新貼文
```

### 查看今日報告
```
列出今天 _daily_output 中的分析報告
```

### 手動分析單篇貼文
直接貼上貼文內容，請 Claude 按照分析格式產出報告。

### 比較分析
```
比較最近三份報告，找出中共軍事動態的趨勢
```

## 注意事項

- 輸出報告使用繁體中文
- 分析模型：claude-sonnet-4-20250514
- 本地路徑設定在 `analysis.py` 的 `WORKSPACE` 變數
- Windows 使用者注意 UTF-8 編碼設定
