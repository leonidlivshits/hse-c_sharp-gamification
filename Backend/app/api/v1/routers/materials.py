"""
app/api/v1/routers/materials.py
DESCRIPTION: placeholder router for materials. Fill with actual logic later.
"""
from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def list_materials():
    return [{"id": 1, "title": "Welcome material (placeholder)"}]
