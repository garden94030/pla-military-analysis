"""
Gmail Reader — 自動從 Gmail 讀取 Grok 每日中共軍事動態郵件
=====================================
功能：
  1. OAuth2 認證 Gmail API（首次需瀏覽器授權）
  2. 搜尋 Grok 排程郵件（每日 0500 發送）
  3. HTML 轉純文字，保留 URL
  4. 自動存入 _daily_input/ 供 analysis.py 分析

使用前提：
  1. 需要 Google Cloud Console 建立 OAuth2 憑證
  2. 下載 credentials.json 放入專案根目錄
  3. 首次執行會開啟瀏覽器進行授權

Spectra Change: add-gmail-reader
"""

import os
import sys
import re
import io
import json
import base64
import logging
from datetime import datetime, timedelta
from pathlib import Path
from html.parser import HTMLParser

# PDF 文字提取（用於 INDSR 附件）
try:
    from pdfminer.high_level import extract_text as pdf_extract_text
    HAS_PDFMINER = True
except ImportError:
    HAS_PDFMINER = False

# 修正 Windows 終端編碼
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Google API imports
try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
except ImportError:
    print("❌ 請先安裝 Google API 套件：")
    print("   pip install google-auth google-auth-oauthlib google-api-python-client")
    sys.exit(1)

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None

# ============= 常數設定 =============
WORKSPACE = Path(r"C:\Users\garde\OneDrive\3.教務\1.中共軍事體制研究\每日資料蒐集更新")
INPUT_DIR = WORKSPACE / "_daily_input"
SYSTEM_DIR = WORKSPACE / "_system"
LOG_DIR = WORKSPACE / "logs"

CREDENTIALS_FILE = WORKSPACE / "credentials.json"
TOKEN_FILE = WORKSPACE / "token.json"
PROCESSED_LOG = SYSTEM_DIR / "processed_emails.json"

# Gmail API 權限（讀取 + 發送）
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send',
]

# 郵件搜尋條件（多來源自動蒐集）
MAIL_SEARCH_QUERIES = [
    # Grok 每日排程（noreply@x.ai）
    'from:(noreply@x.ai) newer_than:1d',
    'subject:(中共議題搜集分析) newer_than:1d',
    'subject:(is ready) from:(x.ai) newer_than:1d',
    # Tom Shugart - The Shugart Update (CNAS)
    'from:(thomasshugart) newer_than:1d',
    # Mick Ryan - Futura Doctrina (The Big Five newsletter)
    'from:(mickryan) newer_than:1d',
    # 國防安全研究院（INDSR）編輯組
    'from:(publication@indsr.org.tw) newer_than:1d',
]
# 向後相容
GROK_SEARCH_QUERIES = MAIL_SEARCH_QUERIES

# ============= 日誌設定 =============
os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(INPUT_DIR, exist_ok=True)
os.makedirs(SYSTEM_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler(
            LOG_DIR / f"{datetime.now().strftime('%Y%m%d')}.log",
            encoding='utf-8'
        ),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('gmail_reader')


# ============= HTML 文字提取器 =============
class HTMLTextExtractor(HTMLParser):
    """從 HTML 郵件中提取純文字，保留 URL"""

    def __init__(self):
        super().__init__()
        self.result = []
        self.urls = []
        self.skip = False
        self._current_href = None

    def handle_starttag(self, tag, attrs):
        if tag in ('style', 'script', 'head'):
            self.skip = True
        if tag in ('p', 'h1', 'h2', 'h3', 'h4', 'li', 'br', 'div', 'tr'):
            self.result.append('\n')
        if tag == 'a':
            for attr_name, attr_value in attrs:
                if attr_name == 'href' and attr_value:
                    self._current_href = attr_value
                    # 保留重要連結
                    if any(domain in attr_value for domain in [
                        'x.com', 'twitter.com', 'nids.mod.go.jp',
                        'csis.org', 'rand.org', 'grok.com',
                        'mod.go.jp', 'ltn.com.tw', 'substack.com',
                        'indsr.org.tw'
                    ]):
                        self.urls.append(attr_value)

    def handle_endtag(self, tag):
        if tag in ('style', 'script', 'head'):
            self.skip = False
        if tag in ('p', 'h1', 'h2', 'h3', 'h4', 'li', 'ul', 'ol'):
            self.result.append('\n')
        if tag == 'a' and self._current_href:
            # 在連結文字後附加 URL
            if self._current_href in self.urls:
                self.result.append(f' [{self._current_href}]')
            self._current_href = None

    def handle_data(self, data):
        if not self.skip:
            text = data.strip()
            if text and text != '\xa0':
                self.result.append(text + ' ')


def html_to_text(html_content: str) -> str:
    """
    將 HTML 轉換為純文字
    優先使用 BeautifulSoup（品質較好），備用 HTMLParser
    """
    if BeautifulSoup:
        return _html_to_text_bs4(html_content)
    return _html_to_text_parser(html_content)


def _html_to_text_bs4(html_content: str) -> str:
    """使用 BeautifulSoup 解析 HTML"""
    soup = BeautifulSoup(html_content, 'html.parser')

    # 移除不需要的標籤
    for tag in soup.find_all(['style', 'script', 'head']):
        tag.decompose()

    # 收集重要 URL
    urls = []
    for a_tag in soup.find_all('a', href=True):
        href = a_tag['href']
        if any(domain in href for domain in [
            'x.com', 'twitter.com', 'nids.mod.go.jp', 'csis.org',
            'rand.org', 'grok.com', 'mod.go.jp', 'ltn.com.tw',
            'substack.com', 'gov.tw', 'defense.gov', 'indsr.org.tw'
        ]):
            urls.append(href)
            # 在連結文字後附加 URL
            a_tag.append(f' [{href}]')

    # 提取純文字
    text = soup.get_text(separator='\n', strip=True)

    # 清理多餘空白行
    lines = text.split('\n')
    cleaned = []
    prev_empty = False
    for line in lines:
        stripped = line.strip()
        if stripped:
            cleaned.append(stripped)
            prev_empty = False
        elif not prev_empty:
            cleaned.append('')
            prev_empty = True

    text = '\n'.join(cleaned)

    # 移除郵件尾部版權資訊
    for marker in ['© 2026 X.AI', '© 2025 X.AI', 'Unsubscribe', '取消訂閱']:
        idx = text.find(marker)
        if idx > 0:
            text = text[:idx].rstrip()
            break

    return text


def _html_to_text_parser(html_content: str) -> str:
    """使用內建 HTMLParser 解析（備用方案）"""
    extractor = HTMLTextExtractor()
    extractor.feed(html_content)
    raw = ''.join(extractor.result)

    lines = raw.split('\n')
    cleaned = [line.strip() for line in lines if line.strip()]
    text = '\n'.join(cleaned)

    for marker in ['© 2026 X.AI', '© 2025 X.AI', 'Unsubscribe']:
        idx = text.find(marker)
        if idx > 0:
            text = text[:idx].rstrip()
            break

    return text


# ============= Gmail Reader 主類別 =============
class GrokEmailReader:
    """
    Grok 郵件自動讀取器

    完整流程: authenticate → search → extract → convert → save
    """

    def __init__(
        self,
        credentials_path: Path = CREDENTIALS_FILE,
        token_path: Path = TOKEN_FILE,
        input_dir: Path = INPUT_DIR,
        processed_log: Path = PROCESSED_LOG
    ):
        self.credentials_path = Path(credentials_path)
        self.token_path = Path(token_path)
        self.input_dir = Path(input_dir)
        self.processed_log = Path(processed_log)
        self.service = None
        self._processed_ids = None

    # ---------- Task 2: OAuth2 認證 ----------
    def authenticate(self):
        """
        Gmail API OAuth2 認證
        - 首次：開啟瀏覽器授權
        - 後續：自動使用/刷新 token

        Implements requirement: Gmail API authentication
        """
        creds = None

        # 嘗試載入已存在的 token
        if self.token_path.exists():
            try:
                creds = Credentials.from_authorized_user_file(
                    str(self.token_path), SCOPES
                )
                logger.info("已載入快取的認證 token")
            except Exception as e:
                logger.warning(f"Token 載入失敗，將重新授權: {e}")
                creds = None

        # Token 不存在或已過期
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                # 自動刷新 token
                try:
                    creds.refresh(Request())
                    logger.info("Token 已自動刷新")
                except Exception as e:
                    logger.warning(f"Token 刷新失敗，需要重新授權: {e}")
                    creds = None

            if not creds:
                # 首次授權或刷新失敗
                if not self.credentials_path.exists():
                    logger.error(
                        f"❌ 找不到 credentials.json\n"
                        f"   請依照以下步驟設定 Google Cloud Console：\n"
                        f"   1. 前往 https://console.cloud.google.com/\n"
                        f"   2. 建立新專案 → 啟用 Gmail API\n"
                        f"   3. 建立 OAuth 2.0 用戶端 ID（桌面應用程式）\n"
                        f"   4. 下載 credentials.json 放到:\n"
                        f"      {self.credentials_path}"
                    )
                    raise FileNotFoundError(
                        f"Missing credentials.json at {self.credentials_path}"
                    )

                flow = InstalledAppFlow.from_client_secrets_file(
                    str(self.credentials_path), SCOPES
                )
                creds = flow.run_local_server(port=0)
                logger.info("✅ 首次 OAuth2 授權完成")

            # 儲存 token 供下次使用
            with open(self.token_path, 'w') as f:
                f.write(creds.to_json())
            logger.info(f"Token 已儲存至 {self.token_path}")

        # 建立 Gmail API service
        self.service = build('gmail', 'v1', credentials=creds)
        logger.info("✅ Gmail API 連線成功")
        return self.service

    # ---------- Task 3: 搜尋 Grok 郵件 ----------
    def search_grok_emails(self, hours: int = 24) -> list:
        """
        搜尋最近 N 小時內的 Grok 排程郵件

        Implements requirement: Grok email search and retrieval

        Returns:
            list of message dicts with id, threadId
        """
        if not self.service:
            raise RuntimeError("請先呼叫 authenticate()")

        all_messages = []

        for query in GROK_SEARCH_QUERIES:
            try:
                results = self.service.users().messages().list(
                    userId='me',
                    q=query,
                    maxResults=5
                ).execute()

                messages = results.get('messages', [])
                if messages:
                    logger.info(f"搜尋 '{query}' → 找到 {len(messages)} 封郵件")
                    all_messages.extend(messages)
            except HttpError as e:
                logger.warning(f"搜尋失敗 '{query}': {e}")

        # 去重（by message id）
        seen = set()
        unique = []
        for msg in all_messages:
            if msg['id'] not in seen:
                seen.add(msg['id'])
                unique.append(msg)

        if not unique:
            logger.warning("⚠️ 未找到 Grok 郵件，將使用手動輸入模式")
        else:
            logger.info(f"📬 共找到 {len(unique)} 封不重複的 Grok 郵件")

        return unique

    # ---------- Task 3: 取得郵件內容 ----------
    def get_email_content(self, msg_id: str) -> dict:
        """
        取得郵件完整內容（metadata + body）

        Implements requirement: Grok email search and retrieval

        Returns:
            dict with keys: id, subject, date, sender, body_html, body_text
        """
        try:
            message = self.service.users().messages().get(
                userId='me',
                id=msg_id,
                format='full'
            ).execute()
        except HttpError as e:
            logger.error(f"讀取郵件 {msg_id} 失敗: {e}")
            return None

        # 解析 headers
        headers = {}
        for header in message.get('payload', {}).get('headers', []):
            name = header['name'].lower()
            if name in ('subject', 'date', 'from'):
                headers[name] = header['value']

        # 解析 body
        body_html = ''
        body_text = ''
        payload = message.get('payload', {})

        def extract_parts(payload_part):
            nonlocal body_html, body_text
            mime_type = payload_part.get('mimeType', '')
            body_data = payload_part.get('body', {}).get('data', '')

            if body_data:
                decoded = base64.urlsafe_b64decode(body_data).decode('utf-8', errors='replace')
                if 'html' in mime_type:
                    body_html += decoded
                elif 'text/plain' in mime_type:
                    body_text += decoded

            # 遞迴處理 multipart
            for part in payload_part.get('parts', []):
                extract_parts(part)

        extract_parts(payload)

        result = {
            'id': msg_id,
            'subject': headers.get('subject', '(無主題)'),
            'date': headers.get('date', ''),
            'sender': headers.get('from', ''),
            'body_html': body_html,
            'body_text': body_text,
        }

        # 收集 PDF 附件 ID（用於 INDSR 等含附件來源）
        pdf_attachments = []
        def collect_attachments(part):
            mime = part.get('mimeType', '')
            filename = part.get('filename', '')
            att_id = part.get('body', {}).get('attachmentId', '')
            if 'pdf' in mime and att_id and filename:
                pdf_attachments.append({'filename': filename, 'attachment_id': att_id})
            for sub in part.get('parts', []):
                collect_attachments(sub)
        collect_attachments(payload)
        result['pdf_attachments'] = pdf_attachments

        logger.info(f"📧 郵件: {result['subject']} ({result['date']})")
        if pdf_attachments:
            logger.info(f"   📎 含 {len(pdf_attachments)} 個 PDF 附件")
        return result

    # ---------- PDF 附件文字提取 ----------
    def extract_pdf_attachment(self, msg_id: str, attachment_id: str, filename: str) -> str:
        """下載 PDF 附件並提取文字內容"""
        if not HAS_PDFMINER:
            logger.warning("pdfminer 未安裝，跳過 PDF 提取")
            return ''
        try:
            attachment = self.service.users().messages().attachments().get(
                userId='me', messageId=msg_id, id=attachment_id
            ).execute()
            pdf_bytes = base64.urlsafe_b64decode(attachment['data'])
            text = pdf_extract_text(io.BytesIO(pdf_bytes))
            # 清理多餘空白行
            lines = [l.strip() for l in text.splitlines() if l.strip()]
            return '\n'.join(lines)
        except Exception as e:
            logger.warning(f"PDF 提取失敗 {filename}: {e}")
            return ''

    # ---------- Task 4: HTML 轉文字 ----------
    def convert_to_text(self, email_data: dict) -> str:
        """
        將郵件內容轉為純文字

        Implements requirement: HTML to text conversion
        """
        if email_data.get('body_html'):
            text = html_to_text(email_data['body_html'])
            logger.info(f"HTML → 純文字轉換完成 ({len(text)} 字)")
        elif email_data.get('body_text'):
            text = email_data['body_text']
            logger.info(f"使用純文字內容 ({len(text)} 字)")
        else:
            logger.warning("郵件內容為空")
            return ''

        # 依寄件者決定來源標籤
        sender_lower = email_data.get('sender', '').lower()
        if 'shugart' in sender_lower:
            source_label = "Tom Shugart Daily Update (CNAS)"
        elif 'mickryan' in sender_lower or 'futura' in sender_lower:
            source_label = "Mick Ryan - Futura Doctrina (The Big Five)"
        elif 'indsr.org.tw' in sender_lower:
            source_label = "國防安全研究院（INDSR）研究出版品"
        else:
            source_label = "Grok 每日中共議題搜集分析"

        # 加上 metadata header
        header = (
            f"來源: {source_label}\n"
            f"日期: {email_data.get('date', 'N/A')}\n"
            f"主題: {email_data.get('subject', 'N/A')}\n"
            f"寄件者: {email_data.get('sender', 'N/A')}\n"
            f"郵件ID: {email_data.get('id', 'N/A')}\n"
            f"{'=' * 60}\n\n"
        )

        return header + text

    # ---------- Task 5: 存入 daily_input ----------
    def save_to_input(self, content: str, email_date: str = '', sender: str = '') -> Path:
        """
        存入 _daily_input/ 資料夾

        Implements requirement: Auto-save to daily input

        命名格式依來源：
        - Grok: YYYY MMDD Grok每日彙整.txt
        - Shugart: YYYY MMDD Shugart Daily Update.txt
        - 其他: YYYY MMDD 郵件主題.txt
        """
        if not content or not content.strip():
            logger.warning("內容為空，跳過儲存")
            return None

        # 解析日期
        try:
            # 嘗試多種日期格式
            for fmt in [
                "%a, %d %b %Y %H:%M:%S %z",
                "%a, %d %b %Y %H:%M:%S",
                "%Y-%m-%d",
            ]:
                try:
                    dt = datetime.strptime(email_date.strip()[:31], fmt)
                    break
                except ValueError:
                    continue
            else:
                dt = datetime.now()
        except Exception:
            dt = datetime.now()

        date_str = dt.strftime("%Y %m%d")

        # 根據寄件者決定檔名
        sender_lower = sender.lower()
        if 'shugart' in sender_lower:
            source_label = "Shugart Daily Update"
        elif 'x.ai' in sender_lower or 'grok' in sender_lower:
            source_label = "Grok每日彙整"
        elif 'mickryan' in sender_lower or 'futura' in sender_lower:
            source_label = "Futura Doctrina"
        elif 'indsr.org.tw' in sender_lower:
            source_label = "INDSR國防研究院"
        else:
            source_label = "郵件彙整"
        filename = f"{date_str} {source_label}.txt"
        filepath = self.input_dir / filename

        # 處理檔名衝突
        if filepath.exists():
            version = 2
            while True:
                filename = f"{date_str} {source_label}_v{version}.txt"
                filepath = self.input_dir / filename
                if not filepath.exists():
                    break
                version += 1
            logger.info(f"檔名衝突，改用: {filename}")

        # 寫入檔案
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

        logger.info(f"✅ 已儲存: {filepath.name} ({len(content)} 字)")
        return filepath

    # ---------- 已處理郵件追蹤 ----------
    def _load_processed_ids(self) -> set:
        """載入已處理的郵件 ID"""
        if self._processed_ids is not None:
            return self._processed_ids

        if self.processed_log.exists():
            try:
                with open(self.processed_log, 'r', encoding='utf-8') as f:
                    self._processed_ids = set(json.load(f))
            except (json.JSONDecodeError, Exception):
                self._processed_ids = set()
        else:
            self._processed_ids = set()

        return self._processed_ids

    def _save_processed_ids(self):
        """儲存已處理的郵件 ID"""
        if self._processed_ids is not None:
            with open(self.processed_log, 'w', encoding='utf-8') as f:
                json.dump(list(self._processed_ids), f, indent=2)

    # ---------- Task 6: 完整流程 ----------
    def run(self) -> list:
        """
        執行完整 Gmail 讀取流程

        Implements requirement: Grok email auto-parsing
        Implements design: class: GrokEmailReader

        流程: authenticate → search → extract → convert → save

        Returns:
            list of Path objects for saved files
        """
        saved_files = []

        # Step 1: 認證
        logger.info("=" * 50)
        logger.info("🔄 開始 Gmail 自動讀取流程")
        logger.info("=" * 50)

        try:
            self.authenticate()
        except FileNotFoundError:
            logger.error("認證失敗：缺少 credentials.json")
            return saved_files
        except Exception as e:
            logger.error(f"認證失敗: {e}")
            return saved_files

        # Step 2: 搜尋 Grok 郵件
        try:
            messages = self.search_grok_emails(hours=24)
        except Exception as e:
            logger.error(f"搜尋郵件失敗: {e}")
            return saved_files

        if not messages:
            logger.info("沒有新的 Grok 郵件")
            return saved_files

        # 載入已處理清單
        processed_ids = self._load_processed_ids()

        # Step 3-5: 逐封處理
        for msg in messages:
            msg_id = msg['id']

            # 跳過已處理
            if msg_id in processed_ids:
                logger.info(f"⏭️ 已處理過: {msg_id}")
                continue

            # 取得內容
            email_data = self.get_email_content(msg_id)
            if not email_data:
                continue

            sender_lower = email_data.get('sender', '').lower()
            pdf_attachments = email_data.get('pdf_attachments', [])

            # INDSR 等 PDF 附件來源：每個 PDF 另存一份分析檔
            if 'indsr.org.tw' in sender_lower and pdf_attachments and HAS_PDFMINER:
                for att in pdf_attachments:
                    pdf_text = self.extract_pdf_attachment(
                        msg_id, att['attachment_id'], att['filename']
                    )
                    if not pdf_text:
                        continue
                    # 組合 header + PDF 全文
                    header = (
                        f"來源: 國防安全研究院（INDSR）研究出版品\n"
                        f"日期: {email_data.get('date', 'N/A')}\n"
                        f"主題: {att['filename'].replace('.pdf','')}\n"
                        f"寄件者: {email_data.get('sender', 'N/A')}\n"
                        f"郵件ID: {msg_id}\n"
                        f"{'=' * 60}\n\n"
                    )
                    filepath = self.save_to_input(
                        header + pdf_text,
                        email_data.get('date', ''),
                        email_data.get('sender', '')
                    )
                    if filepath:
                        saved_files.append(filepath)
                processed_ids.add(msg_id)
                continue

            # 一般郵件：轉換 HTML/純文字
            text = self.convert_to_text(email_data)
            if not text:
                continue

            # 存入 _daily_input
            filepath = self.save_to_input(
                text,
                email_data.get('date', ''),
                email_data.get('sender', '')
            )
            if filepath:
                saved_files.append(filepath)
                processed_ids.add(msg_id)

        # 更新已處理清單
        self._save_processed_ids()

        logger.info(f"\n{'=' * 50}")
        logger.info(f"✅ Gmail 讀取完成: {len(saved_files)} 封新郵件已存入")
        logger.info(f"{'=' * 50}")

        return saved_files


# ============= 獨立執行入口 =============
def main():
    """
    獨立執行 Gmail 讀取器
    用法: python gmail_reader.py
    """
    print("\n" + "=" * 60)
    print("  Grok 郵件自動讀取器 v2.0")
    print("  Spectra Change: add-gmail-reader")
    print("=" * 60 + "\n")

    reader = GrokEmailReader()

    try:
        saved_files = reader.run()

        if saved_files:
            print(f"\n📂 已存入 _daily_input/ 的檔案:")
            for f in saved_files:
                print(f"   📄 {f.name}")
            print(f"\n💡 接下來可執行 analysis.py 進行分析")
        else:
            print("\n⚠️ 沒有新郵件需要處理")
            print("   - 可能原因: 今日 Grok 尚未發送 / 已處理過 / 認證問題")
            print("   - 你也可以手動放 .txt 檔案到 _daily_input/ 資料夾")

    except Exception as e:
        print(f"\n❌ 執行失敗: {e}")
        logger.exception("Gmail 讀取器執行失敗")
        print("\n如果是首次使用，請確認:")
        print("  1. credentials.json 已放入專案根目錄")
        print("  2. Google Cloud Console 已啟用 Gmail API")
        print("  3. OAuth 2.0 範圍設定為 gmail.readonly")


if __name__ == "__main__":
    main()
