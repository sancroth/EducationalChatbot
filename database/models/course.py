from sqlalchemy import Column, Integer, String, Time, ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import relationship
from .base import Base, TimestampMixin

class Class(Base, TimestampMixin):
    """Course/Class model - represents university courses"""
    __tablename__ = 'classes'
    
    class_id = Column(Integer, primary_key=True, autoincrement=True)
    class_name = Column(String(100), nullable=False)
    class_type = Column(String(100), nullable=False, comment="ΘΕΩΡΙΑ, ΕΡΓΑΣΤΗΡΙΟ, etc.")
    department_id = Column(Integer, ForeignKey('departments.id', ondelete='SET NULL'), nullable=False)
    program = Column(String(50), nullable=False, default='ΠΡΟΠΤΥΧΙΑΚΟ')
    semester = Column(Integer, nullable=False, comment="Which semester this course belongs to")
    credits = Column(Integer, default=3, comment="Credit hours for this course")
    description = Column(String(500), nullable=True)
    prerequisites = Column(String(200), nullable=True, comment="Comma-separated prerequisite course IDs")
    
    # Relationships
    department = relationship("Department", back_populates="classes")
    schedules = relationship("ClassSchedule", back_populates="course")
    enrollments = relationship("StudentEnrollment", back_populates="course")
    
    def __repr__(self):
        return f"<Class(id={self.class_id}, name='{self.class_name}', semester={self.semester})>"

class ClassSchedule(Base, TimestampMixin):
    """Class schedule - when and where classes are held"""
    __tablename__ = 'class_schedules'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    semester = Column(Integer, nullable=False, comment="Academic semester")
    class_team = Column(Integer, nullable=False, default=1, comment="Team/group number (for split classes)")
    teacher_id = Column(Integer, ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    class_id = Column(Integer, ForeignKey('classes.class_id', ondelete='CASCADE'), nullable=False)
    classroom = Column(String(50), nullable=False)
    day_of_week = Column(Integer, nullable=False, comment="1=Monday, 7=Sunday")
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    
    # Relationships
    teacher = relationship("User", back_populates="taught_classes")
    course = relationship("Class", back_populates="schedules")
    
    # Indexes for fast querying
    __table_args__ = (
        Index('idx_class_schedule_time', 'day_of_week', 'start_time', 'end_time'),
        Index('idx_class_schedule_teacher', 'teacher_id', 'day_of_week'),
        Index('idx_class_schedule_course', 'class_id', 'semester'),
    )
    
    def __repr__(self):
        return f"<ClassSchedule(id={self.id}, class_id={self.class_id}, day={self.day_of_week}, time={self.start_time}-{self.end_time})>"

class StudentEnrollment(Base, TimestampMixin):
    """Student course enrollments"""
    __tablename__ = 'student_enrollments'
    
    enrollment_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    class_id = Column(Integer, ForeignKey('classes.class_id', ondelete='CASCADE'), nullable=False)
    department_id = Column(Integer, ForeignKey('departments.id', ondelete='SET NULL'), nullable=False)
    enrollment_status = Column(String(20), default='ACTIVE', comment="ACTIVE, COMPLETED, DROPPED, FAILED")
    grade = Column(String(10), nullable=True, comment="Final grade")
    
    # Relationships
    student = relationship("User", back_populates="enrollments")
    course = relationship("Class", back_populates="enrollments")
    department = relationship("Department", back_populates="enrollments")
    
    # Unique constraint to prevent duplicate enrollments
    __table_args__ = (
        UniqueConstraint('user_id', 'class_id', name='uq_student_class_enrollment'),
        Index('idx_enrollment_student', 'user_id'),
        Index('idx_enrollment_course', 'class_id'),
    )
    
    def __repr__(self):
        return f"<StudentEnrollment(id={self.enrollment_id}, user_id={self.user_id}, class_id={self.class_id}, status='{self.enrollment_status}')>"