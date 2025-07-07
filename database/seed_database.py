#!/usr/bin/env python3
"""
Database seeding script - populates the database with initial data
"""
import sys
import os
from sqlalchemy.exc import IntegrityError

# Add the current directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import db_config
from seeds import (
    seed_departments, 
    seed_roles, 
    seed_users, 
    seed_classes, 
    seed_schedules
)

def main():
    """Main seeding function"""
    print("Starting database seeding...")
    
    session = db_config.get_session()
    
    try:
        # Seed in order of dependencies
        print("1. Seeding departments...")
        seed_departments(session)
        
        print("2. Seeding roles...")
        seed_roles(session)
        
        print("3. Seeding users...")
        seed_users(session)
        
        print("4. Seeding classes...")
        seed_classes(session)
        
        print("5. Seeding schedules and enrollments...")
        seed_schedules(session)
        
        print("✅ Database seeding completed successfully!")
        
    except IntegrityError as e:
        print(f"❌ Database integrity error: {e}")
        session.rollback()
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error during seeding: {e}")
        session.rollback()
        sys.exit(1)
    finally:
        session.close()

if __name__ == "__main__":
    main()