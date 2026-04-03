"""
Notifier — 分析結果通知模組（Email + LINE Bot）
================================================
功能：
  1. Email：透過 Gmail API 發送分析報告摘要
  2. LINE Bot：透過 LINE Messaging API 推送通知

Spectra Change: add-notifications
"""

import os
import sys
import json
import logging
import base64
from pathlib import Path
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

try:
    import requests
except ImportError:
    requests = None

logger = logging.getLogger('notifier')

# ============= 設定 =============
WORKSPACE = Path(r"C:\Users\garde\OneDrive\3.教務\1.中共軍事體制研究\每日資料蒐集更新")
ENV_FILE = WORKSPACE / ".env"


def load_env():
    """從 .env 載入設定"""
    config = {}
    if ENV_FILE.exists():
        with open(ENV_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    config[key.strip()] = value.strip()
    return config


# ============================================================
#  Email 通知（透過 Gmail API）
# ============================================================
class EmailNotifier:
    """
    使用已認證的 Gmail API 發送分析報告摘要
    """

    def __init__(self, gmail_service=None, recipients=None):
        self.service = gmail_service
        # 支援多個收信人：列表或逗號分隔的字符串
        if recipients is None:
            # 從 .env 讀取，或使用預設值
            config = load_env()
            email_str = config.get('NOTIFICATION_EMAILS', 'garden94030@gmail.com,chengkunma@gmail.com,y0528.gary@gmail.com,gm@securetaiwan.org')
            self.recipients = [e.strip() for e in email_str.split(',') if e.strip()]
        elif isinstance(recipients, str):
            self.recipients = [e.strip() for e in recipients.split(',') if e.strip()]
        elif isinstance(recipients, list):
            self.recipients = recipients
        else:
            self.recipients = ['garden94030@gmail.com']

    def _get_gmail_service(self):
        """取得 Gmail API service（重用 gmail_reader 的認證）"""
        if self.service:
            return self.service

        try:
            from gmail_reader import GrokEmailReader
            reader = GrokEmailReader()
            self.service = reader.authenticate()
            return self.service
        except Exception as e:
            logger.error(f"Gmail API 認證失敗: {e}")
            return None

    def _markdown_to_html(self, md_text: str) -> str:
        """簡易 Markdown 轉 HTML"""
        lines = md_text.split('\n')
        html_lines = []
        in_list = False

        for line in lines:
            stripped = line.strip()

            if stripped.startswith('# '):
                if in_list:
                    html_lines.append('</ul>')
                    in_list = False
                html_lines.append(f'<h1 style="color:#1a5276;border-bottom:2px solid #2c3e50;">{stripped[2:]}</h1>')
            elif stripped.startswith('## '):
                if in_list:
                    html_lines.append('</ul>')
                    in_list = False
                html_lines.append(f'<h2 style="color:#2c3e50;margin-top:20px;">{stripped[3:]}</h2>')
            elif stripped.startswith('### '):
                if in_list:
                    html_lines.append('</ul>')
                    in_list = False
                html_lines.append(f'<h3 style="color:#34495e;">{stripped[4:]}</h3>')
            elif stripped.startswith('- ') or stripped.startswith('* '):
                if not in_list:
                    html_lines.append('<ul style="margin-left:20px;">')
                    in_list = True
                content = stripped[2:]
                # Bold
                while '**' in content:
                    content = content.replace('**', '<strong>', 1)
                    content = content.replace('**', '</strong>', 1)
                html_lines.append(f'<li>{content}</li>')
            elif stripped.startswith('---'):
                if in_list:
                    html_lines.append('</ul>')
                    in_list = False
                html_lines.append('<hr style="border:1px solid #bdc3c7;margin:15px 0;">')
            elif stripped:
                if in_list:
                    html_lines.append('</ul>')
                    in_list = False
                # Bold
                while '**' in stripped:
                    stripped = stripped.replace('**', '<strong>', 1)
                    stripped = stripped.replace('**', '</strong>', 1)
                html_lines.append(f'<p>{stripped}</p>')
            else:
                if in_list:
                    html_lines.append('</ul>')
                    in_list = False

        if in_list:
            html_lines.append('</ul>')

        return '\n'.join(html_lines)

    def send_report(self, report_path: Path, subject: str = None) -> bool:
        """
        發送分析報告到 Email

        Args:
            report_path: 報告 .md 檔案路徑
            subject: 郵件主題（預設自動生成）
        """
        service = self._get_gmail_service()
        if not service:
            logger.error("無法取得 Gmail API service")
            return False

        # 讀取報告
        try:
            with open(report_path, 'r', encoding='utf-8') as f:
                report_content = f.read()
        except Exception as e:
            logger.error(f"讀取報告失敗: {e}")
            return False

        # 生成主題
        if not subject:
            date_str = datetime.now().strftime('%Y-%m-%d')
            subject = f"📊 中共軍事動態分析報告 — {date_str}"

        # 建立郵件
        msg = MIMEMultipart('alternative')
        msg['To'] = ', '.join(self.recipients)
        msg['Subject'] = subject

        # 純文字版
        msg.attach(MIMEText(report_content, 'plain', 'utf-8'))

        # HTML 版（美化）
        html_body = f"""
        <html>
        <body style="font-family:'Microsoft JhengHei','PingFang TC',sans-serif;max-width:800px;margin:0 auto;padding:20px;background:#fafafa;">
            <div style="background:#2c3e50;color:white;padding:20px;border-radius:8px 8px 0 0;">
                <h1 style="margin:0;font-size:20px;">🔍 中共軍事動態分析系統</h1>
                <p style="margin:5px 0 0;opacity:0.8;font-size:14px;">{datetime.now().strftime('%Y-%m-%d %H:%M')} 自動產出</p>
            </div>
            <div style="background:white;padding:20px;border:1px solid #e0e0e0;border-radius:0 0 8px 8px;">
                {self._markdown_to_html(report_content)}
            </div>
            <p style="color:#999;font-size:12px;text-align:center;margin-top:20px;">
                此郵件由中共軍事動態分析系統自動發送
            </p>
        </body>
        </html>
        """
        msg.attach(MIMEText(html_body, 'html', 'utf-8'))

        # 發送
        try:
            raw = base64.urlsafe_b64encode(msg.as_bytes()).decode('utf-8')
            service.users().messages().send(
                userId='me',
                body={'raw': raw}
            ).execute()
            logger.info(f"📧 報告已寄送至 {', '.join(self.recipients)}")
            return True
        except Exception as e:
            logger.error(f"郵件發送失敗: {e}")
            return False

    def send_summary(self, summary_text: str, subject: str = None) -> bool:
        """發送簡短摘要（不需要檔案）"""
        service = self._get_gmail_service()
        if not service:
            return False

        if not subject:
            date_str = datetime.now().strftime('%Y-%m-%d')
            subject = f"📊 中共軍事動態每日摘要 — {date_str}"

        msg = MIMEText(summary_text, 'plain', 'utf-8')
        msg['To'] = ', '.join(self.recipients)
        msg['Subject'] = subject

        try:
            raw = base64.urlsafe_b64encode(msg.as_bytes()).decode('utf-8')
            service.users().messages().send(
                userId='me', body={'raw': raw}
            ).execute()
            logger.info(f"📧 摘要已寄送至 {', '.join(self.recipients)}")
            return True
        except Exception as e:
            logger.error(f"摘要發送失敗: {e}")
            return False


# ============================================================
#  LINE Bot 通知
# ============================================================
class LineBotNotifier:
    """
    使用 LINE Messaging API 推送分析報告摘要

    需要設定：
      LINE_CHANNEL_ACCESS_TOKEN: LINE Bot 的 Channel Access Token
      LINE_USER_ID: 接收通知的使用者 ID
    """

    API_URL = 'https://api.line.me/v2/bot/message/push'
    MAX_TEXT_LENGTH = 5000  # LINE 單則訊息上限

    def __init__(self, channel_token: str = None, user_id: str = None):
        config = load_env()
        self.channel_token = channel_token or config.get('LINE_CHANNEL_ACCESS_TOKEN', '')
        self.user_id = user_id or config.get('LINE_USER_ID', '')

        if not self.channel_token or not self.user_id:
            logger.warning("LINE Bot 設定不完整，請檢查 .env 檔案")

    def _truncate(self, text: str, max_len: int = None) -> str:
        """截斷文字至 LINE 長度限制"""
        max_len = max_len or self.MAX_TEXT_LENGTH
        if len(text) <= max_len:
            return text
        return text[:max_len - 20] + '\n\n...（內容已截斷）'

    def send_text(self, text: str) -> bool:
        """發送純文字訊息"""
        if not requests:
            logger.error("需要安裝 requests 套件: pip install requests")
            return False

        if not self.channel_token or not self.user_id:
            logger.error("LINE Bot 設定不完整")
            return False

        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.channel_token}'
        }

        # 如果文字太長，分割成多則訊息
        chunks = []
        if len(text) > self.MAX_TEXT_LENGTH:
            lines = text.split('\n')
            current_chunk = []
            current_len = 0
            for line in lines:
                if current_len + len(line) + 1 > self.MAX_TEXT_LENGTH - 100:
                    chunks.append('\n'.join(current_chunk))
                    current_chunk = [line]
                    current_len = len(line)
                else:
                    current_chunk.append(line)
                    current_len += len(line) + 1
            if current_chunk:
                chunks.append('\n'.join(current_chunk))
        else:
            chunks = [text]

        success = True
        for i, chunk in enumerate(chunks):
            payload = {
                'to': self.user_id,
                'messages': [{
                    'type': 'text',
                    'text': chunk
                }]
            }

            try:
                resp = requests.post(self.API_URL, headers=headers, json=payload, timeout=10)
                if resp.status_code == 200:
                    logger.info(f"📱 LINE 訊息已發送 ({i+1}/{len(chunks)})")
                else:
                    logger.error(f"LINE API 錯誤 {resp.status_code}: {resp.text}")
                    success = False
            except Exception as e:
                logger.error(f"LINE 發送失敗: {e}")
                success = False

        return success

    def send_report_summary(self, report_path: Path) -> bool:
        """
        從報告檔案提取摘要並發送到 LINE

        只發送標題 + 重點事件摘要（控制在 LINE 訊息長度內）
        """
        try:
            with open(report_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            logger.error(f"讀取報告失敗: {e}")
            return False

        # 提取摘要（前 2000 字 + 標題資訊）
        date_str = datetime.now().strftime('%Y-%m-%d %H:%M')
        summary = (
            f"🔍 中共軍事動態分析報告\n"
            f"📅 {date_str}\n"
            f"{'─' * 25}\n\n"
        )

        # 提取標題和重點
        lines = content.split('\n')
        extracted = []
        for line in lines:
            stripped = line.strip()
            if stripped.startswith('# '):
                extracted.append(f"📌 {stripped[2:]}")
            elif stripped.startswith('## '):
                extracted.append(f"\n▸ {stripped[3:]}")
            elif stripped.startswith('### '):
                extracted.append(f"  • {stripped[4:]}")
            elif stripped.startswith('- **') or stripped.startswith('* **'):
                extracted.append(f"  {stripped}")

        summary += '\n'.join(extracted[:50])  # 最多 50 行

        summary += (
            f"\n\n{'─' * 25}\n"
            f"📂 完整報告已存入 _daily_output/\n"
            f"📧 詳細報告已寄送至 Email"
        )

        return self.send_text(self._truncate(summary))


# ============================================================
#  統一通知介面
# ============================================================
class Notifier:
    """
    統一通知管理器 — 同時發送 Email 和 LINE

    用法：
        notifier = Notifier()
        notifier.notify_report(report_path)
    """

    def __init__(self, gmail_service=None):
        self.email = EmailNotifier(gmail_service=gmail_service)
        self.line = LineBotNotifier()
        self._line_available = bool(self.line.channel_token and self.line.user_id)

    def notify_report(self, report_path: Path, subject: str = None) -> dict:
        """
        發送報告通知（Email + LINE）

        Returns:
            dict: {'email': bool, 'line': bool}
        """
        results = {'email': False, 'line': False}

        # Email（完整報告）
        try:
            results['email'] = self.email.send_report(report_path, subject)
        except Exception as e:
            logger.error(f"Email 通知失敗: {e}")

        # LINE（摘要）
        if self._line_available:
            try:
                results['line'] = self.line.send_report_summary(report_path)
            except Exception as e:
                logger.error(f"LINE 通知失敗: {e}")
        else:
            logger.info("LINE Bot 未設定，跳過 LINE 通知")

        return results

    def notify_summary(self, text: str, subject: str = None) -> dict:
        """發送文字摘要通知"""
        results = {'email': False, 'line': False}

        try:
            results['email'] = self.email.send_summary(text, subject)
        except Exception as e:
            logger.error(f"Email 摘要失敗: {e}")

        if self._line_available:
            try:
                results['line'] = self.line.send_text(text)
            except Exception as e:
                logger.error(f"LINE 摘要失敗: {e}")

        return results


# ============= 獨立測試 =============
if __name__ == "__main__":
    print("=" * 50)
    print("  分析報告通知發送")
    print("=" * 50)

    notifier = Notifier()

    # 發送 2026-03-31 完整分析報告
    report_path = Path(r"C:\Users\garde\OneDrive\3.教務\1.中共軍事體制研究\每日資料蒐集更新\_daily_output\20260331_中共軍事動態綜合分析報告.md")

    if report_path.exists():
        print(f"📄 發送報告: {report_path.name}")
        result = notifier.notify_report(report_path, subject="📊 2026-03-31 中共軍事動態綜合分析報告")
        print(f"\n✅ Email: {'成功' if result['email'] else '失敗'}")
        print(f"✅ LINE:  {'成功' if result['line'] else '未設定或失敗'}")
    else:
        print(f"❌ 報告檔案不存在: {report_path}")
