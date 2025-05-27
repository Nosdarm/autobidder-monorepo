from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from app.services.bids_service import (
    create_bid_service,
    get_user_bids_service,
    get_all_bids_service
)
from app.services.bid_outcome_service import create_bid_outcome_service
from app.schemas.bid import BidCreate as BidCreateInput, BidResponse, Bid
from app.schemas.bid_outcome import BidOutcomeCreate, BidOutcome # Added imports
from typing import List
from app.auth.jwt import get_current_user_with_role
from app.database import get_db
# Potentially HTTPException if we were to handle errors directly here, but service does it.
# from fastapi import HTTPException

router = APIRouter()


@router.post("/", summary="Создать ставку",
             response_model=Bid)  # Use consolidated Bid schema
def create_bid(
    data: BidCreateInput, # Use BidCreateInput for creation
    payload: dict = Depends(get_current_user_with_role),
    db: Session = Depends(get_db)
):
    return create_bid_service(data, payload["user_id"], db)


@router.get("/",
            summary="Получить все ставки пользователя или все (если superadmin)",
            response_model=List[Bid]  # Use consolidated Bid schema
            )
def list_bids(
    request: Request,
    payload: dict = Depends(get_current_user_with_role),
    db: Session = Depends(get_db)
):
    if payload["role"] == "superadmin":
        return get_all_bids_service(db)
    return get_user_bids_service(payload["user_id"], db)


@router.post("/{bid_id}/outcomes", response_model=BidOutcome, summary="Create a new outcome for a bid")
def create_bid_outcome_endpoint(
    bid_id: str,
    outcome_data: BidOutcomeCreate,
    db: Session = Depends(get_db)
) -> BidOutcome:
    """
    Creates a new outcome for a specific bid.
    """
    # The create_bid_outcome_service will handle bid existence check and raise HTTPException if not found.
    db_bid_outcome = create_bid_outcome_service(db=db, bid_id=bid_id, outcome_data=outcome_data)
    return db_bid_outcome
