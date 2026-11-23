"""phase_11_mobile_sync

Revision ID: f2a3b4c5d6e7
Revises: e1f2a3b4c5d6
Create Date: 2026-11-23 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'f2a3b4c5d6e7'
down_revision = 'e1f2a3b4c5d6'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # 1. Alter student_card_reviews to add state_version for clock-independent ordering
    op.add_column('student_card_reviews', sa.Column('state_version', sa.BigInteger(), server_default='1', nullable=False))

    # 2. Alter student_card_review_logs for offline tracking, versioning & superseding
    op.add_column('student_card_review_logs', sa.Column('client_reviewed_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('student_card_review_logs', sa.Column('device_id', sa.String(length=100), nullable=True))
    op.add_column('student_card_review_logs', sa.Column('is_superseded', sa.Boolean(), server_default='false', nullable=False))
    op.add_column('student_card_review_logs', sa.Column('base_state_version', sa.BigInteger(), nullable=True))
    op.add_column('student_card_review_logs', sa.Column('resulting_state_version', sa.BigInteger(), nullable=True))

    # 3. Table: mobile_device_tokens
    op.create_table(
        'mobile_device_tokens',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('user_id', sa.String(length=36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('device_id', sa.String(length=100), nullable=False),
        sa.Column('expo_push_token', sa.String(length=255), nullable=False),
        sa.Column('device_os', sa.String(length=32), server_default='ANDROID', nullable=False),
        sa.Column('device_model', sa.String(length=100), nullable=True),
        sa.Column('app_version', sa.String(length=32), server_default='1.0.0', nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('last_used_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.UniqueConstraint('user_id', 'device_id', name='uq_mobile_device_user_device')
    )
    op.create_index('ix_mobile_device_user_active', 'mobile_device_tokens', ['user_id', 'is_active'])
    op.create_index('ix_mobile_device_expo_token', 'mobile_device_tokens', ['expo_push_token'])

    # 4. Table: user_sync_counters (One row per user, global monotonic counter & retention horizon)
    op.create_table(
        'user_sync_counters',
        sa.Column('user_id', sa.String(length=36), sa.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('current_val', sa.BigInteger(), server_default='0', nullable=False),
        sa.Column('min_available_seq', sa.BigInteger(), server_default='1', nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False)
    )

    # 5. Table: user_sync_watermarks (One row per user per physical device)
    op.create_table(
        'user_sync_watermarks',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('user_id', sa.String(length=36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('device_id', sa.String(length=100), nullable=False),
        sa.Column('last_acknowledged_seq', sa.BigInteger(), server_default='0', nullable=False),
        sa.Column('last_synced_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('client_app_version', sa.String(length=32), server_default='1.0.0', nullable=False),
        sa.UniqueConstraint('user_id', 'device_id', name='uq_sync_watermarks_user_device')
    )
    op.create_index('ix_sync_watermarks_user_synced', 'user_sync_watermarks', ['user_id', 'last_synced_at'])

    # 6. Table: user_sync_change_feed (Append-only change ledger ordered by change_seq)
    op.create_table(
        'user_sync_change_feed',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('user_id', sa.String(length=36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('change_seq', sa.BigInteger(), nullable=False),
        sa.Column('entity_type', sa.String(length=50), nullable=False),
        sa.Column('entity_id', sa.String(length=36), nullable=False),
        sa.Column('operation', sa.String(length=20), nullable=False),
        sa.Column('payload', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.UniqueConstraint('user_id', 'change_seq', name='uq_change_feed_user_seq')
    )
    op.create_index('ix_change_feed_user_seq', 'user_sync_change_feed', ['user_id', 'change_seq'])

    # 7. Table: user_sync_tombstones (Sequence-based deletion events supporting re-deletion)
    op.create_table(
        'user_sync_tombstones',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('user_id', sa.String(length=36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('entity_type', sa.String(length=50), nullable=False),
        sa.Column('entity_id', sa.String(length=36), nullable=False),
        sa.Column('change_seq', sa.BigInteger(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.UniqueConstraint('user_id', 'change_seq', name='uq_tombstones_user_seq')
    )
    op.create_index('ix_tombstones_user_entity', 'user_sync_tombstones', ['user_id', 'entity_type', 'entity_id'])
    op.create_index('ix_tombstones_deleted_at', 'user_sync_tombstones', ['deleted_at'])

def downgrade() -> None:
    op.drop_table('user_sync_tombstones')
    op.drop_table('user_sync_change_feed')
    op.drop_table('user_sync_watermarks')
    op.drop_table('user_sync_counters')
    op.drop_table('mobile_device_tokens')
    op.drop_column('student_card_review_logs', 'resulting_state_version')
    op.drop_column('student_card_review_logs', 'base_state_version')
    op.drop_column('student_card_review_logs', 'is_superseded')
    op.drop_column('student_card_review_logs', 'device_id')
    op.drop_column('student_card_review_logs', 'client_reviewed_at')
    op.drop_column('student_card_reviews', 'state_version')
