"""
LINE Webhook 背景服務版 v2 (line_webhook_service.py)
=====================================================
修正:
  - Flask 改用獨立子 process（非 daemon 執行緒），不會提前結束
  - LINE API 呼叫加入完整 debug，確保 token 正確傳入
  - Cloudflare Tunnel 斷線自動重試
"""
import subprocess
import sys
import time
import os
import re
import json
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path

# ── 路徑設定 ───────────────────────────────────────────────
PYTHON      = r"C:\Users\garde\AppData\Local\Programs\Python\Python313\python.exe"
HERE        = Path(__file__).parent.resolve()
CLOUDFLARED = (
    Path(r"C:\Users\garde\AppData\Local\Microsoft\WinGet\Packages")
    / r"Cloudflare.cloudflared_Microsoft.Winget.Source_8wekyb3d8bbwe"
    / "cloudflared.exe"
)
ENV_FILE    = HERE / ".env"
LOG_FILE    = HERE / "logs" / "line_service.log"
FLASK_LOG   = HERE / "logs" / "flask.log"
LOG_FILE.parent.mkdir(exist_ok=True)

# ── 日誌 ──────────────────────────────────────────────────
def log(msg: str):
    ts   = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass

# ── 讀取 .env ──────────────────────────────────────────────
def load_env() -> dict:
    config = {}
    if not ENV_FILE.exists():
        return config
    for raw in ENV_FILE.read_text(encoding="utf-8").splitlines():
        raw = raw.strip()
        if not raw or raw.startswith("#"):
            continue
        if "=" not in raw:
            continue
        k, v = raw.split("=", 1)
        config[k.strip()] = v.strip()
    return config

# ── 自動更新 LINE Webhook ──────────────────────────────────
def update_line_webhook(tunnel_url: str, token: str) -> bool:
    if not token:
        log("❌ LINE_CHANNEL_ACCESS_TOKEN 為空，跳過更新")
        return False

    webhook_url = tunnel_url.rstrip("/") + "/webhook"
    log(f"🔄 更新 LINE Webhook → {webhook_url}")

    headers = {
        "Content-Type":  "application/json",
        "Authorization": f"Bearer {token}",
    }

    # ── Step A: 等 Tunnel 真正可以連線（最多等 30 秒）────
    log("   等待 Tunnel 可連線...")
    time.sleep(8)  # 給 Tunnel 多一點時間穩定

    # ── Step B: PUT 設定 webhook URL ─────────────────────
    for attempt in range(3):
        body = json.dumps({"endpoint": webhook_url}).encode("utf-8")
        req  = urllib.request.Request(
            "https://api.line.me/v2/bot/channel/webhook/endpoint",
            data=body, method="PUT", headers=headers,
        )
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                resp_body = resp.read().decode()
                log(f"✅ LINE Webhook URL 設定成功！{resp_body}")
                break
        except urllib.error.HTTPError as e:
            err = e.read().decode()
            log(f"⚠️  PUT 失敗 (第{attempt+1}次) {e.code}: {err}")
            if attempt < 2:
                log("   30 秒後重試...")
                time.sleep(30)
        except Exception as e:
            log(f"⚠️  PUT 例外: {e}")
            time.sleep(30)
    else:
        log("❌ 設定 webhook URL 失敗，將在下次 Tunnel 重連時重試")
        return False

    # ── Step C: POST /test 進行 Verify ────────────────────
    time.sleep(3)
    verify_req = urllib.request.Request(
        "https://api.line.me/v2/bot/channel/webhook/test",
        data=b"{}",
        method="POST",
        headers=headers,
    )
    try:
        with urllib.request.urlopen(verify_req, timeout=15) as resp:
            resp_body = resp.read().decode()
            log(f"✅ LINE Webhook Verify 成功！{resp_body}")
            return True
    except urllib.error.HTTPError as e:
        err = e.read().decode()
        log(f"⚠️  Verify 失敗 {e.code}: {err}（Webhook URL 已設定，但 Verify 未通過）")
        return True  # URL 已設定，繼續運行
    except Exception as e:
        log(f"⚠️  Verify 例外: {e}")
        return True


# ── Tunnel URL 偵測 ────────────────────────────────────────
URL_RE = re.compile(r"https://[a-z0-9\-]+\.trycloudflare\.com")

def run_tunnel_once(token: str) -> int:
    """
    執行一次 Cloudflare Tunnel，偵測到 URL 後更新 LINE Webhook。
    回傳 exit code。
    """
    log("🌐 Cloudflare Tunnel 啟動中...")
    proc = subprocess.Popen(
        [str(CLOUDFLARED), "tunnel", "--url", "http://localhost:5000"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    webhook_updated = False
    for line in proc.stdout:
        stripped = line.rstrip()
        # 只記錄重要行（避免日誌爆炸）
        if any(k in stripped for k in ["ERR", "WRN", "trycloudflare", "Registered", "INF Request"]):
            log(f"[CF] {stripped}")

        if not webhook_updated:
            m = URL_RE.search(stripped)
            if m:
                tunnel_url = m.group(0)
                log(f"✅ Tunnel URL 取得: {tunnel_url}")
                webhook_updated = update_line_webhook(tunnel_url, token)

    proc.wait()
    return proc.returncode

# ── 主程序 ────────────────────────────────────────────────
def main():
    log("=" * 55)
    log("LINE Webhook 背景服務 v2 啟動")
    log("=" * 55)

    cfg   = load_env()
    token = cfg.get("LINE_CHANNEL_ACCESS_TOKEN", "")

    if not token:
        log("❌ .env 缺少 LINE_CHANNEL_ACCESS_TOKEN，停止")
        sys.exit(1)

    log(f"✅ Token 已載入（{len(token)} 字元）")

    # ── Step 1: 啟動 Flask（獨立子 process）──────────────
    log("🚀 Flask server 啟動中...")
    flask_log_f = open(FLASK_LOG, "a", encoding="utf-8")
    flask_proc  = subprocess.Popen(
        [PYTHON, str(HERE / "line_webhook_server.py")],
        stdout=flask_log_f,
        stderr=flask_log_f,
        cwd=str(HERE),
    )
    log(f"✅ Flask server 已啟動 (PID {flask_proc.pid})")
    time.sleep(4)  # 等 Flask 就緒

    # ── Step 2: Tunnel 主迴圈（自動重連）─────────────────
    attempt = 0
    RETRY   = 60
    while True:
        attempt += 1
        log(f"🔄 Tunnel 啟動嘗試 #{attempt}")
        try:
            rc = run_tunnel_once(token)
            log(f"Tunnel 結束 (exit={rc})，{RETRY}s 後重試...")
        except Exception as e:
            log(f"❌ Tunnel 例外: {e}，{RETRY}s 後重試...")

        # 若 Flask 意外結束，重啟它
        if flask_proc.poll() is not None:
            log("⚠️  Flask 意外結束，重啟中...")
            flask_proc = subprocess.Popen(
                [PYTHON, str(HERE / "line_webhook_server.py")],
                stdout=flask_log_f,
                stderr=flask_log_f,
                cwd=str(HERE),
            )
            log(f"✅ Flask 重啟完成 (PID {flask_proc.pid})")
            time.sleep(4)

        time.sleep(RETRY)

if __name__ == "__main__":
    main()
