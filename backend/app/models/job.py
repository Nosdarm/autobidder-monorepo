import uuid
from sqlalchemy import Column, String, Text, JSON, DateTime # Added DateTime
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base

class Job(Base):
    __tablename__ = "jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4) # Internal UUID

    # Upwork specific fields
    upwork_job_id = Column(String, unique=True, index=True, nullable=False) # Upwork's own job ID (e.g., ciphertext)
    url = Column(String, nullable=True) # URL to the job posting on Upwork
    posted_time = Column(DateTime, nullable=True) # When the job was posted
    raw_data = Column(JSON, nullable=True) # Full JSON object of the job from Upwork API

    # General job fields (can be from Upwork or other sources)
    title = Column(String, nullable=True)
    description = Column(Text, nullable=True) # This might store a snippet or full description

    # Field for embedding, assuming it will be stored as JSON or needs specific handling if it's a vector
    description_embedding = Column(JSON, nullable=True) # Stores embedding as JSON array or object
