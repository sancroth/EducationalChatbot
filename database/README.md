# Database Schema & Migrations

This directory contains the SQLAlchemy models and Alembic migrations for the university chatbot system.

## 🏗️ Architecture

### Core Tables
- **departments**: University departments (ICE, Library Science, etc.)
- **department_secretariats**: Contact information for each department
- **roles**: User roles (student, teacher, admin, secretary)
- **users**: All system users (students and teachers)
- **user_credentials**: Authentication data
- **student_info**: Additional student-specific information
- **classes**: University courses/subjects
- **class_schedules**: When and where classes are held
- **student_enrollments**: Which students are enrolled in which classes

### Future-Ready Tables
- **academic_calendar**: Exam dates, holidays, registration periods
- **assignments**: Course assignments and deadlines
- **assignment_submissions**: Student submissions with grading
- **grades**: Student grades and progress tracking
- **study_groups**: Student study groups for collaboration
- **study_sessions**: Organized study sessions
- **user_preferences**: Personalized chatbot settings
- **conversation_history**: Chat history for analytics and context
- **user_feedback**: User feedback for bot improvement

## 🚀 Quick Start

### Prerequisites
```bash
pip install -r requirements.txt
```

### Initialize Database
```bash
# Initialize database with tables and seed data
python manage.py init
```

### Available Commands
```bash
# Run migrations
python manage.py migrate

# Create new migration
python manage.py new-migration "Add user preferences table"

# Reset database (⚠️ DESTRUCTIVE!)
python manage.py reset

# Show help
python manage.py help
```

## 📊 Database Models

### Core Models

#### User
```python
user = User(
    first_name="Νίκος",
    last_name="Παπαδόπουλος", 
    email="nikos@uniwa.gr",
    department_id=1,
    role_id=1  # student
)
```

#### Class
```python
course = Class(
    class_name="ΜΑΘΗΜΑΤΙΚΗ ΑΝΑΛΥΣΗ I",
    class_type="ΘΕΩΡΙΑ",
    department_id=1,
    semester=1,
    credits=6
)
```

#### ClassSchedule
```python
schedule = ClassSchedule(
    class_id=1,
    teacher_id=2,
    classroom="ΑΜΦΙΘΕΑΤΡΟ",
    day_of_week=1,  # Monday
    start_time=time(9, 0),
    end_time=time(11, 0)
)
```

### Future Models

#### StudyGroup
```python
group = StudyGroup(
    name="Μαθηματικά Α' Εξαμήνου",
    class_id=1,
    creator_id=48,
    max_members=8
)
```

#### UserPreference
```python
prefs = UserPreference(
    user_id=48,
    communication_style="FRIENDLY",
    detail_level="HIGH",
    enable_reminders=True
)
```

## 🔄 Migration Workflow

### Creating Migrations
1. Modify models in `models/` directory
2. Generate migration: `python manage.py new-migration "Description"`
3. Review generated migration in `migrations/versions/`
4. Run migration: `python manage.py migrate`

### Database Schema Changes
- Always create migrations for schema changes
- Never modify existing migrations that have been deployed
- Use descriptive migration messages
- Test migrations on development data first

## 🌱 Seeding Data

The seeding system populates the database with initial data from CSV files:

- `seeds/departments.py` - University departments
- `seeds/roles.py` - User roles
- `seeds/users.py` - Students and teachers from CSV
- `seeds/classes.py` - Courses from CSV
- `seeds/schedules.py` - Class schedules and enrollments

### Custom Seeding
```python
from config import db_config
from models import User

session = db_config.get_session()
user = User(name="Test User", email="test@uniwa.gr")
session.add(user)
session.commit()
session.close()
```

## 🔍 Querying Examples

### Get Student's Next Class
```python
from datetime import datetime
from models import User, ClassSchedule, Class

student = session.query(User).filter(User.email == "student@uniwa.gr").first()
now = datetime.now()

next_class = session.query(ClassSchedule, Class).join(Class).filter(
    ClassSchedule.day_of_week == now.weekday() + 1,
    ClassSchedule.start_time > now.time()
).first()
```

### Get Teacher's Classes
```python
teacher_classes = session.query(ClassSchedule, Class).join(Class).filter(
    ClassSchedule.teacher_id == teacher_id
).all()
```

### Get Student Enrollments
```python
enrollments = session.query(StudentEnrollment, Class).join(Class).filter(
    StudentEnrollment.user_id == student_id
).all()
```

## 🛠️ Environment Variables

Configure database connection:
```bash
# Database connection
DB_HOST=localhost
DB_USER=postgres  
DB_PASSWORD=mysecretpassword
DB_PORT=5432
DB_NAME=ice

# Development
DB_ECHO=false  # Set to 'true' for SQL query logging
```

## 📈 Performance Considerations

### Indexes
The schema includes optimized indexes for common queries:
- `idx_class_schedule_time` - For time-based queries
- `idx_class_schedule_teacher` - For teacher schedules
- `idx_enrollment_student` - For student enrollments

### Query Optimization
- Use eager loading for relationships: `session.query(User).options(joinedload(User.department))`
- Batch queries when possible
- Use database-level constraints for data integrity

## 🔐 Security Notes

- Passwords are hashed with bcrypt
- Foreign key constraints maintain referential integrity  
- Soft deletes used where appropriate (is_active flags)
- Unique constraints prevent duplicate data

## 🤝 Contributing

When adding new models:
1. Create model in appropriate `models/` file
2. Add to `models/__init__.py`
3. Generate migration
4. Update this README
5. Add seeding logic if needed

---

## 🆚 Comparison with Original Schema

### Improvements Made

#### ✅ **Better Organization**
- **Before**: Single `init_db.py` file with mixed SQL and Python
- **After**: Organized models, migrations, and seeds

#### ✅ **Type Safety** 
- **Before**: Raw SQL strings, no validation
- **After**: SQLAlchemy models with type hints and validation

#### ✅ **Migrations**
- **Before**: Drop/recreate database each time
- **After**: Versioned migrations with rollback capability

#### ✅ **Relationships**
- **Before**: Manual foreign key management
- **After**: Automatic relationship handling

#### ✅ **Future-Ready**
- **Before**: Basic academic structure only
- **After**: Extended with study groups, preferences, analytics

#### ✅ **Performance**
- **Before**: No indexes except basic ones
- **After**: Optimized indexes for common query patterns

#### ✅ **Maintainability**
- **Before**: Hard to modify, no version control
- **After**: Modular, version-controlled, easy to extend

This migration system provides a solid foundation for both the current chatbot functionality and the advanced features we discussed earlier!