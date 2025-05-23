# backend/app/routers/auth/auth_routes.py

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.auth import RegisterInput, LoginInput, MessageResponse
from app.schemas.user import UserOut, TokenResponse
from app.services.auth_service import (
    register_user_service,
    verify_email_service,
    get_current_user_service,
    logout_user_service,
)
from app.auth.jwt import create_access_token, get_current_user_with_role
from app.models.user import User
from app.utils.auth import verify_password

router = APIRouter(tags=["Auth"])
auth_scheme = HTTPBearer()


@router.post(
    "/register",
    response_model=UserOut,
    status_code=status.HTTP_201_CREATED,
)
async def register_user(
    data: RegisterInput,
    db: Session = Depends(get_db),
):
    return await register_user_service(data, db)


@router.post(
    "/login",
    response_model=TokenResponse,
)
async def login_user(
    data: LoginInput,
    db: Session = Depends(get_db),
):
    """
    Аутентифицируем пользователя прямо в роутере,
    чтобы отловить ошибки и сразу вернуть токен.
    """
    user = db.query(User).filter(User.email == data.email).first()
    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    token = create_access_token({"sub": user.email})
    return {"access_token": token, "token_type": "bearer"}


@router.get(
    "/verify",
    response_model=MessageResponse,
)
async def verify_email(
    token: str,
    db: Session = Depends(get_db),
):
    return await verify_email_service(token, db)


@router.get(
    "/me",
    response_model=UserOut,
)
async def read_current_user(
    payload: dict = Depends(get_current_user_with_role),
    db: Session = Depends(get_db),
):
    return await get_current_user_service(payload, db)


@router.post(
    "/logout",
    response_model=None,
    status_code=status.HTTP_204_NO_CONTENT,
)
async def logout_user(
    credentials: HTTPAuthorizationCredentials = Depends(auth_scheme),
):
    return await logout_user_service(credentials.credentials)
