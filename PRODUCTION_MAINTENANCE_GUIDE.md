# Production Readiness & Maintenance Guide

## 🔧 Backend Maintenance & Scalability

### 1. **Database Management**

#### Current State Assessment
```bash
# Check current database sizes
ls -la *.db
ls -la backend/weekly_databases/*.db
```

#### Database Maintenance Tasks
- **Weekly Database Cleanup**: Archive old weekly databases
- **Backup Strategy**: Implement automated backups
- **Database Migration**: Prepare for PostgreSQL migration when scaling

#### Recommended Script: `database_maintenance.py`
```python
#!/usr/bin/env python3
"""
Database maintenance and backup script
Run weekly via cron job
"""
import os
import sqlite3
import shutil
from datetime import datetime, timedelta
import zipfile

def backup_databases():
    """Create timestamped backups of all databases"""
    backup_dir = "backups"
    os.makedirs(backup_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Backup main database
    shutil.copy2("mh-bookings.db", f"{backup_dir}/mh-bookings_{timestamp}.db")
    
    # Backup weekly databases
    weekly_backup_dir = f"{backup_dir}/weekly_{timestamp}"
    if os.path.exists("backend/weekly_databases"):
        shutil.copytree("backend/weekly_databases", weekly_backup_dir)
    
    print(f"✅ Backup completed: {timestamp}")

def cleanup_old_weekly_dbs():
    """Archive weekly databases older than 6 months"""
    cutoff_date = datetime.now() - timedelta(days=180)
    weekly_dir = "backend/weekly_databases"
    archive_dir = "archived_weekly_dbs"
    
    if not os.path.exists(weekly_dir):
        return
    
    os.makedirs(archive_dir, exist_ok=True)
    
    for filename in os.listdir(weekly_dir):
        if filename.endswith('.db'):
            file_path = os.path.join(weekly_dir, filename)
            file_date = datetime.fromtimestamp(os.path.getctime(file_path))
            
            if file_date < cutoff_date:
                shutil.move(file_path, os.path.join(archive_dir, filename))
                print(f"📦 Archived: {filename}")

if __name__ == "__main__":
    backup_databases()
    cleanup_old_weekly_dbs()
```

### 2. **Environment Configuration**

#### Create `.env` files for different environments:
