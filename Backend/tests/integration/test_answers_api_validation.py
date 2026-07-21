import json

import pytest

from app.core.security import get_password_hash
from app.models.user import User

pytestmark = pytest.mark.asyncio


class _FakeRedis:
    def __init__(self):
        self.rpush_calls: list[tuple[str, str]] = []

    async def rpush(self, queue_name: str, payload: str):
        self.rpush_calls.append((queue_name, payload))


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def login(client, username: str, password: str) -> str:
    response = await client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": password},
    )
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


async def seed_user(db, *, username: str, password: str, role: str) -> User:
    user = User(
        username=username,
        password_hash=get_password_hash(password),
        role=role,
    )
    db.add(user)
    await db.flush()
    return user


async def _create_test(client, token: str, *, title: str) -> dict:
    response = await client.post(
        "/api/v1/tests/",
        headers=auth_headers(token),
        json={"title": title, "published": True, "max_attempts": 2},
    )
    assert response.status_code == 201, response.text
    return response.json()


async def _create_open_question(client, token: str, *, test_id: int, text: str) -> dict:
    response = await client.post(
        "/api/v1/questions/",
        headers=auth_headers(token),
        json={
            "test_id": test_id,
            "text": text,
            "points": 3.0,
            "is_open_answer": True,
            "choices": [],
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


async def _create_mcq_question(client, token: str, *, test_id: int, text: str) -> dict:
    response = await client.post(
        "/api/v1/questions/",
        headers=auth_headers(token),
        json={
            "test_id": test_id,
            "text": text,
            "points": 2.0,
            "is_open_answer": False,
            "choices": [
                {"value": "Correct", "ordinal": 1, "is_correct": True},
                {"value": "Wrong", "ordinal": 2, "is_correct": False},
            ],
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


async def _start_attempt(client, token: str, test_id: int) -> dict:
    response = await client.post(
        f"/api/v1/tests/{test_id}/attempts/start",
        headers=auth_headers(token),
    )
    assert response.status_code == 201, response.text
    return response.json()


async def test_answers_api_accepts_blank_open_payload_as_skipped(client, db):
    teacher = await seed_user(db, username="answers_blank_teacher@example.com", password="teach123", role="teacher")
    student = await seed_user(db, username="answers_blank_student@example.com", password="stud123", role="user")

    teacher_token = await login(client, teacher.username, "teach123")
    student_token = await login(client, student.username, "stud123")

    created_test = await _create_test(client, teacher_token, title="Blank open payload")
    question = await _create_open_question(
        client,
        teacher_token,
        test_id=created_test["id"],
        text="Explain interfaces",
    )
    attempt = await _start_attempt(client, student_token, created_test["id"])

    response = await client.post(
        "/api/v1/answers/",
        headers=auth_headers(student_token),
        json={
            "test_id": created_test["id"],
            "attempt_id": attempt["id"],
            "question_id": question["id"],
            "answer_payload": "   ",
        },
    )
    assert response.status_code == 201, response.text
    payload = response.json()
    assert payload["score"] == 0.0

    pending = await client.get("/api/v1/answers/pending/open", headers=auth_headers(teacher_token))
    assert pending.status_code == 200, pending.text
    pending_ids = {item["id"] for item in pending.json()}
    assert payload["id"] not in pending_ids


async def test_answers_api_accepts_null_closed_payload_as_skipped(client, db):
    teacher = await seed_user(db, username="answers_null_teacher@example.com", password="teach123", role="teacher")
    student = await seed_user(db, username="answers_null_student@example.com", password="stud123", role="user")

    teacher_token = await login(client, teacher.username, "teach123")
    student_token = await login(client, student.username, "stud123")

    created_test = await _create_test(client, teacher_token, title="Null closed payload")
    question = await _create_mcq_question(
        client,
        teacher_token,
        test_id=created_test["id"],
        text="Pick one",
    )
    attempt = await _start_attempt(client, student_token, created_test["id"])

    response = await client.post(
        "/api/v1/answers/",
        headers=auth_headers(student_token),
        json={
            "test_id": created_test["id"],
            "attempt_id": attempt["id"],
            "question_id": question["id"],
            "answer_payload": "null",
        },
    )
    assert response.status_code == 201, response.text
    payload = response.json()
    assert payload["score"] == 0.0


async def test_submit_attempt_batches_answers_and_completes_attempt(client, db):
    teacher = await seed_user(db, username="answers_batch_teacher@example.com", password="teach123", role="teacher")
    student = await seed_user(db, username="answers_batch_student@example.com", password="stud123", role="user")

    teacher_token = await login(client, teacher.username, "teach123")
    student_token = await login(client, student.username, "stud123")

    created_test = await _create_test(client, teacher_token, title="Batch submit payload")
    first_question = await _create_mcq_question(
        client,
        teacher_token,
        test_id=created_test["id"],
        text="First MCQ",
    )
    second_question = await _create_mcq_question(
        client,
        teacher_token,
        test_id=created_test["id"],
        text="Second MCQ",
    )
    attempt = await _start_attempt(client, student_token, created_test["id"])

    submit_response = await client.post(
        f"/api/v1/tests/attempts/{attempt['id']}/submit",
        headers=auth_headers(student_token),
        json={
            "answers": [
                {
                    "question_id": first_question["id"],
                    "answer_payload": str(first_question["choices"][0]["id"]),
                },
                {
                    "question_id": second_question["id"],
                    "answer_payload": str(second_question["choices"][0]["id"]),
                },
            ]
        },
    )
    assert submit_response.status_code == 200, submit_response.text
    submit_payload = submit_response.json()
    assert submit_payload["id"] == attempt["id"]
    assert submit_payload["status"] == "completed"

    quota_response = await client.get(
        f"/api/v1/tests/{created_test['id']}/attempts/quota",
        headers=auth_headers(student_token),
    )
    assert quota_response.status_code == 200, quota_response.text
    quota_payload = quota_response.json()
    assert quota_payload["completed_attempts"] == 1
    assert quota_payload["remaining_attempts"] == 1

    answers_response = await client.get(
        f"/api/v1/answers/test/{created_test['id']}",
        headers=auth_headers(student_token),
    )
    assert answers_response.status_code == 200, answers_response.text
    assert len(answers_response.json()) == 2


async def test_submit_attempt_enqueues_attempt_complete_postprocess_job(client, db, monkeypatch):
    from app.services import test_attempt_api_service

    teacher = await seed_user(db, username="answers_queue_teacher@example.com", password="teach123", role="teacher")
    student = await seed_user(db, username="answers_queue_student@example.com", password="stud123", role="user")

    teacher_token = await login(client, teacher.username, "teach123")
    student_token = await login(client, student.username, "stud123")

    created_test = await _create_test(client, teacher_token, title="Attempt complete queue")
    question = await _create_mcq_question(
        client,
        teacher_token,
        test_id=created_test["id"],
        text="Queue event question",
    )
    attempt = await _start_attempt(client, student_token, created_test["id"])

    fake_redis = _FakeRedis()
    monkeypatch.setattr(test_attempt_api_service, "get_redis_client", lambda: fake_redis)

    submit_response = await client.post(
        f"/api/v1/tests/attempts/{attempt['id']}/submit",
        headers=auth_headers(student_token),
        json={
            "answers": [
                {
                    "question_id": question["id"],
                    "answer_payload": str(question["choices"][0]["id"]),
                },
            ]
        },
    )
    assert submit_response.status_code == 200, submit_response.text

    queue_payloads = [
        payload
        for queue_name, payload in fake_redis.rpush_calls
        if queue_name == "answers:postprocess"
    ]
    assert queue_payloads, "attempt completion must enqueue deferred postprocess job"

    last_payload = json.loads(queue_payloads[-1])
    assert last_payload["job_type"] == "attempt_complete"
    assert int(last_payload["user_id"]) == int(student.id)
    assert int(last_payload["test_id"]) == int(created_test["id"])
    assert int(last_payload["attempt_id"]) == int(attempt["id"])
    assert int(last_payload["answers_count"]) == 1
    assert float(last_payload["points_delta"]) == 2.0
