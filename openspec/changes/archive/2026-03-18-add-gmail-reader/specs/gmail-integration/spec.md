## ADDED Requirements

### Requirement: Gmail API authentication

The system SHALL authenticate with Gmail API using OAuth2 credentials stored in `credentials.json`. The system SHALL cache the access token in `token.json` for subsequent runs. On first run, the system SHALL open a browser for user authorization.

#### Scenario: First-time authentication

- **WHEN** the system runs for the first time without `token.json`
- **THEN** it opens a browser for OAuth2 authorization and saves the token to `token.json`

#### Scenario: Token refresh

- **WHEN** the cached token has expired
- **THEN** the system automatically refreshes the token without user interaction

#### Scenario: Missing credentials file

- **WHEN** `credentials.json` does not exist
- **THEN** the system prints setup instructions for Google Cloud Console and exits

### Requirement: Grok email search and retrieval

The system SHALL search Gmail for emails matching the Grok scheduled task subject pattern. The system SHALL retrieve emails from the last 24 hours by default. The system SHALL extract the full HTML body content.

#### Scenario: Grok email found

- **WHEN** a Grok scheduled email exists from today
- **THEN** the system retrieves the full email body and metadata (subject, date, sender)

#### Scenario: No Grok email today

- **WHEN** no matching email is found in the last 24 hours
- **THEN** the system logs a warning and proceeds with any manually added input files

#### Scenario: Multiple Grok emails found

- **WHEN** multiple matching emails exist from today
- **THEN** the system processes the most recent one

### Requirement: HTML to text conversion

The system SHALL convert HTML email content to clean plain text. The system SHALL preserve structured data (lists, tables, headings). The system SHALL extract and preserve all URLs from the original HTML.

#### Scenario: HTML email converted

- **WHEN** a Grok HTML email is retrieved
- **THEN** it is converted to plain text with URLs preserved and saved as UTF-8 `.txt`

#### Scenario: Plain text email received

- **WHEN** the email body is already plain text
- **THEN** it is saved directly without conversion

### Requirement: Auto-save to daily input

The system SHALL save extracted email content to `_daily_input/` with filename format `YYYY MMDD Grok每日彙整.txt`. The system SHALL NOT overwrite existing files with the same name.

#### Scenario: Email saved to input

- **WHEN** email content is successfully extracted
- **THEN** it is saved to `_daily_input/YYYY MMDD Grok每日彙整.txt`

#### Scenario: File already exists

- **WHEN** a file with the same name already exists in `_daily_input/`
- **THEN** the system appends `_v2` to the filename to avoid overwriting
