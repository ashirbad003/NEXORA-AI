"""phase_4_topic_feedback_table

Revision ID: 74a123b456cd
Revises: 639a0bda8ebc
Create Date: 2026-11-20 17:35:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '74a123b456cd'
down_revision: Union[str, Sequence[str], None] = '639a0bda8ebc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.create_table(
        'topic_feedback',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('module_id', sa.String(length=36), nullable=False),
        sa.Column('difficulty_rating', sa.Integer(), nullable=False),
        sa.Column('confusing_sections', sa.Text(), nullable=True),
        sa.Column('feedback_text', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['module_id'], ['learning_modules.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_topic_feedback_module_id'), 'topic_feedback', ['module_id'], unique=False)
    op.create_index(op.f('ix_topic_feedback_user_id'), 'topic_feedback', ['user_id'], unique=False)

def downgrade() -> None:
    op.drop_index(op.f('ix_topic_feedback_user_id'), table_name='topic_feedback')
    op.drop_index(op.f('ix_topic_feedback_module_id'), table_name='topic_feedback')
    op.drop_table('topic_feedback')
