## ADDED Requirements

### Requirement: Standardized Markdown format

The system SHALL produce all reports in Markdown format with consistent heading hierarchy: H1 for report title, H2 for chapters, H3 for subsections. Each report SHALL include research timestamp, source file reference, and analyst attribution at the top.

#### Scenario: Report header generated

- **WHEN** a new analysis report is created
- **THEN** the report header includes date, source filename, and research timestamp

### Requirement: Automatic folder management

The system SHALL create output folders named `YYYYMMDD_議題XX_主題名稱/` for each topic. The system SHALL prevent folder name collisions by appending a numeric suffix if a folder already exists.

#### Scenario: New topic folder created

- **WHEN** a new topic is identified for analysis
- **THEN** a folder is created with the standardized naming pattern

#### Scenario: Folder name collision

- **WHEN** a folder with the same name already exists
- **THEN** the system appends `_v2`, `_v3` etc. to avoid overwriting

### Requirement: Chicago citation format

The system SHALL format all bibliographic references in Chicago author-date style with automatic numbering. Each citation SHALL include: author, title, source, date, and URL.

#### Scenario: Citation generated

- **WHEN** a source is referenced in the analysis
- **THEN** a numbered Chicago-format citation is appended to the bibliography section
