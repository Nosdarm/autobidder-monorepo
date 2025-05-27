import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List # Added List
from pydantic import BaseModel, Field, ConfigDict

# Forward references for Job and Profile if they are included in responses
# from .job import Job  # Assuming Job schema is in job.py
# from .profile import Profile  # Assuming Profile schema is in profile.py
# from .bid_outcome import BidOutcome # Assuming BidOutcome schema is in bid_outcome.py

class BidBase(BaseModel):
    profile_id: str = Field(..., description="ID of the profile making the bid")
    job_id: uuid.UUID = Field(..., description="ID of the job being bid on")
    amount: float = Field(..., gt=0, description="Bid amount")
    status: str = Field("created", description="Status of the bid")
    prompt_template_id: Optional[int] = Field(None, description="ID of the AI prompt template used")
    generated_bid_text: Optional[str] = Field(None, description="AI-generated bid text")
    bid_settings_snapshot: Optional[Dict[str, Any]] = Field(None, description="Snapshot of bid settings at creation")
    external_signals_snapshot: Optional[Dict[str, Any]] = Field(None, description="Snapshot of external signals at creation")

class BidCreate(BidBase):
    pass

class BidUpdate(BaseModel): # Separate schema for updates
    amount: Optional[float] = Field(None, gt=0, description="Updated bid amount")
    status: Optional[str] = Field(None, description="Updated status of the bid")
    generated_bid_text: Optional[str] = Field(None, description="Updated AI-generated bid text")
    # Potentially other updatable fields

class BidInDBBase(BidBase):
    id: str
    submitted_at: datetime
    model_config = ConfigDict(from_attributes=True)

class Bid(BidInDBBase):
    # If you want to include related objects in the response, define them here.
    # For example:
    # job: Optional[Job] = None
    # profile: Optional[Profile] = None
    # outcomes: List[BidOutcome] = []
    pass

class BidResponse(Bid): # Specific response model, can be same as Bid or tailored
    pass
