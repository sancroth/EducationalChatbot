#!/usr/bin/env python3
"""
Database management script
"""
import sys
import os
import subprocess
from sqlalchemy.exc import OperationalError

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import db_config

def run_migrations():
    """Run Alembic migrations"""
    print("Running database migrations...")
    try:
        result = subprocess.run(['alembic', 'upgrade', 'head'], 
                              cwd=os.path.dirname(os.path.abspath(__file__)),
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Migrations completed successfully!")
            print(result.stdout)
        else:
            print("❌ Migration failed!")
            print(result.stderr)
            return False
    except FileNotFoundError:
        print("❌ Alembic not found. Please install: pip install alembic")
        return False
    return True

def create_migration(message):
    """Create a new migration"""
    print(f"Creating migration: {message}")
    try:
        result = subprocess.run(['alembic', 'revision', '--autogenerate', '-m', message], 
                              cwd=os.path.dirname(os.path.abspath(__file__)),
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Migration created successfully!")
            print(result.stdout)
        else:
            print("❌ Migration creation failed!")
            print(result.stderr)
            return False
    except FileNotFoundError:
        print("❌ Alembic not found. Please install: pip install alembic")
        return False
    return True

def init_database():
    """Initialize database with tables and seed data"""
    print("Initializing database...")
    
    # Test database connection
    try:
        session = db_config.get_session()
        session.execute("SELECT 1")
        session.close()
        print("✅ Database connection successful!")
    except OperationalError as e:
        print(f"❌ Database connection failed: {e}")
        return False
    
    # Run migrations
    if not run_migrations():
        return False
    
    # Seed data
    print("Seeding database with initial data...")
    try:
        result = subprocess.run([sys.executable, 'seed_database.py'], 
                              cwd=os.path.dirname(os.path.abspath(__file__)),
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Database seeding completed!")
            print(result.stdout)
        else:
            print("❌ Database seeding failed!")
            print(result.stderr)
            return False
    except Exception as e:
        print(f"❌ Error running seeding script: {e}")
        return False
    
    return True

def reset_database():
    """Reset database - drop all tables and recreate"""
    print("⚠️  WARNING: This will delete ALL data in the database!")
    confirm = input("Are you sure you want to continue? (yes/no): ")
    
    if confirm.lower() != 'yes':
        print("Operation cancelled.")
        return
    
    print("Dropping all tables...")
    try:
        db_config.drop_all_tables()
        print("✅ All tables dropped!")
    except Exception as e:
        print(f"❌ Error dropping tables: {e}")
        return False
    
    # Reinitialize
    return init_database()

def show_help():
    """Show available commands"""
    print("""
Database Management Commands:

  init        Initialize database with migrations and seed data
  migrate     Run pending migrations
  new-migration <message>  Create a new migration
  reset       Reset database (⚠️  DESTRUCTIVE!)
  help        Show this help message

Examples:
  python manage.py init
  python manage.py migrate
  python manage.py new-migration "Add user preferences table"
  python manage.py reset
    """)

def main():
    """Main management function"""
    if len(sys.argv) < 2:
        show_help()
        return
    
    command = sys.argv[1].lower()
    
    if command == 'init':
        init_database()
    elif command == 'migrate':
        run_migrations()
    elif command == 'new-migration':
        if len(sys.argv) < 3:
            print("❌ Please provide a migration message")
            print("Example: python manage.py new-migration 'Add user preferences table'")
            return
        create_migration(sys.argv[2])
    elif command == 'reset':
        reset_database()
    elif command == 'help':
        show_help()
    else:
        print(f"❌ Unknown command: {command}")
        show_help()

if __name__ == "__main__":
    main()