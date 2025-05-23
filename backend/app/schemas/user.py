from pydantic import BaseModel, Field, EmailStr
from typing import Optional

# Schema for user data from file-based store (user_api.py)


class UserBase(BaseModel):
    email: EmailStr
    role: str = "user"  # Default role


class UserResponse(UserBase):
    id: str  # UUID as string from users.json

    # No ConfigDict(from_attributes=True) needed as it's from dicts
    # (users.json)

# Schema for user data from ORM (original UserOut)


class UserOut(BaseModel):  # This is for ORM based user models.
    id: int  # Typically int for auto-incrementing PK in DB
    email: EmailStr
    # profile_id: int # This field might be specific to an ORM context with a
    # direct profile link
    role: Optional[str] = None  # Assuming role might exist in ORM User model
    is_verified: Optional[bool] = None  # Assuming is_verified might exist

    model_config = {
        "from_attributes": True  # For ORM to Pydantic conversion
    }


class UserRegisterResponse(BaseModel):
    message: str
    id: str  # User ID created


class TokenResponse(BaseModel):
    access_token: str = Field(..., description="JWT токен")
    token_type: str = Field(..., description="Тип токена, обычно 'bearer'")

# Schema for RoleUpdateInput in user_roles_routes.py


class RoleUpdateInput(BaseModel):
    user_id: str
    role: str

# Schema for the response of /admin/set-role


class UserRoleUpdateResponse(BaseModel):
    status: str
    user_id: str
    new_role: str
