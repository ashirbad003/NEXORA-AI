"""phase_8_resume_github_job_tables

Revision ID: c8a1fe910202
Revises: b7fcde829101
Create Date: 2026-11-21 20:25:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'c8a1fe910202'
down_revision = 'b7fcde829101'
branch_labels = None
depends_on = None

def upgrade():
    # 1. Resume Documents Table (FEAT-181 to FEAT-200)
    op.create_table(
        'resume_documents',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('student_id', sa.String(length=36), nullable=False),
        sa.Column('title', sa.String(length=100), nullable=False, server_default='My Technical Resume'),
        sa.Column('template_type', sa.String(length=50), nullable=False, server_default='Modern'),
        sa.Column('raw_content', sa.Text(), nullable=True),
        sa.Column('structured_data', sa.JSON(), nullable=False),
        sa.Column('ats_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('completeness_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('is_primary', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['student_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_resume_documents_student_id', 'resume_documents', ['student_id'], unique=False)

    # 2. GitHub Profile Caches Table (FEAT-201 to FEAT-216)
    op.create_table(
        'github_profile_caches',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('student_id', sa.String(length=36), nullable=False),
        sa.Column('github_username', sa.String(length=100), nullable=False),
        sa.Column('portfolio_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('public_repos_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('languages_distribution', sa.JSON(), nullable=False),
        sa.Column('repository_health_metrics', sa.JSON(), nullable=False),
        sa.Column('recommendations', sa.JSON(), nullable=False),
        sa.Column('last_scanned_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['student_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_github_profile_caches_student_id', 'github_profile_caches', ['student_id'], unique=False)

    # 3. Job Opportunities Table (FEAT-217 to FEAT-234)
    op.create_table(
        'job_opportunities',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('company_name', sa.String(length=150), nullable=False),
        sa.Column('role_title', sa.String(length=150), nullable=False),
        sa.Column('opportunity_type', sa.String(length=50), nullable=False, server_default='Full-Time'),
        sa.Column('location', sa.String(length=100), nullable=False, server_default='Remote'),
        sa.Column('stipend_or_salary', sa.String(length=100), nullable=False, server_default='Competitive'),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('required_skills', sa.JSON(), nullable=False),
        sa.Column('deadline', sa.DateTime(), nullable=True),
        sa.Column('is_on_campus', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('application_url', sa.String(length=255), nullable=False, server_default='#'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id')
    )

    # 4. Job Applications Table (Kanban status FEAT-219)
    op.create_table(
        'job_applications',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('job_id', sa.String(length=36), nullable=False),
        sa.Column('student_id', sa.String(length=36), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='Wishlist'),
        sa.Column('match_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('applied_at', sa.DateTime(), nullable=True),
        sa.Column('interview_date', sa.DateTime(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['job_id'], ['job_opportunities.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['student_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_job_applications_student_id', 'job_applications', ['student_id'], unique=False)
    op.create_index('ix_job_applications_job_id', 'job_applications', ['job_id'], unique=False)


def downgrade():
    op.drop_table('job_applications')
    op.drop_table('job_opportunities')
    op.drop_table('github_profile_caches')
    op.drop_table('resume_documents')
