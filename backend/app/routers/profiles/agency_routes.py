from fastapi import APIRouter, Depends  # HTTPException removed
from sqlalchemy.orm import Session
from uuid import uuid4
# Keep if AgencyProfileCreate remains here, or remove if it's moved/unused
from pydantic import BaseModel
from typing import List

from app.database import get_db
from app.models.profile import Profile
from app.schemas.profile import Profile as ProfileOut  # Import Profile as ProfileOut
from app.auth.jwt import get_current_user_with_role

router = APIRouter(
    prefix="/agency-profiles",
    tags=["Agency Profiles"]
)

# AgencyProfileCreate is already defined in app.schemas.agency.py
# If this router is meant to use that, it should be imported.
# For now, assuming this local definition is intentional or to be replaced.
# If it's from app.schemas.agency, then `from pydantic import BaseModel`
# might not be needed here.

# AgencyProfileCreate is defined in app.schemas.agency
from app.schemas.agency import AgencyProfileCreate


@router.post("/create", response_model=ProfileOut)
def create_agency_profile(
    data: AgencyProfileCreate, # Use imported schema
    payload: dict = Depends(get_current_user_with_role),
    db: Session = Depends(get_db)
):
    profile = Profile(
        id=str(uuid4()),
        name=data.name,
        profile_type="agency", # Corrected field name
        autobid_enabled=data.autobid_enabled,
        user_id=payload["user_id"] # Corrected field name
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


@router.get("/my", response_model=List[ProfileOut])  # Add response_model
def get_user_agency_profiles(
    payload: dict = Depends(get_current_user_with_role),
    db: Session = Depends(get_db)
):
    return db.query(Profile).filter(
        Profile.user_id == payload["user_id"], # Corrected field name
        Profile.profile_type == "agency" # Corrected field name
    ).all()
