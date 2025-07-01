@echo off
REM Windows Task Scheduler Batch Script for My Hibachi Database Backup
REM This script runs the automated backup system daily at 12:00 AM

REM Change to the backend directory
cd /d "C:\Users\surya\my-hibachi-backend"

REM Run the backup script
echo Starting My Hibachi Database Backup...
python automated_backup_system.py

REM Log the execution
echo Backup script completed at %DATE% %TIME% >> backup_scheduler.log

REM Optional: Add system event log entry
eventcreate /T INFORMATION /ID 1001 /L APPLICATION /SO "MyHibachi" /D "Daily database backup completed"

echo Backup process finished.
