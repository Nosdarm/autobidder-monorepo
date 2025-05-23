from sqlalchemy import Column, String, Boolean, Integer
from sqlalchemy.orm import relationship
from app.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="user")
    is_verified = Column(Boolean, default=False)

    profiles = relationship(
        "Profile",
        back_populates="owner",
        cascade="all, delete",
        passive_deletes=True
    )
