# app/schemas/ai_prompt.py

from pydantic import BaseModel, Field
from typing import Optional

# --- Схемы для AI Промптов ---

# Базовая схема
class PromptBase(BaseModel):
    name: str = Field(..., description="Name for the prompt")
    prompt_text: str = Field(..., description="Prompt text") # <-- ИЗМЕНЕНО 'content' на 'prompt_text'

# Схема для СОЗДАНИЯ
class PromptCreate(PromptBase):
     is_active: bool = Field(True, description="Is this prompt currently active?")
     # Наследует 'name' и 'prompt_text'

# Схема для ОБНОВЛЕНИЯ
class PromptUpdate(BaseModel):
    # name: Optional[str] = Field(None, description="New name for the prompt") # Раскомментируйте, если имя можно обновлять
    prompt_text: Optional[str] = Field(None, description="New prompt text") # <-- ИЗМЕНЕНО 'content' на 'prompt_text'
    is_active: Optional[bool] = Field(None, description="New active status")

# Схема для ВЫВОДА
class PromptOut(PromptBase):
    id: int = Field(..., description="Prompt ID (Integer)")
    profile_id: str = Field(..., description="Associated Profile ID (UUID as string)")
    is_active: bool = Field(..., description="Is this prompt currently active?")
    # Наследует 'name' и 'prompt_text'

    model_config = {
        "from_attributes": True
    }

# Схема для запроса превью
class PromptPreviewRequest(BaseModel):
    description: str = Field(..., description="Job description to use for preview")