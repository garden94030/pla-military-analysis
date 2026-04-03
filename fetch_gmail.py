"""
從 Gmail 自動擷取 Grok 每日中共軍事分析郵件，存入 _daily_input/
需要 Google Gmail API 憑證才能獨立運行。
此腳本可搭配 analysis.py 使用。
"""
import os
import sys
import json
import re
import base64
from datetime import datetime, timedelta
from pathlib import Path
from html.parser import HTMLParser

# 修正 Windows 終端編碼問題
sys.stdout.reconfigure(encoding='utf-8')

# ============= 設定 =============
WORKSPACE = r"C:\Users\garde\OneDrive\3.教務\1.中共軍事體制研究\每日資料蒐集更新"
INPUT_DIR = Path(WORKSPACE) / "_daily_input"
PROCESSED_LOG = Path(WORKSPACE) / "_system" / "processed_emails.json"

os.makedirs(INPUT_DIR, exist_ok=True)
os.makedirs(PROCESSED_LOG.parent, exist_ok=True)


# ============= HTML 文字提取器 =============
class HTMLTextExtractor(HTMLParser):
    """從 HTML 郵件中提取純文字內容"""

    def __init__(self):
        super().__init__()
        self.result = []
        self.skip = False

    def handle_starttag(self, tag, attrs):
        if tag in ('style', 'script', 'head'):
            self.skip = True
        if tag in ('p', 'h1', 'h2', 'h3', 'li', 'br', 'div', 'tr'):
            self.result.append('\n')
        if tag == 'a':
            for attr_name, attr_value in attrs:
                if attr_name == 'href' and attr_value and 'grok.com/chat' in attr_value:
                    self.result.append(f'\n[Grok 全文連結: {attr_value}]\n')

    def handle_endtag(self, tag):
        if tag in ('style', 'script', 'head'):
            self.skip = False
        if tag in ('p', 'h1', 'h2', 'h3', 'li', 'ul', 'ol'):
            self.result.append('\n')

    def handle_data(self, data):
        if not self.skip:
            text = data.strip()
            if text and text != '\xa0':
                self.result.append(text)


def html_to_text(html_content: str) -> str:
    """將 HTML 轉換為純文字"""
    extractor = HTMLTextExtractor()
    extractor.feed(html_content)
    raw = ' '.join(extractor.result)
    # 清理多餘空白行
    lines = raw.split('\n')
    cleaned = []
    for line in lines:
        stripped = line.strip()
        if stripped:
            cleaned.append(stripped)
    text = '\n'.join(cleaned)
    # 移除郵件尾部版權資訊
    for marker in ['© 2026 X.AI', '© 2025 X.AI', 'Unsubscribe']:
        idx = text.find(marker)
        if idx > 0:
            text = text[:idx].rstrip()
            break
    return text


def load_processed_ids() -> set:
    """載入已處理的郵件 ID"""
    if PROCESSED_LOG.exists():
        with open(PROCESSED_LOG, 'r', encoding='utf-8') as f:
            return set(json.load(f))
    return set()


def save_processed_ids(ids: set):
    """儲存已處理的郵件 ID"""
    with open(PROCESSED_LOG, 'w', encoding='utf-8') as f:
        json.dump(list(ids), f)


def process_email(email_id: str, subject: str, date_str: str, html_body: str) -> Path:
    """處理單封郵件，提取內容並儲存為 txt"""
    text = html_to_text(html_body)

    # 生成檔名
    try:
        dt = datetime.strptime(date_str[:25], "%a, %d %b %Y %H:%M:%S")
    except (ValueError, IndexError):
        dt = datetime.now()

    date_tag = dt.strftime("%Y%m%d")
    safe_subject = re.sub(r'[\\/:*?"<>|]', '_', subject)[:50]
    filename = f"{date_tag}_grok_{safe_subject}.txt"
    filepath = INPUT_DIR / filename

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(f"來源: Grok 每日中共議題搜集分析\n")
        f.write(f"日期: {date_str}\n")
        f.write(f"主題: {subject}\n")
        f.write(f"郵件ID: {email_id}\n")
        f.write(f"{'='*60}\n\n")
        f.write(text)

    return filepath


# ============= 供 Claude Code 呼叫的介面 =============
def process_gmail_data(messages_data: list) -> list:
    """
    處理從 Gmail MCP 工具取得的郵件資料
    messages_data: [{"id": ..., "subject": ..., "date": ..., "body": ...}, ...]
    """
    processed_ids = load_processed_ids()
    new_files = []

    for msg in messages_data:
        email_id = msg["id"]
        if email_id in processed_ids:
            print(f"⏭️ 已處理過: {msg.get('subject', 'unknown')}")
            continue

        filepath = process_email(
            email_id=email_id,
            subject=msg.get("subject", "no_subject"),
            date_str=msg.get("date", ""),
            html_body=msg.get("body", "")
        )
        processed_ids.add(email_id)
        new_files.append(filepath)
        print(f"✅ 已儲存: {filepath.name}")

    save_processed_ids(processed_ids)
    return new_files


if __name__ == "__main__":
    print("此腳本需要透過 Claude Code 呼叫 Gmail MCP 工具來取得郵件。")
    print("請在 Claude Code 中執行自動化流程。")
