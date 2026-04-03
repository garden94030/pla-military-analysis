# Archive Management 歸檔管理

## Purpose
管理已處理資料的歸檔與歷史查詢。

## Requirements

### R1: 自動歸檔
- 分析完成後將 `_daily_input/` 檔案移至 `_archive/`
- 歸檔檔名加上時間戳: `YYYYMMDD_HHMMSS_原始檔名.txt`
- 歸檔前確認分析報告已成功產出

### R2: 歸檔索引
- 維護歸檔索引檔 `_archive/index.json`
- 記錄: 原始檔名、歸檔時間、對應分析報告路徑、議題標籤

### R3: 歷史查詢
- 支援按日期範圍查詢歷史分析
- 支援按關鍵字搜尋歸檔內容
- 支援按議題類別篩選

### Requirement: Automatic archival

The system SHALL move processed files from `_daily_input/` to `_archive/` after successful analysis. Archived files SHALL be renamed with timestamp prefix: `YYYYMMDD_HHMMSS_originalname.txt`. The system SHALL NOT archive files whose analysis failed.

#### Scenario: Successful archival

- **WHEN** analysis for a file completes successfully
- **THEN** the original file is moved to `_archive/` with a timestamp prefix

#### Scenario: Failed analysis prevents archival

- **WHEN** analysis for a file fails
- **THEN** the original file remains in `_daily_input/` for retry

---
### Requirement: Archive index

The system SHALL maintain an archive index file at `_archive/index.json`. Each entry SHALL record: original filename, archive timestamp, corresponding output report path, and topic tags.

#### Scenario: Index updated after archival

- **WHEN** a file is archived
- **THEN** a new entry is appended to `_archive/index.json`

---
### Requirement: Historical query

The system SHALL support querying archived analyses by date range, keyword, and topic category.

#### Scenario: Query by date range

- **WHEN** a user queries archives for a specific date range
- **THEN** the system returns all matching archived analyses
