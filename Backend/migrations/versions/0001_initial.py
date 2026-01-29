"""initial

Revision ID: 0001_initial
Revises: 
Create Date: 2026-01-16 20:25:06.0646285

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("username", sa.String(length=100), nullable=False, unique=True, index=True),
        sa.Column("full_name", sa.String(length=200), nullable=True),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=50), nullable=False, server_default="user"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=True),
    )
    # Add indexes explicitly if desired (create_index not directly in op.create_table signature)
    op.create_index("ix_users_username", "users", ["username"], unique=False)


def downgrade():
    op.drop_index("ix_users_username", table_name="users")
    op.drop_table("users")
