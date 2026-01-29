from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.session import Base

class Analytics(Base):
    __tablename__ = "analytics"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True, index=True)
    total_points = Column(Float, default=0.0)
    tests_taken = Column(Integer, default=0)
    last_active = Column(DateTime, nullable=True)
    streak_days = Column(Integer, default=0)
    current_level_id = Column(Integer, ForeignKey("levels.id"), nullable=True)

    user = relationship("User", back_populates="analytics", lazy="selectin")
    level = relationship("Level", lazy="selectin")
