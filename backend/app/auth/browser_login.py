# app/auth/browser_login.py
import asyncio
import os
import json # Added json import
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

async def save_session_from_cookies(profile_id: str, cookies: str | list[dict]):
    os.makedirs(AUTH_STATE_DIR, exist_ok=True)
    # USER_DATA_DIR is not strictly needed here as we are not using persistent context,
    # but creating AUTH_STATE_DIR is good practice.

    if isinstance(cookies, str):
        try:
            parsed_cookies = json.loads(cookies)
        except json.JSONDecodeError:
            print("[❌] Ошибка: Неверный формат JSON для cookies.")
            return
    else:
        parsed_cookies = cookies

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False, # Set to True for production/CI if needed
            args=[
                "--no-sandbox",
                "--disable-blink-features=AutomationControlled"
            ]
        )
        context = await browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            extra_http_headers={"Accept-Language": "en-US,en;q=0.9"}
        )

        try:
            await context.add_cookies(parsed_cookies)
            print("[INFO] Cookies добавлены в контекст браузера.")
        except Exception as e:
            print(f"[❌] Ошибка при добавлении cookies: {e}")
            await browser.close()
            return

        page = await context.new_page()
        test_url = "https://www.upwork.com/ab/find-work/"
        print(f"[INFO] Переход на страницу: {test_url} для проверки сессии...")

        try:
            await page.goto(test_url, wait_until="networkidle") # Wait for network to be idle

            # Check if still on the find-work page or redirected to login
            # A more robust check would be to look for a specific element that only appears when logged in.
            # For example, the user's profile picture or a logout button.
            # For now, we'll check if the URL is still the test_url and doesn't contain 'login' or 'visitor'
            current_url = page.url
            if test_url in current_url and "login" not in current_url and "visitor" not in current_url:
                state_path = os.path.join(AUTH_STATE_DIR, f"{profile_id}_auth.json")
                await context.storage_state(path=state_path)
                print(f"[✅] Сессия успешно проверена и сохранена: {state_path}")
            else:
                print(f"[❌] Ошибка проверки сессии. URL после перехода: {current_url}")
                print("[INFO] Убедитесь, что предоставленные cookies действительны и имеют правильный формат.")
                # Optionally, save a screenshot for debugging
                # await page.screenshot(path=f"debug_screenshot_{profile_id}.png")
                # print(f"[INFO] Скриншот для отладки сохранен: debug_screenshot_{profile_id}.png")

        except Exception as e:
            print(f"[❌] Ошибка при навигации или проверке сессии: {e}")
            # await page.screenshot(path=f"error_screenshot_{profile_id}.png")
            # print(f"[INFO] Скриншот ошибки сохранен: error_screenshot_{profile_id}.png")
        finally:
            await browser.close()

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Использование:")
        print("  Для ручного входа: python app/auth/browser_login.py login <profile_id>")
        print("  Для сохранения сессии из cookies: python app/auth/browser_login.py cookies <profile_id> '<json_string_of_cookies>'")
        print("  Или: python app/auth/browser_login.py cookies <profile_id> \"path/to/cookies.json\"")
        sys.exit(1)

    command = sys.argv[1]
    profile_id_arg = sys.argv[2]

    if command == "login":
        if len(sys.argv) != 3:
            print("Использование: python app/auth/browser_login.py login <profile_id>")
            sys.exit(1)
        asyncio.run(login_and_save_session(profile_id_arg))
    elif command == "cookies":
        if len(sys.argv) != 4:
            print("Использование: python app/auth/browser_login.py cookies <profile_id> '<json_string_of_cookies_or_path_to_json_file>'")
            sys.exit(1)

        cookie_input = sys.argv[3]
        cookies_data = None

        if os.path.exists(cookie_input):
            try:
                with open(cookie_input, 'r') as f:
                    cookies_data = json.load(f)
                print(f"[INFO] Cookies загружены из файла: {cookie_input}")
            except Exception as e:
                print(f"[❌] Ошибка при чтении файла cookies: {e}")
                sys.exit(1)
        else:
            try:
                cookies_data = json.loads(cookie_input)
                print("[INFO] Cookies загружены из строки JSON.")
            except json.JSONDecodeError:
                print("[❌] Ошибка: Предоставленная строка cookies не является валидным JSON и не является путем к файлу.")
                sys.exit(1)

        if cookies_data:
            asyncio.run(save_session_from_cookies(profile_id_arg, cookies_data))
        else:
            print("[❌] Не удалось загрузить данные cookies.")
            sys.exit(1)
    else:
        print(f"Неизвестная команда: {command}")
        sys.exit(1)
