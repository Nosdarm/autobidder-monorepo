from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.autobid_settings import AutobidSettings
from app.schemas.autobid import AutobidSettingsUpdate


def get_settings_for_profile(profile_id: str, db: Session):
    settings = db.query(AutobidSettings).filter(
        AutobidSettings.profile_id == profile_id).first()
    if not settings:
        # Автоматически создаём настройки, если не существуют
        settings = AutobidSettings(profile_id=profile_id)
        db.add(settings)
        db.commit()
        db.refresh(settings)
    return settings


def update_settings_for_profile(
        profile_id: str,
        data: AutobidSettingsUpdate,
        db: Session):
    settings = db.query(AutobidSettings).filter(
        AutobidSettings.profile_id == profile_id).first()
    if not settings:
        raise HTTPException(status_code=404, detail="Настройки не найдены")

    settings.enabled = data.enabled
    settings.interval_minutes = data.interval_minutes
    settings.daily_limit = data.daily_limit
    db.commit()
    db.refresh(settings)
    return settings
