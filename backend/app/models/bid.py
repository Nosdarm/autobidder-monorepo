from sqlalchemy import Column, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class Bid(Base):
    __tablename__ = "bids"

    id = Column(String, primary_key=True, index=True)
    profile_id = Column(
        String,
        ForeignKey(
            "profiles.id",
            ondelete="CASCADE"),
        nullable=False)
    job_id = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    submitted_at = Column(DateTime, default=datetime.utcnow)

    profile = relationship("Profile", backref="bids")
