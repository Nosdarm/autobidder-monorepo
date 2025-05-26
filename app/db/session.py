import os
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool 


DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./app.db") 


engine = create_async_engine(
    DATABASE_URL,
    echo=True, 
    connect_args={"check_same_thread": False},
    poolclass=NullPool 
)


AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency function that yields an async SQLAlchemy session.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
          
        except Exception:
            await session.rollback()
            raise
   