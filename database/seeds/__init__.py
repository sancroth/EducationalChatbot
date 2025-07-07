from .departments import seed_departments
from .roles import seed_roles  
from .users import seed_users
from .classes import seed_classes
from .schedules import seed_schedules

__all__ = [
    'seed_departments',
    'seed_roles',
    'seed_users', 
    'seed_classes',
    'seed_schedules'
]