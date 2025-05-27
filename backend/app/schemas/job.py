import uuid
from typing import Optional, Any
from pydantic import BaseModel, ConfigDict

class JobBase(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    description_embedding: Optional[Any] = None # Using Any for JSON type

class JobCreate(JobBase):
    title: str # Title is required for creation
    description: str # Description is required for creation

class JobUpdate(JobBase):
    pass

class JobInDBBase(JobBase):
    id: uuid.UUID
    model_config = ConfigDict(from_attributes=True)

class Job(JobInDBBase):
    pass

class JobInDB(JobInDBBase): # If needed for DB representation
    pass
