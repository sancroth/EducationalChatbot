from .base import Base
from .department import Department, DepartmentSecretariat
from .user import User, UserCredential, StudentInfo
from .role import Role
from .course import Class, ClassSchedule, StudentEnrollment
from .academic import AcademicCalendar, Assignment, AssignmentSubmission, Grade
from .social import StudyGroup, StudyGroupMember, StudySession, StudySessionAttendee
from .preferences import UserPreference, ConversationHistory, UserFeedback

__all__ = [
    'Base',
    'Department',
    'DepartmentSecretariat', 
    'User',
    'UserCredential',
    'StudentInfo',
    'Role',
    'Class',
    'ClassSchedule',
    'StudentEnrollment',
    'AcademicCalendar',
    'Assignment',
    'AssignmentSubmission',
    'Grade',
    'StudyGroup',
    'StudyGroupMember',
    'StudySession',
    'StudySessionAttendee',
    'UserPreference',
    'ConversationHistory',
    'UserFeedback'
]