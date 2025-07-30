from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base, TimestampMixin

class Department(Base, TimestampMixin):
    """Department model - represents university departments"""
    __tablename__ = 'departments'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, comment="Department name in Greek")
    key = Column(String(50), nullable=False, unique=True, comment="Department abbreviation key")
    
    # Relationships
    users = relationship("User", back_populates="department")
    classes = relationship("Class", back_populates="department")
    secretariat = relationship("DepartmentSecretariat", back_populates="department", uselist=False)
    enrollments = relationship("StudentEnrollment", back_populates="department")
    
    def __repr__(self):
        return f"<Department(id={self.id}, name='{self.name}', key='{self.key}')>"

class DepartmentSecretariat(Base, TimestampMixin):
    """Department secretariat contact information"""
    __tablename__ = 'department_secretariats'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    department_id = Column(Integer, ForeignKey('departments.id', ondelete='CASCADE'), nullable=False)
    email = Column(String(100), nullable=False)
    contact_phone = Column(String(50), nullable=False)
    address = Column(Text, nullable=True)
    working_hours = Column(String(100), nullable=True)
    website_url = Column(String(255), nullable=True)
    
    # Relationships
    department = relationship("Department", back_populates="secretariat")
    
    def __repr__(self):
        return f"<DepartmentSecretariat(id={self.id}, department_id={self.department_id}, email='{self.email}')>"