from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.db.session import Base

class Material(Base):
    __tablename__ = "materials"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(300), nullable=False, index=True)
    description = Column(Text, nullable=True)
    content_url = Column(String(1000), nullable=True)
    published_at = Column(DateTime, server_default=func.now(), nullable=True)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)

    # relation to User.author <-> User.materials
    author = relationship(
        "User",
        back_populates="materials",
        lazy="selectin",
    )

    # relation to Test.material <-> Material.tests
    tests = relationship(
        "Test",
        back_populates="material",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
