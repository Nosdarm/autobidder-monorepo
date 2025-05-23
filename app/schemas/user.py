from pydantic import BaseModel, Field

class UserOut(BaseModel):
    id: int
    email: str
    profile_id: int

    model_config = {
        "from_attributes": True  # вместо orm_mode
    }

class TokenResponse(BaseModel):
    access_token: str = Field(..., description="JWT токен")
    token_type: str   = Field(..., description="Тип токена, обычно 'bearer'")