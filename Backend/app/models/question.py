from sqlalchemy import Column, Integer, Text, Boolean, Float, ForeignKey
from sqlalchemy.orm import relationship
from app.db.session import Base

class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    test_id = Column(Integer, ForeignKey("tests.id"), nullable=False, index=True)
    text = Column(Text, nullable=False)
    points = Column(Float, default=1.0, nullable=False)
    is_open_answer = Column(Boolean, default=False, nullable=False)

    # Question.test <-> Test.questions
    test = relationship(
        "Test",
        back_populates="questions",
        lazy="selectin",
    )

    # Question.choices <-> Choice.question
    choices = relationship(
        "Choice",
        back_populates="question",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    # Question.answers <-> Answer.question
    answers = relationship(
        "Answer",
        back_populates="question",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
