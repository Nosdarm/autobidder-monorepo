import uuid # Added import
from sqlalchemy import Column, String, Boolean, ForeignKey, JSON, Integer # Added JSON
from sqlalchemy.dialects.postgresql import JSON # Explicit import for clarity if needed, though sqlalchemy.JSON often suffices
from sqlalchemy.orm import relationship

from app.db.base import Base


class Profile(Base):
    """Модель SQLAlchemy для таблицы профилей."""
    __tablename__ = "profiles"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    profile_type = Column(String, nullable=False)
    user_id = Column(
        Integer, # Changed from String to Integer
        ForeignKey(
            "users.id",
            ondelete="CASCADE"),
        nullable=False)
    skills = Column(JSON, nullable=True)
    experience_level = Column(String, nullable=True)

    autobid_enabled = Column(Boolean, default=False)

    autobid_logs = relationship(
        "AutobidLog",
        back_populates="profile",
        cascade="all, delete")
    prompts = relationship(
        "AIPrompt",
        back_populates="profile",
        cascade="all, delete")
    owner = relationship("User", back_populates="profiles")

    def __repr__(self):

        return (
            f"<Profile(id='{self.id}', name='{self.name}', "
            f"type='{self.profile_type}')>"
        )
