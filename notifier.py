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
            email_str = config.get('NOTIFICATION_EMAILS', 'garden94030@gmail.com,chengkunma@gmail.com,y0528.gary@gmail.com,gm@securetaiwan.org,nec3366@gmail.com')
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
        """簡易 Markdown 轉 HTML（支援超連結、行內程式碼、有序清單、front matter）"""
        lines = md_text.split('\n')
        html_lines = []
        in_ul = False
        in_fm = False   # front matter block

        for line in lines:
            stripped = line.strip()

            # ── Headings ──
            if stripped.startswith('# '):
                self._close_list(html_lines, in_ul); in_ul = False
                html_lines.append(f'<h1 style="color:#1a5276;border-bottom:2px solid #2c3e50;">{self._inline_md(stripped[2:])}</h1>')
                continue
            if stripped.startswith('## '):
                self._close_list(html_lines, in_ul); in_ul = False
                html_lines.append(f'<h2 style="color:#2c3e50;margin-top:20px;">{self._inline_md(stripped[3:])}</h2>')
                continue
            if stripped.startswith('### '):
                self._close_list(html_lines, in_ul); in_ul = False
                html_lines.append(f'<h3 style="color:#34495e;">{self._inline_md(stripped[4:])}</h3>')
                continue
            if stripped.startswith('#### '):
                self._close_list(html_lines, in_ul); in_ul = False
                html_lines.append(f'<h4 style="color:#566573;">{self._inline_md(stripped[5:])}</h4>')
                continue

            # ── HR ──
            if stripped.startswith('---'):
                self._close_list(html_lines, in_ul); in_ul = False
                html_lines.append('<hr style="border:1px solid #bdc3c7;margin:15px 0;">')
                continue

            # ── 無序清單 ──
            if stripped.startswith('- ') or stripped.startswith('* '):
                if not in_ul:
                    html_lines.append('<ul style="margin-left:20px;">')
                    in_ul = True
                html_lines.append(f'<li>{self._inline_md(stripped[2:])}</li>')
                continue

            # ── 有序清單  1. / 2. … ──
            import re as _re
            ol_m = _re.match(r'^(\d+)\.\s+(.+)', stripped)
            if ol_m:
                self._close_list(html_lines, in_ul); in_ul = False
                html_lines.append(
                    f'<p style="margin:4px 0 4px 8px;">'
                    f'<strong>{ol_m.group(1)}.</strong> {self._inline_md(ol_m.group(2))}</p>'
                )
                continue

            # ── Front matter 型 key: value（短行） ──
            fm_m = _re.match(r'^([a-zA-Z_\u4e00-\u9fff]{1,20}):\s+(.+)$', stripped)
            if fm_m and len(stripped) < 150 and not stripped.startswith('http'):
                self._close_list(html_lines, in_ul); in_ul = False
                k, v = fm_m.group(1), fm_m.group(2)
                html_lines.append(
                    f'<p style="margin:2px 0;font-size:13px;color:#555;">'
                    f'<strong style="color:#2c3e50;">{k}</strong>: {self._inline_md(v)}</p>'
                )
                continue

            # ── 一般段落 ──
            if stripped:
                self._close_list(html_lines, in_ul); in_ul = False
                html_lines.append(f'<p style="line-height:1.7;">{self._inline_md(stripped)}</p>')
            else:
                self._close_list(html_lines, in_ul); in_ul = False

        if in_ul:
            html_lines.append('</ul>')

        return '\n'.join(html_lines)

    @staticmethod
    def _close_list(html_lines: list, in_ul: bool):
        """如果在清單中，先關閉 </ul>"""
        if in_ul:
            html_lines.append('</ul>')

    @staticmethod
    def _inline_md(text: str) -> str:
        """行內 Markdown：[text](url) 超連結 / `code` / **bold** / *italic*"""
        import re
        # [text](url) → <a href>
        text = re.sub(
            r'\[([^\]]+)\]\((https?://[^\)\s]+)\)',
            r'<a href="\2" style="color:#2980b9;text-decoration:underline;">\1</a>',
            text
        )
        # `code` → <code>
        text = re.sub(
            r'`([^`]+)`',
            r'<code style="background:#f0f0f0;padding:1px 5px;border-radius:3px;font-family:monospace;">\1</code>',
            text
        )
        # **bold**
        text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
        # *italic*
        text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
        return text

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

        # 建立郵件（密件副本，收件人互不可見）
        msg = MIMEMultipart('alternative')
        msg['Bcc'] = ', '.join(self.recipients)
        msg['Subject'] = subject

        # 純文字版
        msg.attach(MIMEText(report_content, 'plain', 'utf-8'))

        # HTML 版（美化）
        # 解析 front matter（title, date, type, status, author, reviewer）
        lines = report_content.split('\n')
        fm_dict = {}
        body_lines = []
        fm_parsing = True
        for line in lines:
            if fm_parsing and ':' in line and not line.startswith('---') and line.strip() != '':
                # 只取第一個 ':' 前後作為 key/value
                key, val = line.split(':', 1)
                fm_dict[key.strip().lower()] = val.strip()
                continue
            else:
                fm_parsing = False
                body_lines.append(line)
        body_md = '\n'.join(body_lines).strip()
        # 建立 HTML
        html_body = f"""
        <html>
        <body style="font-family:'Microsoft JhengHei','PingFang TC',sans-serif;max-width:800px;margin:0 auto;padding:20px;background:#fafafa;">
            <div style="background:#2c3e50;color:white;padding:20px;border-radius:8px 8px 0 0;">
                <h1 style="margin:0;font-size:20px;">🔍 中共軍事動態分析系統</h1>
                <p style="margin:5px 0 0;opacity:0.8;font-size:14px;">{datetime.now().strftime('%Y-%m-%d %H:%M')} 自動產出</p>
            </div>
            <div style="background:white;padding:20px;border:1px solid #e0e0e0;border-radius:0 0 8px 8px;">
                <h2 style="color:#1a5276;">{fm_dict.get('title', '綜合分析報告')}</h2>
                <p style="margin:2px 0;font-size:13px;color:#555;"><strong style="color:#2c3e50;">date</strong>: {fm_dict.get('date', datetime.now().strftime('%Y-%m-%d'))}</p>
                <p style="margin:2px 0;font-size:13px;color:#555;"><strong style="color:#2c3e50;">type</strong>: {fm_dict.get('type', '')}</p>
                <p style="margin:2px 0;font-size:13px;color:#555;"><strong style="color:#2c3e50;">status</strong>: {fm_dict.get('status', '')}</p>
                <p style="margin:2px 0;font-size:13px;color:#555;"><strong style="color:#2c3e50;">author</strong>: {fm_dict.get('author', '')}</p>
                <p style="margin:2px 0;font-size:13px;color:#555;"><strong style="color:#2c3e50;">reviewer</strong>: {fm_dict.get('reviewer', '')}</p>
                <hr style="border:1px solid #bdc3c7;margin:15px 0;"/>
                {self._markdown_to_html(body_md)}
            </div>
            <p style="color:#999;font-size:12px;text-align:center;margin-top:20px;">此郵件由中共軍事動態分析系統自動發送</p>
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
        msg['Bcc'] = ', '.join(self.recipients)
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
        將完整綜合分析報告內容發送到 LINE（去除 Markdown 語法）

        超過 5000 字時自動分段發送多則訊息。
        """
        try:
            with open(report_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            logger.error(f"讀取報告失敗: {e}")
            return False

        # 將 Markdown 轉為適合 LINE 純文字閱讀的格式
        import re
        lines = content.split('\n')
        clean_lines = []
        for line in lines:
            stripped = line.strip()
            # 跳過 YAML frontmatter 分隔線
            if stripped == '---':
                continue
            # 標題轉換
            if stripped.startswith('# '):
                clean_lines.append(f"【{stripped[2:]}】")
            elif stripped.startswith('## '):
                clean_lines.append(f"\n◆ {stripped[3:]}")
            elif stripped.startswith('### '):
                clean_lines.append(f"  ▸ {stripped[4:]}")
            elif stripped.startswith('#### '):
                clean_lines.append(f"    • {stripped[5:]}")
            else:
                # 去除 Markdown 粗體/斜體、行內程式碼
                clean = re.sub(r'\*\*(.+?)\*\*', r'\1', stripped)
                clean = re.sub(r'\*(.+?)\*', r'\1', clean)
                clean = re.sub(r'`(.+?)`', r'\1', clean)
                # 去除表格分隔行（|---|---|）
                if re.match(r'^[\|\s\-:]+$', clean):
                    continue
                clean_lines.append(clean)

        text = '\n'.join(clean_lines).strip()
        return self.send_text(text)


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


# ============= 獨立執行 =============
if __name__ == "__main__":
    import argparse
    import glob

    parser = argparse.ArgumentParser(description="發送分析報告通知")
    parser.add_argument("--report", type=str, default=None, help="報告 .md 檔案路徑（不指定則自動選最新）")
    parser.add_argument("--subject", type=str, default=None, help="郵件主題")
    args = parser.parse_args()

    print("=" * 50)
    print("  分析報告通知發送")
    print("=" * 50)

    notifier = Notifier()

    if args.report:
        report_path = Path(args.report)
    else:
        # 自動偵測 _daily_output/ 中最新的綜合分析報告
        base_dir = Path(__file__).parent / "_daily_output"
        candidates = sorted(base_dir.glob("*中共軍事動態綜合分析報告.md"), reverse=True)
        if not candidates:
            print("❌ 找不到任何綜合分析報告，請確認 _daily_output/ 目錄")
            exit(1)
        report_path = candidates[0]

    if report_path.exists():
        print(f"📄 發送報告: {report_path.name}")
        result = notifier.notify_report(report_path, subject=args.subject)
        print(f"\n✅ Email: {'成功' if result.get('email') else '失敗'}")
        print(f"✅ LINE:  {'成功' if result.get('line') else '未設定或失敗'}")
    else:
        print(f"❌ 報告檔案不存在: {report_path}")
