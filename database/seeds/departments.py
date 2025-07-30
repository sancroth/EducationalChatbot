from sqlalchemy.orm import Session
from models.department import Department, DepartmentSecretariat

def seed_departments(session: Session):
    """Seed departments and their secretariat information"""
    
    # Check if departments already exist
    if session.query(Department).count() > 0:
        print("Departments already exist, skipping seed")
        return
    
    # Create departments
    departments_data = [
        {
            'name': 'ΣΧΟΛΗ ΜΗΑΝΙΚΩΝ ΥΠΟΛΙΣΤΩΝ', 
            'key': 'ice',
            'secretariat': {
                'email': 'ice@uniwa.gr',
                'contact_phone': '210538-5382/5308/5309/5384',
                'address': '',
                'working_hours': 'Δευτ-Τετ-Παρ, 9:00-13:00',
                'website_url': 'http://www.ice.uniwa.gr'
            }
        },
        {
            'name': 'ΒΙΒΛΙΟΘΗΚΟΝΟΜΙΑ',
            'key': 'lib',
            'secretariat': {
                'email': 'alis@uniwa.gr', 
                'contact_phone': '2105385203',
                'address': '',
                'working_hours': 'Δευτ-Τετ-Παρ, 10:00-14:00',
                'website_url': 'http://alis.uniwa.gr'
            }
        }
    ]
    
    for dept_data in departments_data:
        # Create department
        dept = Department(
            name=dept_data['name'],
            key=dept_data['key']
        )
        session.add(dept)
        session.flush()  # Get the ID
        
        # Create secretariat
        secretariat = DepartmentSecretariat(
            department_id=dept.id,
            **dept_data['secretariat']
        )
        session.add(secretariat)
    
    session.commit()
    print(f"Seeded {len(departments_data)} departments with secretariat info")