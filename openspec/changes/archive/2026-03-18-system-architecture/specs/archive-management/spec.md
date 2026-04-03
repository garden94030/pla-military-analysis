## ADDED Requirements

### Requirement: Automatic archival

The system SHALL move processed files from `_daily_input/` to `_archive/` after successful analysis. Archived files SHALL be renamed with timestamp prefix: `YYYYMMDD_HHMMSS_originalname.txt`. The system SHALL NOT archive files whose analysis failed.

#### Scenario: Successful archival

- **WHEN** analysis for a file completes successfully
- **THEN** the original file is moved to `_archive/` with a timestamp prefix

#### Scenario: Failed analysis prevents archival

- **WHEN** analysis for a file fails
- **THEN** the original file remains in `_daily_input/` for retry

### Requirement: Archive index

The system SHALL maintain an archive index file at `_archive/index.json`. Each entry SHALL record: original filename, archive timestamp, corresponding output report path, and topic tags.

#### Scenario: Index updated after archival

- **WHEN** a file is archived
- **THEN** a new entry is appended to `_archive/index.json`

### Requirement: Historical query

The system SHALL support querying archived analyses by date range, keyword, and topic category.

#### Scenario: Query by date range

- **WHEN** a user queries archives for a specific date range
- **THEN** the system returns all matching archived analyses
