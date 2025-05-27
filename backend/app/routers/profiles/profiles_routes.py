from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.profile import ProfileCreate, Profile as ProfileOut
from app.models.profile import Profile
from app.models.user import User
from app.services.profile_service import create_profile_service
from app.auth.jwt import get_current_user_with_role
from app.services.auth_service import get_current_user_service

router = APIRouter(tags=["Profiles"])  # prefix задаётся в main.py


def get_current_user(
    payload: dict = Depends(get_current_user_with_role),
    db: Session = Depends(get_db),
) -> User:
    """
    Синхронно получаем User из БД по payload из JWT.
    """
    user = get_current_user_service(payload, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )
    return user


@router.post(
    "/",
    response_model=ProfileOut,
    status_code=status.HTTP_201_CREATED,
)
def create_profile(
    data: ProfileCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Создаёт новый профиль для текущего пользователя.
    """
    return create_profile_service(data, current_user.id, db)


@router.get(
    "/",
    response_model=List[ProfileOut],
)
def list_profiles(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Возвращает все профили текущего пользователя.
    """
    return (
        db
        .query(Profile)
        .filter(Profile.user_id == current_user.id)
        .all()
    )
