## ADDED Requirements

### Requirement: Comprehensive analysis report

The system SHALL read all `.txt` files from `_daily_input/` and produce a single comprehensive analysis report. The report SHALL identify and categorize all distinct topics. Output file SHALL be named `YYYYMMDD_中共軍事動態綜合分析報告.md`.

#### Scenario: Multiple input files processed

- **WHEN** multiple `.txt` files exist in `_daily_input/`
- **THEN** the system produces one comprehensive report covering all topics with a summary index

#### Scenario: Single input file processed

- **WHEN** only one `.txt` file exists in `_daily_input/`
- **THEN** the system produces a comprehensive report for that single source

### Requirement: Per-topic deep analysis

The system SHALL produce independent deep-dive analysis reports for each topic identified in the comprehensive report. Each analysis SHALL contain 12 standard sections with 300-500 words per section. Output SHALL be saved in `_daily_output/YYYYMMDD_議題XX_主題名稱/深度分析_主題名稱.md`.

#### Scenario: Deep analysis generated

- **WHEN** the comprehensive report identifies N topics
- **THEN** the system creates N separate folders and N deep-dive analysis reports

#### Scenario: Deep analysis sections complete

- **WHEN** a deep-dive analysis is generated
- **THEN** it SHALL contain all 12 sections: research summary, background, technical analysis, operational concept, impact assessment, cost analysis, historical comparison, countermeasure recommendations, future trends, and bibliography

### Requirement: Bilingual summary

The system SHALL produce Chinese-English bilingual summaries with sentence-by-sentence alignment in table format. Left column SHALL contain English original text, right column SHALL contain Traditional Chinese translation.

#### Scenario: English source translated

- **WHEN** the input contains English text
- **THEN** the output includes a bilingual comparison table with aligned sentences

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
