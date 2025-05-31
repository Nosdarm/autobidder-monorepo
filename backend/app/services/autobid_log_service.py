from sqlalchemy.ext.asyncio import AsyncSession # Added AsyncSession
from typing import Optional # Added Optional
from datetime import datetime

from app.models.autobid_log import AutobidLog


async def log_autobid_attempt( # Changed to async def
    db: AsyncSession, # Changed to AsyncSession
    profile_id: int,
    job_title: str,
    job_link: str,
    bid_text: str,
    status: str,
    error_message: Optional[str] = None, # Added Optional hint
    score: Optional[float] = None  # Added Optional hint
) -> AutobidLog: # Added return type hint
    log = AutobidLog(
        profile_id=profile_id,
        job_title=job_title,
        job_link=job_link,
        bid_text=bid_text,
        status=status,
        error_message=error_message,
        created_at=datetime.utcnow(), # datetime.utcnow() is fine, consider timezone awareness if needed
        score=score
    )
    db.add(log) # This is fine with AsyncSession
    await db.commit() # Changed to await
    await db.refresh(log) # Changed to await
    return log
