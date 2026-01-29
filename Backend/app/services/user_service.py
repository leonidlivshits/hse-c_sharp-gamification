"""
app/services/user_service.py
DESCRIPTION: business logic for users. Password hashing done here (passlib).
"""
from passlib.context import CryptContext
from app.repositories import user_repo

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

async def register_user(session, username: str, password: str, full_name: str | None = None):
    existing = await user_repo.get_user_by_username(session, username)
    if existing:
        raise ValueError("username already exists")
    pw_hash = hash_password(password)
    return await user_repo.create_user(session, username, pw_hash, full_name)
