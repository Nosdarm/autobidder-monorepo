from pydantic import BaseModel, Field, ConfigDict
from typing import Literal, Optional, List, Any # Added List and Any

# --- Схемы для Профиля ---

class ProfileBase(BaseModel):
    name: str = Field(..., description="Profile name")
    profile_type: Literal["personal", "agency"] = Field(
        ..., description="Profile type: 'personal' or 'agency'"
    )
    autobid_enabled: bool = Field(
        False, description="Is autobidder enabled for this profile"
    )
    skills: Optional[List[str]] = Field(None, description="List of skills") # Changed to List[str]
    experience_level: Optional[str] = Field(None, description="Experience level")

class ProfileCreate(ProfileBase):
    user_id: str # user_id is required for creation, but not in ProfileBase for updates

class ProfileUpdate(BaseModel): # Using BaseModel directly for more flexibility in updates
    name: Optional[str] = Field(None, description="New profile name")
    profile_type: Optional[Literal["personal", "agency"]] = Field(
        None, description="New profile type"
    )
    autobid_enabled: Optional[bool] = Field(
        None, description="New state for autobidder"
    )
    skills: Optional[List[str]] = Field(None, description="New list of skills")
    experience_level: Optional[str] = Field(None, description="New experience level")

class ProfileInDBBase(ProfileBase):
    id: str
    user_id: str
    model_config = ConfigDict(from_attributes=True)

class Profile(ProfileInDBBase):
    pass

class ProfileWithOwner(Profile): # Example if you need to nest owner info
    # owner: Optional[User] # Assuming User schema from .user
    pass
