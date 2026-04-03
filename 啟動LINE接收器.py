"""
LINE Webhook 啟動器
直接雙擊此 .py 檔即可啟動
"""
import subprocess
import threading
import sys
import time
import os

PYTHON   = sys.executable
HERE     = os.path.dirname(os.path.abspath(__file__))
CLOUDFLARED = (
    r"C:\Users\garde\AppData\Local\Microsoft\WinGet\Packages"
    r"\Cloudflare.cloudflared_Microsoft.Winget.Source_8wekyb3d8bbwe"
    r"\cloudflared.exe"
)

def run_flask():
    subprocess.run([PYTHON, os.path.join(HERE, "line_webhook_server.py")])

print("=" * 50)
print("  LINE Webhook 啟動中...")
print("=" * 50)

# 背景啟動 Flask
t = threading.Thread(target=run_flask, daemon=True)
t.start()
time.sleep(3)
print("[1/2] Flask server 已啟動 (port 5000)")
print()
print("[2/2] 啟動 Cloudflare Tunnel...")
print()
print("=" * 50)
print("  複製下方 https:// 網址")
print("  加上 /webhook 填入 LINE Developers")
print("=" * 50)
print()

# 前景執行 cloudflared（會顯示 URL）
subprocess.run([CLOUDFLARED, "tunnel", "--url", "http://localhost:5000"])
