#!/usr/bin/env python3
"""
System Health Monitor & Maintenance Script
Automated health checks and maintenance for My Hibachi booking system
"""

import os
import sys
import json
import sqlite3
import datetime
from pathlib import Path
from typing import Dict, Any, Optional


class SystemHealthMonitor:
    def __init__(self, config_path: Optional[str] = None):
        self.config = self.load_config(config_path)
        self.results = {
            'timestamp': datetime.datetime.now().isoformat(),
            'status': 'unknown',
            'checks': {},
            'warnings': [],
            'errors': [],
            'recommendations': []
        }
    
    def load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """Load configuration from file or use defaults"""
        default_config = {
            'database_path': './mh-bookings.db',
            'backup_dir': './backups',
            'log_dir': './logs',
            'max_backup_age_days': 30,
            'max_log_age_days': 7,
            'check_api_health': True,
            'check_database_integrity': True,
            'check_disk_space': True,
            'min_disk_space_mb': 1000,
            'api_url': 'http://localhost:8000',
            'api_timeout': 10
        }
        
        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    user_config = json.load(f)
                    default_config.update(user_config)
            except Exception as e:
                print(f"Warning: Could not load config file "
                      f"{config_path}: {e}")
        
        return default_config
    
    def check_database_health(self) -> Dict[str, Any]:
        """Check database connectivity and basic integrity"""
        check_result = {
            'status': 'unknown',
            'details': {},
            'issues': []
        }
        
        try:
            db_path = self.config['database_path']
            
            if not os.path.exists(db_path):
                check_result['status'] = 'error'
                check_result['issues'].append(f"Database file not found: {db_path}")
                return check_result
            
            # Check file size
            db_size = os.path.getsize(db_path)
            check_result['details']['size_bytes'] = db_size
            check_result['details']['size_mb'] = round(db_size / (1024 * 1024), 2)
            
            # Test connection and basic queries
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Check table existence
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            check_result['details']['tables'] = tables
            
            expected_tables = ['bookings', 'waitlist', 'admins']
            missing_tables = [t for t in expected_tables if t not in tables]
            if missing_tables:
                check_result['issues'].append(f"Missing tables: {missing_tables}")
            
            # Check record counts
            for table in ['bookings', 'waitlist', 'admins']:
                if table in tables:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    check_result['details'][f'{table}_count'] = count
            
            # Check for recent activity
            cursor.execute("""
                SELECT COUNT(*) FROM bookings 
                WHERE date >= date('now', '-7 days')
            """)
            recent_bookings = cursor.fetchone()[0]
            check_result['details']['recent_bookings_7days'] = recent_bookings
            
            # Database integrity check
            cursor.execute("PRAGMA integrity_check")
            integrity_result = cursor.fetchone()[0]
            check_result['details']['integrity'] = integrity_result
            
            if integrity_result != 'ok':
                check_result['issues'].append(f"Database integrity issue: {integrity_result}")
            
            conn.close()
            
            if not check_result['issues']:
                check_result['status'] = 'healthy'
            else:
                check_result['status'] = 'warning'
                
        except Exception as e:
            check_result['status'] = 'error'
            check_result['issues'].append(f"Database check failed: {str(e)}")
        
        return check_result
    
    def check_api_health(self) -> Dict[str, Any]:
        """Check API server health"""
        check_result = {
            'status': 'unknown',
            'details': {},
            'issues': []
        }
        
        if not self.config.get('check_api_health', True):
            check_result['status'] = 'skipped'
            return check_result
        
        try:
            import requests
            
            api_url = self.config['api_url']
            timeout = self.config['api_timeout']
            
            # Test root endpoint
            response = requests.get(f"{api_url}/", timeout=timeout)
            check_result['details']['root_status'] = response.status_code
            check_result['details']['response_time_ms'] = round(response.elapsed.total_seconds() * 1000, 2)
            
            if response.status_code != 200:
                check_result['issues'].append(f"API root endpoint returned status {response.status_code}")
            
            # Test health endpoint if available
            try:
                health_response = requests.get(f"{api_url}/health", timeout=timeout)
                check_result['details']['health_status'] = health_response.status_code
            except:
                pass  # Health endpoint might not exist
            
            if not check_result['issues']:
                check_result['status'] = 'healthy'
            else:
                check_result['status'] = 'warning'
                
        except ImportError:
            check_result['status'] = 'skipped'
            check_result['issues'].append("requests library not available")
        except Exception as e:
            check_result['status'] = 'error'
            check_result['issues'].append(f"API health check failed: {str(e)}")
        
        return check_result
    
    def check_disk_space(self) -> Dict[str, Any]:
        """Check available disk space"""
        check_result = {
            'status': 'unknown',
            'details': {},
            'issues': []
        }
        
        try:
            import shutil
            
            # Check current directory disk space
            total, used, free = shutil.disk_usage('.')
            
            free_mb = free / (1024 * 1024)
            total_mb = total / (1024 * 1024)
            used_mb = used / (1024 * 1024)
            
            check_result['details'] = {
                'total_mb': round(total_mb, 2),
                'used_mb': round(used_mb, 2),
                'free_mb': round(free_mb, 2),
                'used_percent': round((used / total) * 100, 2)
            }
            
            min_space = self.config.get('min_disk_space_mb', 1000)
            
            if free_mb < min_space:
                check_result['status'] = 'warning'
                check_result['issues'].append(f"Low disk space: {free_mb:.2f}MB free (minimum: {min_space}MB)")
            else:
                check_result['status'] = 'healthy'
                
        except Exception as e:
            check_result['status'] = 'error'
            check_result['issues'].append(f"Disk space check failed: {str(e)}")
        
        return check_result
    
    def check_log_files(self) -> Dict[str, Any]:
        """Check log files for errors and warnings"""
        check_result = {
            'status': 'unknown',
            'details': {},
            'issues': []
        }
        
        try:
            log_dir = Path(self.config.get('log_dir', './logs'))
            
            if not log_dir.exists():
                check_result['status'] = 'warning'
                check_result['issues'].append(f"Log directory not found: {log_dir}")
                return check_result
            
            log_files = list(log_dir.glob('*.log'))
            check_result['details']['log_files'] = len(log_files)
            
            recent_errors = 0
            recent_warnings = 0
            
            # Check recent log entries
            for log_file in log_files:
                try:
                    with open(log_file, 'r') as f:
                        lines = f.readlines()
                        for line in lines[-100:]:  # Check last 100 lines
                            if 'ERROR' in line.upper():
                                recent_errors += 1
                            elif 'WARNING' in line.upper():
                                recent_warnings += 1
                except:
                    continue
            
            check_result['details']['recent_errors'] = recent_errors
            check_result['details']['recent_warnings'] = recent_warnings
            
            if recent_errors > 0:
                check_result['status'] = 'warning'
                check_result['issues'].append(f"Found {recent_errors} recent errors in logs")
            elif recent_warnings > 5:
                check_result['status'] = 'warning'
                check_result['issues'].append(f"Found {recent_warnings} recent warnings in logs")
            else:
                check_result['status'] = 'healthy'
                
        except Exception as e:
            check_result['status'] = 'error'
            check_result['issues'].append(f"Log file check failed: {str(e)}")
        
        return check_result
    
    def check_dependencies(self) -> Dict[str, Any]:
        """Check if all required dependencies are available"""
        check_result = {
            'status': 'unknown',
            'details': {},
            'issues': []
        }
        
        try:
            # Check Python version
            python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
            check_result['details']['python_version'] = python_version
            
            if sys.version_info < (3, 8):
                check_result['issues'].append(f"Python version {python_version} is too old (minimum: 3.8)")
            
            # Check critical packages
            critical_packages = ['fastapi', 'uvicorn', 'sqlite3', 'passlib', 'jose']
            available_packages = []
            missing_packages = []
            
            for package in critical_packages:
                try:
                    if package == 'sqlite3':
                        import sqlite3
                    elif package == 'fastapi':
                        import fastapi
                    elif package == 'uvicorn':
                        import uvicorn
                    elif package == 'passlib':
                        import passlib
                    elif package == 'jose':
                        import jose
                    
                    available_packages.append(package)
                except ImportError:
                    missing_packages.append(package)
            
            check_result['details']['available_packages'] = available_packages
            check_result['details']['missing_packages'] = missing_packages
            
            if missing_packages:
                check_result['status'] = 'error'
                check_result['issues'].append(f"Missing required packages: {missing_packages}")
            else:
                check_result['status'] = 'healthy'
                
        except Exception as e:
            check_result['status'] = 'error'
            check_result['issues'].append(f"Dependency check failed: {str(e)}")
        
        return check_result
    
    def cleanup_old_files(self) -> Dict[str, Any]:
        """Clean up old backup and log files"""
        cleanup_result = {
            'status': 'unknown',
            'details': {},
            'actions': []
        }
        
        try:
            actions_taken = []
            
            # Clean old backups
            backup_dir = Path(self.config.get('backup_dir', './backups'))
            if backup_dir.exists():
                max_age = self.config.get('max_backup_age_days', 30)
                cutoff_date = datetime.datetime.now() - datetime.timedelta(days=max_age)
                
                backup_files = list(backup_dir.glob('*.db'))
                old_backups = []
                
                for backup_file in backup_files:
                    file_time = datetime.datetime.fromtimestamp(backup_file.stat().st_mtime)
                    if file_time < cutoff_date:
                        old_backups.append(backup_file)
                
                for old_backup in old_backups:
                    try:
                        old_backup.unlink()
                        actions_taken.append(f"Deleted old backup: {old_backup.name}")
                    except Exception as e:
                        actions_taken.append(f"Failed to delete {old_backup.name}: {e}")
            
            # Clean old logs
            log_dir = Path(self.config.get('log_dir', './logs'))
            if log_dir.exists():
                max_age = self.config.get('max_log_age_days', 7)
                cutoff_date = datetime.datetime.now() - datetime.timedelta(days=max_age)
                
                log_files = list(log_dir.glob('*.log'))
                old_logs = []
                
                for log_file in log_files:
                    file_time = datetime.datetime.fromtimestamp(log_file.stat().st_mtime)
                    if file_time < cutoff_date:
                        old_logs.append(log_file)
                
                for old_log in old_logs:
                    try:
                        old_log.unlink()
                        actions_taken.append(f"Deleted old log: {old_log.name}")
                    except Exception as e:
                        actions_taken.append(f"Failed to delete {old_log.name}: {e}")
            
            cleanup_result['actions'] = actions_taken
            cleanup_result['status'] = 'completed'
            
        except Exception as e:
            cleanup_result['status'] = 'error'
            cleanup_result['actions'] = [f"Cleanup failed: {str(e)}"]
        
        return cleanup_result
    
    def create_backup(self) -> Dict[str, Any]:
        """Create database backup"""
        backup_result = {
            'status': 'unknown',
            'details': {},
            'issues': []
        }
        
        try:
            db_path = Path(self.config['database_path'])
            if not db_path.exists():
                backup_result['status'] = 'error'
                backup_result['issues'].append(f"Database file not found: {db_path}")
                return backup_result
            
            backup_dir = Path(self.config.get('backup_dir', './backups'))
            backup_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_name = f"mh-bookings-backup-{timestamp}.db"
            backup_path = backup_dir / backup_name
            
            # Copy database file
            import shutil
            shutil.copy2(db_path, backup_path)
            
            backup_size = backup_path.stat().st_size
            backup_result['details'] = {
                'backup_file': str(backup_path),
                'backup_size_bytes': backup_size,
                'backup_size_mb': round(backup_size / (1024 * 1024), 2),
                'timestamp': timestamp
            }
            
            backup_result['status'] = 'success'
            
        except Exception as e:
            backup_result['status'] = 'error'
            backup_result['issues'].append(f"Backup failed: {str(e)}")
        
        return backup_result
    
    def run_all_checks(self) -> Dict[str, Any]:
        """Run all health checks"""
        print("🔍 Running system health checks...")
        
        # Database health
        print("  📊 Checking database health...")
        self.results['checks']['database'] = self.check_database_health()
        
        # API health
        print("  🌐 Checking API health...")
        self.results['checks']['api'] = self.check_api_health()
        
        # Disk space
        print("  💾 Checking disk space...")
        self.results['checks']['disk_space'] = self.check_disk_space()
        
        # Log files
        print("  📝 Checking log files...")
        self.results['checks']['logs'] = self.check_log_files()
        
        # Dependencies
        print("  📦 Checking dependencies...")
        self.results['checks']['dependencies'] = self.check_dependencies()
        
        # Cleanup old files
        print("  🧹 Cleaning up old files...")
        self.results['cleanup'] = self.cleanup_old_files()
        
        # Create backup
        print("  💾 Creating backup...")
        self.results['backup'] = self.create_backup()
        
        # Determine overall status
        error_checks = [k for k, v in self.results['checks'].items() if v['status'] == 'error']
        warning_checks = [k for k, v in self.results['checks'].items() if v['status'] == 'warning']
        
        if error_checks:
            self.results['status'] = 'error'
            self.results['errors'].extend([f"{check}: {v['issues']}" for check, v in self.results['checks'].items() if v['status'] == 'error'])
        elif warning_checks:
            self.results['status'] = 'warning'
            self.results['warnings'].extend([f"{check}: {v['issues']}" for check, v in self.results['checks'].items() if v['status'] == 'warning'])
        else:
            self.results['status'] = 'healthy'
        
        # Generate recommendations
        self.generate_recommendations()
        
        return self.results
    
    def generate_recommendations(self):
        """Generate recommendations based on check results"""
        recommendations = []
        
        # Database recommendations
        db_check = self.results['checks'].get('database', {})
        if db_check.get('status') == 'warning':
            recommendations.append("Consider running database maintenance and integrity checks")
        
        # Disk space recommendations
        disk_check = self.results['checks'].get('disk_space', {})
        if disk_check.get('status') == 'warning':
            recommendations.append("Free up disk space or increase storage capacity")
        
        # API recommendations
        api_check = self.results['checks'].get('api', {})
        if api_check.get('status') == 'error':
            recommendations.append("Check API server status and restart if necessary")
        
        # Log recommendations
        log_check = self.results['checks'].get('logs', {})
        if log_check.get('details', {}).get('recent_errors', 0) > 0:
            recommendations.append("Review recent error logs and address issues")
        
        # General recommendations
        recommendations.extend([
            "Schedule regular backups (daily recommended)",
            "Monitor system logs regularly",
            "Keep dependencies updated",
            "Run this health check weekly"
        ])
        
        self.results['recommendations'] = recommendations
    
    def save_report(self, report_path: Optional[str] = None):
        """Save health check report to file"""
        if not report_path:
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            report_path = f"health_report_{timestamp}.json"
        
        try:
            with open(report_path, 'w') as f:
                json.dump(self.results, f, indent=2)
            print(f"📄 Health report saved to: {report_path}")
        except Exception as e:
            print(f"❌ Failed to save report: {e}")
    
    def print_report(self):
        """Print health check report to console"""
        print("\n" + "="*60)
        print("🏥 SYSTEM HEALTH REPORT")
        print("="*60)
        
        status_emoji = {
            'healthy': '✅',
            'warning': '⚠️',
            'error': '❌',
            'unknown': '❓',
            'skipped': '⏭️'
        }
        
        print(f"📅 Timestamp: {self.results['timestamp']}")
        print(f"🎯 Overall Status: {status_emoji.get(self.results['status'], '❓')} {self.results['status'].upper()}")
        print()
        
        # Check results
        print("🔍 CHECK RESULTS:")
        for check_name, check_result in self.results['checks'].items():
            status = check_result['status']
            emoji = status_emoji.get(status, '❓')
            print(f"  {emoji} {check_name.title()}: {status}")
            
            if check_result.get('issues'):
                for issue in check_result['issues']:
                    print(f"    • {issue}")
        
        print()
        
        # Errors
        if self.results['errors']:
            print("❌ ERRORS:")
            for error in self.results['errors']:
                print(f"  • {error}")
            print()
        
        # Warnings
        if self.results['warnings']:
            print("⚠️  WARNINGS:")
            for warning in self.results['warnings']:
                print(f"  • {warning}")
            print()
        
        # Backup info
        backup_info = self.results.get('backup', {})
        if backup_info.get('status') == 'success':
            print("💾 BACKUP CREATED:")
            details = backup_info.get('details', {})
            print(f"  • File: {details.get('backup_file', 'N/A')}")
            print(f"  • Size: {details.get('backup_size_mb', 'N/A')} MB")
            print()
        
        # Recommendations
        if self.results['recommendations']:
            print("💡 RECOMMENDATIONS:")
            for rec in self.results['recommendations']:
                print(f"  • {rec}")
            print()
        
        print("="*60)


def main():
    """Main function to run health checks"""
    import argparse
    
    parser = argparse.ArgumentParser(description='My Hibachi System Health Monitor')
    parser.add_argument('--config', '-c', help='Configuration file path')
    parser.add_argument('--save-report', '-s', help='Save report to file')
    parser.add_argument('--quiet', '-q', action='store_true', help='Suppress output')
    
    args = parser.parse_args()
    
    monitor = SystemHealthMonitor(args.config)
    results = monitor.run_all_checks()
    
    if not args.quiet:
        monitor.print_report()
    
    if args.save_report:
        monitor.save_report(args.save_report)
    
    # Exit with appropriate code
    if results['status'] == 'error':
        sys.exit(1)
    elif results['status'] == 'warning':
        sys.exit(2)
    else:
        sys.exit(0)


if __name__ == '__main__':
    main()
