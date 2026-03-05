"""add lead channel and unread_count

Revision ID: b1e8bce99663
Revises: 4986cb506276
Create Date: 2026-03-04 22:25:14.375792

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b1e8bce99663'
down_revision: Union[str, Sequence[str], None] = '4986cb506276'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Added for multichannel inbox + unread tracking
    op.add_column('leads', sa.Column('channel', sa.String(), nullable=True, server_default='whatsapp'))
    op.add_column('leads', sa.Column('unread_count', sa.Integer(), nullable=True, server_default='0'))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('leads', 'unread_count')
    op.drop_column('leads', 'channel')
