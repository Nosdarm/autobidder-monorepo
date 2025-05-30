from sqlalchemy import String, Boolean, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class AutobidSettings(Base):
    __tablename__ = "autobid_settings"

    profile_id: Mapped[str] = mapped_column(
        String, ForeignKey("profiles.id", ondelete="CASCADE"), primary_key=True
    )
    enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    daily_limit: Mapped[int] = mapped_column(Integer, default=5)
