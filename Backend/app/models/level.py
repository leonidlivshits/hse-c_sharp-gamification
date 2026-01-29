"""
DESCRIPTION: Level entity (mapping points -> level).
Fields: id, name, required_points, description
"""
from sqlalchemy import Column, Integer, String, Text
from app.db.session import Base

class Level(Base):
    __tablename__ = "levels"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    required_points = Column(Integer, nullable=False, default=0)
    description = Column(Text, nullable=True)
