from pydantic import BaseModel

class AutobidSettingsUpdate(BaseModel):
    enabled: bool
    daily_limit: int

class AutobidSettingsOut(BaseModel):
    profile_id: str
    enabled: bool
    daily_limit: int

    class Config:
        orm_mode = True
