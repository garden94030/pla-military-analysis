## ADDED Requirements

### Requirement: Grok email auto-parsing

The system SHALL read Grok scheduled emails from Gmail (daily at 0500 TST) and extract the full text content. The system SHALL save extracted content as UTF-8 `.txt` files in the `_daily_input/` directory with naming format `YYYY MMDD Grok每日彙整.txt`.

#### Scenario: Successful Grok email extraction

- **WHEN** a new Grok scheduled email arrives in Gmail
- **THEN** the system extracts the full text content and saves it as a `.txt` file in `_daily_input/`

#### Scenario: No Grok email found

- **WHEN** no Grok email is found for today
- **THEN** the system logs a warning and continues processing any manually added files

### Requirement: Manual file input

The system SHALL support users manually placing `.txt` files into the `_daily_input/` directory. The system SHALL detect all `.txt` files in `_daily_input/` and process them in filename order.

#### Scenario: Manual files detected

- **WHEN** one or more `.txt` files exist in `_daily_input/`
- **THEN** the system reads each file with UTF-8 encoding and queues it for analysis

#### Scenario: Empty input directory

- **WHEN** no `.txt` files exist in `_daily_input/`
- **THEN** the system prints a warning message and exits gracefully

### Requirement: URL content extraction

The system SHALL detect URLs within input files (X/Twitter posts, think tank reports) and attempt to fetch the full text content from those URLs.

#### Scenario: Valid URL detected and fetched

- **WHEN** an input file contains a valid HTTP/HTTPS URL
- **THEN** the system fetches the page content and appends it to the analysis context

#### Scenario: URL fetch fails

- **WHEN** a URL is unreachable or returns an error
- **THEN** the system logs the failure and continues analysis with available content

### Requirement: Input validation

The system SHALL validate input files before processing. Empty files SHALL be skipped with a warning. Duplicate files (content similarity > 90%) SHALL be flagged.

#### Scenario: Empty file detected

- **WHEN** an input file has zero bytes or only whitespace
- **THEN** the system skips the file and logs a warning

#### Scenario: Duplicate content detected

- **WHEN** two input files have content similarity exceeding 90%
- **THEN** the system processes only the first file and logs the duplicate
