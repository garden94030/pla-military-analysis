# Report Generation 報告產出系統

## Purpose
標準化分析報告的格式、結構和輸出管理。

## Requirements

### R1: 報告 Markdown 格式
- 統一標題層級: H1 報告標題, H2 章節, H3 子節
- 每份報告開頭: 研究時間、來源檔案、分析師標記
- 結尾: Chicago 格式引用文獻

### R2: 資料夾自動管理
- 依議題自動建立資料夾: `YYYYMMDD_議題XX_主題名稱/`
- 資料夾內放置: 深度分析 .md 檔、原始資料備份
- 防止資料夾名稱衝突

### R3: 綜合報告整合
- 所有議題的摘要整合為單一綜合報告
- 包含議題索引（含連結至各深度分析）
- 當日分析統計（議題數、來源數、關鍵字詞頻）

### R4: 輸出品質檢查
- 檢查 Markdown 語法正確性
- 確認所有章節已產出（不得有空白章節）
- 確認引用文獻格式一致

### Requirement: Standardized Markdown format

The system SHALL produce all reports in Markdown format with consistent heading hierarchy: H1 for report title, H2 for chapters, H3 for subsections. Each report SHALL include research timestamp, source file reference, and analyst attribution at the top.

#### Scenario: Report header generated

- **WHEN** a new analysis report is created
- **THEN** the report header includes date, source filename, and research timestamp

---
### Requirement: Automatic folder management

The system SHALL create output folders named `YYYYMMDD_議題XX_主題名稱/` for each topic. The system SHALL prevent folder name collisions by appending a numeric suffix if a folder already exists.

#### Scenario: New topic folder created

- **WHEN** a new topic is identified for analysis
- **THEN** a folder is created with the standardized naming pattern

#### Scenario: Folder name collision

- **WHEN** a folder with the same name already exists
- **THEN** the system appends `_v2`, `_v3` etc. to avoid overwriting

---
### Requirement: Chicago citation format

The system SHALL format all bibliographic references in Chicago author-date style with automatic numbering. Each citation SHALL include: author, title, source, date, and URL.

#### Scenario: Citation generated

- **WHEN** a source is referenced in the analysis
- **THEN** a numbered Chicago-format citation is appended to the bibliography section
