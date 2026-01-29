from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.db.session import Base

class Choice(Base):
    __tablename__ = "choices"

    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("questions.id", ondelete="CASCADE"), nullable=False, index=True)
    value = Column(String(1000), nullable=False)
    ordinal = Column(Integer, nullable=True)
    is_correct = Column(Boolean, nullable=False, default=False)

    # Choice.question <-> Question.choices
    question = relationship(
        "Question",
        back_populates="choices",
        lazy="selectin",
    )
