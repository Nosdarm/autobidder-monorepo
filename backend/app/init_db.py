from app.db.base import Base, engine
from app.models.autobid_log import AutobidLog

# ВАЖНО: импортируй все модели, которые ты хочешь создать
Base.metadata.create_all(bind=engine)

print("✅ Таблицы успешно созданы.")
