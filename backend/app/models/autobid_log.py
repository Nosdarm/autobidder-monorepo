from sqlalchemy import (Column, Integer, String, Float,
                        ForeignKey, DateTime, Text)
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class AutobidLog(Base):
    __tablename__ = "autobid_logs"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("profiles.id"), nullable=False)
    job_title = Column(String, nullable=False)
    job_link = Column(String, nullable=False)
    bid_text = Column(Text, nullable=True)
    status = Column(String, default="pending")  # success / failed / skipped
    score = Column(Float)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    profile = relationship(
        "app.models.profile.Profile",
        back_populates="autobid_logs")
