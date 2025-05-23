from pydantic import BaseModel, Field
from typing import Literal, Optional

# --- Схемы для Профиля ---
class ProfileBase(BaseModel):
    name: str = Field(..., description="Profile name")
    profile_type: Literal["personal", "agency"] = Field(
        ..., description="Profile type: 'personal' or 'agency'"
    )
    autobid_enabled: bool = Field(
        False, description="Is autobidder enabled for this profile"
    )

class ProfileCreate(ProfileBase):
    pass

class ProfileOut(ProfileBase):
    id: str = Field(..., description="Profile ID (UUID as string)")
    user_id: str = Field(..., description="Owner User ID (UUID as string)")

    model_config = {
        "from_attributes": True
    }

class ProfileUpdate(BaseModel):
    name: Optional[str] = Field(None, description="New profile name")
    profile_type: Optional[Literal["personal", "agency"]] = Field(
        None, description="New profile type"
    )
    autobid_enabled: Optional[bool] = Field(
        None, description="New state for autobidder"
    )