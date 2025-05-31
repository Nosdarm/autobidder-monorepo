from pydantic import BaseModel, Field, ConfigDict
from typing import Literal, Optional, List
from app.schemas.user import UserOut # Changed import for circular dependency fix

# --- Схемы для Профиля ---

class ProfileBase(BaseModel):
    name: str = Field(..., description="Profile name")
    profile_type: Literal["personal", "agency"] = Field(
        ..., description="Profile type: 'personal' or 'agency'"
    )
    autobid_enabled: bool = Field(
        False, description="Is autobidder enabled for this profile"
    )
    skills: Optional[List[str]] = Field(None, description="List of skills")
    experience_level: Optional[str] = Field(None, description="Experience level")
    title: Optional[str] = Field(None, description="Profile title/headline") # New field
    overview: Optional[str] = Field(None, description="Profile overview/summary") # New field

class ProfileCreate(ProfileBase):
    user_id: int

class ProfileUpdate(BaseModel):
    name: Optional[str] = Field(None, description="New profile name")
    profile_type: Optional[Literal["personal", "agency"]] = Field(
        None, description="New profile type"
    )
    autobid_enabled: Optional[bool] = Field(
        None, description="New state for autobidder"
    )
    skills: Optional[List[str]] = Field(None, description="New list of skills")
    experience_level: Optional[str] = Field(None, description="New experience level")
    title: Optional[str] = Field(None, description="New profile title/headline") # New field
    overview: Optional[str] = Field(None, description="New profile overview/summary") # New field

class ProfileInDBBase(ProfileBase):
    id: str  # Profile ID is a string (UUID)
    user_id: int # User ID is an integer
    model_config = ConfigDict(from_attributes=True)

class Profile(ProfileInDBBase): # This is the Pydantic schema for outputting Profile data
    pass

# Optional: If ProfileWithOwner is used elsewhere, keep it. Otherwise, it can be removed for simplicity.
class ProfileWithOwner(Profile):
    owner: Optional[UserOut] = None # Changed type hint for circular dependency fix
