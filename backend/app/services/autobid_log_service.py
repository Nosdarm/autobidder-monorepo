from app.models.autobid_log import AutobidLog
from sqlalchemy.orm import Session
from datetime import datetime


def log_autobid_attempt(
    db: Session,
    profile_id: int,
    job_title: str,
    job_link: str,
    bid_text: str,
    status: str,
    error_message: str = None,
    score: float = None  # ← Добавили сюда
):
    log = AutobidLog(
        profile_id=profile_id,
        job_title=job_title,
        job_link=job_link,
        bid_text=bid_text,
        status=status,
        error_message=error_message,
        created_at=datetime.utcnow(),
        score=score  # ← И сохраняем сюда
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log
