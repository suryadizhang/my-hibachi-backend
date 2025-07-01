# Automated Database Backup System

## 🎯 Overview

The automated backup system creates daily backups of the My Hibachi booking database and emails them to `suraydizhang.chef@gmail.com` every night at 12:00 AM.

---

## 🔧 System Components

### 1. **automated_backup_system.py**
- **Purpose**: Main backup script that creates, compresses, and emails database backups
- **Features**:
  - Creates timestamped database backups
  - Compresses backups using ZIP compression
  - Generates database statistics report
  - Emails backup with detailed report
  - Cleans up old backup files (keeps 30 days)
  - Comprehensive error handling and logging

### 2. **run_daily_backup.bat**
- **Purpose**: Windows batch script wrapper for the backup system
- **Features**:
  - Changes to correct directory
  - Runs the Python backup script
  - Logs execution times
  - Creates Windows event log entries

### 3. **setup_backup_scheduler.ps1**
- **Purpose**: PowerShell script to configure Windows Task Scheduler
- **Features**:
  - Creates scheduled task for daily execution
  - Configures task to run at 12:00 AM daily
  - Sets up proper permissions and settings
  - Includes test run functionality

---

## 📧 Email Configuration

### **Email Details**
- **From**: cs@myhibachichef.com
- **To**: suraydizhang.chef@gmail.com
- **SMTP Server**: smtp.ionos.com (Port 587)
- **Security**: TLS encryption
- **Schedule**: Daily at 12:00 AM

### **Email Content**
Each backup email includes:
- **Subject**: "My Hibachi Database Backup - YYYY-MM-DD"
- **Database Statistics**: Table counts, recent activity, pending deposits
- **Backup Information**: File size, compression details
- **Attached File**: Compressed database backup (.zip)

---

## 🚀 Setup Instructions

### **Step 1: Install Dependencies**
```bash
# The backup system uses built-in Python modules, no additional packages needed
# Ensure Python 3.6+ is installed and accessible via 'python' command
```

### **Step 2: Configure Environment Variables**
```bash
# Set email credentials (if different from defaults)
set SMTP_USER=cs@myhibachichef.com
set SMTP_PASS=myhibachicustomers!
```

### **Step 3: Run Setup Script (As Administrator)**
```powershell
# Open PowerShell as Administrator
cd "C:\Users\surya\my-hibachi-backend"
powershell -ExecutionPolicy Bypass -File setup_backup_scheduler.ps1
```

### **Step 4: Verify Setup**
```powershell
# Check if task was created
Get-ScheduledTask -TaskName "MyHibachi-DailyBackup"

# Test run the backup manually
Start-ScheduledTask -TaskName "MyHibachi-DailyBackup"
```

---

## 📊 Database Statistics Included

Each backup email includes comprehensive statistics:

### **Table Counts**
- Total Bookings
- Waitlist Entries  
- Admin Accounts
- Newsletter Recipients

### **Recent Activity (Last 7 days)**
- New Bookings
- Pending Deposits

### **System Information**
- Backup file size
- Compression ratio
- Backup timestamp
- Local storage location

---

## 🔍 Monitoring & Logs

### **Log Files**
- **backup_system.log**: Detailed backup process logs
- **backup_scheduler.log**: Task scheduler execution logs

### **Log Locations**
```
C:\Users\surya\my-hibachi-backend\backup_system.log
C:\Users\surya\my-hibachi-backend\backup_scheduler.log
```

### **Monitoring Commands**
```powershell
# View recent backup logs
Get-Content "backup_system.log" -Tail 20

# Check task status
Get-ScheduledTask -TaskName "MyHibachi-DailyBackup" | Select State, LastRunTime, NextRunTime

# View Windows Event Log entries
Get-WinEvent -FilterHashtable @{LogName='Application'; ProviderName='MyHibachi'} -MaxEvents 10
```

---

## 📁 Backup Storage

### **Local Storage**
- **Location**: `C:\Users\surya\my-hibachi-backend\backups\`
- **Format**: `mh-bookings-backup-YYYYMMDD_HHMMSS.zip`
- **Retention**: 30 days (automatic cleanup)

### **Email Delivery**
- **Recipient**: suraydizhang.chef@gmail.com
- **Attachment**: Compressed database backup
- **Report**: Detailed statistics and system information

---

## 🚨 Error Handling

### **Automatic Error Notifications**
If backup fails, an error email is automatically sent including:
- Failure timestamp
- Error description
- Troubleshooting steps
- Contact information

### **Common Issues & Solutions**

**Issue**: Email sending fails
```
Solution: 
1. Verify SMTP credentials
2. Check network connectivity
3. Ensure SMTP_USER and SMTP_PASS environment variables are set
```

**Issue**: Database file not found
```
Solution:
1. Verify mh-bookings.db exists in backend directory
2. Check file permissions
3. Ensure database is not locked by another process
```

**Issue**: Backup directory not writable
```
Solution:
1. Check directory permissions
2. Ensure sufficient disk space
3. Create backups directory if missing
```

---

## 🔧 Management Commands

### **Task Management**
```powershell
# Start backup immediately
Start-ScheduledTask -TaskName "MyHibachi-DailyBackup"

# Stop running backup
Stop-ScheduledTask -TaskName "MyHibachi-DailyBackup"

# Disable/Enable backup
Disable-ScheduledTask -TaskName "MyHibachi-DailyBackup"
Enable-ScheduledTask -TaskName "MyHibachi-DailyBackup"

# Remove backup task
Unregister-ScheduledTask -TaskName "MyHibachi-DailyBackup" -Confirm:$false
```

### **Manual Backup**
```bash
cd "C:\Users\surya\my-hibachi-backend"
python automated_backup_system.py
```

---

## 📞 Support & Maintenance

### **Regular Checks**
- **Weekly**: Verify backup emails are being received
- **Monthly**: Check local backup storage space
- **Quarterly**: Test backup restoration process

### **Contact Information**
- **Technical Support**: info@myhibachichef.com
- **System Administrator**: Your IT department
- **Backup Recipient**: suraydizhang.chef@gmail.com

---

## ✅ Features Summary

| Feature | Status | Description |
|---------|--------|-------------|
| **Daily Automation** | ✅ | Runs every night at 12:00 AM |
| **Email Delivery** | ✅ | Sends to suraydizhang.chef@gmail.com |
| **Compression** | ✅ | ZIP compression for smaller files |
| **Statistics** | ✅ | Detailed database statistics |
| **Error Handling** | ✅ | Automatic error notifications |
| **Log Management** | ✅ | Comprehensive logging system |
| **Cleanup** | ✅ | Automatic old backup removal |
| **Security** | ✅ | TLS encrypted email transmission |

---

**🎉 Your database is now protected with automated daily backups sent directly to your email!**

*Last Updated: June 30, 2025*
