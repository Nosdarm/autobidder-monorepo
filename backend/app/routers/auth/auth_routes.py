# backend/app/routers/auth/auth_routes.py

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession # Added
from sqlalchemy.orm import Session # Will be removed if not used elsewhere

from app.database import get_db
from app.schemas.auth import RegisterInput, LoginInput, MessageResponse
from app.schemas.user import UserOut, TokenResponse # UserOut is used
from app.services.auth_service import (
    register_user_service,
    login_user_service, # Added
    verify_email_service,
    get_current_user_service,
    logout_user_service,
)
# create_access_token, verify_password, User model are no longer needed directly in this file
# if login logic is fully moved to service.
# from app.auth.jwt import create_access_token, get_current_user_with_role
# from app.models.user import User
# from app.utils.auth import verify_password
from app.auth.jwt import get_current_user_with_role # Keep this for /me

router = APIRouter(tags=["Auth"])
auth_scheme = HTTPBearer()


@router.post(
    "/register",
    response_model=UserOut,
    status_code=status.HTTP_201_CREATED,
)
async def register_user(
    data: RegisterInput,
    db: AsyncSession = Depends(get_db), # Changed to AsyncSession
):
    return await register_user_service(data, db)


@router.post(
    "/login",
    response_model=TokenResponse,
)
async def login_user(
    data: LoginInput,
    db: AsyncSession = Depends(get_db), # Changed to AsyncSession
):
    return await login_user_service(data, db)


@router.get(
    "/verify",
    response_model=MessageResponse,
)
async def verify_email(
    token: str,
    db: AsyncSession = Depends(get_db), # Changed to AsyncSession
):
    return await verify_email_service(token, db)


@router.get(
    "/me",
    response_model=UserOut,
)
async def read_current_user(
    payload: dict = Depends(get_current_user_with_role),
    db: AsyncSession = Depends(get_db), # Changed to AsyncSession
):
    return await get_current_user_service(payload, db)


@router.post(
    "/logout",
    response_model=None,
    status_code=status.HTTP_204_NO_CONTENT,
)
async def logout_user( # Removed db: AsyncSession as it's not used by logout_user_service
    credentials: HTTPAuthorizationCredentials = Depends(auth_scheme),
):
    # The logout_user_service does not require db session based on its current implementation.
    # If it were to interact with the DB (e.g. for token blacklisting with DB),
    # then db: AsyncSession = Depends(get_db) would be needed here.
    return await logout_user_service(credentials.credentials) # This service is synchronous
