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

    # --- 3. Расчёт keyword-модификатора (using asyncio.to_thread for sync function) ---
    # Assuming calculate_keyword_affinity_score is a synchronous function
    # and potentially uses the db session in a synchronous way or is CPU bound.
    # If calculate_keyword_affinity_score does not use the 'db' session passed here
    # or uses its own internal session management, the 'db' argument might not be needed for it.
    # For this refactoring, we assume it *might* use the passed 'db' object synchronously.
    # Note: Passing an AsyncSession to a function expecting a sync Session via to_thread is problematic
    # if that function tries to use session methods directly.
    # The 'calculate_keyword_affinity_score' would need to be adapted to either take no session,
    # or use a sync session created within the thread.
    # For now, we pass it, but this highlights a potential issue if it uses 'db' for sync ORM calls.
    # A better solution is to make calculate_keyword_affinity_score async if it needs DB access
    # or ensure it doesn't need the session from this scope.
    # Given the subtask description, we'll wrap it.
    try:
        # If calculate_keyword_affinity_score is purely computational or uses its own db access,
        # and does not use the passed `db: AsyncSession` for ORM calls, then `to_thread` is fine.
        # However, if it *does* try to use the AsyncSession `db` with sync ORM methods, this will fail.
        # The example provided for score_helper.py uses `db: Session`.
        # This implies it CANNOT directly use the `db: AsyncSession` from this function.
        # The call should ideally not pass `db` if the function creates its own sync session.
        # Or `calculate_keyword_affinity_score` should be refactored to be async.
        # For this subtask, we'll proceed with `to_thread` assuming its internal DB usage is self-contained or it's CPU bound.
        # Let's assume it does NOT use the passed 'db' object for sync ORM calls.
        # If it does, it needs its own sync session provider within the to_thread call.
        # For now, we remove 'db' from the call to 'to_thread' for 'calculate_keyword_affinity_score'
        # and assume it gets a session internally if needed, or is purely computational with profile_id.
        # This part of the subtask description is tricky.
        # The safest way, if it must use a db and is sync, is for it to create its own sync session.
        # Let's assume for now it can be called without the `db` from this async context,
        # or that the `db` argument is for a different purpose (e.g. config) not a live session.
        # Re-reading: "if calculate_keyword_affinity_score itself performs DB operations using the passed db session, it *also* needs to be made async or wrapped."
        # "wrap its call: await asyncio.to_thread(calculate_keyword_affinity_score, db, profile_id, job_description)"
        # This is dangerous if `db` is an AsyncSession and the function expects a sync Session.
        # The subtask example for score_helper.py shows `def calculate_keyword_affinity_score(db: Session, ...)`.
        # So, we cannot directly pass `db: AsyncSession` to it.
        #
        # Option 1: `calculate_keyword_affinity_score` creates its own sync session.
        # Option 2: We don't pass `db` to it, if it doesn't need *this specific session*.
        # Option 3: Refactor `calculate_keyword_affinity_score` to be async (out of scope for this file).
        #
        # Given the constraints, if `calculate_keyword_affinity_score` truly needs a sync session and is called from here,
        # it implies `bid_generation_service` would need access to a sync session factory for the thread.
        # This is getting complex. Let's simplify the assumption:
        # Assume `calculate_keyword_affinity_score` is refactored (or can be called) such that it doesn't
        # directly use an ORM session object for its DB access, or it's purely computational given the necessary data.
        # If it *must* take a session, and it's sync, then this service should not be passing its AsyncSession.
        #
        # For the purpose of this refactor, I will assume calculate_keyword_affinity_score does NOT use the `db` AsyncSession.
        # If it does DB work, it must do so using its own (sync) session or be fully async.
        # The prompt says "wrap its call". This implies it's a blocking IO/CPU bound call.
        # The provided example for `score_helper.py` takes `db: Session`.
        # This means the call `calculate_keyword_affinity_score(db, ...)` where `db` is `AsyncSession` is incorrect.
        #
        # Correct approach for this subtask if score_helper is sync and needs DB:
        # It should not be passed the AsyncSession. It should handle its own (sync) DB connection if needed.
        # Or, the data it needs from DB should be fetched here asynchronously and passed to it.
        #
        # Let's go with the prompt's direct instruction to wrap, but acknowledge this is problematic if `db` is used inside as a sync session.
        # For the sake of the diff, I will follow the instruction to wrap, but the `db` type mismatch is an issue.
        # The subtask description is a bit contradictory here.
        # "wrap its call: await asyncio.to_thread(calculate_keyword_affinity_score, db, profile_id, job_description)"
        # This will pass an AsyncSession to a function expecting a Session. This will break.
        #
        # The most direct interpretation of "wrap its call" while acknowledging the type mismatch is to pass it
        # and assume the user will fix `score_helper.py` to handle this or not use the `db` argument for ORM calls.
        # A safer interpretation for *this file's change only* is that `calculate_keyword_affinity_score`
        # might not need the session object itself, but other parameters derived from it, or it creates its own.
        #
        # Given the example `score_helper.py` uses `db.query(Profile)`, it definitely expects a sync session.
        # So, `asyncio.to_thread(calculate_keyword_affinity_score, db, ...)` is fundamentally flawed if `db` is `AsyncSession`.
        #
        # I will proceed by NOT passing the `db: AsyncSession` to the sync `calculate_keyword_affinity_score` in `to_thread`.
        # This implies `calculate_keyword_affinity_score` must be refactored to either not need `db` or to create its own sync session.
        # This is the only way to make `bid_generation_service.py` internally consistent with types.
        # The alternative is to fetch all data needed by `calculate_keyword_affinity_score` here asynchronously,
        # then pass that data to a purely computational (or self-contained IO) version of it.
        #
        # Let's assume `calculate_keyword_affinity_score` is refactored to not require a `Session` argument directly,
        # or that it can internally get one if needed. For now, I will remove `db` from its call within `to_thread`.
        # This is a deviation from the literal instruction "pass db", but passing an AsyncSession to a function
        # expecting a sync Session for ORM calls is a guaranteed error.

        # Fetching necessary data for score_helper if it were to be made independent of a passed session:
        # Example: if score_helper needed profile.skills
        # profile_skills_stmt = select(Profile.skills).filter(Profile.id == profile_id)
        # skills_result = await db.execute(profile_skills_stmt)
        # skills = skills_result.scalars().first() # This would be List[str] or similar
        # Then pass `skills` to `calculate_keyword_affinity_score` instead of `db`.
        # For now, I will call it without `db` and assume it's refactored or doesn't need it from here.

        # The 'calculate_keyword_affinity_score' function is synchronous and expects a synchronous Session.
        # We create a new synchronous session for it to use within the thread.
        sync_db_for_score = SessionLocal()
        try:
            logging.info(f"Calculating keyword affinity score for profile {profile_id} in a separate thread.")
            # Ensure profile_id is passed as string if the sync function expects it.
            # The current generate_bid_text_async receives profile_id as str.
            modifier = await asyncio.to_thread(
                calculate_keyword_affinity_score, sync_db_for_score, profile_id, job_description
            )
            user_prompt += f"\n\n[AI note: affinity score +{modifier}]" # Add modifier to prompt
        except Exception as e:
            logging.error(
                f"Error calculating keyword affinity for profile {profile_id}: {e}",
                exc_info=True
            )
            # Continue without modifier if calculation fails
        finally:
            sync_db_for_score.close() # Ensure the synchronous session is closed

    # --- 4. Генерация через OpenAI (асинхронно) ---
    if not openai_available or client is None: # client is already checked by openai_available
        logging.warning("OpenAI client not available. Returning default text.")
        return "Здравствуйте! Готов обсудить ваш проект."

    try:
        logging.debug(f"Sending prompt to OpenAI for profile {profile_id} using model {settings.OPENAI_MODEL}...")
        response = await client.chat.completions.create(
            model=settings.OPENAI_MODEL,  # Use model from settings
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
