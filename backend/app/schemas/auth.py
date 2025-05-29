from pydantic import BaseModel, EmailStr, Field
from app.models.user import AccountType


class RegisterInput(BaseModel):
    email: EmailStr = Field(..., description="Email пользователя")
    password: str = Field(..., min_length=6,
                          description="Пароль (не менее 6 символов)")
    account_type: AccountType = Field(..., description="Тип аккаунта")


class LoginInput(BaseModel):
    email: EmailStr = Field(..., description="Email пользователя")
    password: str = Field(..., min_length=6, description="Пароль")


class MessageResponse(BaseModel):
    message: str
