# 每日中共軍事動態分析 - Windows 工作排程器設定腳本
# 以系統管理員身份執行此腳本

$TaskName = "DailyChinaMilAnalysis"
$ProjectDir = "C:\Users\garde\OneDrive\3.教務\1.中共軍事體制研究\每日資料蒐集更新"
$BatchFile = "$ProjectDir\run_daily_analysis.bat"

# 刪除舊任務（若存在）
Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue

# 設定觸發器：每天 05:07
$Trigger = New-ScheduledTaskTrigger -Daily -At "05:07AM"

# 設定動作：執行 batch 腳本
$Action = New-ScheduledTaskAction `
    -Execute "cmd.exe" `
    -Argument "/c `"$BatchFile`"" `
    -WorkingDirectory $ProjectDir

# 設定選項
$Settings = New-ScheduledTaskSettingsSet `
    -ExecutionTimeLimit (New-TimeSpan -Hours 4) `
    -MultipleInstances IgnoreNew `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -WakeToRun

# 以當前使用者身份執行
$Principal = New-ScheduledTaskPrincipal `
    -UserId $env:USERNAME `
    -LogonType Interactive `
    -RunLevel Highest

# 建立任務
Register-ScheduledTask `
    -TaskName $TaskName `
    -Trigger $Trigger `
    -Action $Action `
    -Settings $Settings `
    -Principal $Principal `
    -Description "每日 05:07 自動執行中共軍事動態情資分析" `
    -Force

Write-Host "✅ 工作排程器任務建立完成：$TaskName" -ForegroundColor Green
Write-Host "   每天 05:07 自動執行（電腦需開機或休眠，不能關機）" -ForegroundColor Yellow

# 顯示任務狀態
Get-ScheduledTask -TaskName $TaskName | Get-ScheduledTaskInfo
