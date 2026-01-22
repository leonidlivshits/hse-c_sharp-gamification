from sqlalchemy import Column, Integer, Text, Float, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from app.db.session import Base

class Answer(Base):
    __tablename__ = "answers"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    test_id = Column(Integer, ForeignKey("tests.id"), nullable=False, index=True)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False, index=True)
    answer_payload = Column(Text, nullable=True)  # MCQ: choice.id as string; open: free text
    score = Column(Float, nullable=True)
    graded_by = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    graded_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=True)

    # relationships (explicit foreign_keys to avoid ambiguity)
    user = relationship(
        "User",
        back_populates="answers",
        foreign_keys=[user_id],
        lazy="selectin",
    )

    grader = relationship(
        "User",
        back_populates="graded_answers",
        foreign_keys=[graded_by],
        lazy="selectin",
    )

    question = relationship(
        "Question",
        back_populates="answers",
        foreign_keys=[question_id],
        lazy="selectin",
    )
