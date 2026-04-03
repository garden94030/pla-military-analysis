# Security Config 安全設定

## Purpose
確保 API 金鑰和敏感資料的安全管理。

## Requirements

### R1: 環境變數管理
- API 金鑰從 `.env` 檔案讀取
- 使用 `python-dotenv` 套件
- `.env` 範例檔: `.env.example`（不含真實金鑰）

### R2: Git 安全
- `.gitignore` 排除: `.env`, `_daily_input/`, `_archive/`
- 禁止 API 金鑰出現在程式碼中
- commit 前自動檢查敏感資料

### R3: 錯誤處理
- API 金鑰無效時明確提示
- 網路連線失敗時的優雅降級
- 所有錯誤記錄至 `logs/` 資料夾

### Requirement: Environment variable management

The system SHALL read API keys from a `.env` file using the `python-dotenv` package. The system SHALL provide a `.env.example` template without actual keys. API keys SHALL NOT appear in source code.

#### Scenario: API key loaded from .env

- **WHEN** the application starts
- **THEN** it reads `ANTHROPIC_API_KEY` from the `.env` file

#### Scenario: Missing .env file

- **WHEN** the `.env` file does not exist
- **THEN** the system prints a clear error message with setup instructions and exits

---
### Requirement: Git security

The `.gitignore` file SHALL exclude: `.env`, `_daily_input/`, `_archive/`, and `logs/`. The system SHALL NOT commit any file containing API keys or tokens.

#### Scenario: Sensitive files excluded from git

- **WHEN** a user runs `git add .`
- **THEN** `.env`, `_daily_input/`, `_archive/`, and `logs/` are excluded by `.gitignore`

---
### Requirement: Error logging

The system SHALL log all errors to timestamped files in the `logs/` directory. Log entries SHALL include: timestamp, severity level, module name, and error details.

#### Scenario: Error logged to file

- **WHEN** any error occurs during processing
- **THEN** the error is recorded in `logs/YYYYMMDD.log` with full details
