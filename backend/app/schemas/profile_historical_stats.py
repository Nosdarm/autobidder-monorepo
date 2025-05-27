from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

class ProfileHistoricalStatsBase(BaseModel):
    profile_id: str
    success_rate_7d: Optional[float] = None
    success_rate_30d: Optional[float] = None
    success_rate_90d: Optional[float] = None
    bid_frequency_7d: Optional[float] = None
    bid_frequency_30d: Optional[float] = None
    bid_frequency_90d: Optional[float] = None
    last_updated_at: Optional[datetime] = None

class ProfileHistoricalStatsCreate(ProfileHistoricalStatsBase):
    # All fields are optional or have defaults in the model, so no specific create schema needed unless validation differs
    pass

class ProfileHistoricalStatsUpdate(BaseModel): # For partial updates
    success_rate_7d: Optional[float] = None
    success_rate_30d: Optional[float] = None
    success_rate_90d: Optional[float] = None
    bid_frequency_7d: Optional[float] = None
    bid_frequency_30d: Optional[float] = None
    bid_frequency_90d: Optional[float] = None

class ProfileHistoricalStatsInDBBase(ProfileHistoricalStatsBase):
    model_config = ConfigDict(from_attributes=True)

class ProfileHistoricalStats(ProfileHistoricalStatsInDBBase):
    pass
