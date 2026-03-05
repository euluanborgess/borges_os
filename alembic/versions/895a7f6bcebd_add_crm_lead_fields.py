"""add crm lead fields

Revision ID: 895a7f6bcebd
Revises: b1e8bce99663
Create Date: 2026-03-04 23:34:19.006938

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '895a7f6bcebd'
down_revision: Union[str, Sequence[str], None] = 'b1e8bce99663'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('leads', sa.Column('email', sa.String(), nullable=True))
    op.add_column('leads', sa.Column('origin', sa.String(), nullable=True, server_default='whatsapp'))
    op.add_column('leads', sa.Column('responsible', sa.String(), nullable=True))
    op.add_column('leads', sa.Column('next_step', sa.String(), nullable=True))
    op.add_column('leads', sa.Column('estimated_value', sa.Float(), nullable=True, server_default='0'))
    op.add_column('leads', sa.Column('closed_value', sa.Float(), nullable=True, server_default='0'))
    op.add_column('leads', sa.Column('last_contact_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('leads', 'last_contact_at')
    op.drop_column('leads', 'closed_value')
    op.drop_column('leads', 'estimated_value')
    op.drop_column('leads', 'next_step')
    op.drop_column('leads', 'responsible')
    op.drop_column('leads', 'origin')
    op.drop_column('leads', 'email')
