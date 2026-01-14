"""
app/models/user.py
DESCRIPTION: SQLAlchemy model for users (simple fields for demo).
TODO: Extend with indexes, constraints and relationships.
"""
from sqlalchemy import Column, Integer, String, DateTime, func
from app.db.session import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    full_name = Column(String(200), nullable=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), default="user", nullable=False)
    created_at = Column(DateTime, server_default=func.now())
