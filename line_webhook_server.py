"""
LINE Webhook 伺服器 — 接收連結自動存入 _daily_input
=====================================================
功能：
  1. 接收 Moltmilitary LINE Bot 的傳入訊息
  2. 偵測 URL → 抓取網頁/PDF 全文
  3. 純文字訊息 → 直接存檔
  4. 存入 _daily_input/YYYYMMDD_LINE_標題.txt
  5. 回覆 LINE 確認訊息

使用方式：
  python line_webhook_server.py
  （需同時執行 cloudflared，見 start_line_webhook.bat）
"""

import os
import sys
import json
import hmac
import hashlib
import base64
import logging
import re
import subprocess
import threading
import requests
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse, unquote

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

from flask import Flask, request, abort

# ── 路徑設定 ──────────────────────────────────────────────
WORKSPACE   = Path(r"C:\Users\garde\OneDrive\3.教務\1.中共軍事體制研究\每日資料蒐集更新")
INPUT_DIR   = WORKSPACE / "_daily_input"
ENV_FILE    = WORKSPACE / ".env"
LOG_FILE    = WORKSPACE / "line_webhook.log"
INPUT_DIR.mkdir(exist_ok=True)

# ── 日誌 ──────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(str(LOG_FILE), encoding="utf-8"),
    ],
)
log = logging.getLogger("line_webhook")

# ── 載入 .env ─────────────────────────────────────────────
def load_env() -> dict:
    config = {}
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text("utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                config[k.strip()] = v.strip()
    return config

CFG = load_env()
CHANNEL_TOKEN  = CFG.get("LINE_CHANNEL_ACCESS_TOKEN", "")
CHANNEL_SECRET = CFG.get("LINE_CHANNEL_SECRET", "")
USER_ID        = CFG.get("LINE_USER_ID", "")

# ── Flask App ─────────────────────────────────────────────
app = Flask(__name__)

# ── LINE API 工具 ─────────────────────────────────────────
LINE_REPLY_URL = "https://api.line.me/v2/bot/message/reply"
LINE_HEADERS   = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {CHANNEL_TOKEN}",
}

def reply(token: str, text: str):
    """回覆 LINE 訊息"""
    if not CHANNEL_TOKEN or not token:
        return
    # 訊息超長自動截斷
    if len(text) > 5000:
        text = text[:4970] + "\n…（已截斷）"
    payload = {
        "replyToken": token,
        "messages": [{"type": "text", "text": text}],
    }
    try:
        r = requests.post(LINE_REPLY_URL, headers=LINE_HEADERS,
                          json=payload, timeout=10)
        if r.status_code != 200:
            log.warning(f"LINE reply 失敗 {r.status_code}: {r.text[:200]}")
    except Exception as e:
        log.error(f"LINE reply 例外: {e}")


# ── 簽名驗證 ─────────────────────────────────────────────
def verify_signature(body: bytes, sig_header: str) -> bool:
    """驗證 LINE Webhook 簽名（若未設定 SECRET 則跳過）"""
    if not CHANNEL_SECRET:
        log.debug("未設定 LINE_CHANNEL_SECRET，跳過簽名驗證")
        return True
    digest = hmac.new(
        CHANNEL_SECRET.encode("utf-8"), body, hashlib.sha256
    ).digest()
    expected = base64.b64encode(digest).decode("utf-8")
    return hmac.compare_digest(expected, sig_header or "")


# ── URL 偵測 ──────────────────────────────────────────────
URL_RE = re.compile(
    r"https?://[^\s\u3000\uff0c\u3002\uff01\uff1f\u300d\u300f\uff3d\u3011\uff09\uff5d\u2019\u201d>)}\]]+",
    re.IGNORECASE,
)

def extract_urls(text: str) -> list[str]:
    return URL_RE.findall(text)


# ── 網頁抓取 ──────────────────────────────────────────────
FETCH_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
}

def fetch_url_content(url: str) -> tuple[str, str]:
    """
    抓取 URL 內容，回傳 (title, text)
    支援：HTML 網頁、PDF（直連）
    """
    try:
        resp = requests.get(url, headers=FETCH_HEADERS,
                            timeout=20, allow_redirects=True)
        resp.raise_for_status()
        content_type = resp.headers.get("Content-Type", "").lower()

        # ── PDF ───────────────────────────────────────────
        if "pdf" in content_type or url.lower().endswith(".pdf"):
            return _parse_pdf_bytes(resp.content, url)

        # ── HTML ──────────────────────────────────────────
        return _parse_html(resp.text, url)

    except requests.exceptions.Timeout:
        log.warning(f"Timeout: {url}")
        return _url_as_title(url), f"[抓取逾時]\n\nURL: {url}"
    except requests.exceptions.HTTPError as e:
        log.warning(f"HTTP Error {e}: {url}")
        return _url_as_title(url), f"[HTTP 錯誤 {e}]\n\nURL: {url}"
    except Exception as e:
        log.error(f"抓取失敗 {url}: {e}")
        return _url_as_title(url), f"[抓取失敗: {e}]\n\nURL: {url}"


def _parse_html(html: str, url: str) -> tuple[str, str]:
    """BeautifulSoup 解析 HTML → 純文字"""
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        return _url_as_title(url), html[:3000]

    soup = BeautifulSoup(html, "html.parser")

    # 移除雜訊
    for tag in soup(["script", "style", "nav", "footer",
                     "header", "aside", "advertisement"]):
        tag.decompose()

    title = ""
    if soup.title and soup.title.string:
        title = soup.title.string.strip()

    # 嘗試找主要內容區
    main_content = (
        soup.find("article") or
        soup.find(id=re.compile(r"content|article|main|body", re.I)) or
        soup.find(class_=re.compile(r"content|article|main|post|story", re.I)) or
        soup.find("main") or
        soup.body
    )

    if main_content:
        text = main_content.get_text(separator="\n", strip=True)
    else:
        text = soup.get_text(separator="\n", strip=True)

    # 清理多餘空行
    lines = [l for l in text.splitlines() if l.strip()]
    text = "\n".join(lines)

    if not title:
        title = _url_as_title(url)

    return title, f"來源 URL: {url}\n\n{text}"


def _parse_pdf_bytes(data: bytes, url: str) -> tuple[str, str]:
    """pdfminer 解析 PDF bytes"""
    try:
        import io
        from pdfminer.high_level import extract_text
        text = extract_text(io.BytesIO(data))
        title = _url_as_title(url)
        return title, f"來源 URL: {url}\n\n{text}"
    except Exception as e:
        return _url_as_title(url), f"[PDF 解析失敗: {e}]\n\nURL: {url}"


def _url_as_title(url: str) -> str:
    """從 URL 提取可讀標題"""
    try:
        parsed = urlparse(url)
        path = unquote(parsed.path).strip("/")
        parts = [p for p in path.split("/") if p]
        if parts:
            slug = parts[-1]
            slug = re.sub(r"[_\-]", " ", slug)
            slug = re.sub(r"\.\w+$", "", slug)
            return f"{parsed.netloc} - {slug[:60]}"
        return parsed.netloc
    except Exception:
        return url[:80]


# ── 存檔 ─────────────────────────────────────────────────
def safe_filename(s: str, max_len: int = 60) -> str:
    """去除不合法字元，製作安全檔名"""
    s = re.sub(r'[\\/:*?"<>|]', "", s)
    s = s.strip(" .")
    return s[:max_len] if s else "未命名"


def save_to_input(title: str, content: str, source_tag: str = "LINE") -> Path:
    """存入 _daily_input/，回傳路徑"""
    date_str = datetime.now().strftime("%Y %m%d")
    safe_title = safe_filename(title)
    filename = f"{date_str} {source_tag}_{safe_title}.txt"
    filepath = INPUT_DIR / filename

    # 若檔名衝突，加時間戳後綴
    if filepath.exists():
        ts = datetime.now().strftime("%H%M%S")
        filename = f"{date_str} {source_tag}_{safe_title}_{ts}.txt"
        filepath = INPUT_DIR / filename

    header = (
        f"來源: LINE Bot 自動接收 (Moltmilitary)\n"
        f"日期: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"標題: {title}\n"
        f"{'=' * 60}\n\n"
    )
    filepath.write_text(header + content, encoding="utf-8")
    log.info(f"✅ 已存入: {filename}")
    return filepath


# ── Dispatch 指令 ─────────────────────────────────────────
DISPATCH_BAT = WORKSPACE / "run_daily_analysis.bat"
_analysis_lock = threading.Lock()
_analysis_running = False   # 防止重複觸發

DISPATCH_COMMANDS = {"!立即分析", "!分析", "!dispatch", "!run"}
STATUS_COMMANDS   = {"!狀態", "!status", "!state"}
HELP_COMMANDS     = {"!help", "!說明", "!指令"}

def _run_analysis_bg(reply_token: str):
    """在背景執行分析，完成後推送通知"""
    global _analysis_running
    try:
        log.info("🚀 [Dispatch] 啟動每日分析...")
        result = subprocess.run(
            ["cmd", "/c", str(DISPATCH_BAT)],
            cwd=str(WORKSPACE),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=3600,   # 最長等 1 小時
        )
        if result.returncode == 0:
            log.info("✅ [Dispatch] 分析完成")
        else:
            log.error(f"❌ [Dispatch] 分析失敗 (code {result.returncode})\n{result.stderr[:500]}")
    except subprocess.TimeoutExpired:
        log.error("❌ [Dispatch] 分析逾時（超過 1 小時）")
    except Exception as e:
        log.error(f"❌ [Dispatch] 例外: {e}")
    finally:
        _analysis_running = False


def handle_dispatch(reply_token: str) -> bool:
    """處理 !立即分析 等指令，回傳 True 表示已處理"""
    global _analysis_running

    if _analysis_running:
        reply(reply_token,
              "⏳ 分析已在執行中，請稍候...\n完成後將自動發送 Email 與 LINE 通知。")
        return True

    if not DISPATCH_BAT.exists():
        reply(reply_token, f"❌ 找不到執行腳本：{DISPATCH_BAT}")
        return True

    with _analysis_lock:
        if _analysis_running:   # double-check
            reply(reply_token, "⏳ 分析已在執行中，請稍候...")
            return True
        _analysis_running = True

    reply(reply_token,
          "🚀 已啟動每日分析！\n\n"
          "⏱️ 預計需要 10–20 分鐘\n"
          "📧 完成後自動發送 Email 與 LINE 通知\n"
          "─────────────────\n"
          "傳 !狀態 可查詢目前進度")

    t = threading.Thread(target=_run_analysis_bg, args=(reply_token,), daemon=True)
    t.start()
    return True


def handle_status(reply_token: str) -> bool:
    """處理 !狀態 指令"""
    # 最新報告
    output_dir = WORKSPACE / "_daily_output"
    reports = sorted(output_dir.glob("*中共軍事動態綜合分析報告.md"), reverse=True)
    latest = reports[0].name if reports else "（尚無報告）"

    # 待處理檔案
    waiting = list((WORKSPACE / "_daily_input").glob("*.txt"))

    # 分析狀態
    status_icon = "🔄 執行中" if _analysis_running else "✅ 閒置"

    text = (
        f"📊 系統狀態\n"
        f"─────────────────\n"
        f"分析引擎：{status_icon}\n"
        f"最新報告：{latest}\n"
        f"待處理檔案：{len(waiting)} 個\n"
        f"─────────────────\n"
        f"指令：!立即分析 / !狀態 / !說明"
    )
    reply(reply_token, text)
    return True


def handle_help(reply_token: str) -> bool:
    """處理 !說明 指令"""
    text = (
        "📖 可用指令\n"
        "─────────────────\n"
        "!立即分析　立即執行今日情資分析\n"
        "!狀態　　　查看系統與分析進度\n"
        "!說明　　　顯示此說明\n"
        "─────────────────\n"
        "傳送 URL 或文字 → 自動存入待分析資料夾\n"
        "完成後由 Email 與 LINE 通知結果"
    )
    reply(reply_token, text)
    return True


# ── 主要 Webhook 邏輯 ─────────────────────────────────────
def handle_message(event: dict):
    """處理單一 LINE 訊息事件"""
    reply_token = event.get("replyToken", "")
    msg = event.get("message", {})
    msg_type = msg.get("type", "")
    text = msg.get("text", "").strip()

    if msg_type != "text" or not text:
        reply(reply_token, "⚠️ 目前僅支援文字訊息（含 URL 連結）")
        return

    log.info(f"收到訊息: {text[:100]}")

    # ── 指令攔截（優先於 URL 偵測）────────────────────────
    cmd = text.lower().strip()
    if text in DISPATCH_COMMANDS or cmd in DISPATCH_COMMANDS:
        handle_dispatch(reply_token)
        return
    if text in STATUS_COMMANDS or cmd in STATUS_COMMANDS:
        handle_status(reply_token)
        return
    if text in HELP_COMMANDS or cmd in HELP_COMMANDS:
        handle_help(reply_token)
        return

    urls = extract_urls(text)

    if urls:
        # ── 有 URL：抓取每個連結 ──────────────────────────
        results = []
        for url in urls[:3]:  # 最多同時處理 3 個 URL
            log.info(f"正在抓取: {url}")
            reply(reply_token, f"⏳ 正在抓取連結內容...\n{url[:80]}")
            title, content = fetch_url_content(url)
            fp = save_to_input(title, content, source_tag="LINE")
            results.append(f"✅ {fp.name}")

        msg_back = (
            f"📥 已存入 _daily_input/\n"
            f"{'─' * 20}\n"
            + "\n".join(results) +
            f"\n{'─' * 20}\n"
            f"下次分析排程執行時將自動納入。"
        )
        reply(reply_token, msg_back)

    else:
        # ── 純文字：直接存檔 ─────────────────────────────
        # 用前 30 字作為標題
        title = text[:30].replace("\n", " ")
        content = text
        fp = save_to_input(title, content, source_tag="LINE文字")
        reply(
            reply_token,
            f"📝 已存入純文字情報\n{fp.name}\n\n下次分析時將自動納入。"
        )


# ── Flask 路由 ────────────────────────────────────────────
@app.route("/webhook", methods=["POST"])
def webhook():
    body = request.get_data()
    sig  = request.headers.get("X-Line-Signature", "")

    if not verify_signature(body, sig):
        log.warning("簽名驗證失敗！")
        abort(400)

    try:
        data = json.loads(body.decode("utf-8"))
    except Exception as e:
        log.error(f"JSON 解析失敗: {e}")
        abort(400)

    for event in data.get("events", []):
        if event.get("type") == "message":
            handle_message(event)

    return "OK", 200


@app.route("/health", methods=["GET"])
def health():
    return json.dumps({
        "status": "running",
        "input_dir": str(INPUT_DIR),
        "files_waiting": len(list(INPUT_DIR.glob("*.txt"))),
        "time": datetime.now().isoformat(),
    }), 200, {"Content-Type": "application/json"}


# ── 啟動 ─────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 55)
    print("  LINE Webhook 伺服器 — 中共軍事動態分析系統")
    print("=" * 55)
    print(f"📂 Input 目錄: {INPUT_DIR}")
    print(f"🔑 Channel Token: {'已設定' if CHANNEL_TOKEN else '❌ 未設定'}")
    print(f"🔒 Channel Secret: {'已設定' if CHANNEL_SECRET else '⚠️ 未設定（跳過驗證）'}")
    print(f"🚀 啟動在 http://localhost:5000/webhook")
    print("=" * 55)

    if not CHANNEL_TOKEN:
        print("❌ 請先在 .env 設定 LINE_CHANNEL_ACCESS_TOKEN")
        sys.exit(1)

    app.run(host="0.0.0.0", port=5000, debug=False)
