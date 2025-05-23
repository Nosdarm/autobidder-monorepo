from openai import AsyncOpenAI  # Используем асинхронный клиент
from app.config import settings
import logging # For logging cache operations

# Initialize cache
preview_cache = {}
MAX_CACHE_SIZE = 100
logger = logging.getLogger(__name__)

# !!! Важно: Создайте клиент правильно !!!
# Лучше создать его один раз при старте приложения или через DI FastAPI,
# а не внутри каждой функции. Убедитесь, что API ключ доступен.
# Пример (убедитесь, что ключ задан через переменную окружения OPENAI_API_KEY):
client = AsyncOpenAI(
    api_key=settings.OPENAI_API_KEY,
    timeout=settings.OPENAI_TIMEOUT,
)


async def generate_preview(full_text: str):
    # Check cache first
    if full_text in preview_cache:
        logger.info("Cache hit for generate_preview.")
        return preview_cache[full_text]

    logger.info("Cache miss for generate_preview. Calling API.")
    try:
        chat_completion = await client.chat.completions.create(
            model=settings.OPENAI_MODEL,  # Используем модель из настроек
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a concise assistant. Generate a brief "
                        "preview or summary of the user's text."
                    ),
                },
                {"role": "user", "content": full_text},
            ]
        )
        # Получаем результат (проверьте структуру ответа в док-ции V1+)
        preview_text_obj = chat_completion.choices[0].message.content
        
        if preview_text_obj:
            preview_text = preview_text_obj.strip()
            # Cache successful result
            if len(preview_cache) >= MAX_CACHE_SIZE:
                logger.info(f"Cache is full (size {len(preview_cache)}). Clearing cache.")
                preview_cache.clear()
            preview_cache[full_text] = preview_text
            logger.info("Successfully cached new preview.")
            return preview_text
        else:
            logger.warning("OpenAI returned empty preview text.")
            return "Could not generate preview."
            
    except Exception as e:
        # Добавьте логирование ошибки
        logger.error(f"Error calling OpenAI API: {e}", exc_info=True)
        # Верните сообщение об ошибке или выбросите исключение,
        # чтобы FastAPI мог вернуть 500 Internal Server Error
        return "Error generating preview due to API issue."
