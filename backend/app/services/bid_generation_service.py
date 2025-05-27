# app/services/bid_generation_service.py

import logging  # asyncio removed
from sqlalchemy.orm import Session
# Импортируем AsyncOpenAI и OpenAIError
from openai import AsyncOpenAI, OpenAIError
from app.models.ai_prompt import AIPrompt
from app.services.score_helper import calculate_keyword_affinity_score
from app.config import settings

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
        db: Session) -> str:
    """
    Асинхронно генерирует текст отклика на вакансию с использованием AI.
    """
    logging.info(f"Generating bid text for profile_id: {profile_id}")

    # --- 1. Получение активного промпта для профиля ---
    # ПРИМЕЧАНИЕ: Этот DB-запрос все еще синхронный. Если он станет узким местом,
    # его нужно будет сделать асинхронным (с AsyncSession) или вынести в
    # asyncio.to_thread.
    try:
        prompt_obj: AIPrompt | None = (
            db.query(AIPrompt)
            .filter(AIPrompt.profile_id == profile_id, AIPrompt.is_active)
            .first()
        )
    except Exception as e:
        logging.error(
            f"Database error fetching prompt for profile {profile_id}: {e}",
            exc_info=True
        )
        prompt_obj = None

    if not prompt_obj:
        logging.warning(
            f"No active prompt found for profile {profile_id}. "
            "Returning default text."
        )
        return "Здравствуйте! Заинтересован в вашем проекте."

    # --- 2. Подготовка промпта для AI ---
    job_description = job.get("description", "")
    user_prompt = prompt_obj.prompt_text.replace(
        "{job_description}", job_description.strip()
    )

    # --- 3. Расчёт keyword-модификатора ---
    # ПРИМЕЧАНИЕ: Эта функция тоже синхронная. При необходимости - в
    # asyncio.to_thread.
    try:
        modifier = calculate_keyword_affinity_score(
            db, profile_id, job_description
        )
        # Добавляем для информации AI
        user_prompt += f"\n\n[AI note: affinity score +{modifier}]"
    except Exception as e:
        logging.error(
            f"Error calculating keyword affinity for profile {profile_id}: {e}",
            exc_info=True
        )
        # Продолжаем без модификатора

    # --- 4. Генерация через OpenAI (асинхронно) ---
    if not openai_available or client is None:
        logging.warning("OpenAI client not available. Returning default text.")
        return "Здравствуйте! Готов обсудить ваш проект."

    try:
        logging.debug(f"Sending prompt to OpenAI for profile {profile_id}...")
        response = await client.chat.completions.create(
            model="gpt-4",  # Или другая модель, например gpt-3.5-turbo
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
            max_tokens=350  # Немного увеличил лимит
        )
        generated_text = response.choices[0].message.content.strip()
        logging.info(
            f"Successfully generated bid text for profile {profile_id}."
        )
        return generated_text

    except OpenAIError as e:  # Ловим специфичные ошибки OpenAI
        logging.error(
            f"OpenAI API error for profile {profile_id}: {e}", exc_info=True
        )
        return (
            "Здравствуйте! К сожалению, произошла ошибка при генерации "
            "отклика. Готов обсудить ваш проект."
        )
    except Exception as e:
        logging.error(
            f"Unexpected error during generation for profile {profile_id}: {e}",
            exc_info=True
        )
        return "Здравствуйте! Готов обсудить ваш проект."

# --- Тут могут быть другие функции сервиса ---
