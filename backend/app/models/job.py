import uuid
from sqlalchemy import Column, String, Text, JSON # Added JSON
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base

class Job(Base):
    __tablename__ = "jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    description_embedding = Column(JSON, nullable=True) # New column
