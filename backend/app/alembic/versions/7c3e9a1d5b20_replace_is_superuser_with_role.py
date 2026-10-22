"""Replace is_superuser with role

Revision ID: 7c3e9a1d5b20
Revises: fe56fa70289e
Create Date: 2026-10-22 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7c3e9a1d5b20'
down_revision = 'fe56fa70289e'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'user',
        sa.Column('role', sa.String(length=20), nullable=False, server_default='member'),
    )
    op.execute("UPDATE \"user\" SET role = 'admin' WHERE is_superuser")
    op.drop_column('user', 'is_superuser')


def downgrade():
    # Managers have no equivalent in the old model and become regular users
    op.add_column(
        'user',
        sa.Column('is_superuser', sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.execute("UPDATE \"user\" SET is_superuser = TRUE WHERE role = 'admin'")
    op.alter_column('user', 'is_superuser', server_default=None)
    op.drop_column('user', 'role')
