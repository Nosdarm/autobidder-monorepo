import logging
from sqlalchemy.orm import Session
from sqlalchemy import select
from fastapi import HTTPException
from app.models import AutobidSettings # Убедитесь, что AutobidSettings импортирован правильно

# ---> ВАЖНО: Импортируйте SessionLocal (или ваш аналог) <---
# ---> Путь может отличаться в вашем проекте <---
from app.database import SessionLocal # Предполагаем, что он здесь

# Настройка логирования (если еще не настроено глобально)
logging.basicConfig(level=logging.INFO)

# Получение всех включённых профилей (исправлено управление сессией)
def get_enabled_autobid_settings():
    logging.info(">>> Entering get_enabled_autobid_settings")
    db: Session | None = None # Инициализируем db как None
    try:
        # Создаем новую сессию ЯВНО
        db = SessionLocal()
        result = db.execute(
            select(AutobidSettings).where(AutobidSettings.enabled == True)
        )
        settings = result.scalars().all()
        logging.info(f"<<< Exiting get_enabled_autobid_settings with {len(settings)} settings")
        return settings
    except Exception as e:
        logging.error(f"[ERROR] Inside get_enabled_autobid_settings: {e}", exc_info=True)
        # Можно вернуть пустой список или перевыбросить ошибку в зависимости от логики
        return [] # Возвращаем пустой список при ошибке
    finally:
        # ГАРАНТИРОВАННО закрываем сессию
        if db is not None:
            db.close()
            logging.debug("--- Database session closed in get_enabled_autobid_settings")

# Получение настроек по профилю (исправлено управление сессией)
def get_autobid_settings(profile_id: str):
    logging.info(f">>> Entering get_autobid_settings for profile_id: {profile_id}")
    db: Session | None = None
    try:
        db = SessionLocal()
        result = db.execute(
            select(AutobidSettings).where(AutobidSettings.profile_id == profile_id)
        )
        settings = result.scalar_one_or_none()
        logging.info(f"<<< Exiting get_autobid_settings for profile_id: {profile_id}")
        if not settings:
            # Лучше не бросать HTTPException здесь, а вернуть None или кастомное исключение,
            # т.к. эта функция может вызываться вне HTTP контекста.
            # Оставим пока так для минимальных изменений.
             raise HTTPException(status_code=404, detail="Autobid settings not found")
        return settings
    except Exception as e:
        logging.error(f"[ERROR] Inside get_autobid_settings for {profile_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error fetching autobid settings.")
    finally:
        if db is not None:
            db.close()
            logging.debug(f"--- Database session closed in get_autobid_settings for {profile_id}")


# Обновление или создание настроек (исправлено управление сессией)
def upsert_autobid_settings(profile_id: str, enabled: bool, daily_limit: int):
    logging.info(f">>> Entering upsert_autobid_settings for profile_id: {profile_id}")
    db: Session | None = None
    try:
        db = SessionLocal()
        result = db.execute(
            select(AutobidSettings).where(AutobidSettings.profile_id == profile_id)
        )
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
        logging.info(f"<<< Exiting upsert_autobid_settings for profile_id: {profile_id}")
        return settings
    except Exception as e:
        if db is not None:
            db.rollback() # Откатываем изменения при ошибке
        logging.error(f"[ERROR] Inside upsert_autobid_settings for {profile_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error upserting autobid settings.")
    finally:
        if db is not None:
            db.close()
            logging.debug(f"--- Database session closed in upsert_autobid_settings for {profile_id}")