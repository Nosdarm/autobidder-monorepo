"""add_job_model_and_extend_bid_profile_models

Revision ID: 43b4ac944f63
Revises: c781b2273045
Create Date: 2025-05-25 07:57:54.460398

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '43b4ac944f63'
down_revision: Union[str, None] = 'c781b2273045'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
