"""
app/api/v1/routers/tests.py
DESCRIPTION: placeholder router for tests.
"""
from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def list_tests():
    return [{"id": 1, "title": "Sample test (placeholder)"}]
