import logging
from typing import List, Optional # Added Optional for Session type hint
from sqlalchemy.orm import Session # Added missing import for Session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException # This might not be needed here if errors are handled differently in async service
# Убедитесь, что AutobidSettings импортирован правильно
from app.models.autobid_settings import AutobidSettings # Assuming this is the correct model path
# from app.models import AutobidSettings # Original was this, ensure correct path

# SessionLocal (sync session factory) is not needed for the async version of get_enabled_autobid_settings
# but kept for other synchronous functions in the file if they exist and are not refactored.
from app.database import SessionLocal

# Настройка логирования (если еще не настроено глобально)
# logging.basicConfig(level=logging.INFO) # Typically configured at application entry point
logger = logging.getLogger(__name__) # Use module-level logger

# Получение всех включённых профилей (refactored to async)
async def get_enabled_autobid_settings(db: AsyncSession) -> List[AutobidSettings]:
    logger.info(">>> Entering get_enabled_autobid_settings (async)")
    try:
        # The AsyncSession `db` is now passed as an argument
        stmt = select(AutobidSettings).where(AutobidSettings.enabled == True) # Explicit boolean check
        result = await db.execute(stmt)
        settings_list = result.scalars().all()
        logger.info(
            f"<<< Exiting get_enabled_autobid_settings (async) with "
            f"{len(settings_list)} settings"
        )
        return settings_list
    except Exception as e:
        logger.error(
            f"[ERROR] Inside get_enabled_autobid_settings (async): {e}", exc_info=True
        )
        # В асинхронном контексте, особенно если это вызывается фоновой задачей,
        # HTTPException может быть не лучшим выбором. Рассмотрите возврат пустого списка
        # или кастомного исключения сервисного уровня.
        return []  # Возвращаем пустой список при ошибке
    # No finally block to close db here, as the session is managed by the caller.

# Получение настроек по профилю (исправлено управление сессией)
# This function remains synchronous as per subtask scope, but shows original pattern.
# If called from async code, it would need to be wrapped or refactored.


def get_autobid_settings(profile_id: str):
    logging.info(
        f">>> Entering get_autobid_settings for profile_id: {profile_id}")
    db: Optional[Session] = None # Corrected: single type hint
    try:
        db = SessionLocal()
        result = db.execute(
            select(AutobidSettings).where(
                AutobidSettings.profile_id == profile_id))
        settings = result.scalar_one_or_none()
        logging.info(
            f"<<< Exiting get_autobid_settings for profile_id: {profile_id}"
        )
        if not settings:
            # Лучше не бросать HTTPException здесь, а вернуть None или кастомное исключение,
            # т.к. эта функция может вызываться вне HTTP контекста.
            # Оставим пока так для минимальных изменений.
            raise HTTPException(
                status_code=404, detail="Autobid settings not found"
            )
        return settings
    except Exception as e:
        logging.error(
            f"[ERROR] Inside get_autobid_settings for {profile_id}: {e}",
            exc_info=True
        )
        raise HTTPException(
            status_code=500, detail="Error fetching autobid settings."
        )
    finally:
        if db is not None:
            db.close()
            logging.debug(
                f"--- Database session closed in get_autobid_settings "
                f"for {profile_id}"
            )


# Обновление или создание настроек (исправлено управление сессией)
def upsert_autobid_settings(profile_id: str, enabled: bool, daily_limit: int):
    logging.info(
        f">>> Entering upsert_autobid_settings for profile_id: {profile_id}"
    )
    db: Optional[Session] = None # Applied Optional type hint here as well
    try:
        db = SessionLocal()
        result = db.execute(
            select(AutobidSettings).where(
                AutobidSettings.profile_id == profile_id))
        settings = result.scalar_one_or_none()

        if settings:
            logging.debug(f"Updating settings for {profile_id}")
            settings.enabled = enabled
            settings.daily_limit = daily_limit
        else:
            logging.debug(f"Creating new settings for {profile_id}")
            settings = AutobidSettings(
                profile_id=profile_id,
                enabled=enabled,
                daily_limit=daily_limit
            )
            db.add(settings)

        db.commit()
        db.refresh(settings)
        logging.info(
            f"<<< Exiting upsert_autobid_settings for profile_id: "
            f"{profile_id}"
        )
        return settings
    except Exception as e:
        if db is not None:
            db.rollback()  # Откатываем изменения при ошибке
        logging.error(
            f"[ERROR] Inside upsert_autobid_settings for {profile_id}: {e}",
            exc_info=True
        )
        raise HTTPException(
            status_code=500, detail="Error upserting autobid settings."
        )
    finally:
        if db is not None:
            db.close()
            logging.debug(
                f"--- Database session closed in upsert_autobid_settings "
                f"for {profile_id}"
            )
