import csv
import os
from datetime import time, datetime
from sqlalchemy.orm import Session
from models.course import Class, ClassSchedule, StudentEnrollment
from models.user import User

def seed_schedules(session: Session):
    """Seed class schedules and student enrollments from CSV file"""
    
    # Check if schedules already exist
    if session.query(ClassSchedule).count() > 0:
        print("Schedules already exist, skipping seed")
        return
    
    # Get the sample_data directory path
    sample_data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'sample_data')
    schedule_file = os.path.join(sample_data_dir, 'schedule.csv')
    
    schedules_count = 0
    
    if os.path.exists(schedule_file):
        with open(schedule_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Find teacher by last name
                teacher = session.query(User).filter(
                    User.last_name == row['teacher'].strip(),
                    User.role_id == 2  # teacher role
                ).first()
                
                if not teacher:
                    print(f"Teacher '{row['teacher']}' not found, skipping schedule")
                    continue
                
                # Find class by name
                course = session.query(Class).filter(
                    Class.class_name == row['class_name']
                ).first()
                
                if not course:
                    print(f"Class '{row['class_name']}' not found, skipping schedule")
                    continue
                
                # Parse times using strptime for HH:MM format
                start_time = datetime.strptime(row['start_time'], '%H:%M').time()
                end_time = datetime.strptime(row['end_time'], '%H:%M').time()
                
                schedule = ClassSchedule(
                    semester=course.semester,
                    class_team=int(row['class_team']),
                    teacher_id=teacher.user_id,
                    class_id=course.class_id,
                    classroom=row['classroom'],
                    day_of_week=int(row['day']),
                    start_time=start_time,
                    end_time=end_time
                )
                session.add(schedule)
                schedules_count += 1
    
    session.commit()
    print(f"Seeded {schedules_count} class schedules")
    
    # Now seed student enrollments
    seed_student_enrollments(session)

def seed_student_enrollments(session: Session):
    """Seed student enrollments based on semester and department"""
    
    # Check if enrollments already exist
    if session.query(StudentEnrollment).count() > 0:
        print("Student enrollments already exist, skipping seed")
        return
    
    enrollments_count = 0
    
    # Get all students
    students = session.query(User).filter(User.role_id == 1).all()  # student role
    
    for student in students:
        if not student.student_info:
            continue
            
        # Get all classes for this student's semester and department
        classes = session.query(Class).filter(
            Class.semester == student.student_info.semester,
            Class.department_id == student.department_id
        ).all()
        
        for course in classes:
            enrollment = StudentEnrollment(
                user_id=student.user_id,
                class_id=course.class_id,
                department_id=student.department_id,
                enrollment_status='ACTIVE'
            )
            session.add(enrollment)
            enrollments_count += 1
    
    session.commit()
    print(f"Seeded {enrollments_count} student enrollments")