from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import settings

# Асинхронный движок
engine = create_async_engine(
    settings.DATABASE_URL
    # echo=True, # Removed echo=True as per example's implication
)

# Фабрика сессий
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Базовый класс для моделей
Base = declarative_base()

# Зависимость для роутеров
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
