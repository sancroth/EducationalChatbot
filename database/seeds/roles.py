from sqlalchemy.orm import Session
from models.role import Role

def seed_roles(session: Session):
    """Seed user roles"""
    
    # Check if roles already exist
    if session.query(Role).count() > 0:
        print("Roles already exist, skipping seed")
        return
    
    roles_data = [
        {'role_name': 'student'},
        {'role_name': 'teacher'},
        {'role_name': 'admin'},
        {'role_name': 'secretary'}
    ]
    
    for role_data in roles_data:
        role = Role(**role_data)
        session.add(role)
    
    session.commit()
    print(f"Seeded {len(roles_data)} roles")