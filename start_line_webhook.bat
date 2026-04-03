@echo off
chcp 65001 >nul 2>&1
title LINE Webhook Server

:: 使用 %~dp0 取得批次檔自身所在目錄（自動處理中文路徑）
set "HERE=%~dp0"
set "PYTHON=C:\Users\garde\AppData\Local\Programs\Python\Python313\python.exe"
set "CLOUDFLARED=C:\Users\garde\AppData\Local\Microsoft\WinGet\Packages\Cloudflare.cloudflared_Microsoft.Winget.Source_8wekyb3d8bbwe\cloudflared.exe"

echo ============================================
echo  LINE Webhook Server Starting...
echo ============================================
echo.

:: 切換到腳本目錄
cd /d "%HERE%"

:: 確認 Python 存在
if not exist "%PYTHON%" (
    echo ERROR: Python not found at %PYTHON%
    pause
    exit /b 1
)

:: 確認 cloudflared 存在
if not exist "%CLOUDFLARED%" (
    echo ERROR: cloudflared not found
    pause
    exit /b 1
)

:: 啟動 Flask Server
echo [1/2] Starting Flask server on port 5000...
start "FlaskServer" "%PYTHON%" "%HERE%line_webhook_server.py"

:: 等待 Flask 啟動（用 ping 延遲 3 秒）
ping -n 4 127.0.0.1 >nul 2>&1

echo [1/2] Flask server started.
echo.
echo [2/2] Starting Cloudflare Tunnel...
echo.
echo ================================================
echo  Copy the https://xxxx.trycloudflare.com URL
echo  Add /webhook at the end
echo  Paste into LINE Developers Console
echo ================================================
echo.

:: 啟動 Cloudflare Tunnel（前景執行，顯示 URL）
"%CLOUDFLARED%" tunnel --url http://localhost:5000

:: 關閉時結束 Flask
echo.
echo Stopping Flask server...
for /f "tokens=5" %%p in ('netstat -ano 2^>nul ^| findstr ":5000 " ^| findstr "LISTENING"') do (
    taskkill /F /PID %%p >nul 2>&1
)
echo Done.
pause
