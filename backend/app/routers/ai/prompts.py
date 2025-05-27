# backend/app/routers/ai/prompts.py

from fastapi import APIRouter, Depends, HTTPException, status, Request # Add Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.limiter import limiter # Import the shared limiter instance
# Используем ваш путь импорта get_db
from app.database import get_db
# Используем ваш путь импорта ORM Модели
# from app.models.orm_prompt import Prompt as ORMPrompt # Replaced
from app.models.ai_prompt import AIPrompt as ORMModelForPrompts # Use the target ORM model
# Импортируем все схемы
# from app.models.prompt import ( # Replaced with imports from app.schemas.ai_prompt
#     PromptTemplate,
#     PromptTemplateCreate,
#     PromptTemplateUpdate,
#     PromptRequest,
#     PromptResponse,
# )
from app.schemas.ai_prompt import ( # Import consolidated schemas
    AIPromptCreate,
    AIPromptOut,
    AIPromptUpdate,
    AIPromptPreviewRequest,
    AIPromptPreviewResponse,
)
# Импортируем ваш сервис
from app.services.ai_prompt_service import generate_preview

router = APIRouter(
    prefix="/prompts",
    tags=["AI Prompts"], # Changed tag for consistency if needed, or keep as "AI Prompts"
)

# CRUD для шаблонов промптов


@router.post("/", response_model=AIPromptOut, # Use new schema
             status_code=status.HTTP_201_CREATED)
async def create_prompt(
    prompt_in: AIPromptCreate, # Use new schema
    db: AsyncSession = Depends(get_db),
):
    # <<< Печатаем ID сессии, полученной через Depends(get_db) >>>
    print(f"--- [API create_prompt] Received db session with id: {id(db)} ---")

    # Ensure all fields from AIPromptCreate are passed to ORMModelForPrompts
    # AIPromptCreate has: name, prompt_text, profile_id, is_active
    # ORMModelForPrompts (AIPrompt) has: id, profile_id, name, prompt_text, is_active
    # id is auto-generated for AIPrompt (SQLAlchemy model)
    prompt_data = prompt_in.model_dump()
    prompt = ORMModelForPrompts(**prompt_data) # Use target ORM model
    db.add(prompt)

    # try-except для IntegrityError УБРАН для диагностики
    await db.commit()
    await db.refresh(prompt)

    # Используем model_validate вместо from_orm
    return AIPromptOut.model_validate(prompt) # Use new schema


@router.get("/", response_model=list[AIPromptOut]) # Use new schema
async def list_prompts(
    db: AsyncSession = Depends(get_db),
):
    # Для интереса
    print(f"--- [API list_prompts] Received db session with id: {id(db)} ---")
    from sqlalchemy import select
    result = await db.execute(select(ORMModelForPrompts)) # Use target ORM model
    prompts = result.scalars().all()
    return [AIPromptOut.model_validate(p) for p in prompts] # Use new schema


@router.get("/{prompt_id}", response_model=AIPromptOut) # Use new schema
async def get_prompt(
    prompt_id: str, # Assuming prompt_id is string, consistent with AIPromptOut.id
    db: AsyncSession = Depends(get_db),
):
    # Для интереса
    print(f"--- [API get_prompt] Received db session with id: {id(db)} ---")
    prompt = await db.get(ORMModelForPrompts, prompt_id) # Use target ORM model
    if not prompt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Prompt with id '{prompt_id}' not found",
        )
    return AIPromptOut.model_validate(prompt) # Use new schema


@router.put(
    "/{prompt_id}",
    response_model=AIPromptOut, # Use new schema
    summary="Update a specific prompt"
)
async def update_prompt(
    prompt_id: str, # Assuming prompt_id is string
    prompt_update: AIPromptUpdate, # Use new schema
    db: AsyncSession = Depends(get_db)
):
    # Для интереса
    print(f"--- [API update_prompt] Received db session with id: {id(db)} ---")
    prompt = await db.get(ORMModelForPrompts, prompt_id) # Use target ORM model
    if not prompt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Prompt with id '{prompt_id}' not found",
        )
    
    # Update fields from prompt_update schema
    update_data = prompt_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(prompt, key, value)
        
    try:
        await db.commit()
        await db.refresh(prompt)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500,
                            detail=f"Database error during update: {e}")
    return AIPromptOut.model_validate(prompt) # Use new schema


@router.delete("/{prompt_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_prompt(
    prompt_id: str, # Assuming prompt_id is string
    db: AsyncSession = Depends(get_db),
):
    # Для интереса
    print(f"--- [API delete_prompt] Received db session with id: {id(db)} ---")
    prompt = await db.get(ORMModelForPrompts, prompt_id) # Use target ORM model
    if not prompt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Prompt with id '{prompt_id}' not found",
        )
    try:
        await db.delete(prompt)
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500,
                            detail=f"Database error during deletion: {e}")
    return None


# The first /preview endpoint is removed as it's duplicated by the rate-limited one.

# Applying rate limit to the existing POST /preview endpoint.
# This endpoint uses generate_preview.
@router.post("/preview", response_model=AIPromptPreviewResponse) # Use new schema
@limiter.limit("5/minute") # Apply rate limit
async def preview_prompt( 
    request_data: AIPromptPreviewRequest, # Use new schema
    request: Request, # Renamed for slowapi
    db: AsyncSession = Depends(get_db),
):
    # Для интереса
    print(
        f"--- [API preview_prompt] Received db session with id: {id(db)} ---") # Log adjusted
    # Use target ORM model, assuming prompt_id in request_data refers to an AIPrompt/ORMModelForPrompts ID
    stored = await db.get(ORMModelForPrompts, request_data.prompt_id) 
    if not stored:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Prompt template with id '{request_data.prompt_id}' not found",
        )
    # Assuming 'stored' (ORMModelForPrompts) has 'prompt_text' and 'name' attributes
    # The AIPromptPreviewRequest has 'description'.
    # The service function generate_preview expects 'full_text'.
    # We need to construct full_text based on the stored prompt's text and the input description.
    full_text = f"{stored.prompt_text}\n\n{request_data.description}"
    try:
        generated_preview_text = await generate_preview(full_text) # Renamed for clarity
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"AI service error: {e}"
        )
    return AIPromptPreviewResponse(preview=generated_preview_text) # Use new schema
