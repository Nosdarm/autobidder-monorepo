# app/schemas/ai_prompt.py
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional

# Base schema for common attributes
class AIPromptBase(BaseModel):
    name: str = Field(..., description="Descriptive name for the AI prompt template")
    prompt_text: str = Field(..., description="The actual template text with placeholders like {job_description}")

# Schema for creating a new AI Prompt (input)
class AIPromptCreate(AIPromptBase):
    profile_id: str = Field(..., description="The ID of the profile this prompt belongs to")
    is_active: bool = Field(True, description="Whether this prompt is active by default")

# Schema for updating an existing AI Prompt (input, all fields optional)
class AIPromptUpdate(BaseModel):
    name: Optional[str] = Field(None, description="New name for the prompt")
    prompt_text: Optional[str] = Field(None, description="New prompt text")
    is_active: Optional[bool] = Field(None, description="New active status for the prompt")

# Schema for representing an AI Prompt in API responses (output)
class AIPromptOut(AIPromptBase):
    id: str = Field(..., description="Unique identifier for the AI prompt") # Changed from int to str
    profile_id: str = Field(..., description="The ID of the profile this prompt belongs to")
    is_active: bool = Field(..., description="Current active status of the prompt")

    model_config = ConfigDict(from_attributes=True) # Pydantic V2 for ORM mode

# Schema for requesting a preview using an AI Prompt (input)
class AIPromptPreviewRequest(BaseModel):
    prompt_id: str = Field(..., description="ID of the prompt template to use for preview")
    description: str = Field(..., description="Job description or other text to fill into the prompt")

# Schema for the response of a preview generation (output)
class AIPromptPreviewResponse(BaseModel):
    preview: str = Field(..., description="The generated preview text")
