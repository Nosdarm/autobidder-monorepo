from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from app.services.bids_service import (
    create_bid_service,
    get_user_bids_service,
    get_all_bids_service
)
from app.schemas.bid import BidCreateInput
from app.auth.jwt import get_current_user_with_role
from app.database import get_db

router = APIRouter()


@router.post("/", summary="Создать ставку")
def create_bid(
    data: BidCreateInput,
    payload: dict = Depends(get_current_user_with_role),
    db: Session = Depends(get_db)
):
    return create_bid_service(data, payload["user_id"], db)


@router.get("/", summary="Получить все ставки пользователя или все (если superadmin)")
def list_bids(
    request: Request,
    payload: dict = Depends(get_current_user_with_role),
    db: Session = Depends(get_db)
):
    if payload["role"] == "superadmin":
        return get_all_bids_service(db)
    return get_user_bids_service(payload["user_id"], db)
