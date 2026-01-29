from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, func
from sqlalchemy.orm import relationship
from app.db.session import Base

class Test(Base):
    __tablename__ = "tests"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(300), nullable=False)
    description = Column(Text, nullable=True)
    time_limit_minutes = Column(Integer, nullable=True)
    max_score = Column(Integer, nullable=True)
    published = Column(Boolean, default=False, nullable=False)
    published_at = Column(DateTime, server_default=func.now(), nullable=True)
    material_id = Column(Integer, ForeignKey("materials.id"), nullable=True, index=True)

    # Material.tests <-> Test.material
    material = relationship(
        "Material",
        back_populates="tests",
        lazy="selectin",
    )

    # Test.questions <-> Question.test
    questions = relationship(
        "Question",
        back_populates="test",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
