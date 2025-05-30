from sqlalchemy import Column, Integer, String, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.db.base import Base


class AIPrompt(Base):
    __tablename__ = "ai_prompts"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(String, ForeignKey("profiles.id"), nullable=False)
    name = Column(String, nullable=False)
    prompt_text = Column(String, nullable=False)
    is_active = Column(Boolean, default=False)

    profile = relationship(
        "app.models.profile.Profile",
        back_populates="prompts")
