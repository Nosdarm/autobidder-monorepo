from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import uuid4
from pydantic import BaseModel
from typing import List

from app.database import get_db
from app.models.profile import Profile
from app.auth.jwt import get_current_user_with_role

router = APIRouter(
    prefix="/agency-profiles",
    tags=["Agency Profiles"]
)

class AgencyProfileCreate(BaseModel):
    name: str
    autobid_enabled: bool = False

@router.post("/create")
def create_agency_profile(
    data: AgencyProfileCreate,
    payload: dict = Depends(get_current_user_with_role),
    db: Session = Depends(get_db)
):
    profile = Profile(
        id=str(uuid4()),
        name=data.name,
        type="agency",
        autobid_enabled=data.autobid_enabled,
        owner_id=payload["user_id"]
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


@router.get("/my")
def get_user_agency_profiles(
    payload: dict = Depends(get_current_user_with_role),
    db: Session = Depends(get_db)
):
    return db.query(Profile).filter(
        Profile.owner_id == payload["user_id"],
        Profile.type == "agency"
    ).all()
