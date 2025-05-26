from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class AutobidLogOut(BaseModel):
    id: int
    profile_id: int
    job_title: str
    job_link: str
    bid_text: Optional[str]
    status: str
    error_message: Optional[str]
    created_at: datetime

    class Config:
        orm_mode = True
