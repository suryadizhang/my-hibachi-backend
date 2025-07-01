# PowerShell Script to Set Up Automated Daily Database Backup
# Run this script as Administrator to create the scheduled task

# Task configuration
$TaskName = "MyHibachi-DailyBackup"
$TaskDescription = "My Hibachi database automated backup system - runs daily at 12:00 AM"
$BackendPath = "C:\Users\surya\my-hibachi-backend"
$BatchScript = "$BackendPath\run_daily_backup.bat"

Write-Host "Setting up My Hibachi Daily Database Backup Task..." -ForegroundColor Green

# Check if task already exists
$ExistingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue

if ($ExistingTask) {
    Write-Host "Task '$TaskName' already exists. Updating..." -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
}

# Create the scheduled task action
$Action = New-ScheduledTaskAction -Execute $BatchScript -WorkingDirectory $BackendPath

# Create the trigger (daily at 12:00 AM)
$Trigger = New-ScheduledTaskTrigger -Daily -At "12:00 AM"

# Create task settings
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -RunOnlyIfNetworkAvailable

# Create the principal (run as SYSTEM account for reliability)
$Principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest

# Register the scheduled task
try {
    Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings -Principal $Principal -Description $TaskDescription
    Write-Host "Scheduled task '$TaskName' created successfully!" -ForegroundColor Green
    Write-Host "Backup will run daily at 12:00 AM" -ForegroundColor Cyan
    Write-Host "Backups will be sent to: suraydizhang.chef@gmail.com" -ForegroundColor Cyan
    
    # Display task information
    Write-Host "`nTask Details:" -ForegroundColor Yellow
    Write-Host "Name: $TaskName"
    Write-Host "Description: $TaskDescription"
    Write-Host "Script: $BatchScript"
    Write-Host "Schedule: Daily at 12:00 AM"
    Write-Host "Status: " -NoNewline
    
    $Task = Get-ScheduledTask -TaskName $TaskName
    Write-Host $Task.State -ForegroundColor Green
    
    # Test the backup system
    Write-Host "`n🧪 Testing backup system..." -ForegroundColor Yellow
    Write-Host "Running test backup (this may take a moment)..."
    
    Set-Location $BackendPath
    python automated_backup_system.py
    
    Write-Host "Test completed! Check your email and the backups folder." -ForegroundColor Green
    
} catch {
    Write-Host "❌ Failed to create scheduled task: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Make sure you're running this script as Administrator." -ForegroundColor Yellow
}

Write-Host "`n📋 Management Commands:" -ForegroundColor Cyan
Write-Host "View task: Get-ScheduledTask -TaskName '$TaskName'"
Write-Host "Run now: Start-ScheduledTask -TaskName '$TaskName'"
Write-Host "Delete task: Unregister-ScheduledTask -TaskName '$TaskName'"
Write-Host "View logs: Get-Content '$BackendPath\backup_system.log'"

Write-Host "`nAutomated backup system setup complete!" -ForegroundColor Green
