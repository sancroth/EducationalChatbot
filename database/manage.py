#!/usr/bin/env python3
"""
Database management script
"""
import sys
import os
import subprocess
from sqlalchemy.exc import OperationalError
from sqlalchemy import create_engine, text

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import db_config

def create_database_if_not_exists():
    """Create the database if it doesn't exist"""
    print("Checking if database exists...")
    
    # Parse database connection info
    db_host = os.getenv("DB_HOST", "localhost")
    db_user = os.getenv("DB_USER", "postgres")
    db_password = os.getenv("DB_PASSWORD", "mysecretpassword")
    db_port = os.getenv("DB_PORT", "5432")
    db_name = os.getenv("DB_NAME", "ice")
    
    # Connect to PostgreSQL without specifying database (connects to default 'postgres' db)
    admin_url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/postgres"
    
    try:
        admin_engine = create_engine(admin_url, isolation_level='AUTOCOMMIT')
        
        with admin_engine.connect() as conn:
            # Check if database exists
            result = conn.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :db_name"), {"db_name": db_name}
            ).fetchone()
            
            if result:
                print(f"✅ Database '{db_name}' already exists!")
            else:
                print(f"Creating database '{db_name}'...")
                conn.execute(text(f'CREATE DATABASE "{db_name}"'))
                print(f"✅ Database '{db_name}' created successfully!")
        
        admin_engine.dispose()
        return True
        
    except Exception as e:
        print(f"❌ Failed to create database: {e}")
        return False

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
    
    # Create database if it doesn't exist
    if not create_database_if_not_exists():
        return False
    
    # Test database connection
    try:
        session = db_config.get_session()
        session.execute(text("SELECT 1"))
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
        # Create database if it doesn't exist before running migrations
        if create_database_if_not_exists():
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