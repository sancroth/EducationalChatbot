"""Initial schema creation

Revision ID: 001
Revises: 
Create Date: 2025-01-07 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create departments table
    op.create_table('departments',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False, comment='Department name in Greek'),
        sa.Column('key', sa.String(length=50), nullable=False, comment='Department abbreviation key'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('key')
    )

    # Create department_secretariats table
    op.create_table('department_secretariats',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('department_id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=100), nullable=False),
        sa.Column('contact_phone', sa.String(length=50), nullable=False),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('working_hours', sa.String(length=100), nullable=True),
        sa.Column('website_url', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['department_id'], ['departments.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create roles table
    op.create_table('roles',
        sa.Column('role_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('role_name', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('role_id'),
        sa.UniqueConstraint('role_name')
    )

    # Create users table
    op.create_table('users',
        sa.Column('user_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('first_name', sa.String(length=50), nullable=True),
        sa.Column('last_name', sa.String(length=50), nullable=False),
        sa.Column('email', sa.String(length=100), nullable=False),
        sa.Column('date_of_birth', sa.Date(), nullable=True),
        sa.Column('enrollment_date', sa.Date(), nullable=False),
        sa.Column('department_id', sa.Integer(), nullable=False),
        sa.Column('gender', sa.String(length=20), nullable=False),
        sa.Column('role_id', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['department_id'], ['departments.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['role_id'], ['roles.role_id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('user_id'),
        sa.UniqueConstraint('email')
    )

    # Create user_credentials table
    op.create_table('user_credentials',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('password_hash', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )

    # Create student_info table
    op.create_table('student_info',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('am', sa.String(length=50), nullable=False, comment='Student registration number'),
        sa.Column('semester', sa.Integer(), nullable=False),
        sa.Column('special_needs', postgresql.JSON(astext_type=sa.Text()), nullable=True, comment='JSON array of special needs'),
        sa.Column('gpa', sa.String(length=10), nullable=True, comment='Current GPA'),
        sa.Column('total_credits', sa.Integer(), server_default='0', nullable=True, comment='Total credits earned'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('am'),
        sa.UniqueConstraint('user_id')
    )

    # Create classes table
    op.create_table('classes',
        sa.Column('class_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('class_name', sa.String(length=100), nullable=False),
        sa.Column('class_type', sa.String(length=100), nullable=False, comment='ΘΕΩΡΙΑ, ΕΡΓΑΣΤΗΡΙΟ, etc.'),
        sa.Column('department_id', sa.Integer(), nullable=False),
        sa.Column('program', sa.String(length=50), nullable=False, server_default='ΠΡΟΠΤΥΧΙΑΚΟ'),
        sa.Column('semester', sa.Integer(), nullable=False, comment='Which semester this course belongs to'),
        sa.Column('credits', sa.Integer(), server_default='3', nullable=True, comment='Credit hours for this course'),
        sa.Column('description', sa.String(length=500), nullable=True),
        sa.Column('prerequisites', sa.String(length=200), nullable=True, comment='Comma-separated prerequisite course IDs'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['department_id'], ['departments.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('class_id')
    )

    # Create class_schedules table
    op.create_table('class_schedules',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('semester', sa.Integer(), nullable=False, comment='Academic semester'),
        sa.Column('class_team', sa.Integer(), nullable=False, server_default='1', comment='Team/group number (for split classes)'),
        sa.Column('teacher_id', sa.Integer(), nullable=False),
        sa.Column('class_id', sa.Integer(), nullable=False),
        sa.Column('classroom', sa.String(length=50), nullable=False),
        sa.Column('day_of_week', sa.Integer(), nullable=False, comment='1=Monday, 7=Sunday'),
        sa.Column('start_time', sa.Time(), nullable=False),
        sa.Column('end_time', sa.Time(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['class_id'], ['classes.class_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['teacher_id'], ['users.user_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create student_enrollments table
    op.create_table('student_enrollments',
        sa.Column('enrollment_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('class_id', sa.Integer(), nullable=False),
        sa.Column('department_id', sa.Integer(), nullable=False),
        sa.Column('enrollment_status', sa.String(length=20), server_default='ACTIVE', nullable=True, comment='ACTIVE, COMPLETED, DROPPED, FAILED'),
        sa.Column('grade', sa.String(length=10), nullable=True, comment='Final grade'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['class_id'], ['classes.class_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['department_id'], ['departments.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('enrollment_id'),
        sa.UniqueConstraint('user_id', 'class_id', name='uq_student_class_enrollment')
    )

    # Create indexes
    op.create_index('idx_class_schedule_course', 'class_schedules', ['class_id', 'semester'])
    op.create_index('idx_class_schedule_teacher', 'class_schedules', ['teacher_id', 'day_of_week'])
    op.create_index('idx_class_schedule_time', 'class_schedules', ['day_of_week', 'start_time', 'end_time'])
    op.create_index('idx_enrollment_course', 'student_enrollments', ['class_id'])
    op.create_index('idx_enrollment_student', 'student_enrollments', ['user_id'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_enrollment_student', table_name='student_enrollments')
    op.drop_index('idx_enrollment_course', table_name='student_enrollments')
    op.drop_index('idx_class_schedule_time', table_name='class_schedules')
    op.drop_index('idx_class_schedule_teacher', table_name='class_schedules')
    op.drop_index('idx_class_schedule_course', table_name='class_schedules')
    
    # Drop tables in reverse order
    op.drop_table('student_enrollments')
    op.drop_table('class_schedules')
    op.drop_table('classes')
    op.drop_table('student_info')
    op.drop_table('user_credentials')
    op.drop_table('users')
    op.drop_table('roles')
    op.drop_table('department_secretariats')
    op.drop_table('departments')