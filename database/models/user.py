from sqlalchemy import Column, Integer, String, Date, ForeignKey, Text, JSON, Boolean, UniqueConstraint
from sqlalchemy.orm import relationship
from .base import Base, TimestampMixin

class User(Base, TimestampMixin):
    """User model - represents both students and teachers"""
    __tablename__ = 'users'
    
    user_id = Column(Integer, primary_key=True, autoincrement=True)
    first_name = Column(String(50), nullable=True)
    last_name = Column(String(50), nullable=False)
    email = Column(String(100), nullable=False, unique=True)
    date_of_birth = Column(Date, nullable=True)
    enrollment_date = Column(Date, nullable=False)
    department_id = Column(Integer, ForeignKey('departments.id', ondelete='SET NULL'), nullable=False)
    gender = Column(String(20), nullable=False)
    role_id = Column(Integer, ForeignKey('roles.role_id', ondelete='SET NULL'), nullable=False, default=1)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    department = relationship("Department", back_populates="users")
    role = relationship("Role", back_populates="users")
    credential = relationship("UserCredential", back_populates="user", uselist=False)
    student_info = relationship("StudentInfo", back_populates="user", uselist=False)
    enrollments = relationship("StudentEnrollment", back_populates="student")
    taught_classes = relationship("ClassSchedule", back_populates="teacher")
    
    def __repr__(self):
        return f"<User(id={self.user_id}, email='{self.email}', role_id={self.role_id})>"
    
    @property
    def full_name(self):
        if self.first_name:
            return f"{self.first_name} {self.last_name}"
        return self.last_name
    
    @property
    def is_student(self):
        return self.role_id == 1
    
    @property
    def is_teacher(self):
        return self.role_id == 2

class UserCredential(Base, TimestampMixin):
    """User authentication credentials"""
    __tablename__ = 'user_credentials'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False, unique=True)
    password_hash = Column(Text, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="credential")
    
    def __repr__(self):
        return f"<UserCredential(id={self.id}, user_id={self.user_id})>"

class StudentInfo(Base, TimestampMixin):
    """Additional information specific to students"""
    __tablename__ = 'student_info'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False, unique=True)
    am = Column(String(50), nullable=False, unique=True, comment="Student registration number")
    semester = Column(Integer, nullable=False)
    special_needs = Column(JSON, nullable=True, comment="JSON array of special needs")
    gpa = Column(String(10), nullable=True, comment="Current GPA")
    total_credits = Column(Integer, default=0, comment="Total credits earned")
    
    # Relationships
    user = relationship("User", back_populates="student_info")
    
    def __repr__(self):
        return f"<StudentInfo(id={self.id}, am='{self.am}', semester={self.semester})>"