from sqlalchemy import Column, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base


class Profile(Base):
    """Модель SQLAlchemy для таблицы профилей."""
    __tablename__ = "profiles"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    profile_type = Column(String, nullable=False)
    user_id = Column(
        String,
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
