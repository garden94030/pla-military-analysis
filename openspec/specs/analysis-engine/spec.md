# Analysis Engine 分析引擎

## Purpose
透過 Claude API 對原始資料進行多層次分析。

## Requirements

### R1: 綜合分析報告
- 讀取當日所有 `_daily_input/` 檔案
- 產出一份綜合分析報告，包含所有議題摘要
- 自動識別並分類不同議題主題
- 輸出: `YYYYMMDD_中共軍事動態綜合分析報告.md`

### R2: 單議題深度分析
- 對綜合報告中每個議題產出獨立深度分析
- 每份分析 12 個標準章節，每節 300-500 字
- 包含: 研究摘要、背景脈絡、技術分析、作戰概念、影響評估、反制建議、引用文獻
- 輸出: `_daily_output/YYYYMMDD_議題XX_主題名稱/深度分析_主題名稱.md`

### R3: 中英對照處理
- 英文原文逐句對照繁體中文翻譯
- 表格格式呈現

### R4: Claude API 管理
- 使用 claude-opus-4-1 模型
- max_tokens: 4096（深度分析）/ 2000（摘要）
- 錯誤重試機制（最多 3 次，指數退避）
- API 使用量記錄

### Requirement: Comprehensive analysis report

The system SHALL read all `.txt` files from `_daily_input/` and produce a single comprehensive analysis report. The report SHALL identify and categorize all distinct topics. Output file SHALL be named `YYYYMMDD_中共軍事動態綜合分析報告.md`.

#### Scenario: Multiple input files processed

- **WHEN** multiple `.txt` files exist in `_daily_input/`
- **THEN** the system produces one comprehensive report covering all topics with a summary index

#### Scenario: Single input file processed

- **WHEN** only one `.txt` file exists in `_daily_input/`
- **THEN** the system produces a comprehensive report for that single source

---
### Requirement: Per-topic deep analysis

The system SHALL produce independent deep-dive analysis reports for each topic identified in the comprehensive report. Each analysis SHALL contain 12 standard sections with 300-500 words per section. Output SHALL be saved in `_daily_output/YYYYMMDD_議題XX_主題名稱/深度分析_主題名稱.md`.

#### Scenario: Deep analysis generated

- **WHEN** the comprehensive report identifies N topics
- **THEN** the system creates N separate folders and N deep-dive analysis reports

#### Scenario: Deep analysis sections complete

- **WHEN** a deep-dive analysis is generated
- **THEN** it SHALL contain all 12 sections: research summary, background, technical analysis, operational concept, impact assessment, cost analysis, historical comparison, countermeasure recommendations, future trends, and bibliography

---
### Requirement: Bilingual summary

The system SHALL produce Chinese-English bilingual summaries with sentence-by-sentence alignment in table format. Left column SHALL contain English original text, right column SHALL contain Traditional Chinese translation.

#### Scenario: English source translated

- **WHEN** the input contains English text
- **THEN** the output includes a bilingual comparison table with aligned sentences

---
### Requirement: Claude API management

The system SHALL use the claude-opus-4-1 model with max_tokens of 4096 for deep analysis and 2000 for summaries. The system SHALL implement retry logic with exponential backoff (max 3 retries). The system SHALL log API usage (tokens consumed, cost estimate).

#### Scenario: API call succeeds

- **WHEN** Claude API returns a valid response
- **THEN** the system extracts the analysis text and records token usage

#### Scenario: API call fails with retryable error

- **WHEN** Claude API returns a 429 or 500 error
- **THEN** the system retries up to 3 times with exponential backoff (2s, 4s, 8s)

#### Scenario: API call fails permanently

- **WHEN** all 3 retries are exhausted
- **THEN** the system logs the error, skips the current file, and continues with remaining files
