import logging
from typing import List, Optional
# from sqlalchemy.orm import Session # Removed unused sync Session import
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
# from fastapi import HTTPException # Removed unused HTTPException import
# Убедитесь, что AutobidSettings импортирован правильно
from app.models.autobid_settings import AutobidSettings

# SessionLocal (sync session factory) is not needed as all functions are now async
# from app.database import SessionLocal

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

# Получение настроек по профилю (refactored to async)
async def get_autobid_settings(db: AsyncSession, profile_id: str) -> Optional[AutobidSettings]:
    logger.info(
        f">>> Entering get_autobid_settings (async) for profile_id: {profile_id}")
    try:
        # Ensure profile_id type matches AutobidSettings.profile_id type for comparison
        # If AutobidSettings.profile_id is e.g. UUID, profile_id might need casting.
        # Assuming it's string for now based on original type hints.
        stmt = select(AutobidSettings).where(AutobidSettings.profile_id == profile_id)
        result = await db.execute(stmt)
        settings: Optional[AutobidSettings] = result.scalars().first()

        if not settings:
            logger.info(f"No AutobidSettings found for profile_id: {profile_id}")
            return None # Return None instead of raising HTTPException directly from service

        logger.info(
            f"<<< Exiting get_autobid_settings (async) for profile_id: {profile_id}"
        )
        return settings
    except Exception as e:
        logger.error(
            f"[ERROR] Inside get_autobid_settings (async) for {profile_id}: {e}",
            exc_info=True
        )
        # Consider raising a custom service exception or returning None
        # Re-raising the original exception might be too low-level for some callers.
        # For now, returning None on error as well, or letting specific DB errors propagate.
        return None # Or raise specific service error
    # Session managed by caller

# Обновление или создание настроек (refactored to async)
async def upsert_autobid_settings(db: AsyncSession, profile_id: str, enabled: bool, daily_limit: int) -> AutobidSettings:
    logger.info(
        f">>> Entering upsert_autobid_settings (async) for profile_id: {profile_id}"
    )
    try:
        stmt = select(AutobidSettings).where(AutobidSettings.profile_id == profile_id)
        result = await db.execute(stmt)
        settings: Optional[AutobidSettings] = result.scalars().first()

        if settings:
            logger.debug(f"Updating settings for {profile_id}")
            settings.enabled = enabled
            settings.daily_limit = daily_limit
        else:
            logger.debug(f"Creating new settings for {profile_id}")
            settings = AutobidSettings(
                profile_id=profile_id, # Ensure profile_id type matches model
                enabled=enabled,
                daily_limit=daily_limit
            )
            db.add(settings)

        await db.commit()
        await db.refresh(settings)
        logger.info(
            f"<<< Exiting upsert_autobid_settings (async) for profile_id: "
            f"{profile_id}"
        )
        return settings
    except Exception as e: # Catch potential commit or refresh errors
        await db.rollback()
        logger.error(
            f"[ERROR] Inside upsert_autobid_settings (async) for {profile_id}: {e}",
            exc_info=True
        )
        # Re-raise a more specific service-level exception or the original one
        # depending on how the calling code should handle it.
        raise # Re-raise the caught exception after rollback
    # Session managed by caller
