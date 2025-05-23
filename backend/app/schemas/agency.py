from pydantic import BaseModel


class AgencyProfileCreate(BaseModel):
    name: str
    autobid_enabled: bool = False
