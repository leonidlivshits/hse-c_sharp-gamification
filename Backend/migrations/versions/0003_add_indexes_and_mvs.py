"""add indexes and materialized views

Revision ID: 0003_add_indexes_and_mvs
Revises: 0002_add_domain_tables
Create Date: 2026-01-21 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = "0003_add_indexes_and_mvs"
down_revision = "0002_add_domain_tables"
branch_labels = None
depends_on = None

def upgrade():
    # Indexes
    op.create_index("ix_tests_published", "tests", ["published"])
    op.create_index("ix_questions_test_id", "questions", ["test_id"])
    op.create_index("ix_choices_question_id", "choices", ["question_id"])
    op.create_index("ix_answers_test_id", "answers", ["test_id"])
    op.create_index("ix_answers_question_id", "answers", ["question_id"])
    op.create_index("ix_answers_user_test", "answers", ["user_id", "test_id"])
    op.create_index("ix_answers_created_at", "answers", ["created_at"])
    op.create_index("ix_analytics_user_id", "analytics", ["user_id"], unique=True)

    # Materialized view: leaderboard
    op.execute("""
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_leaderboard AS
    SELECT a.user_id, u.username, a.total_points
    FROM analytics a
    JOIN users u ON u.id = a.user_id
    ORDER BY a.total_points DESC;
    """)
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS ux_mv_leaderboard_user_id ON mv_leaderboard (user_id);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_mv_leaderboard_points ON mv_leaderboard (total_points DESC);")

    # Materialized view: test summary (aggregated answers per test)
    op.execute("""
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_test_summary AS
    SELECT t.id as test_id,
           count(distinct q.id) as total_questions,
           count(a.id) as total_attempts,
           avg(a.score) as avg_score
    FROM tests t
    LEFT JOIN questions q ON q.test_id = t.id
    LEFT JOIN answers a ON a.test_id = t.id
    GROUP BY t.id;
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_mv_test_summary_test_id ON mv_test_summary (test_id);")

    # Materialized view: per-question stats
    op.execute("""
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_question_stats AS
    SELECT q.id as question_id,
           count(a.id) as attempts,
           avg(a.score) as avg_score,
           count(distinct a.user_id) as distinct_users
    FROM questions q
    LEFT JOIN answers a ON a.question_id = q.id
    GROUP BY q.id;
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_mv_question_stats_qid ON mv_question_stats (question_id);")

def downgrade():
    op.execute("DROP MATERIALIZED VIEW IF EXISTS mv_question_stats;")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS mv_test_summary;")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS mv_leaderboard;")
    op.drop_index("ix_mv_question_stats_qid", table_name=None)
    op.drop_index("ix_mv_test_summary_test_id", table_name=None)
    op.drop_index("ix_mv_leaderboard_points", table_name=None)
    op.drop_index("ux_mv_leaderboard_user_id", table_name=None)

    # drop indexes created
    op.drop_index("ix_answers_created_at", table_name="answers")
    op.drop_index("ix_answers_user_test", table_name="answers")
    op.drop_index("ix_answers_question_id", table_name="answers")
    op.drop_index("ix_answers_test_id", table_name="answers")
    op.drop_index("ix_choices_question_id", table_name="choices")
    op.drop_index("ix_questions_test_id", table_name="questions")
    op.drop_index("ix_tests_published", table_name="tests")
    op.drop_index("ix_analytics_user_id", table_name="analytics")
