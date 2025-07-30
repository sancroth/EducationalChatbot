from sqlalchemy import Column, Integer, String, Date, Text, Boolean, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from .base import Base, TimestampMixin

class AcademicCalendar(Base, TimestampMixin):
    """Academic calendar events - exams, holidays, registration periods"""
    __tablename__ = 'academic_calendar'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    event_type = Column(String(50), nullable=False, comment="EXAM, HOLIDAY, REGISTRATION, DEADLINE")
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)
    department_id = Column(Integer, ForeignKey('departments.id', ondelete='CASCADE'), nullable=True)
    semester = Column(Integer, nullable=True, comment="Specific semester or null for all")
    is_active = Column(Boolean, default=True)
    
    # Relationships
    department = relationship("Department")
    
    def __repr__(self):
        return f"<AcademicCalendar(id={self.id}, type='{self.event_type}', title='{self.title}')>"

class Assignment(Base, TimestampMixin):
    """Course assignments and deadlines"""
    __tablename__ = 'assignments'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    class_id = Column(Integer, ForeignKey('classes.class_id', ondelete='CASCADE'), nullable=False)
    teacher_id = Column(Integer, ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    due_date = Column(DateTime, nullable=False)
    max_points = Column(Integer, default=100)
    submission_format = Column(String(100), nullable=True, comment="PDF, DOC, CODE, etc.")
    is_active = Column(Boolean, default=True)
    
    # Relationships
    course = relationship("Class")
    teacher = relationship("User")
    submissions = relationship("AssignmentSubmission", back_populates="assignment")
    
    def __repr__(self):
        return f"<Assignment(id={self.id}, title='{self.title}', due_date={self.due_date})>"

class AssignmentSubmission(Base, TimestampMixin):
    """Student assignment submissions"""
    __tablename__ = 'assignment_submissions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    assignment_id = Column(Integer, ForeignKey('assignments.id', ondelete='CASCADE'), nullable=False)
    student_id = Column(Integer, ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    submission_date = Column(DateTime, default=func.current_timestamp())
    file_path = Column(String(500), nullable=True, comment="Path to submitted file")
    comments = Column(Text, nullable=True)
    grade = Column(Integer, nullable=True)
    graded_by = Column(Integer, ForeignKey('users.user_id'), nullable=True)
    graded_date = Column(DateTime, nullable=True)
    
    # Relationships
    assignment = relationship("Assignment", back_populates="submissions")
    student = relationship("User", foreign_keys=[student_id])
    grader = relationship("User", foreign_keys=[graded_by])
    
    def __repr__(self):
        return f"<AssignmentSubmission(id={self.id}, assignment_id={self.assignment_id}, student_id={self.student_id})>"

class Grade(Base, TimestampMixin):
    """Student grades for courses"""
    __tablename__ = 'grades'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    class_id = Column(Integer, ForeignKey('classes.class_id', ondelete='CASCADE'), nullable=False)
    grade_type = Column(String(50), nullable=False, comment="MIDTERM, FINAL, PROJECT, ASSIGNMENT")
    grade_value = Column(String(10), nullable=False, comment="Numeric grade or letter grade")
    max_points = Column(Integer, default=100)
    weight = Column(Integer, default=100, comment="Percentage weight in final grade")
    graded_by = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    grade_date = Column(Date, nullable=False)
    comments = Column(Text, nullable=True)
    
    # Relationships
    student = relationship("User", foreign_keys=[student_id])
    course = relationship("Class")
    grader = relationship("User", foreign_keys=[graded_by])
    
    def __repr__(self):
        return f"<Grade(id={self.id}, student_id={self.student_id}, grade='{self.grade_value}')>"