import uuid
from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, ConfigDict

class BidOutcomeBase(BaseModel):
    bid_id: str
    is_success: bool
    details: Optional[str] = None
    outcome_timestamp: Optional[datetime] = None

class BidOutcomeCreate(BidOutcomeBase):
    pass

class BidOutcomeUpdate(BaseModel): # Separate update schema if partial updates are allowed
    is_success: Optional[bool] = None
    details: Optional[str] = None

class BidOutcomeInDBBase(BidOutcomeBase):
    id: str
    model_config = ConfigDict(from_attributes=True)

class BidOutcome(BidOutcomeInDBBase):
    pass

class BidOutcomeInDB(BidOutcomeInDBBase):
    pass
