from sqlalchemy import Column, String, Float, ForeignKey, DateTime, JSON, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base
from .job import Job # Import the Job model


class Bid(Base):
    __tablename__ = "bids"

    id = Column(String, primary_key=True, index=True)
    profile_id = Column(String, ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id"), nullable=False) # Changed to ForeignKey
    amount = Column(Float, nullable=False)
    submitted_at = Column(DateTime, default=datetime.utcnow)
    prompt_template_id = Column(Integer, ForeignKey("ai_prompts.id"), nullable=True) # Changed to Integer
    generated_bid_text = Column(String, nullable=True)
    bid_settings_snapshot = Column(JSON, nullable=True)

    profile = relationship("Profile", backref="bids")
    job = relationship("Job", backref="bids") # Added relationship to Job
