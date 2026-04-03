# setup_line_service.ps1
# =====================
# 將 LINE Webhook 服務設定為 Windows 開機自動啟動
# 用法：以系統管理員身分執行此腳本（或直接執行，腳本會自動提權）
#
# 建立的工作排程任務：
#   - 名稱: LINE Webhook Service
#   - 觸發: 開機後啟動（無需登入）
#   - 執行: pythonw.exe line_webhook_service.py（無視窗）
#   - 失敗自動重試: 1分鐘後，最多3次

$TaskName    = "LINE Webhook Service"
$ProjectDir  = "C:\Users\garde\OneDrive\3.教務\1.中共軍事體制研究\每日資料蒐集更新"
$PythonW     = "C:\Users\garde\AppData\Local\Programs\Python\Python313\pythonw.exe"
$ServiceScript = "$ProjectDir\line_webhook_service.py"

Write-Host ""
Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host "  LINE Webhook 服務安裝程式" -ForegroundColor Cyan
Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host ""

# ── 檢查 pythonw.exe 是否存在 ─────────────────────────────
if (-not (Test-Path $PythonW)) {
    Write-Host "❌ 找不到 pythonw.exe: $PythonW" -ForegroundColor Red
    Write-Host "   請確認 Python 313 已安裝"
    Read-Host "按 Enter 結束"
    exit 1
}

# ── 移除舊工作（如有）────────────────────────────────────
$existing = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($existing) {
    Write-Host "🔄 移除舊的工作任務..." -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
}

# ── 建立工作任務 ──────────────────────────────────────────
$action = New-ScheduledTaskAction `
    -Execute $PythonW `
    -Argument $ServiceScript `
    -WorkingDirectory $ProjectDir

# 開機後 30 秒啟動（等待網路就緒）
$trigger = New-ScheduledTaskTrigger -AtStartup
$trigger.Delay = "PT30S"   # ISO 8601: 30秒後

$settings = New-ScheduledTaskSettingsSet `
    -MultipleInstances IgnoreNew `
    -RestartCount 99 `
    -RestartInterval (New-TimeSpan -Minutes 1) `
    -ExecutionTimeLimit ([TimeSpan]::Zero) `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable

# 以目前使用者身分執行（確保能存取 OneDrive）
$principal = New-ScheduledTaskPrincipal `
    -UserId $env:USERNAME `
    -LogonType Interactive `
    -RunLevel Highest

$task = Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Principal $principal `
    -Description "LINE Webhook 伺服器 — 24/7 中共軍事情資蒐集系統" `
    -Force

if ($task) {
    Write-Host ""
    Write-Host "✅ 工作任務建立成功！" -ForegroundColor Green
    Write-Host ""
    Write-Host "  任務名稱  : $TaskName"
    Write-Host "  執行腳本  : $ServiceScript"
    Write-Host "  啟動時機  : 開機後 30 秒（自動）"
    Write-Host "  失敗重試  : 每 1 分鐘，無限次"
    Write-Host ""
    Write-Host "----------------------------------------------------"
    Write-Host "  立即啟動服務？" -ForegroundColor Yellow
    Write-Host "----------------------------------------------------"
    $choice = Read-Host "  立即啟動 [Y/n]"
    if ($choice -ne "n") {
        Write-Host ""
        Write-Host "🚀 正在啟動..." -ForegroundColor Cyan
        Start-ScheduledTask -TaskName $TaskName
        Start-Sleep -Seconds 5
        $status = (Get-ScheduledTask -TaskName $TaskName).State
        Write-Host "   狀態: $status" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "✅ 服務已在背景啟動！" -ForegroundColor Green
        Write-Host "   日誌位置: $ProjectDir\logs\line_service.log"
        Write-Host ""
        Write-Host "   約 30 秒後，LINE Webhook URL 將自動更新。"
        Write-Host "   可用記事本開啟日誌確認狀態："
        Write-Host "   $ProjectDir\logs\line_service.log" -ForegroundColor Yellow
    }
} else {
    Write-Host "❌ 工作任務建立失敗" -ForegroundColor Red
}

Write-Host ""
Write-Host "=====================================================" -ForegroundColor Cyan
Read-Host "按 Enter 結束"
