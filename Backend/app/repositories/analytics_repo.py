from sqlalchemy import desc, func, select, insert, text, update
from Backend.app.models.answer import Answer
from Backend.app.models.level import Level
from Backend.app.models.user import User
from app.models.analytics import Analytics

async def get_analytics_for_user(session, user_id: int):
    q = select(Analytics).where(Analytics.user_id == user_id)
    res = await session.execute(q)
    return res.scalars().first()

async def create_or_update_analytics(session, user_id: int, points_delta: float = 0.0):
    # naive
    item = await get_analytics_for_user(session, user_id)
    if not item:
        item = Analytics(user_id=user_id, total_points=points_delta, tests_taken=1 if points_delta else 0)
        session.add(item)
        await session.commit()
        await session.refresh(item)
        return item
    item.total_points = (item.total_points or 0.0) + points_delta
    item.tests_taken = (item.tests_taken or 0) + (1 if points_delta else 0)
    await session.commit()
    await session.refresh(item)
    return item


async def get_user_analytics(session, user_id: int):
    q = select(Analytics).where(Analytics.user_id == user_id)
    res = await session.execute(q)
    return res.scalars().first()

async def get_leaderboard(session, limit: int = 50, offset: int = 0):
    """
    Leaderboard by total_points (Analytics).
    """
    q = select(User.id, User.username, Analytics.total_points).join(Analytics, Analytics.user_id == User.id).order_by(desc(Analytics.total_points)).limit(limit).offset(offset)
    res = await session.execute(q)
    return [dict(row) for row in res.all()]

async def users_below_level(session, level_id: int):
    """
    Return users whose total_points < required_points for the given level.
    """
    lvl = await session.get(Level, level_id)
    if not lvl:
        return []
    req = lvl.required_points
    q = select(User).join(Analytics, Analytics.user_id == User.id).where(Analytics.total_points < req)
    res = await session.execute(q)
    return res.scalars().all()

async def users_reached_level(session, level_id: int):
    q = select(User).join(Analytics, Analytics.user_id == User.id).where(Analytics.current_level_id == level_id)
    res = await session.execute(q)
    return res.scalars().all()

async def question_statistics(session, question_id: int):
    """
    Per-question statistics:
    - attempts: total answers
    - avg_score
    - correct_count (for MCQ where answer_payload == choice.id)
    - correct_rate (correct / attempts)
    - distinct_users
    """
    attempts = await session.scalar(select(func.count(Answer.id)).where(Answer.question_id == question_id))
    avg_score = await session.scalar(select(func.avg(Answer.score)).where(Answer.question_id == question_id))
    distinct_users = await session.scalar(select(func.count(func.distinct(Answer.user_id))).where(Answer.question_id == question_id))

    # Correct detection: attempt to compute for MCQ by comparing payload to choice.is_correct
    # We rely on payload storing choice.id as text — this needs convention.
    correct_q = text(
        """
        SELECT COUNT(a.id) FROM answers a
        JOIN choices c ON c.id::text = a.answer_payload
        WHERE a.question_id = :qid AND c.is_correct = true
        """
    )
    conn = await session.connection()
    res = await conn.execute(correct_q, {"qid": question_id})
    correct_count = res.scalar_one_or_none() or 0

    correct_rate = (correct_count / attempts) if attempts and attempts > 0 else None

    return {
        "question_id": question_id,
        "attempts": attempts or 0,
        "avg_score": float(avg_score) if avg_score is not None else None,
        "correct_count": int(correct_count),
        "correct_rate": float(correct_rate) if correct_rate is not None else None,
        "distinct_users": distinct_users or 0,
    }

async def average_score_per_test(session, test_id: int):
    q = select(func.avg(Answer.score)).where(Answer.test_id == test_id)
    avg_ = await session.scalar(q)
    return float(avg_) if avg_ is not None else None

async def daily_active_users(session, days: int = 7):
    """
    DAU over last N days: returns list of (day, dau_count)
    Assumes Answer.created_at is present and stores activity time. Could also use last_active in analytics.
    """
    # raw SQL for convenience
    raw = text(
        """
        SELECT date_trunc('day', created_at) as day, count(DISTINCT user_id) as dau
        FROM answers
        WHERE created_at >= now() - interval ':days days'
        GROUP BY day
        ORDER BY day DESC
        """
    )
    conn = await session.connection()
    res = await conn.execute(raw, {"days": days})
    return [{"day": row["day"], "dau": row["dau"]} for row in res.fetchall()]

async def retention_cohort(session, start_date: str, period_days: int = 7, windows: int = 4):
    """
    Example cohort analysis skeleton: returns counts of users in cohort who return in subsequent windows.
    start_date: 'YYYY-MM-DD' (string) - cohort start day
    period_days: cohort size (days)
    windows: how many windows to compute (e.g., 4)
    Implementation note: this uses SQL windowing and date_trunc; could be moved to materialized view.
    """
    sql = text(
        """
        WITH cohort AS (
          SELECT DISTINCT user_id
          FROM answers
          WHERE created_at >= :start_date::date
            AND created_at < (:start_date::date + (:period_days || ' days')::interval)
        ), activity AS (
          SELECT user_id, date_trunc('day', created_at) as day
          FROM answers
          WHERE created_at >= :start_date::date
        )
        SELECT c.user_id,
          array_agg(distinct a.day) as active_days
        FROM cohort c
        LEFT JOIN activity a ON a.user_id = c.user_id
        GROUP BY c.user_id
        """
    )
    conn = await session.connection()
    res = await conn.execute(sql, {"start_date": start_date, "period_days": period_days})
    rows = res.fetchall()
    # Post-process into retention windows (simple example)
    # this is a skeleton — implement exact retention windows as required
    return [{"user_id": r["user_id"], "active_days": r["active_days"]} for r in rows]