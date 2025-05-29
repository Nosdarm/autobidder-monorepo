from datetime import datetime, timedelta
from typing import Optional

from jose import JWTError, jwt
# from dotenv import load_dotenv # Removed
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.utils.token_blacklist import is_token_blacklisted
from app.config import settings # Import settings
from app.models.user import AccountType # Import AccountType

# 🔐 Загрузка .env переменных
# load_dotenv() # Removed
# SECRET_KEY = os.getenv("SECRET_KEY") # Replaced
# ALGORITHM = "HS256" # Replaced
# ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 дней # Replaced

if not settings.SECRET_KEY:
    raise ValueError("❌ SECRET_KEY is not set in .env or settings")

auth_scheme = HTTPBearer()

# ✅ Создание JWT токена
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES) # Use settings
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM) # Use settings

# ✅ Декодирование JWT токена
def decode_token(token: str):
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]) # Use settings
    except JWTError:
        return None

# ✅ Получение текущего пользователя (email из sub)
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(auth_scheme)):
    token = credentials.credentials

    if is_token_blacklisted(token):
        raise HTTPException(status_code=401, detail="Token has been revoked")

    payload = decode_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    return payload["sub"]

# ✅ Получение пользователя с ролью
def get_current_user_with_role(
    credentials: HTTPAuthorizationCredentials = Depends(auth_scheme),
    request: Request = None
) -> dict: # Added return type hint for clarity, can be more specific if needed
    token = credentials.credentials

    if is_token_blacklisted(token):
        raise HTTPException(status_code=401, detail="Token has been revoked")

    payload = decode_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user_email = payload["sub"]
    role = payload.get("role", "user") # Default to "user" if not present
    account_type_value = payload.get("account_type")
    
    account_type: Optional[AccountType] = None
    if account_type_value:
        try:
            account_type = AccountType(account_type_value)
        except ValueError:
            # Handle cases where account_type in token is not a valid AccountType enum value
            # For now, let's default to None or raise an error, depending on desired strictness
            # Raising an error might be safer to ensure token integrity.
            raise HTTPException(status_code=401, detail="Invalid account_type in token")


    if request:
        request.state.user_id = user_email
        request.state.role = role
        request.state.account_type = account_type

    return {"user_id": user_email, "role": role, "account_type": account_type}

# ✅ Проверка доступа по роли
def require_role(*allowed_roles: str):
    def role_checker(
        credentials: HTTPAuthorizationCredentials = Depends(auth_scheme),
    ):
        token = credentials.credentials

        if is_token_blacklisted(token):
            raise HTTPException(status_code=401, detail="Token has been revoked")

        payload = decode_token(token)
        if not payload or "sub" not in payload or "role" not in payload:
            raise HTTPException(status_code=401, detail="Invalid or expired token")

        user_role = payload["role"]
        if user_role not in allowed_roles:
            raise HTTPException(status_code=403, detail="Access forbidden")

        return payload

    return role_checker
