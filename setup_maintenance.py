#!/usr/bin/env python3
"""
Quick Setup and Maintenance Script for My Hibachi System
One-command setup for development and maintenance operations
"""

import os
import sys
import subprocess
import sqlite3
from pathlib import Path


def print_banner():
    """Print system banner"""
    print("="*60)
    print("🍴 MY HIBACHI BOOKING SYSTEM")
    print("   Development & Maintenance Toolkit")
    print("="*60)


def check_requirements():
    """Check if all requirements are met"""
    print("🔍 Checking system requirements...")
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ is required")
        return False
    
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}")
    
    # Check if we're in the right directory
    if not os.path.exists('main.py'):
        print("❌ Please run this script from the backend directory")
        return False
    
    print("✅ Backend directory confirmed")
    
    # Check required files
    required_files = ['requirements.txt', 'app/routes.py', 'app/database.py']
    for file in required_files:
        if not os.path.exists(file):
            print(f"❌ Missing required file: {file}")
            return False
    
    print("✅ All required files present")
    return True


def setup_database():
    """Setup database with required tables"""
    print("🗄️ Setting up database...")
    
    try:
        conn = sqlite3.connect('mh-bookings.db')
        cursor = conn.cursor()
        
        # Create bookings table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bookings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                phone TEXT NOT NULL,
                address TEXT,
                city TEXT,
                zipcode TEXT,
                date TEXT NOT NULL,
                time_slot TEXT NOT NULL,
                contact_preference TEXT DEFAULT 'email',
                status TEXT DEFAULT 'pending',
                deposit_confirmed BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create waitlist table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS waitlist (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                phone TEXT NOT NULL,
                preferred_date TEXT,
                message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create admins table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS admins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                full_name TEXT,
                email TEXT,
                role TEXT DEFAULT 'admin',
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP
            )
        """)
        
        # Create newsletter recipients table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS newsletter_recipients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                city TEXT,
                state TEXT,
                zipcode TEXT,
                subscribed BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
        
        print("✅ Database setup complete")
        return True
        
    except Exception as e:
        print(f"❌ Database setup failed: {e}")
        return False


def install_dependencies():
    """Install Python dependencies"""
    print("📦 Installing dependencies...")
    
    try:
        result = subprocess.run(
            [sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'],
            capture_output=True,
            text=True,
            timeout=300
        )
        
        if result.returncode == 0:
            print("✅ Dependencies installed successfully")
            return True
        else:
            print(f"❌ Dependency installation failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Dependency installation failed: {e}")
        return False


def create_test_admin():
    """Create a test admin account"""
    print("👤 Creating test admin account...")
    
    try:
        from passlib.context import CryptContext
        
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        password_hash = pwd_context.hash("admin123")
        
        conn = sqlite3.connect('mh-bookings.db')
        cursor = conn.cursor()
        
        # Check if admin already exists
        cursor.execute("SELECT id FROM admins WHERE username = ?", ("testadmin",))
        if cursor.fetchone():
            print("✅ Test admin account already exists (username: testadmin)")
            conn.close()
            return True
        
        # Create test admin
        cursor.execute("""
            INSERT INTO admins (username, password_hash, full_name, role, is_active)
            VALUES (?, ?, ?, ?, ?)
        """, ("testadmin", password_hash, "Test Administrator", "admin", 1))
        
        conn.commit()
        conn.close()
        
        print("✅ Test admin created (username: testadmin, password: admin123)")
        return True
        
    except Exception as e:
        print(f"❌ Admin creation failed: {e}")
        return False


def run_health_check():
    """Run system health check"""
    print("🏥 Running health check...")
    
    try:
        if os.path.exists('system_health_monitor.py'):
            result = subprocess.run(
                [sys.executable, 'system_health_monitor.py'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                print("✅ Health check passed")
            else:
                print("⚠️ Health check found issues (check output above)")
                
            # Show brief output
            lines = result.stdout.split('\n')
            for line in lines:
                if 'Overall Status:' in line or 'CHECK RESULTS:' in line:
                    print(f"   {line.strip()}")
            
            return True
        else:
            print("⚠️ Health monitor not found, skipping health check")
            return True
            
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False


def start_development_server():
    """Start the development server"""
    print("🚀 Starting development server...")
    print("   Server will be available at: http://localhost:8000")
    print("   API documentation: http://localhost:8000/docs")
    print("   Press Ctrl+C to stop the server")
    print("-"*60)
    
    try:
        subprocess.run([sys.executable, 'main.py'])
    except KeyboardInterrupt:
        print("\n👋 Server stopped")
    except Exception as e:
        print(f"❌ Server failed to start: {e}")


def show_menu():
    """Show interactive menu"""
    while True:
        print("\n🛠️ MAINTENANCE MENU:")
        print("1. 🔧 Full Setup (dependencies + database + admin)")
        print("2. 📦 Install Dependencies Only")
        print("3. 🗄️ Setup Database Only")
        print("4. 👤 Create Test Admin Only")
        print("5. 🏥 Run Health Check")
        print("6. 🚀 Start Development Server")
        print("7. 📊 Show System Status")
        print("8. 🧹 Run Maintenance Tasks")
        print("9. ❓ Show Help")
        print("0. 🚪 Exit")
        
        choice = input("\nSelect option (0-9): ").strip()
        
        if choice == "1":
            full_setup()
        elif choice == "2":
            install_dependencies()
        elif choice == "3":
            setup_database()
        elif choice == "4":
            create_test_admin()
        elif choice == "5":
            run_health_check()
        elif choice == "6":
            start_development_server()
        elif choice == "7":
            show_system_status()
        elif choice == "8":
            run_maintenance_tasks()
        elif choice == "9":
            show_help()
        elif choice == "0":
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid option. Please try again.")


def full_setup():
    """Run full system setup"""
    print("\n🔧 Running full system setup...")
    
    success = True
    success &= install_dependencies()
    success &= setup_database()
    success &= create_test_admin()
    success &= run_health_check()
    
    if success:
        print("\n🎉 Setup completed successfully!")
        print("   You can now start the development server (option 6)")
    else:
        print("\n⚠️ Setup completed with some issues. Check the messages above.")


def show_system_status():
    """Show current system status"""
    print("\n📊 SYSTEM STATUS:")
    
    # Check database
    if os.path.exists('mh-bookings.db'):
        try:
            conn = sqlite3.connect('mh-bookings.db')
            cursor = conn.cursor()
            
            # Get table info
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            print(f"✅ Database: {len(tables)} tables")
            
            # Get record counts
            for table in ['bookings', 'waitlist', 'admins']:
                if table in tables:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    print(f"   • {table}: {count} records")
            
            conn.close()
        except Exception as e:
            print(f"❌ Database error: {e}")
    else:
        print("❌ Database: Not found")
    
    # Check dependencies
    try:
        import fastapi
        import uvicorn
        import passlib
        print("✅ Dependencies: Core packages available")
    except ImportError as e:
        print(f"❌ Dependencies: Missing packages - {e}")
    
    # Check files
    important_files = [
        'main.py', 'app/routes.py', 'app/database.py',
        'system_health_monitor.py', 'requirements.txt'
    ]
    
    missing_files = [f for f in important_files if not os.path.exists(f)]
    if missing_files:
        print(f"⚠️ Missing files: {', '.join(missing_files)}")
    else:
        print("✅ Files: All important files present")


def run_maintenance_tasks():
    """Run maintenance tasks"""
    print("\n🧹 Running maintenance tasks...")
    
    # Create backup
    if os.path.exists('mh-bookings.db'):
        try:
            import shutil
            from datetime import datetime
            
            backup_dir = Path('backups')
            backup_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_file = backup_dir / f'mh-bookings-backup-{timestamp}.db'
            
            shutil.copy2('mh-bookings.db', backup_file)
            print(f"✅ Backup created: {backup_file}")
        except Exception as e:
            print(f"❌ Backup failed: {e}")
    
    # Run health check
    run_health_check()
    
    print("✅ Maintenance tasks completed")


def show_help():
    """Show help information"""
    print("\n❓ HELP INFORMATION:")
    print("""
🔧 QUICK START:
   1. Run option 1 (Full Setup) for first-time setup
   2. Use option 6 to start the development server
   3. Access the admin panel at http://localhost:8000/admin-login
   
👤 TEST CREDENTIALS:
   Username: testadmin
   Password: admin123
   
📚 DOCUMENTATION:
   • FUTURE_DEVELOPMENT_GUIDE.md - Development guide
   • DEVELOPMENT_WORKFLOW.md - Coding standards
   • system_health_monitor.py --help - Health monitoring
   
🛠️ COMMON TASKS:
   • Option 5: Check system health
   • Option 8: Run backup and maintenance
   • Option 7: View current system status
   
🆘 TROUBLESHOOTING:
   • Database issues: Try option 3 (Setup Database)
   • Dependency issues: Try option 2 (Install Dependencies)
   • Access issues: Try option 4 (Create Test Admin)
""")


def main():
    """Main function"""
    print_banner()
    
    if not check_requirements():
        print("\n❌ Requirements check failed. Please fix the issues above.")
        sys.exit(1)
    
    # Check if this is first run
    if not os.path.exists('mh-bookings.db'):
        print("\n🎯 First time setup detected!")
        print("   Recommend running Full Setup (option 1)")
    
    # Show menu
    show_menu()


if __name__ == '__main__':
    main()
