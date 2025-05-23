from uuid import uuid4
from sqlalchemy.orm import Session
from fastapi import HTTPException
from datetime import datetime

from app.models.bid import Bid
from app.models.profile import Profile
from app.schemas.bid import BidCreateInput


def create_bid_service(data: BidCreateInput, user_id: str, db: Session):
    # Проверка профиля
    profile = db.query(Profile).filter(Profile.id == data.profile_id, Profile.owner_id == user_id).first()
    if not profile:
        raise HTTPException(status_code=403, detail="Вы не можете делать ставки от имени этого профиля")

    new_bid = Bid(
        id=str(uuid4()),
        profile_id=data.profile_id,
        job_id=data.job_id,
        amount=data.amount,
        submitted_at=datetime.utcnow()
    )
    db.add(new_bid)
    db.commit()
    db.refresh(new_bid)
    return new_bid


def get_user_bids_service(user_id: str, db: Session):
    return db.query(Bid).join(Profile).filter(Profile.owner_id == user_id).all()


def get_all_bids_service(db: Session):
    return db.query(Bid).all()
