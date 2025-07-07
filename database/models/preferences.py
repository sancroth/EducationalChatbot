from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from .base import Base, TimestampMixin

class UserPreference(Base, TimestampMixin):
    """User preferences for chatbot behavior"""
    __tablename__ = 'user_preferences'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False, unique=True)
    
    # Communication preferences
    preferred_language = Column(String(10), default='el', comment="Language code (el, en, etc.)")
    communication_style = Column(String(20), default='FRIENDLY', comment="FORMAL, FRIENDLY, CASUAL")
    detail_level = Column(String(20), default='MEDIUM', comment="LOW, MEDIUM, HIGH")
    
    # Notification preferences
    enable_reminders = Column(Boolean, default=True)
    reminder_advance_minutes = Column(Integer, default=15, comment="Minutes before class to remind")
    enable_deadline_alerts = Column(Boolean, default=True)
    enable_grade_notifications = Column(Boolean, default=True)
    
    # UI preferences
    theme = Column(String(20), default='LIGHT', comment="LIGHT, DARK, AUTO")
    timezone = Column(String(50), default='Europe/Athens')
    
    # Advanced preferences (stored as JSON)
    advanced_settings = Column(JSON, nullable=True, comment="Custom settings as JSON")
    
    # Relationships
    user = relationship("User")
    
    def __repr__(self):
        return f"<UserPreference(id={self.id}, user_id={self.user_id}, style='{self.communication_style}')>"

class ConversationHistory(Base, TimestampMixin):
    """Track conversation history for context and analytics"""
    __tablename__ = 'conversation_history'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    session_id = Column(String(100), nullable=False, comment="Unique session identifier")
    
    # Message details
    message_type = Column(String(20), nullable=False, comment="USER, BOT")
    intent = Column(String(100), nullable=True, comment="Detected intent for user messages")
    message_text = Column(Text, nullable=False)
    
    # Context information
    entities_extracted = Column(JSON, nullable=True, comment="Extracted entities as JSON")
    confidence_score = Column(String(10), nullable=True, comment="Intent confidence")
    response_time_ms = Column(Integer, nullable=True, comment="Bot response time in milliseconds")
    
    # Success tracking
    user_satisfied = Column(Boolean, nullable=True, comment="User satisfaction if available")
    follow_up_needed = Column(Boolean, default=False)
    
    # Relationships
    user = relationship("User")
    
    def __repr__(self):
        return f"<ConversationHistory(id={self.id}, user_id={self.user_id}, type='{self.message_type}')>"

class UserFeedback(Base, TimestampMixin):
    """User feedback on bot interactions"""
    __tablename__ = 'user_feedback'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    conversation_id = Column(Integer, ForeignKey('conversation_history.id', ondelete='SET NULL'), nullable=True)
    
    # Feedback details
    rating = Column(Integer, nullable=False, comment="1-5 star rating")
    feedback_type = Column(String(50), nullable=False, comment="HELPFUL, NOT_HELPFUL, INCORRECT, SUGGESTION")
    feedback_text = Column(Text, nullable=True)
    
    # Context
    intent_involved = Column(String(100), nullable=True)
    issue_category = Column(String(50), nullable=True, comment="UI, ACCURACY, SPEED, OTHER")
    
    # Status
    status = Column(String(20), default='OPEN', comment="OPEN, REVIEWED, RESOLVED")
    admin_response = Column(Text, nullable=True)
    
    # Relationships
    user = relationship("User")
    conversation = relationship("ConversationHistory")
    
    def __repr__(self):
        return f"<UserFeedback(id={self.id}, user_id={self.user_id}, rating={self.rating})>"