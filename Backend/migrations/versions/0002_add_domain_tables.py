"""add domain tables

Revision ID: 0002_add_domain_tables
Revises: 0001_initial
Create Date: 2026-01-16 00:10:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = "0002_add_domain_tables"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "materials",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(length=300), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("content_url", sa.String(length=1000), nullable=True),
        sa.Column("published_at", sa.DateTime(), server_default=sa.text("now()"), nullable=True),
        sa.Column("author_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
    )

    op.create_table(
        "tests",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(length=300), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("time_limit_minutes", sa.Integer(), nullable=True),
        sa.Column("max_score", sa.Integer(), nullable=True),
        sa.Column("published", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("published_at", sa.DateTime(), server_default=sa.text("now()"), nullable=True),
        sa.Column("material_id", sa.Integer(), sa.ForeignKey("materials.id"), nullable=True),
    )

    op.create_table(
        "questions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("test_id", sa.Integer(), sa.ForeignKey("tests.id"), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("options", sa.Text(), nullable=True),
        sa.Column("correct_answer", sa.Text(), nullable=True),
        sa.Column("points", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column("is_open_answer", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )

    op.create_table(
        "answers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("test_id", sa.Integer(), sa.ForeignKey("tests.id"), nullable=False),
        sa.Column("question_id", sa.Integer(), sa.ForeignKey("questions.id"), nullable=False),
        sa.Column("answer_payload", sa.Text(), nullable=True),
        sa.Column("score", sa.Float(), nullable=True),
        sa.Column("graded_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("graded_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=True),
    )

    op.create_table(
        "levels",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("required_points", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("description", sa.Text(), nullable=True),
    )

    op.create_table(
        "analytics",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False, unique=True),
        sa.Column("total_points", sa.Float(), nullable=True, server_default="0"),
        sa.Column("tests_taken", sa.Integer(), nullable=True, server_default="0"),
        sa.Column("last_active", sa.DateTime(), nullable=True),
        sa.Column("streak_days", sa.Integer(), nullable=True, server_default="0"),
        sa.Column("current_level_id", sa.Integer(), sa.ForeignKey("levels.id"), nullable=True),
    )


def downgrade():
    op.drop_table("analytics")
    op.drop_table("levels")
    op.drop_table("answers")
    op.drop_table("questions")
    op.drop_table("tests")
    op.drop_table("materials")
