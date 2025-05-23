from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.auth import RegisterInput, LoginInput
from app.schemas.user import UserOut, TokenResponse
from app.services.auth_service import (
    register_user_service,
    login_user_service,
    verify_email_service,
    get_current_user_service,
    logout_user_service,
)
from app.auth.jwt import get_current_user_with_role

router = APIRouter(prefix="/auth", tags=["Auth"])
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
    """
    Регистрирует нового пользователя и возвращает схему UserOut.
    """
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
    Аутентифицирует пользователя и возвращает токен.
    """
    return await login_user_service(data, db)


@router.get(
    "/verify",
    response_model=None,
)
async def verify_email(
    token: str,
    db: Session = Depends(get_db),
):
    """
    Подтверждает email по токену и возвращает None.
    """
    return await verify_email_service(token, db)


@router.get(
    "/me",
    response_model=UserOut,
)
async def read_current_user(
    payload: dict = Depends(get_current_user_with_role),
    db: Session = Depends(get_db),
):
    """
    Возвращает данные текущего пользователя в схеме UserOut.
    """
    return await get_current_user_service(payload, db)


@router.post(
    "/logout",
    response_model=None,
    status_code=status.HTTP_204_NO_CONTENT,
)
async def logout_user(
    credentials: HTTPAuthorizationCredentials = Depends(auth_scheme),
):
    """
    Инвалидация текущего токена, возвращает None.
    """
    return await logout_user_service(credentials.credentials)
