# backend/app/routers/ai/prompts.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
# Используем ваш путь импорта get_db
from app.database import get_db
# Используем ваш путь импорта ORM Модели
from app.models.orm_prompt import Prompt as ORMPrompt
# Импортируем все схемы
from app.models.prompt import (
    PromptTemplate,
    PromptTemplateCreate,
    PromptTemplateUpdate,
    PromptRequest,
    PromptResponse,
)
# Импортируем ваш сервис
from app.services.ai_prompt_service import generate_preview

router = APIRouter(
    prefix="/prompts",
    tags=["AI Prompts"],
)

# CRUD для шаблонов промптов

@router.post("/", response_model=PromptTemplate, status_code=status.HTTP_201_CREATED)
async def create_prompt(
    prompt_in: PromptTemplateCreate,
    db: AsyncSession = Depends(get_db),
):
    # <<< Печатаем ID сессии, полученной через Depends(get_db) >>>
    print(f"--- [API create_prompt] Received db session with id: {id(db)} ---")

    prompt = ORMPrompt(**prompt_in.model_dump())
    db.add(prompt)

    # try-except для IntegrityError УБРАН для диагностики
    await db.commit()
    await db.refresh(prompt)

    # Используем model_validate вместо from_orm
    return PromptTemplate.model_validate(prompt)

@router.get("/", response_model=list[PromptTemplate])
async def list_prompts(
    db: AsyncSession = Depends(get_db),
):
    print(f"--- [API list_prompts] Received db session with id: {id(db)} ---") # Для интереса
    from sqlalchemy import select
    result = await db.execute(select(ORMPrompt))
    prompts = result.scalars().all()
    return [PromptTemplate.model_validate(p) for p in prompts]

@router.get("/{prompt_id}", response_model=PromptTemplate)
async def get_prompt(
    prompt_id: str,
    db: AsyncSession = Depends(get_db),
):
    print(f"--- [API get_prompt] Received db session with id: {id(db)} ---") # Для интереса
    prompt = await db.get(ORMPrompt, prompt_id)
    if not prompt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Prompt with id '{prompt_id}' not found",
        )
    return PromptTemplate.model_validate(prompt)

@router.put(
    "/{prompt_id}",
    response_model=PromptTemplate,
    summary="Update a specific prompt"
    )
async def update_prompt(
    prompt_id: str,
    prompt_update: PromptTemplateUpdate,
    db: AsyncSession = Depends(get_db)
):
    print(f"--- [API update_prompt] Received db session with id: {id(db)} ---") # Для интереса
    prompt = await db.get(ORMPrompt, prompt_id)
    if not prompt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Prompt with id '{prompt_id}' not found",
        )
    prompt.prompt_text = prompt_update.prompt_text
    try:
        await db.commit()
        await db.refresh(prompt)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error during update: {e}")
    return PromptTemplate.model_validate(prompt)

@router.delete("/{prompt_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_prompt(
    prompt_id: str,
    db: AsyncSession = Depends(get_db),
):
    print(f"--- [API delete_prompt] Received db session with id: {id(db)} ---") # Для интереса
    prompt = await db.get(ORMPrompt, prompt_id)
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
        raise HTTPException(status_code=500, detail=f"Database error during deletion: {e}")
    return None

@router.post("/preview", response_model=PromptResponse)
async def preview_prompt(
    request: PromptRequest,
    db: AsyncSession = Depends(get_db),
):
    print(f"--- [API preview_prompt] Received db session with id: {id(db)} ---") # Для интереса
    stored = await db.get(ORMPrompt, request.prompt_id)
    if not stored:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Prompt template with id '{request.prompt_id}' not found",
        )
    full_text = f"{stored.prompt_text}\n\n{request.description}"
    try:
        generated = await generate_preview(full_text)
    except Exception as e:
         raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"AI service error: {e}"
        )
    return PromptResponse(preview=generated)