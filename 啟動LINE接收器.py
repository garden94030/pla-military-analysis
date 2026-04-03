"""
LINE Webhook 啟動器 v2
=====================
直接雙擊此 .py 檔即可啟動。

新功能：自動偵測 Cloudflare Tunnel URL，並自動更新 LINE Webhook 設定。
完全不需要手動複製貼上！
"""
import subprocess
import threading
import sys
import time
import os
import re
import json
import urllib.request
import urllib.error

# ── 固定使用有 Flask 的 Python ─────────────────────────────
PYTHON = r"C:\Users\garde\AppData\Local\Programs\Python\Python313\python.exe"

HERE = os.path.dirname(os.path.abspath(__file__))
CLOUDFLARED = (
    r"C:\Users\garde\AppData\Local\Microsoft\WinGet\Packages"
    r"\Cloudflare.cloudflared_Microsoft.Winget.Source_8wekyb3d8bbwe"
    r"\cloudflared.exe"
)
ENV_FILE = os.path.join(HERE, ".env")

# ── 讀取 .env ──────────────────────────────────────────────
def load_env():
    config = {}
    if os.path.exists(ENV_FILE):
        with open(ENV_FILE, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    config[k.strip()] = v.strip()
    return config

# ── 自動更新 LINE Webhook URL ──────────────────────────────
def update_line_webhook(tunnel_url: str, channel_token: str) -> bool:
    webhook_url = tunnel_url.rstrip("/") + "/webhook"
    api_url = "https://api.line.me/v2/bot/channel/webhook/endpoint"

    payload = json.dumps({"webhook_url": webhook_url}).encode("utf-8")
    req = urllib.request.Request(
        api_url,
        data=payload,
        method="PUT",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {channel_token}",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            ok = resp.status == 200
            if ok:
                print(f"\n✅ LINE Webhook 已自動更新！")
                print(f"   Webhook URL: {webhook_url}")
            return ok
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"\n⚠️  LINE API 回應 {e.code}: {body}")
        return False
    except Exception as e:
        print(f"\n⚠️  更新 LINE Webhook 失敗: {e}")
        return False

# ── 啟動 Flask (背景) ──────────────────────────────────────
def run_flask():
    subprocess.run([PYTHON, os.path.join(HERE, "line_webhook_server.py")])

# ── 主程序 ────────────────────────────────────────────────
def main():
    print("=" * 55)
    print("  LINE Webhook 啟動器 v2（自動更新 Webhook URL）")
    print("=" * 55)

    cfg = load_env()
    token = cfg.get("LINE_CHANNEL_ACCESS_TOKEN", "")
    if not token:
        print("❌ .env 缺少 LINE_CHANNEL_ACCESS_TOKEN，請確認設定")
        input("按 Enter 結束...")
        return

    # [1/3] 啟動 Flask
    print("\n[1/3] 啟動 Flask server (port 5000)...")
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    time.sleep(3)
    print("      ✅ Flask 已啟動")

    # [2/3] 啟動 Cloudflare Tunnel，擷取 URL
    print("\n[2/3] 啟動 Cloudflare Tunnel，等待取得 URL...")
    url_pattern = re.compile(r"https://[a-z0-9\-]+\.trycloudflare\.com")
    tunnel_url = None

    proc = subprocess.Popen(
        [CLOUDFLARED, "tunnel", "--url", "http://localhost:5000"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        creationflags=0,
    )

    # 即時讀取輸出，找到 URL 後自動更新 LINE
    for line in proc.stdout:
        print(f"  {line}", end="")  # 顯示 cloudflared 原始輸出

        if tunnel_url is None:
            match = url_pattern.search(line)
            if match:
                tunnel_url = match.group(0)
                print(f"\n{'=' * 55}")
                print(f"  🌐 Tunnel URL 已取得: {tunnel_url}")
                print(f"{'=' * 55}")

                # [3/3] 自動更新 LINE Webhook
                print(f"\n[3/3] 自動更新 LINE Webhook URL...")
                success = update_line_webhook(tunnel_url, token)
                if success:
                    print(f"\n{'=' * 55}")
                    print(f"  🎉 全部完成！系統正在執行中")
                    print(f"{'=' * 55}")
                    print(f"\n  現在可以在 LINE 傳訊息給 Moltmilitary Bot 測試：")
                    print(f"  例如傳送：https://www.reuters.com/world/china/")
                    print(f"\n  ⚠️  請勿關閉此視窗（關閉則 Tunnel 中斷）")
                    print(f"{'=' * 55}\n")
                else:
                    print(f"\n  請手動將以下 URL 填入 LINE Developers Console:")
                    print(f"  {tunnel_url}/webhook")

    proc.wait()
    print("\n[系統] Cloudflare Tunnel 已結束。")
    input("按 Enter 關閉...")

if __name__ == "__main__":
    main()
