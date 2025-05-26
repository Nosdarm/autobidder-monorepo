# app/services/captcha_service.py
import httpx
import os # Keep os if needed for other parts, otherwise remove
import asyncio
from app.config import settings # Import settings

# CAPTCHA_API_KEY = os.getenv("CAPTCHA_API_KEY") # Replaced by settings
# CAPTCHA_PROVIDER = os.getenv( # Replaced by settings
#     "CAPTCHA_PROVIDER",
#     "2captcha")

if not settings.CAPTCHA_API_KEY:
    raise ValueError("❌ CAPTCHA_API_KEY не установлен в .env или настройках")


async def solve_cloudflare(url: str, sitekey: str) -> str:
    """
    Отправляет задачу в 2Captcha или CapMonster и возвращает решение
    (g-recaptcha-response)
    """
    task_data = {
        "clientKey": settings.CAPTCHA_API_KEY, # Use settings
        "task": {
            "type": "HCaptchaTaskProxyless",
            "websiteURL": url,
            "websiteKey": sitekey
        }
    }

    async with httpx.AsyncClient() as client:
        # 1. Отправляем задачу
        create_task_url = str(settings.CAPMONSTER_CREATE_TASK_URL) # Use settings
        resp = await client.post(create_task_url, json=task_data)
        task_id = resp.json().get("taskId")
        if not task_id:
            raise RuntimeError(f"❌ Не удалось создать задачу: {resp.text}")

        # 2. Ждём решения
        get_result_url = str(settings.CAPMONSTER_GET_TASK_URL) # Use settings
        payload = {"clientKey": settings.CAPTCHA_API_KEY, "taskId": task_id} # Use settings
        for _ in range(30):
            await asyncio.sleep(5)
            result = await client.post(get_result_url, json=payload)
            status = result.json()
            if status["status"] == "ready":
                return status["solution"]["gRecaptchaResponse"]

    raise TimeoutError("❌ Решение капчи не получено за отведённое время.")
