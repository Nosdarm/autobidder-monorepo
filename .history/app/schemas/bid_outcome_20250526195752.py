from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Dict, Any # Dict & Any for JSON-like 'details' if needed
import uuid # For potential UUID type usage, though using str for now

class BidOutcomeBase(BaseModel):
    bid_id: str = Field(..., description="The ID of the bid this outcome relates to")
    outcome_timestamp: datetime = Field(default_factory=datetime.utcnow, description="Timestamp of when the outcome was recorded")
    is_success: bool = Field(..., description="Whether the bid was successful or not")
    details: Optional[str] = Field(None, description="Additional details about the outcome (e.g., reason for failure, win details)")

class BidOutcomeCreate(BidOutcomeBase):
    pass

class BidOutcomeOut(BidOutcomeBase):
    id: str = Field(..., description="The unique ID of this bid outcome")

    class Config:
        orm_mode = True # Pydantic V1. For Pydantic V2, it's from_attributes = True
        # For Pydantic V2, use model_config = {"from_attributes": True}
        # However, the existing schemas in the project use Pydantic V1 style orm_mode
        # e.g. app/schemas/profile.py : model_config = { "from_attributes": True }
        # e.g. app/schemas/bid.py : orm_mode = True
        # Checking other files, it seems a mix. I'll stick to orm_mode = True for now as it's more common in the project.
        # Upon further review of provided files, profile.py uses model_config.
        # I will use the newer model_config for consistency with potentially newer Pydantic versions.
        # model_config = {"from_attributes": True}
        # Re-checking: profile.py uses `model_config`, bid.py uses `orm_mode`.
        # Given `app/schemas/bid.py` uses `orm_mode = True` and this is `bid_outcome`, I'll use `orm_mode = True`.
        # This is to maintain consistency with the related `BidResponse` schema.
        # If the project is standardizing on Pydantic v2, this should be `from_attributes = True`.
        # For now, sticking to orm_mode = True as seen in bid.py and other older schema files.

class BidOutcomeUpdate(BaseModel): # Optional: if partial updates are needed
    outcome_timestamp: Optional[datetime] = None
    is_success: Optional[bool] = None
    details: Optional[str] = None
