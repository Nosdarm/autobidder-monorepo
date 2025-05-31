import uuid
import datetime # Added datetime
from typing import Optional, Any, Dict, List # Added Dict, List
from pydantic import BaseModel, ConfigDict

# Base schema with fields common to creation, update, and read
class JobBase(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None # Could be a snippet or full description
    upwork_job_id: Optional[str] = None
    url: Optional[str] = None
    posted_time: Optional[datetime.datetime] = None
    raw_data: Optional[Dict[str, Any]] = None # For storing the raw JSON from Upwork
    description_embedding: Optional[List[float]] = None # Assuming embedding is a list of floats

    model_config = ConfigDict(
        from_attributes=True, # Enables ORM mode for Pydantic V2
        # orm_mode = True # For Pydantic V1
    )

# Schema for creating a new job
# Fields required for creation can be made non-optional here if needed
class JobCreate(JobBase):
    # Example: making title mandatory for creation, others can be optional from JobBase
    title: str
    # upwork_job_id is optional on creation, but service checks for duplicates if provided
    # If description is also mandatory for creation:
    # description: str

# Schema for updating an existing job
# All fields are optional by inheriting from JobBase where all are Optional
class JobUpdate(JobBase):
    pass

# Schema for reading a job (API response)
# This will be aliased as JobSchema in routes
class Job(JobBase): # Inherits all fields from JobBase
    id: uuid.UUID # Internal UUID primary key

# If you need a separate schema for jobs as stored in DB (rarely different from response schema)
# class JobInDB(Job):
#     pass
