from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Dict, Any


class BidCreateInput(BaseModel):
    profile_id: str = Field(..., description="ID профиля, с которого делается ставка")
    job_id: str = Field(..., description="ID проекта, на который делается ставка")
    amount: float = Field(..., gt=0, description="Размер ставки")
    prompt_template_id: Optional[int] = Field(None, description="ID шаблона AI-промпта (если используется)")
    generated_bid_text: Optional[str] = Field(None, description="Сгенерированный AI текст ставки (если используется)")
    bid_settings_snapshot: Optional[Dict[str, Any]] = Field(None, description="Снимок настроек ставки на момент создания")


class BidResponse(BaseModel):
    id: str
    profile_id: str
    job_id: str
    amount: float
    submitted_at: datetime
    prompt_template_id: Optional[str] = None
    generated_bid_text: Optional[str] = None
    bid_settings_snapshot: Optional[Dict[str, Any]] = None
    external_signals_snapshot: Optional[Dict[str, Any]] = None

    class Config:
        orm_mode = True
