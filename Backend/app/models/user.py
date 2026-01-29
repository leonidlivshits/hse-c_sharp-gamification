# app/models/user.py
from sqlalchemy import Column, Integer, String, DateTime, func
from sqlalchemy.orm import relationship
from app.db.session import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    full_name = Column(String(200), nullable=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), default="user", nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    # answers authored by this user (Answer.user_id)
    answers = relationship(
        "Answer",
        back_populates="user",
        foreign_keys="Answer.user_id",  # string form avoids import cycles
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    # answers that this user graded (Answer.graded_by)
    graded_answers = relationship(
        "Answer",
        back_populates="grader",
        foreign_keys="Answer.graded_by",
        lazy="selectin",
    )

    # materials authored by this user
    materials = relationship(
        "Material",
        back_populates="author",
        lazy="selectin",
    )

    # analytics (one-to-one)
    analytics = relationship(
        "Analytics",
        back_populates="user",
        uselist=False,
        lazy="selectin",
    )
