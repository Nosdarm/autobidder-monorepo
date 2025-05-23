# app/auth/browser_login.py
import asyncio
import os
from playwright.async_api import async_playwright

AUTH_STATE_DIR = "auth_states"
USER_DATA_DIR = "user_data"

async def login_and_save_session(profile_id: str):
    os.makedirs(AUTH_STATE_DIR, exist_ok=True)
    os.makedirs(USER_DATA_DIR, exist_ok=True)

    profile_path = os.path.join(USER_DATA_DIR, profile_id)

    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir=profile_path,
            headless=False,
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            args=[
                "--start-maximized",
                "--no-sandbox",
                "--disable-blink-features=AutomationControlled"
            ]
        )
        page = await context.new_page()

        await page.set_extra_http_headers({
            "Accept-Language": "en-US,en;q=0.9"
        })

        await page.goto("https://www.upwork.com/")
        print(f"[BROWSER] Войдите вручную под профилем: {profile_id}")
        input("После входа нажмите Enter здесь...")

        state_path = os.path.join(AUTH_STATE_DIR, f"{profile_id}_auth.json")
        await context.storage_state(path=state_path)
        print(f"[✅] Сессия сохранена: {state_path}")

        await context.close()

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Использование: python app/auth/browser_login.py <profile_id>")
    else:
        asyncio.run(login_and_save_session(sys.argv[1]))
