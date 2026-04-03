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

:: ── 啟動 Flask Server（背景，使用 /B 避免 Git Bash 路徑問題）
echo [1/2] 啟動 Flask Webhook Server (port 5000)...
start /B "" "%PYTHON%" line_webhook_server.py > line_webhook.log 2>&1

:: 等待 Flask 啟動
ping -n 4 127.0.0.1 >nul

echo [1/2] Flask 已啟動（port 5000）
echo.

:: ── 啟動 Cloudflare Tunnel ────────────────────────────
echo [2/2] 啟動 Cloudflare Tunnel...
echo.
echo ================================================
echo  ★ 請複製下方 https://xxxx.trycloudflare.com
echo  ★ 加上 /webhook 填入 LINE Developers Console
echo  ★ 範例: https://xxxx.trycloudflare.com/webhook
echo ================================================
echo.
"%CLOUDFLARED%" tunnel --url http://localhost:5000

:: 結束時關閉 Flask
echo.
echo [已停止] 正在關閉 Flask 伺服器...
for /f "tokens=5" %%p in ('netstat -ano ^| findstr :5000 ^| findstr LISTENING') do taskkill /F /PID %%p >nul 2>&1
echo [完成] LINE Webhook 伺服器已關閉
pause
