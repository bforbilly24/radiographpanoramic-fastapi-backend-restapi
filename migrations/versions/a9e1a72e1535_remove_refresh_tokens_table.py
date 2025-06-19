"""remove refresh_tokens table

Revision ID: a9e1a72e1535
Revises: 1fcfe7ae7ab2
Create Date: 2025-04-24 23:43:43.286606

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a9e1a72e1535'
down_revision: Union[str, None] = '1fcfe7ae7ab2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade():
    # Hapus tabel refresh_tokens
    op.drop_table('refresh_tokens')

def downgrade():
    # Buat kembali tabel refresh_tokens jika migrasi dibatalkan
    op.create_table(
        'refresh_tokens',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('user_id', sa.Integer, sa.ForeignKey('users.id'), nullable=False),
        sa.Column('token', sa.String, nullable=False, unique=True),
        sa.Column('expires_at', sa.DateTime, nullable=False),
        sa.Column('created_at', sa.DateTime, nullable=False),
    )