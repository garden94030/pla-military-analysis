## ADDED Requirements

### Requirement: Environment variable management

The system SHALL read API keys from a `.env` file using the `python-dotenv` package. The system SHALL provide a `.env.example` template without actual keys. API keys SHALL NOT appear in source code.

#### Scenario: API key loaded from .env

- **WHEN** the application starts
- **THEN** it reads `ANTHROPIC_API_KEY` from the `.env` file

#### Scenario: Missing .env file

- **WHEN** the `.env` file does not exist
- **THEN** the system prints a clear error message with setup instructions and exits

### Requirement: Git security

The `.gitignore` file SHALL exclude: `.env`, `_daily_input/`, `_archive/`, and `logs/`. The system SHALL NOT commit any file containing API keys or tokens.

#### Scenario: Sensitive files excluded from git

- **WHEN** a user runs `git add .`
- **THEN** `.env`, `_daily_input/`, `_archive/`, and `logs/` are excluded by `.gitignore`

### Requirement: Error logging

The system SHALL log all errors to timestamped files in the `logs/` directory. Log entries SHALL include: timestamp, severity level, module name, and error details.

#### Scenario: Error logged to file

- **WHEN** any error occurs during processing
- **THEN** the error is recorded in `logs/YYYYMMDD.log` with full details
