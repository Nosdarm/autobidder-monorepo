from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class BidCreateInput(BaseModel):
    profile_id: str = Field(..., description="ID профиля, с которого делается ставка")
    job_id: str = Field(..., description="ID проекта, на который делается ставка")
    amount: float = Field(..., gt=0, description="Размер ставки")


class BidResponse(BaseModel):
    id: str
    profile_id: str
    job_id: str
    amount: float
    submitted_at: datetime

    class Config:
        orm_mode = True
