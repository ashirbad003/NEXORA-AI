"""phase_5_coding_arena_tables

Revision ID: 92c890123def
Revises: 74a123b456cd
Create Date: 2026-11-20 18:15:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '92c890123def'
down_revision: Union[str, Sequence[str], None] = '74a123b456cd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # 1. coding_problems table
    op.create_table(
        'coding_problems',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('slug', sa.String(length=100), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('difficulty', sa.String(length=20), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=False),
        sa.Column('tags', sa.String(length=255), nullable=True),
        sa.Column('companies', sa.String(length=255), nullable=True),
        sa.Column('description_markdown', sa.Text(), nullable=False),
        sa.Column('constraints', sa.Text(), nullable=True),
        sa.Column('time_limit_ms', sa.Integer(), nullable=False),
        sa.Column('memory_limit_mb', sa.Integer(), nullable=False),
        sa.Column('starter_code_python', sa.Text(), nullable=True),
        sa.Column('starter_code_java', sa.Text(), nullable=True),
        sa.Column('starter_code_cpp', sa.Text(), nullable=True),
        sa.Column('starter_code_c', sa.Text(), nullable=True),
        sa.Column('is_published', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_coding_problems_category'), 'coding_problems', ['category'], unique=False)
    op.create_index(op.f('ix_coding_problems_difficulty'), 'coding_problems', ['difficulty'], unique=False)
    op.create_index(op.f('ix_coding_problems_slug'), 'coding_problems', ['slug'], unique=True)

    # 2. problem_test_cases table
    op.create_table(
        'problem_test_cases',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('problem_id', sa.String(length=36), nullable=False),
        sa.Column('stdin_input', sa.Text(), nullable=False),
        sa.Column('expected_output', sa.Text(), nullable=False),
        sa.Column('is_sample', sa.Boolean(), nullable=False),
        sa.Column('explanation', sa.Text(), nullable=True),
        sa.Column('order_index', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['problem_id'], ['coding_problems.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_problem_test_cases_problem_id'), 'problem_test_cases', ['problem_id'], unique=False)

    # 3. code_submissions table
    op.create_table(
        'code_submissions',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('problem_id', sa.String(length=36), nullable=False),
        sa.Column('language', sa.String(length=20), nullable=False),
        sa.Column('code_content', sa.Text(), nullable=False),
        sa.Column('verdict', sa.String(length=30), nullable=False),
        sa.Column('passed_test_cases', sa.Integer(), nullable=False),
        sa.Column('total_test_cases', sa.Integer(), nullable=False),
        sa.Column('execution_time_ms', sa.Float(), nullable=False),
        sa.Column('memory_used_mb', sa.Float(), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['problem_id'], ['coding_problems.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_code_submissions_problem_id'), 'code_submissions', ['problem_id'], unique=False)
    op.create_index(op.f('ix_code_submissions_user_id'), 'code_submissions', ['user_id'], unique=False)
    op.create_index(op.f('ix_code_submissions_verdict'), 'code_submissions', ['verdict'], unique=False)
    op.create_index('ix_code_submissions_user_problem', 'code_submissions', ['user_id', 'problem_id'], unique=False)

    # 4. student_coding_stats table
    op.create_table(
        'student_coding_stats',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('total_solved', sa.Integer(), nullable=False),
        sa.Column('easy_solved', sa.Integer(), nullable=False),
        sa.Column('medium_solved', sa.Integer(), nullable=False),
        sa.Column('hard_solved', sa.Integer(), nullable=False),
        sa.Column('current_streak_days', sa.Integer(), nullable=False),
        sa.Column('longest_streak_days', sa.Integer(), nullable=False),
        sa.Column('last_solved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )
    op.create_index(op.f('ix_student_coding_stats_user_id'), 'student_coding_stats', ['user_id'], unique=True)

def downgrade() -> None:
    op.drop_table('student_coding_stats')
    op.drop_table('code_submissions')
    op.drop_table('problem_test_cases')
    op.drop_table('coding_problems')
