"""phase_7_assessment_and_interview_tables

Revision ID: b7fcde829101
Revises: a3ebe19fb261
Create Date: 2026-11-21 07:25:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'b7fcde829101'
down_revision = 'a3ebe19fb261'
branch_labels = None
depends_on = None

def upgrade():
    # 1. Assessment Tests Table
    op.create_table(
        'assessment_tests',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(length=50), nullable=False, server_default='Aptitude'),
        sa.Column('difficulty', sa.String(length=20), nullable=False, server_default='Medium'),
        sa.Column('duration_minutes', sa.Integer(), nullable=False, server_default='30'),
        sa.Column('total_marks', sa.Float(), nullable=False, server_default='30.0'),
        sa.Column('pass_marks', sa.Float(), nullable=False, server_default='15.0'),
        sa.Column('negative_marking_rate', sa.Float(), nullable=False, server_default='0.25'),
        sa.Column('retake_allowed', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('retake_cooldown_hours', sa.Integer(), nullable=False, server_default='24'),
        sa.Column('company_template', sa.String(length=100), nullable=True),
        sa.Column('is_published', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id')
    )

    # 2. Assessment Questions Table
    op.create_table(
        'assessment_questions',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('test_id', sa.String(length=36), nullable=False),
        sa.Column('section_name', sa.String(length=50), nullable=False, server_default='General'),
        sa.Column('order_index', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('question_text', sa.Text(), nullable=False),
        sa.Column('options', sa.JSON(), nullable=False),
        sa.Column('correct_option', sa.String(length=10), nullable=False),
        sa.Column('marks', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('explanation', sa.Text(), nullable=True),
        sa.Column('topic_tag', sa.String(length=100), nullable=False, server_default='General'),
        sa.Column('difficulty', sa.String(length=20), nullable=False, server_default='Medium'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['test_id'], ['assessment_tests.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # 3. Assessment Attempts Table
    op.create_table(
        'assessment_attempts',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('test_id', sa.String(length=36), nullable=False),
        sa.Column('student_id', sa.String(length=36), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='in_progress'),
        sa.Column('start_time', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('end_time', sa.DateTime(), nullable=True),
        sa.Column('score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('accuracy_percentage', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('percentile', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('blur_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('shuffled_question_order', sa.JSON(), nullable=True),
        sa.Column('flagged_question_ids', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['student_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['test_id'], ['assessment_tests.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # 4. Assessment Answers Table
    op.create_table(
        'assessment_answers',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('attempt_id', sa.String(length=36), nullable=False),
        sa.Column('question_id', sa.String(length=36), nullable=False),
        sa.Column('selected_option', sa.String(length=10), nullable=True),
        sa.Column('is_correct', sa.Boolean(), nullable=True),
        sa.Column('marks_awarded', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('time_spent_seconds', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_saved_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['attempt_id'], ['assessment_attempts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['question_id'], ['assessment_questions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # 5. Mock Interview Sessions Table
    op.create_table(
        'mock_interview_sessions',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('student_id', sa.String(length=36), nullable=False),
        sa.Column('role_target', sa.String(length=100), nullable=False, server_default='Software Development Engineer'),
        sa.Column('interview_type', sa.String(length=50), nullable=False, server_default='Technical'),
        sa.Column('company_persona', sa.String(length=50), nullable=False, server_default='Google'),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='in_progress'),
        sa.Column('total_turns', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('overall_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('star_situation_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('star_task_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('star_action_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('star_result_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('tone_clarity_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('filler_word_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('technical_accuracy_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('improvement_plan', sa.JSON(), nullable=True),
        sa.Column('whiteboard_state', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['student_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # 6. Mock Interview Turns Table
    op.create_table(
        'mock_interview_turns',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('session_id', sa.String(length=36), nullable=False),
        sa.Column('turn_index', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('question_text', sa.Text(), nullable=False),
        sa.Column('question_category', sa.String(length=50), nullable=False, server_default='Technical'),
        sa.Column('student_response_text', sa.Text(), nullable=True),
        sa.Column('audio_duration_seconds', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('pacing_verdict', sa.String(length=50), nullable=False, server_default='Optimal'),
        sa.Column('interviewer_feedback', sa.Text(), nullable=True),
        sa.Column('is_followup', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['session_id'], ['mock_interview_sessions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade():
    op.drop_table('mock_interview_turns')
    op.drop_table('mock_interview_sessions')
    op.drop_table('assessment_answers')
    op.drop_table('assessment_attempts')
    op.drop_table('assessment_questions')
    op.drop_table('assessment_tests')
