# app/services/bid_generation_service.py

import logging
import asyncio # Added asyncio
from typing import Optional # Added Optional
from sqlalchemy.ext.asyncio import AsyncSession # Added AsyncSession
from sqlalchemy import select # Added select
# Импортируем AsyncOpenAI и OpenAIError
from openai import AsyncOpenAI, OpenAIError # Assuming this is already async compatible
from app.models.ai_prompt import AIPrompt # Ensure this model is compatible with async sessions if used directly
from app.services.score_helper import calculate_keyword_affinity_score
from app.config import settings
from app.database import SessionLocal # Added for sync session workaround

# --- Клиент OpenAI ---
# Лучше инициализировать клиент один раз.
# В реальном приложении его можно передавать через зависимости FastAPI.
# Для простоты примера - создаем его здесь.
# Убедитесь, что ваш API-ключ OpenAI доступен (например, через переменную
# окружения OPENAI_API_KEY)
try:
    if settings.OPENAI_API_KEY:
        client = AsyncOpenAI(
            api_key=settings.OPENAI_API_KEY,
            timeout=settings.OPENAI_TIMEOUT,
        )
        openai_available = True
    else:
        logging.error("OpenAI API key not configured in settings. AI generation will be disabled.")
        client = None
        openai_available = False
except Exception as e:
    logging.error(
        f"Failed to initialize OpenAI client even with API key: {e}. "
        "AI generation will be disabled."
    )
    client = None
    openai_available = False
# --------------------


async def generate_bid_text_async(
        job: dict,
        profile_id: str,
        db: AsyncSession) -> str: # Changed db type to AsyncSession
    """
    Асинхронно генерирует текст отклика на вакансию с использованием AI.
    """
    logging.info(f"Generating bid text for profile_id: {profile_id}")

    # --- 1. Получение активного промпта для профиля (Async) ---
    prompt_obj: Optional[AIPrompt] = None # Ensure Optional is imported
    try:
        prompt_stmt = select(AIPrompt).filter(
            AIPrompt.profile_id == profile_id,
            AIPrompt.is_active == True # Make sure is_active is a boolean column or use .is_(True)
        )
        prompt_result = await db.execute(prompt_stmt)
        prompt_obj = prompt_result.scalars().first()
    except Exception as e:
        logging.error(
            f"Database error fetching prompt for profile {profile_id}: {e}",
            exc_info=True
        )
        # prompt_obj remains None

    if not prompt_obj:
        logging.warning(
            f"No active prompt found for profile {profile_id}. "
            "Returning default text."
        )
        return "Здравствуйте! Заинтересован в вашем проекте." # Default Russian text

    # --- 2. Подготовка промпта для AI ---
    job_description = job.get("description", "")
    user_prompt = prompt_obj.prompt_text.replace(
        "{job_description}", job_description.strip()
    )

    # --- 3. Расчёт keyword-модификатора ---
    modifier = 0.0 # Default modifier
    sync_db_for_score = None # Initialize sync_db_for_score before try block
    try:
        # Create sync session only if we are going to use it
        sync_db_for_score = SessionLocal()
        logging.info(f"Calculating keyword affinity score for profile {profile_id} in a separate thread.")
        # Ensure all arguments passed to calculate_keyword_affinity_score are of the correct type it expects.
        # profile_id is already a string from the function signature.
        modifier = await asyncio.to_thread(
            calculate_keyword_affinity_score, sync_db_for_score, profile_id, job_description
        )
        user_prompt += f"\n\n[AI note: affinity score +{modifier}]" # Add modifier to prompt
    except Exception as e_score:
        logging.error(
            f"Error calculating keyword affinity for profile {profile_id}: {e_score}",
            exc_info=True
        )
        # Continue without modifier if calculation fails, modifier remains 0.0
    finally:
        if sync_db_for_score: # Check if it was created before trying to close
            sync_db_for_score.close()
            logging.debug("Synchronous session for score calculation closed.")

    # --- 4. Генерация через OpenAI (асинхронно) ---
    if not openai_available or client is None:
        logging.warning("OpenAI client not available. Returning default text for job related to profile %s.", profile_id)
        return "Здравствуйте! Готов обсудить ваш проект." # Ensure this is a valid return path

    # This try block is for the OpenAI API call itself
    try:
        logging.debug(f"Sending prompt to OpenAI for profile {profile_id} using model {settings.OPENAI_MODEL}...")
        response = await client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a helpful assistant writing job proposals "
                        "for a freelancer."
                    ),
                },
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.7,
            max_tokens=350
        )
        generated_text = response.choices[0].message.content.strip()
        logging.info(
            f"Successfully generated bid text for profile {profile_id}."
        )
        return generated_text # Return the generated text

    except OpenAIError as e_openai_api:  # More specific error for OpenAI API issues
        logging.error(
            f"OpenAI API error for profile {profile_id}: {e_openai_api}", exc_info=True
        )
        # Return a specific message or the default one
        return "Здравствуйте! К сожалению, произошла ошибка при генерации отклика через AI. Готов обсудить ваш проект."
    except Exception as e_openai_general: # Catch any other unexpected errors during OpenAI part
        logging.error(
            f"Unexpected error during OpenAI generation for profile {profile_id}: {e_openai_general}",
            exc_info=True
        )
        return "Здравствуйте! Готов обсудить ваш проект." # Fallback default text
