# app/services/captcha_service.py
import httpx
import os
import asyncio

CAPTCHA_API_KEY = os.getenv("CAPTCHA_API_KEY")
CAPTCHA_PROVIDER = os.getenv("CAPTCHA_PROVIDER", "2captcha")  # можно переключать позже

if not CAPTCHA_API_KEY:
    raise ValueError("❌ CAPTCHA_API_KEY не установлен в .env")

async def solve_cloudflare(url: str, sitekey: str) -> str:
    """
    Отправляет задачу в 2Captcha или CapMonster и возвращает решение (g-recaptcha-response)
    """
    task_data = {
        "clientKey": CAPTCHA_API_KEY,
        "task": {
            "type": "HCaptchaTaskProxyless",
            "websiteURL": url,
            "websiteKey": sitekey
        }
    }

    async with httpx.AsyncClient() as client:
        # 1. Отправляем задачу
        resp = await client.post("https://api.capmonster.cloud/createTask", json=task_data)
        task_id = resp.json().get("taskId")
        if not task_id:
            raise RuntimeError(f"❌ Не удалось создать задачу: {resp.text}")

        # 2. Ждём решения
        for _ in range(30):
            await asyncio.sleep(5)
            result = await client.post("https://api.capmonster.cloud/getTaskResult", json={"clientKey": CAPTCHA_API_KEY, "taskId": task_id})
            status = result.json()
            if status["status"] == "ready":
                return status["solution"]["gRecaptchaResponse"]

    raise TimeoutError("❌ Решение капчи не получено за отведённое время.")
