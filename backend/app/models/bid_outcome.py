import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID as PG_UUID # For UUID type if needed for id
from app.db.base import Base

class BidOutcome(Base):
    __tablename__ = "bid_outcomes"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    bid_id = Column(String, ForeignKey("bids.id", ondelete="CASCADE"), nullable=False, index=True)
    outcome_timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    is_success = Column(Boolean, nullable=False)
    details = Column(Text, nullable=True)  # Using Text for potentially longer string details. JSON could be an alternative.

    # Relationship to Bid model (Bid model will have 'outcomes' backref)
    bid = relationship("Bid", back_populates="outcomes")

    def __repr__(self):
        return f"<BidOutcome(id='{self.id}', bid_id='{self.bid_id}', is_success='{self.is_success}')>"
