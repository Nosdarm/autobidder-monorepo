# backend/app/models/prompt.py

# --- Импорты для SQLAlchemy ---
from sqlalchemy import Column, String, Text
from app.db.base import Base  # Импортируем Base из нашего файла base.py

# --- Импорты для Pydantic ---
# Pydantic schemas moved to app.schemas.ai_prompt
# from pydantic import BaseModel, ConfigDict

# --- SQLAlchemy Модель ---
# Описывает структуру таблицы 'prompts' в базе данных.


class Prompt(Base):
    """
    SQLAlchemy модель для таблицы 'prompts'.
    """
    __tablename__ = "prompts"  # Имя таблицы в БД

    # Определяем колонки таблицы:
    # id будет строкой, первичным ключом и индексированным
    id = Column(String, primary_key=True, index=True)
    # Текст промпта, тип Text для длинных строк, не может быть пустым (NULL)
    prompt_text = Column(Text, nullable=False)

# --- Pydantic Схемы ---
# Pydantic schemas have been moved to app.schemas.ai_prompt.py
# Definitions below are now removed from this file.
