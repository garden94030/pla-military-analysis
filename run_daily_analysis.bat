@echo off
REM 每日中共軍事動態分析 - 自動執行腳本
REM 由 Windows 工作排程器於每日 05:07 觸發

set PROJECT_DIR=C:\Users\garde\OneDrive\3.教務\1.中共軍事體制研究\每日資料蒐集更新
set CLAUDE_CMD=C:\Users\garde\AppData\Roaming\npm\claude.cmd

cd /d "%PROJECT_DIR%"

"%CLAUDE_CMD%" --dangerously-skip-permissions -p "/daily-china-military-analysis" --project "%PROJECT_DIR%"
