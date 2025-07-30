import csv
import os
from sqlalchemy.orm import Session
from models.course import Class

def seed_classes(session: Session):
    """Seed classes from CSV file"""
    
    # Check if classes already exist
    if session.query(Class).count() > 0:
        print("Classes already exist, skipping seed")
        return
    
    # Get the sample_data directory path
    sample_data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'sample_data')
    classes_file = os.path.join(sample_data_dir, 'classes.csv')
    
    classes_count = 0
    
    if os.path.exists(classes_file):
        with open(classes_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                course = Class(
                    department_id=int(row['department_id']),
                    semester=int(row['semester']),
                    class_name=row['class_name'],
                    class_type=row['class_type'],
                    program=row['program']
                )
                session.add(course)
                classes_count += 1
    
    session.commit()
    print(f"Seeded {classes_count} classes")