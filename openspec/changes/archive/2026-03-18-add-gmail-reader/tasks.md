# Tasks: add-gmail-reader

## Task 1: Install dependencies
- [ ] `pip install google-auth google-auth-oauthlib google-api-python-client beautifulsoup4`
- [ ] Update `requirements.txt` with all dependencies

## Task 2: Gmail API authentication
Implements requirement: Gmail API authentication
- [ ] Create Google Cloud project at https://console.cloud.google.com/
- [ ] Enable Gmail API
- [ ] Create OAuth 2.0 Client ID (Desktop Application)
- [ ] Download `credentials.json` to project root
- [ ] Add `credentials.json` and `token.json` to `.gitignore`
- [ ] Implement `authenticate()` method
- [ ] Test first-time OAuth2 authorization flow
- [ ] Test token refresh mechanism

## Task 3: Grok email search and retrieval
Implements requirement: Grok email search and retrieval
- [ ] Implement `search_grok_emails()` using Gmail API query
- [ ] Implement `get_email_content()` to retrieve full email body and metadata
- [ ] Handle case: no Grok email found today
- [ ] Handle case: multiple Grok emails found

## Task 4: HTML to text conversion
Implements requirement: HTML to text conversion
- [ ] Implement `html_to_text()` using BeautifulSoup4
- [ ] Preserve structured data (lists, tables, headings)
- [ ] Extract and preserve all URLs from HTML
- [ ] Handle plain text emails

## Task 5: Auto-save to daily input
Implements requirement: Auto-save to daily input
- [ ] Implement `save_to_input()` with naming format `YYYY MMDD Grok每日彙整.txt`
- [ ] Handle filename collision (append `_v2`)
- [ ] Ensure UTF-8 encoding for all output

## Task 6: Grok email auto-parsing integration
Implements requirement: Grok email auto-parsing
Implements design: class: `GrokEmailReader`
- [ ] Implement `GrokEmailReader` class with `run()` method
- [ ] Integrate into `analysis.py` main() with try/except fallback
- [ ] Add logging for each processing step
- [ ] Test end-to-end: authenticate → search → extract → convert → save

## Task 7: Scheduling (optional)
- [ ] Create Windows Task Scheduler task (daily 0530 TST)
- [ ] Or configure Claude Code scheduled task
