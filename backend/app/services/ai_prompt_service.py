from openai import AsyncOpenAI # Используем асинхронный клиент

# !!! Важно: Создайте клиент правильно !!!
# Лучше создать его один раз при старте приложения или через DI FastAPI, 
# а не внутри каждой функции. Убедитесь, что API ключ доступен.
# Пример (убедитесь, что ключ задан через переменную окружения OPENAI_API_KEY):
client = AsyncOpenAI(
    timeout=15.0, # Увеличил таймаут для примера
)

async def generate_preview(full_text: str):
    try:
        chat_completion = await client.chat.completions.create(
             model="gpt-4o-mini", # Или ваша модель
             messages=[
                 {"role": "system", "content": "You are a concise assistant. Generate a brief preview or summary of the user's text."},
                 {"role": "user", "content": full_text}
             ]
        )
        # Получаем результат (проверьте структуру ответа в док-ции V1+)
        preview_text = chat_completion.choices[0].message.content
        return preview_text.strip() if preview_text else "Could not generate preview."
    except Exception as e:
        # Добавьте логирование ошибки
        print(f"Error calling OpenAI API: {e}") 
        # Верните сообщение об ошибке или выбросите исключение, 
        # чтобы FastAPI мог вернуть 500 Internal Server Error
        return "Error generating preview due to API issue."