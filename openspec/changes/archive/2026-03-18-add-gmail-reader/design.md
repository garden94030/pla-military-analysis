# Gmail Reader Design 設計文件

## Architecture 架構

```
┌─────────────────────────────────────────────────┐
│                gmail_reader.py                   │
│                                                  │
│  ┌────────────┐  ┌────────────┐  ┌───────────┐  │
│  │ OAuth2     │  │ Email      │  │ HTML      │  │
│  │ Authenticator│ │ Searcher   │  │ Parser    │  │
│  │            │  │            │  │           │  │
│  │ credentials│  │ Gmail API  │  │ BS4       │  │
│  │ .json      │  │ query      │  │ html2text │  │
│  │ token.json │  │            │  │           │  │
│  └─────┬──────┘  └─────┬──────┘  └─────┬─────┘  │
│        └───────────────┴───────────────┘         │
│                        ↓                          │
│              _daily_input/YYYY MMDD               │
│              Grok每日彙整.txt                      │
└─────────────────────────────────────────────────┘
```

## Module: `gmail_reader.py`

### Class: `GrokEmailReader`

```python
class GrokEmailReader:
    def __init__(self, credentials_path, token_path, input_dir):
        """初始化 Gmail 讀取器"""

    def authenticate(self) -> service:
        """OAuth2 認證，回傳 Gmail API service"""

    def search_grok_emails(self, hours=24) -> list:
        """搜尋最近 N 小時內的 Grok 郵件"""

    def get_email_content(self, msg_id) -> dict:
        """取得郵件完整內容（HTML + metadata）"""

    def html_to_text(self, html_content) -> str:
        """HTML 轉純文字，保留 URL"""

    def save_to_input(self, content, date) -> Path:
        """存入 _daily_input/ 資料夾"""

    def run(self) -> list[Path]:
        """執行完整流程，回傳已存檔案列表"""
```

### Gmail API Query

```
subject:(中共議題搜集分析 OR 中共軍事) newer_than:1d
```

### Dependencies

```
google-auth>=2.0.0
google-auth-oauthlib>=1.0.0
google-api-python-client>=2.0.0
beautifulsoup4>=4.12.0
```

## Integration with `analysis.py`

```python
# analysis.py 整合方式
from gmail_reader import GrokEmailReader

def main():
    # Step 1: 嘗試自動讀取 Gmail
    try:
        reader = GrokEmailReader(
            credentials_path=WORKSPACE / "credentials.json",
            token_path=WORKSPACE / "token.json",
            input_dir=INPUT_DIR
        )
        saved_files = reader.run()
        print(f"✅ Gmail 自動讀取: {len(saved_files)} 封郵件")
    except Exception as e:
        print(f"⚠️ Gmail 讀取失敗，使用手動模式: {e}")

    # Step 2: 處理 _daily_input/ 中所有檔案（含手動 + 自動）
    input_files = list(INPUT_DIR.glob("*.txt"))
    # ... 後續分析流程不變
```

## Security Considerations

- `credentials.json` 和 `token.json` 加入 `.gitignore`
- OAuth2 scope 限制為 `gmail.readonly`（唯讀）
- token 自動刷新，無需重複授權

## Google Cloud Console 設定步驟

1. 前往 https://console.cloud.google.com/
2. 建立新專案 → 啟用 Gmail API
3. 建立 OAuth 2.0 用戶端 ID（桌面應用程式）
4. 下載 `credentials.json` 放入專案根目錄
5. 首次執行時瀏覽器自動開啟授權頁面
