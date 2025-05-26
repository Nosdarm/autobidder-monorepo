from uuid import uuid4
from sqlalchemy.orm import Session
from fastapi import HTTPException
from datetime import datetime
import json # Added import
import asyncio # Added import
from app.websocket_manager import manager # Added import

from app.models.bid import Bid
from app.models.profile import Profile
from app.schemas.bid import BidCreateInput


def create_bid_service(data: BidCreateInput, user_id: str, db: Session):
    # Проверка профиля
    profile = db.query(Profile).filter(
        Profile.id == data.profile_id,
        Profile.owner_id == user_id).first()
    if not profile:
        raise HTTPException(
            status_code=403,
            detail="Вы не можете делать ставки от имени этого профиля")

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

    # WebSocket broadcast logic
    message_data = {
        "type": "bid_update",
        "bid_id": new_bid.id,
        "profile_id": new_bid.profile_id,
        "status": new_bid.status,
        "job_id": new_bid.job_id,
        "amount": new_bid.amount,
        "submitted_at": new_bid.submitted_at.isoformat()
    }
    # profile.owner_id is essentially user_id here, which is the client_id for WebSocket
    asyncio.create_task(manager.broadcast_to_client(json.dumps(message_data), user_id))
    
    return new_bid


def get_user_bids_service(user_id: str, db: Session):
    return db.query(Bid).join(Profile).filter(
        Profile.owner_id == user_id).all()


def get_all_bids_service(db: Session):
    return db.query(Bid).all()
