import csv
import os
import bcrypt
from datetime import datetime
from sqlalchemy.orm import Session
from models.user import User, UserCredential, StudentInfo
from models.department import Department

def seed_users(session: Session):
    """Seed users from CSV files"""
    
    # Check if users already exist
    if session.query(User).count() > 0:
        print("Users already exist, skipping seed")
        return
    
    # Get the sample_data directory path
    sample_data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'sample_data')
    
    # Seed teachers first
    teachers_file = os.path.join(sample_data_dir, 'teachers.csv')
    teachers_count = 0
    
    if os.path.exists(teachers_file):
        with open(teachers_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                teacher = User(
                    user_id=int(row['user_id']),
                    first_name=row['first_name'] if row['first_name'] else None,
                    last_name=row['last_name'],
                    email=row['email'],
                    date_of_birth=datetime.strptime(row['date_of_birth'], '%d/%m/%Y').date() if row['date_of_birth'] else None,
                    enrollment_date=datetime.strptime(row['enrollment_date'], '%d/%m/%Y').date(),
                    department_id=int(row['department_id']),
                    gender=row['gender'],
                    role_id=int(row['role_id'])
                )
                session.add(teacher)
                
                # Add password
                hashed_password = bcrypt.hashpw('StronkP@ssw0rd'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                credential = UserCredential(
                    user_id=teacher.user_id,
                    password_hash=hashed_password
                )
                session.add(credential)
                teachers_count += 1
    
    # Seed students
    students_file = os.path.join(sample_data_dir, 'students.csv')
    students_count = 0
    
    if os.path.exists(students_file):
        with open(students_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                student = User(
                    user_id=int(row['user_id']),
                    first_name=row['first_name'] if row['first_name'] else None,
                    last_name=row['last_name'],
                    email=row['email'],
                    date_of_birth=datetime.strptime(row['date_of_birth'], '%d/%m/%Y').date() if row['date_of_birth'] else None,
                    enrollment_date=datetime.strptime(row['enrollment_date'], '%d/%m/%Y').date(),
                    department_id=int(row['department_id']),
                    gender=row['gender'],
                    role_id=int(row['role_id'])
                )
                session.add(student)
                
                # Add password
                hashed_password = bcrypt.hashpw('StronkP@ssw0rd'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                credential = UserCredential(
                    user_id=student.user_id,
                    password_hash=hashed_password
                )
                session.add(credential)
                
                # Add student info
                dept = session.query(Department).filter(Department.id == int(row['department_id'])).first()
                student_info = StudentInfo(
                    user_id=student.user_id,
                    am=f"{dept.key}{student.user_id}",
                    semester=int(row['semester']),
                    special_needs=None
                )
                session.add(student_info)
                students_count += 1
    
    session.commit()
    print(f"Seeded {teachers_count} teachers and {students_count} students")