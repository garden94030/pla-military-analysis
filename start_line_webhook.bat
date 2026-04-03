@echo off
chcp 65001 >nul
title LINE Webhook - 中共軍事動態分析

echo ============================================
echo  LINE Webhook 伺服器啟動中...
echo ============================================

set WORKSPACE=C:\Users\garde\OneDrive\3.教務\1.中共軍事體制研究\每日資料蒐集更新
set PYTHON=C:\Users\garde\AppData\Local\Programs\Python\Python313\python.exe
set CLOUDFLARED=C:\Users\garde\AppData\Local\Microsoft\WinGet\Packages\Cloudflare.cloudflared_Microsoft.Winget.Source_8wekyb3d8bbwe\cloudflared.exe

cd /d "%WORKSPACE%"

:: ── 啟動 Flask Server（背景）──────────────────────────
echo [1/2] 啟動 Flask Webhook Server (port 5000)...
start "LINE-Flask" /MIN "%PYTHON%" line_webhook_server.py

:: 等待 Flask 啟動
timeout /t 3 /nobreak >nul

:: ── 啟動 Cloudflare Tunnel ────────────────────────────
echo [2/2] 啟動 Cloudflare Tunnel...
echo.
echo ★ 請複製下方 trycloudflare.com 的 https:// 網址
echo ★ 加上 /webhook 後填入 LINE Developers Console
echo ★ 範例: https://xxxx-xxxx.trycloudflare.com/webhook
echo.
"%CLOUDFLARED%" tunnel --url http://localhost:5000

:: 若 cloudflared 關閉，也關閉 Flask
taskkill /F /FI "WINDOWTITLE eq LINE-Flask*" >nul 2>&1
echo.
echo [已停止] LINE Webhook 伺服器已關閉
pause
