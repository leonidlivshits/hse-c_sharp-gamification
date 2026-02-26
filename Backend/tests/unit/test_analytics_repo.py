# tests/unit/test_analytics_repo.py
import pytest
pytestmark = pytest.mark.asyncio
from app.models.user import User
from app.repositories import analytics_repo

@pytest.mark.asyncio
async def test_create_or_update_analytics_and_leaderboard(db):
    # create two users
    u1 = User(username="a", password_hash="x", full_name="A", role="user")
    u2 = User(username="b", password_hash="x", full_name="B", role="user")
    db.add_all([u1, u2])
    await db.flush()

    # add points
    a1 = await analytics_repo.create_or_update_analytics(db, u1.id, points_delta=10.0, mark_active=True)
    a2 = await analytics_repo.create_or_update_analytics(db, u2.id, points_delta=5.0, mark_active=True)

    assert a1.total_points >= 10.0
    assert a2.total_points >= 5.0

    lb = await analytics_repo.get_leaderboard(db, limit=10)
    assert isinstance(lb, list)
    # first entry should be present u1 (10 points)
    assert any(entry["id"] == u1.id for entry in lb)
    # ordering by total_points desc (if at least 2 rows)
    if len(lb) >= 2:
        assert lb[0]["total_points"] >= lb[1]["total_points"]
