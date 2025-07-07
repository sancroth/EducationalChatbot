from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, DateTime, func, UniqueConstraint
from sqlalchemy.orm import relationship
from .base import Base, TimestampMixin

class StudyGroup(Base, TimestampMixin):
    """Study groups for courses"""
    __tablename__ = 'study_groups'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    class_id = Column(Integer, ForeignKey('classes.class_id', ondelete='CASCADE'), nullable=False)
    creator_id = Column(Integer, ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    max_members = Column(Integer, default=10)
    is_active = Column(Boolean, default=True)
    meeting_location = Column(String(100), nullable=True)
    meeting_schedule = Column(Text, nullable=True, comment="JSON or text description of meeting times")
    
    # Relationships
    course = relationship("Class")
    creator = relationship("User", foreign_keys=[creator_id])
    members = relationship("StudyGroupMember", back_populates="group")
    sessions = relationship("StudySession", back_populates="group")
    
    def __repr__(self):
        return f"<StudyGroup(id={self.id}, name='{self.name}', class_id={self.class_id})>"

class StudyGroupMember(Base, TimestampMixin):
    """Study group membership"""
    __tablename__ = 'study_group_members'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    group_id = Column(Integer, ForeignKey('study_groups.id', ondelete='CASCADE'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    role = Column(String(20), default='MEMBER', comment="ADMIN, MODERATOR, MEMBER")
    joined_date = Column(DateTime, default=func.current_timestamp())
    is_active = Column(Boolean, default=True)
    
    # Relationships
    group = relationship("StudyGroup", back_populates="members")
    user = relationship("User")
    
    # Unique constraint to prevent duplicate memberships
    __table_args__ = (
        UniqueConstraint('group_id', 'user_id', name='uq_group_member'),
    )
    
    def __repr__(self):
        return f"<StudyGroupMember(id={self.id}, group_id={self.group_id}, user_id={self.user_id})>"

class StudySession(Base, TimestampMixin):
    """Study sessions organized by groups"""
    __tablename__ = 'study_sessions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    group_id = Column(Integer, ForeignKey('study_groups.id', ondelete='CASCADE'), nullable=False)
    organizer_id = Column(Integer, ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    location = Column(String(100), nullable=False)
    session_date = Column(DateTime, nullable=False)
    duration_minutes = Column(Integer, default=120)
    max_attendees = Column(Integer, nullable=True)
    is_public = Column(Boolean, default=False, comment="Visible to non-group members")
    status = Column(String(20), default='SCHEDULED', comment="SCHEDULED, ONGOING, COMPLETED, CANCELLED")
    
    # Relationships
    group = relationship("StudyGroup", back_populates="sessions")
    organizer = relationship("User")
    attendees = relationship("StudySessionAttendee", back_populates="session")
    
    def __repr__(self):
        return f"<StudySession(id={self.id}, title='{self.title}', date={self.session_date})>"

class StudySessionAttendee(Base, TimestampMixin):
    """Study session attendance tracking"""
    __tablename__ = 'study_session_attendees'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey('study_sessions.id', ondelete='CASCADE'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    rsvp_status = Column(String(20), default='PENDING', comment="PENDING, ATTENDING, NOT_ATTENDING, MAYBE")
    rsvp_date = Column(DateTime, default=func.current_timestamp())
    attended = Column(Boolean, nullable=True, comment="Actual attendance, null if session not completed")
    
    # Relationships
    session = relationship("StudySession", back_populates="attendees")
    user = relationship("User")
    
    # Unique constraint to prevent duplicate RSVPs
    __table_args__ = (
        UniqueConstraint('session_id', 'user_id', name='uq_session_attendee'),
    )
    
    def __repr__(self):
        return f"<StudySessionAttendee(id={self.id}, session_id={self.session_id}, user_id={self.user_id})>"