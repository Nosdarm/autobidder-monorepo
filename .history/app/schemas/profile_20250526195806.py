from typing import Optional
from pydantic import BaseModel
import uuid

class JobBase(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None

class JobCreate(JobBase):
    pass

class JobOut(JobBase):
    id: uuid.UUID

    class Config:
        orm_mode = True
