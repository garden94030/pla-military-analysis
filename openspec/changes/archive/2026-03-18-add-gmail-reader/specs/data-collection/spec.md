## MODIFIED Requirements

### Requirement: Grok email auto-parsing

The system SHALL read Grok scheduled emails from Gmail using the Gmail API OAuth2 integration (via `gmail_reader.py` module). The system SHALL automatically execute email retrieval at 0530 TST daily, 30 minutes after the Grok scheduled collection at 0500. The system SHALL save extracted content as UTF-8 `.txt` files in the `_daily_input/` directory with naming format `YYYY MMDD Grok每日彙整.txt`. The system SHALL support both automated Gmail retrieval and manual file input simultaneously.

#### Scenario: Successful Grok email extraction

- **WHEN** the Gmail reader module runs at 0530
- **THEN** it searches for today's Grok email, extracts content, and saves to `_daily_input/`

#### Scenario: No Grok email found

- **WHEN** no Grok email is found for today
- **THEN** the system logs a warning and continues processing any manually added files

#### Scenario: Gmail API unavailable

- **WHEN** Gmail API authentication fails or network is unavailable
- **THEN** the system logs the error and falls back to manual input mode only
