from sqlalchemy import Column, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship # Keep for potential future use, even if not used now
from datetime import datetime
from app.database import Base

class ProfileHistoricalStats(Base):
    __tablename__ = "profile_historical_stats"

    profile_id = Column(String, ForeignKey("profiles.id", ondelete="CASCADE"), primary_key=True)
    
    success_rate_7d = Column(Float, nullable=True)
    success_rate_30d = Column(Float, nullable=True)
    success_rate_90d = Column(Float, nullable=True)
    
    bid_frequency_7d = Column(Float, nullable=True)
    bid_frequency_30d = Column(Float, nullable=True)
    bid_frequency_90d = Column(Float, nullable=True)
    
    last_updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Optional: Relationship to Profile model
    # If you uncomment this, you'll need to add `historical_stats = relationship("ProfileHistoricalStats", back_populates="profile", uselist=False)`
    # to the Profile model in app/models/profile.py (and ensure uselist=False for one-to-one).
    # profile = relationship("Profile", back_populates="historical_stats")

    def __repr__(self):
        return f"<ProfileHistoricalStats(profile_id='{self.profile_id}', last_updated_at='{self.last_updated_at}')>"
