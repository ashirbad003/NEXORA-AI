"""phase_10_master_tables

Revision ID: e1f2a3b4c5d6
Revises: d9b2ef020303
Create Date: 2026-11-22 08:15:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'e1f2a3b4c5d6'
down_revision = 'd9b2ef020303'
branch_labels = None
depends_on = None

def upgrade():
    # 0. student_profiles timezone column
    op.add_column(
        'student_profiles',
        sa.Column('timezone', sa.String(length=64), nullable=False, server_default='UTC')
    )

    # 1. flashcard_decks (Module H: FEAT-145..162)
    op.create_table(
        'flashcard_decks',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(length=100), nullable=False, server_default='General'),
        sa.Column('tags', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='[]'),
        sa.Column('is_public', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_system', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_approved', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_archived', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('share_slug', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('share_slug')
    )
    op.create_index('ix_flashcard_decks_user_id', 'flashcard_decks', ['user_id'])
    op.create_index('ix_flashcard_decks_category', 'flashcard_decks', ['category'])
    op.create_index('ix_flashcard_decks_is_public', 'flashcard_decks', ['is_public'])
    op.create_index('ix_flashcard_decks_is_approved', 'flashcard_decks', ['is_approved'])

    # 2. flashcard_items
    op.create_table(
        'flashcard_items',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('deck_id', sa.String(length=36), nullable=False),
        sa.Column('prompt', sa.Text(), nullable=False),
        sa.Column('answer', sa.Text(), nullable=False),
        sa.Column('explanation', sa.Text(), nullable=True),
        sa.Column('code_snippet', sa.Text(), nullable=True),
        sa.Column('audio_url', sa.String(length=500), nullable=True),
        sa.Column('order_index', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['deck_id'], ['flashcard_decks.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_flashcard_items_deck_id', 'flashcard_items', ['deck_id'])

    # 3. student_card_reviews
    op.create_table(
        'student_card_reviews',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('card_id', sa.String(length=36), nullable=False),
        sa.Column('repetition', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('interval_days', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('ease_factor', sa.Float(), nullable=False, server_default='2.50'),
        sa.Column('stability', sa.Float(), nullable=False, server_default='1.00'),
        sa.Column('next_review_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('last_reviewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['card_id'], ['flashcard_items.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'card_id', name='uq_student_card_reviews_user_card')
    )
    op.create_index('ix_student_card_reviews_user_id', 'student_card_reviews', ['user_id'])
    op.create_index('ix_student_card_reviews_card_id', 'student_card_reviews', ['card_id'])
    op.create_index('ix_student_card_reviews_user_next_review', 'student_card_reviews', ['user_id', 'next_review_at'])

    # 4. revision_focus_sessions (Needed by review logs FK)
    op.create_table(
        'revision_focus_sessions',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('deck_id', sa.String(length=36), nullable=True),
        sa.Column('duration_minutes', sa.Integer(), nullable=False, server_default='25'),
        sa.Column('elapsed_seconds', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('cards_reviewed', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='IN_PROGRESS'),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('ended_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['deck_id'], ['flashcard_decks.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_revision_focus_sessions_user_id', 'revision_focus_sessions', ['user_id'])

    # 5. student_card_review_logs
    op.create_table(
        'student_card_review_logs',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('card_id', sa.String(length=36), nullable=True),
        sa.Column('review_id', sa.String(length=36), nullable=True),
        sa.Column('session_id', sa.String(length=36), nullable=True),
        sa.Column('idempotency_key', sa.String(length=64), nullable=False),
        sa.Column('request_hash', sa.String(length=64), nullable=False),
        sa.Column('submitted_grade', sa.Integer(), nullable=False),
        sa.Column('time_spent_ms', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('prev_repetition', sa.Integer(), nullable=False),
        sa.Column('new_repetition', sa.Integer(), nullable=False),
        sa.Column('prev_interval', sa.Integer(), nullable=False),
        sa.Column('new_interval', sa.Integer(), nullable=False),
        sa.Column('prev_ease_factor', sa.Float(), nullable=False),
        sa.Column('new_ease_factor', sa.Float(), nullable=False),
        sa.Column('prev_stability', sa.Float(), nullable=False),
        sa.Column('new_stability', sa.Float(), nullable=False),
        sa.Column('prev_next_review_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('new_next_review_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('response_payload', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['card_id'], ['flashcard_items.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['review_id'], ['student_card_reviews.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['session_id'], ['revision_focus_sessions.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'idempotency_key', name='uq_review_logs_user_idempotency')
    )
    op.create_index('ix_review_logs_user_reviewed_at', 'student_card_review_logs', ['user_id', 'reviewed_at'])
    op.create_index('ix_student_card_review_logs_card_id', 'student_card_review_logs', ['card_id'])

    # 6. mistake_notebook_entries
    op.create_table(
        'mistake_notebook_entries',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('source_type', sa.String(length=50), nullable=False, server_default='manual'),
        sa.Column('source_id', sa.String(length=100), nullable=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('question_context', sa.Text(), nullable=True),
        sa.Column('submitted_answer', sa.Text(), nullable=True),
        sa.Column('expected_answer', sa.Text(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('tags', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='[]'),
        sa.Column('is_resolved', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_mistake_notebook_entries_user_id', 'mistake_notebook_entries', ['user_id'])
    op.create_index('ix_mistake_notebook_entries_is_resolved', 'mistake_notebook_entries', ['is_resolved'])

    # 7. peer_discussion_threads (Module O: FEAT-277..292)
    op.create_table(
        'peer_discussion_threads',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('category', sa.String(length=100), nullable=False, server_default='General'),
        sa.Column('context_type', sa.String(length=50), nullable=True),
        sa.Column('context_id', sa.String(length=100), nullable=True),
        sa.Column('upvotes', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('reply_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_resolved', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='OPEN'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_peer_discussion_threads_user_id', 'peer_discussion_threads', ['user_id'])
    op.create_index('ix_peer_discussion_threads_category', 'peer_discussion_threads', ['category'])
    op.create_index('ix_peer_discussion_threads_created_at', 'peer_discussion_threads', ['created_at'])

    # 8. peer_discussion_replies
    op.create_table(
        'peer_discussion_replies',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('thread_id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('code_snippet', sa.Text(), nullable=True),
        sa.Column('upvotes', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_accepted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='ACTIVE'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['thread_id'], ['peer_discussion_threads.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_peer_discussion_replies_thread_id', 'peer_discussion_replies', ['thread_id'])
    op.create_index('ix_peer_discussion_replies_user_id', 'peer_discussion_replies', ['user_id'])

    # 9. peer_study_groups
    op.create_table(
        'peer_study_groups',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('creator_id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('goal_description', sa.String(length=255), nullable=True),
        sa.Column('is_private', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('invite_code', sa.String(length=32), nullable=True),
        sa.Column('member_count', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['creator_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('invite_code')
    )
    op.create_index('ix_peer_study_groups_creator_id', 'peer_study_groups', ['creator_id'])

    # 10. peer_study_group_members
    op.create_table(
        'peer_study_group_members',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('group_id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('role', sa.String(length=30), nullable=False, server_default='MEMBER'),
        sa.Column('joined_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['group_id'], ['peer_study_groups.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('group_id', 'user_id', name='uq_study_group_members_group_user')
    )
    op.create_index('ix_peer_study_group_members_group_id', 'peer_study_group_members', ['group_id'])
    op.create_index('ix_peer_study_group_members_user_id', 'peer_study_group_members', ['user_id'])

    # 11. user_notifications (Module P: FEAT-293..308)
    op.create_table(
        'user_notifications',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=False, server_default='GENERAL'),
        sa.Column('urgency', sa.String(length=20), nullable=False, server_default='NORMAL'),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('action_url', sa.String(length=500), nullable=True),
        sa.Column('payload', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('is_read', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('read_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_user_notifications_user_id', 'user_notifications', ['user_id'])
    op.create_index('ix_user_notifications_category', 'user_notifications', ['category'])
    op.create_index('ix_user_notifications_user_unread', 'user_notifications', ['user_id', 'is_read', 'created_at'])

    # 12. user_notification_preferences
    op.create_table(
        'user_notification_preferences',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('in_app_enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('email_enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('push_enabled', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('category_overrides', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('quiet_hours_start', sa.String(length=5), nullable=True),
        sa.Column('quiet_hours_end', sa.String(length=5), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )


def downgrade():
    op.drop_table('user_notification_preferences')
    op.drop_table('user_notifications')
    op.drop_table('peer_study_group_members')
    op.drop_table('peer_study_groups')
    op.drop_table('peer_discussion_replies')
    op.drop_table('peer_discussion_threads')
    op.drop_table('mistake_notebook_entries')
    op.drop_table('student_card_review_logs')
    op.drop_table('revision_focus_sessions')
    op.drop_table('student_card_reviews')
    op.drop_table('flashcard_items')
    op.drop_table('flashcard_decks')
    op.drop_column('student_profiles', 'timezone')
