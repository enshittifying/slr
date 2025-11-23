"""Initial schema

Revision ID: 001_initial
Revises:
Create Date: 2025-11-12 00:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create ENUM types
    op.execute("""
        CREATE TYPE user_role AS ENUM ('member_editor', 'senior_editor', 'admin');
        CREATE TYPE task_status AS ENUM ('not_started', 'in_progress', 'completed', 'blocked');
        CREATE TYPE article_status AS ENUM ('draft', 'sp_in_progress', 'r1_in_progress', 'r2_in_progress', 'completed', 'published');
        CREATE TYPE pipeline_status AS ENUM ('pending', 'in_progress', 'completed', 'failed', 'manual_required');
        CREATE TYPE attendance_status AS ENUM ('attending', 'not_attending', 'maybe', 'no_response');
    """)

    # Create users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('email', sa.String(255), unique=True, nullable=False),
        sa.Column('full_name', sa.String(255), nullable=False),
        sa.Column('role', postgresql.ENUM('member_editor', 'senior_editor', 'admin', name='user_role'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('last_login', sa.DateTime(timezone=True)),
        sa.Column('is_active', sa.Boolean, default=True, nullable=False),
    )
    op.create_index('idx_users_email', 'users', ['email'])
    op.create_index('idx_users_role', 'users', ['role'])

    # Create tasks table
    op.create_table(
        'tasks',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('due_date', sa.DateTime(timezone=True)),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL')),
        sa.Column('linked_form_id', postgresql.UUID(as_uuid=True)),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('idx_tasks_due_date', 'tasks', ['due_date'])
    op.create_index('idx_tasks_created_by', 'tasks', ['created_by'])

    # Create task_assignments table
    op.create_table(
        'task_assignments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('task_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tasks.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('status', postgresql.ENUM('not_started', 'in_progress', 'completed', 'blocked', name='task_status'), default='not_started', nullable=False),
        sa.Column('assigned_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True)),
        sa.Column('notes', sa.Text),
        sa.UniqueConstraint('task_id', 'user_id', name='uq_task_user'),
    )
    op.create_index('idx_assignments_user_status', 'task_assignments', ['user_id', 'status'])
    op.create_index('idx_assignments_task', 'task_assignments', ['task_id'])

    # Create articles table
    op.create_table(
        'articles',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('title', sa.String(1000), nullable=False),
        sa.Column('author_name', sa.String(500)),
        sa.Column('volume_number', sa.Integer, nullable=False),
        sa.Column('issue_number', sa.Integer, nullable=False),
        sa.Column('status', postgresql.ENUM('draft', 'sp_in_progress', 'r1_in_progress', 'r2_in_progress', 'completed', 'published', name='article_status'), default='draft', nullable=False),
        sa.Column('submitted_at', sa.DateTime(timezone=True)),
        sa.Column('published_at', sa.DateTime(timezone=True)),
        sa.Column('assigned_editor', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('idx_articles_volume_issue', 'articles', ['volume_number', 'issue_number'])
    op.create_index('idx_articles_status', 'articles', ['status'])
    op.create_index('idx_articles_editor', 'articles', ['assigned_editor'])

    # Create citations table
    op.create_table(
        'citations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('article_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('articles.id', ondelete='CASCADE'), nullable=False),
        sa.Column('footnote_number', sa.Integer, nullable=False),
        sa.Column('citation_text', sa.Text, nullable=False),
        sa.Column('proposition', sa.Text),
        sa.Column('source_type', sa.String(100)),
        sa.Column('source_title', sa.String(1000)),
        sa.Column('source_author', sa.String(500)),
        sa.Column('source_url', sa.String(2000)),
        sa.Column('sp_status', postgresql.ENUM('pending', 'in_progress', 'completed', 'failed', 'manual_required', name='pipeline_status'), default='pending', nullable=False),
        sa.Column('sp_pdf_path', sa.String(1000)),
        sa.Column('sp_completed_at', sa.DateTime(timezone=True)),
        sa.Column('r1_status', postgresql.ENUM('pending', 'in_progress', 'completed', 'failed', 'manual_required', name='pipeline_status'), default='pending', nullable=False),
        sa.Column('r1_pdf_path', sa.String(1000)),
        sa.Column('r1_metadata', postgresql.JSONB),
        sa.Column('r1_completed_at', sa.DateTime(timezone=True)),
        sa.Column('r2_status', postgresql.ENUM('pending', 'in_progress', 'completed', 'failed', 'manual_required', name='pipeline_status'), default='pending', nullable=False),
        sa.Column('r2_pdf_path', sa.String(1000)),
        sa.Column('r2_validation_result', postgresql.JSONB),
        sa.Column('r2_completed_at', sa.DateTime(timezone=True)),
        sa.Column('format_valid', sa.Boolean),
        sa.Column('support_valid', sa.Boolean),
        sa.Column('quote_valid', sa.Boolean),
        sa.Column('requires_manual_review', sa.Boolean, default=False, nullable=False),
        sa.Column('manual_review_notes', sa.Text),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint('article_id', 'footnote_number', name='uq_article_footnote'),
    )
    op.create_index('idx_citations_article', 'citations', ['article_id'])
    op.create_index('idx_citations_sp_status', 'citations', ['sp_status'])
    op.create_index('idx_citations_r1_status', 'citations', ['r1_status'])
    op.create_index('idx_citations_r2_status', 'citations', ['r2_status'])
    op.create_index('idx_citations_manual_review', 'citations', ['requires_manual_review'], postgresql_where=sa.text('requires_manual_review = TRUE'))

    # Create forms table
    op.create_table(
        'forms',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(255), unique=True, nullable=False),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('is_active', sa.Boolean, default=True, nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )

    # Create form_fields table
    op.create_table(
        'form_fields',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('form_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('forms.id', ondelete='CASCADE'), nullable=False),
        sa.Column('field_type', sa.String(50), nullable=False),
        sa.Column('label', sa.String(500), nullable=False),
        sa.Column('field_name', sa.String(100), nullable=False),
        sa.Column('is_required', sa.Boolean, default=False, nullable=False),
        sa.Column('options', postgresql.JSONB),
        sa.Column('validation_rules', postgresql.JSONB),
        sa.Column('display_order', sa.Integer, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint('form_id', 'field_name', name='uq_form_field_name'),
    )
    op.create_index('idx_form_fields_form', 'form_fields', ['form_id', 'display_order'])

    # Create form_submissions table
    op.create_table(
        'form_submissions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('form_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('forms.id', ondelete='CASCADE'), nullable=False),
        sa.Column('submitted_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('submission_data', postgresql.JSONB, nullable=False),
        sa.Column('submitted_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('idx_submissions_form', 'form_submissions', ['form_id'])
    op.create_index('idx_submissions_user', 'form_submissions', ['submitted_by'])
    op.create_index('idx_submissions_date', 'form_submissions', ['submitted_at'])

    # Create events table
    op.create_table(
        'events',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('event_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('location', sa.String(500)),
        sa.Column('google_calendar_event_id', sa.String(255)),
        sa.Column('attendance_form_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('forms.id', ondelete='SET NULL')),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('idx_events_date', 'events', ['event_date'])

    # Create attendance_records table
    op.create_table(
        'attendance_records',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('event_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('events.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('status', postgresql.ENUM('attending', 'not_attending', 'maybe', 'no_response', name='attendance_status'), nullable=False),
        sa.Column('confirmed_at', sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint('event_id', 'user_id', name='uq_event_user'),
    )
    op.create_index('idx_attendance_event', 'attendance_records', ['event_id'])
    op.create_index('idx_attendance_user', 'attendance_records', ['user_id'])

    # Create system_config table
    op.create_table(
        'system_config',
        sa.Column('key', sa.String(255), primary_key=True),
        sa.Column('value', sa.Text, nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL')),
    )

    # Create audit_log table
    op.create_table(
        'audit_log',
        sa.Column('id', sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL')),
        sa.Column('action', sa.String(100), nullable=False),
        sa.Column('table_name', sa.String(100)),
        sa.Column('record_id', postgresql.UUID(as_uuid=True)),
        sa.Column('old_values', postgresql.JSONB),
        sa.Column('new_values', postgresql.JSONB),
        sa.Column('ip_address', postgresql.INET),
        sa.Column('user_agent', sa.Text),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('idx_audit_user', 'audit_log', ['user_id'])
    op.create_index('idx_audit_action', 'audit_log', ['action'])
    op.create_index('idx_audit_table_record', 'audit_log', ['table_name', 'record_id'])
    op.create_index('idx_audit_created', 'audit_log', ['created_at'])


def downgrade() -> None:
    # Drop tables
    op.drop_table('audit_log')
    op.drop_table('system_config')
    op.drop_table('attendance_records')
    op.drop_table('events')
    op.drop_table('form_submissions')
    op.drop_table('form_fields')
    op.drop_table('forms')
    op.drop_table('citations')
    op.drop_table('articles')
    op.drop_table('task_assignments')
    op.drop_table('tasks')
    op.drop_table('users')

    # Drop ENUM types
    op.execute("""
        DROP TYPE IF EXISTS attendance_status;
        DROP TYPE IF EXISTS pipeline_status;
        DROP TYPE IF EXISTS article_status;
        DROP TYPE IF EXISTS task_status;
        DROP TYPE IF EXISTS user_role;
    """)
