from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.autobid_log import AutobidLog
from app.schemas.autobid_log import AutobidLogOut

router = APIRouter(prefix="/autobid-logs", tags=["Autobid Logs"])


@router.get("/{profile_id}", response_model=list[AutobidLogOut])
def get_logs_for_profile(profile_id: int, db: Session = Depends(get_db)):
    logs = (
        db.query(AutobidLog)
        .filter(AutobidLog.profile_id == profile_id)
        .order_by(AutobidLog.created_at.desc())
        .all()
    )
    return logs
