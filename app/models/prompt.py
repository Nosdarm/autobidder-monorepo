# backend/app/models/prompt.py

# --- Импорты для SQLAlchemy ---
from sqlalchemy import Column, String, Text
from app.db.base import Base  # Импортируем Base из нашего файла base.py

# --- Импорты для Pydantic ---
from pydantic import BaseModel, ConfigDict

# --- SQLAlchemy Модель ---
# Описывает структуру таблицы 'prompts' в базе данных.
class Prompt(Base):
    """
    SQLAlchemy модель для таблицы 'prompts'.
    """
    __tablename__ = "prompts" # Имя таблицы в БД

    # Определяем колонки таблицы:
    # id будет строкой, первичным ключом и индексированным
    id = Column(String, primary_key=True, index=True)
    # Текст промпта, тип Text для длинных строк, не может быть пустым (NULL)
    prompt_text = Column(Text, nullable=False)


# --- Pydantic Схемы ---
# Описывают структуру данных для API запросов и ответов.

class PromptTemplate(BaseModel):
    """Схема для возврата данных промпта из API."""
    id: str
    prompt_text: str
    model_config = ConfigDict(from_attributes=True)

class PromptTemplateCreate(BaseModel):
    """Схема для данных, принимаемых при создании нового промпта."""
    id: str
    prompt_text: str

# --- НОВАЯ СХЕМА ДЛЯ ОБНОВЛЕНИЯ ---
class PromptTemplateUpdate(BaseModel):
    """Схема для данных, принимаемых при обновлении промпта (PUT)."""
    prompt_text: str # Оставляем только изменяемое поле

class PromptRequest(BaseModel):
    """Схема для данных, принимаемых эндпоинтом /preview."""
    prompt_id: str
    description: str

class PromptResponse(BaseModel):
    """Схема для данных, возвращаемых эндпоинтом /preview."""
    preview: str