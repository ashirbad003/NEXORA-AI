"""phase_9_placement_and_admin_portal_tables

Revision ID: d9b2ef020303
Revises: c8a1fe910202
Create Date: 2026-11-21 20:45:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'd9b2ef020303'
down_revision = 'c8a1fe910202'
branch_labels = None
depends_on = None

def upgrade():
    # 1. Placement Drives Table (FEAT-235, FEAT-237, FEAT-239, FEAT-255)
    op.create_table(
        'placement_drives',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('company_name', sa.String(length=150), nullable=False),
        sa.Column('role_title', sa.String(length=150), nullable=False),
        sa.Column('ctc_lpa', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('tier', sa.String(length=50), nullable=False, server_default='Standard'),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='Scheduled'),
        sa.Column('min_cgpa', sa.Float(), nullable=False, server_default='6.0'),
        sa.Column('allowed_branches', sa.JSON(), nullable=False),
        sa.Column('max_backlogs', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('registration_deadline', sa.DateTime(), nullable=True),
        sa.Column('drive_date', sa.DateTime(), nullable=True),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id')
    )

    # 2. Placement Drive Registrations Table (FEAT-240, FEAT-241, FEAT-250)
    op.create_table(
        'placement_drive_registrations',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('drive_id', sa.String(length=36), nullable=False),
        sa.Column('student_id', sa.String(length=36), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='Pending'),
        sa.Column('is_eligible', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('attendance', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('interview_slot', sa.String(length=100), nullable=True),
        sa.Column('tpo_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['drive_id'], ['placement_drives.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['student_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_placement_drive_registrations_drive_id', 'placement_drive_registrations', ['drive_id'], unique=False)
    op.create_index('ix_placement_drive_registrations_student_id', 'placement_drive_registrations', ['student_id'], unique=False)

    # 3. Placement Offers Table (FEAT-242, FEAT-255)
    op.create_table(
        'placement_offers',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('drive_id', sa.String(length=36), nullable=False),
        sa.Column('student_id', sa.String(length=36), nullable=False),
        sa.Column('company_name', sa.String(length=150), nullable=False),
        sa.Column('designation', sa.String(length=150), nullable=False),
        sa.Column('ctc_lpa', sa.Float(), nullable=False),
        sa.Column('offer_letter_url', sa.String(length=255), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='Offered'),
        sa.Column('offered_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['drive_id'], ['placement_drives.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['student_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # 4. Student Placement Profiles Table (FEAT-248, FEAT-251)
    op.create_table(
        'student_placement_profiles',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('student_id', sa.String(length=36), nullable=False),
        sa.Column('is_blacklisted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('blacklist_reason', sa.Text(), nullable=True),
        sa.Column('is_opted_out', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('opt_out_reason', sa.String(length=100), nullable=True),
        sa.Column('offers_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('highest_offer_lpa', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['student_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('student_id')
    )

    # 5. System Feature Flags Table (FEAT-262)
    op.create_table(
        'system_feature_flags',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('flag_key', sa.String(length=100), nullable=False),
        sa.Column('name', sa.String(length=150), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('updated_by', sa.String(length=36), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('flag_key')
    )

    # 6. System Metric Snapshots Table (FEAT-270, FEAT-272, FEAT-273)
    op.create_table(
        'system_metric_snapshots',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('metric_type', sa.String(length=50), nullable=False),
        sa.Column('payload', sa.JSON(), nullable=False),
        sa.Column('recorded_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade():
    op.drop_table('system_metric_snapshots')
    op.drop_table('system_feature_flags')
    op.drop_table('student_placement_profiles')
    op.drop_table('placement_offers')
    op.drop_table('placement_drive_registrations')
    op.drop_table('placement_drives')
