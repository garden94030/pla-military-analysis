# Data Collection 資料蒐集模組

## Purpose
自動化蒐集中共軍事動態原始資料，支援多來源輸入。

## Requirements

### R1: Grok 郵件自動解析
- 讀取 Gmail 中 Grok 排程郵件（每日 0500）
- 解析郵件 HTML 內容為純文字
- 自動存入 `_daily_input/` 資料夾
- 檔案命名: `YYYY MMDD Grok每日彙整.txt`

### R2: 手動檔案輸入
- 支援使用者手動放入 `.txt` 檔案至 `_daily_input/`
- 自動偵測新檔案觸發分析流程
- 支援 UTF-8 編碼的中英文混合內容

### R3: URL 內容擷取
- 從輸入文件中自動偵測 URL（X 貼文、智庫報告）
- 使用 WebFetch 或 requests 擷取全文內容
- 處理付費牆、登入牆等存取限制的錯誤回報

### R4: 輸入驗證
- 檢查檔案是否為空
- 偵測重複檔案（內容相似度 > 90%）
- 記錄處理日誌

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

---
### Requirement: Manual file input

The system SHALL support users manually placing `.txt` files into the `_daily_input/` directory. The system SHALL detect all `.txt` files in `_daily_input/` and process them in filename order.

#### Scenario: Manual files detected

- **WHEN** one or more `.txt` files exist in `_daily_input/`
- **THEN** the system reads each file with UTF-8 encoding and queues it for analysis

#### Scenario: Empty input directory

- **WHEN** no `.txt` files exist in `_daily_input/`
- **THEN** the system prints a warning message and exits gracefully

---
### Requirement: URL content extraction

The system SHALL detect URLs within input files (X/Twitter posts, think tank reports) and attempt to fetch the full text content from those URLs.

#### Scenario: Valid URL detected and fetched

- **WHEN** an input file contains a valid HTTP/HTTPS URL
- **THEN** the system fetches the page content and appends it to the analysis context

#### Scenario: URL fetch fails

- **WHEN** a URL is unreachable or returns an error
- **THEN** the system logs the failure and continues analysis with available content

---
### Requirement: Input validation

The system SHALL validate input files before processing. Empty files SHALL be skipped with a warning. Duplicate files (content similarity > 90%) SHALL be flagged.

#### Scenario: Empty file detected

- **WHEN** an input file has zero bytes or only whitespace
- **THEN** the system skips the file and logs a warning

#### Scenario: Duplicate content detected

- **WHEN** two input files have content similarity exceeding 90%
- **THEN** the system processes only the first file and logs the duplicate
