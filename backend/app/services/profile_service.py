from uuid import uuid4
from sqlalchemy.orm import Session

from app.models.profile import Profile
from app.schemas.profile import ProfileCreate


def create_profile_service(
    data: ProfileCreate,
    user_id: str,
    db: Session,
) -> Profile:
    """
    Создаёт новую запись Profile в БД.
    """
    new_profile = Profile(
        id=str(uuid4()),
        name=data.name,
        profile_type=data.profile_type,
        autobid_enabled=data.autobid_enabled,
        user_id=user_id,
    )
    db.add(new_profile)
    db.commit()
    db.refresh(new_profile)
    return new_profile
