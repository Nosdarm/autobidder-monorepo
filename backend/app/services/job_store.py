# app/browser/browser_bidder.py
import os
import asyncio
import random
from playwright.async_api import async_playwright
from app.services.captcha_service import solve_cloudflare
from app.services.job_store import is_job_seen, save_job

USER_DATA_DIR = "user_data"


async def run_browser_bidder_for_profile(profile_id: str):
    print(f"[▶️ START] Профиль {profile_id}")
    profile_dir = os.path.join(USER_DATA_DIR, profile_id)

    if not os.path.exists(profile_dir):
        print(f"[❌] user_data_dir не найден: {profile_dir}")
        return

    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir=profile_dir,
            headless=False
        )
        page = await context.new_page()
        await page.goto("https://www.upwork.com/")

        # 👁 Проверка на капчу от Cloudflare
        if await page.locator('[data-sitekey]').count() > 0:
            print("[⚠️] Обнаружена капча, пытаемся решить...")
            sitekey = await page.get_attribute('[data-sitekey]', 'data-sitekey')
            token = await solve_cloudflare("https://www.upwork.com/", sitekey)

            await page.evaluate(
                "document.querySelector('textarea[name=\"g-recaptcha-response\"]')"
                ".value = arguments[0];",
                token
            )

            print("[✅] Токен вставлен. Обновляем страницу...")
            await page.reload()
            await asyncio.sleep(5)

        # 🔁 Имитируем действия пользователя
        await page.mouse.move(200, 300)
        await asyncio.sleep(1)
        await page.mouse.wheel(0, 1000)
        await asyncio.sleep(1)
        await page.keyboard.press("Tab")
        await page.keyboard.type("python")
        await asyncio.sleep(1)

        # ⏳ Ждём случайное время перед откликом (1–10 минут)
        delay = random.randint(60, 600)
        print(f"[⏱️] Ждём {delay} секунд перед откликом...")
        await asyncio.sleep(delay)

        # Переход на страницу проектов
        await page.goto("https://www.upwork.com/ab/find-work/")
        title = await page.title()
        url = page.url
        print(f"[✅ OK] Текущая страница: {title}")
        print(f"[INFO] URL: {url}")

        try:
            await page.wait_for_selector("a[data-cy='user-settings-menu']", timeout=5000)
            print(f"[✅] Успешно вошли в аккаунт: элемент профиля найден")
        except BaseException:
            print(f"[⚠️] Возможно, не авторизованы — элемент профиля не найден")

        # 📥 Сбор джобов
        job_cards = await page.locator(".job-tile-title a").all()
        jobs = []
        for job in job_cards:
            title = await job.inner_text()
            href = await job.get_attribute("href")
            job_id = href.strip().split("/")[-1]
            # последний фрагмент URL

            if is_job_seen(job_id):
                print(f"[⏭️] Уже видели: {job_id} — пропускаем")
                continue

            full_link = f"https://www.upwork.com{href}"
            jobs.append(
                {"id": job_id, "title": title.strip(), "link": full_link})
            save_job(job_id, title.strip(), full_link, profile_id)

        print(f"[📋] Найдено новых заданий: {len(jobs)}")

        for job in jobs:
            print(f"[➡️] Открываем: {job['title']}\n   {job['link']}")
            try:
                await page.goto(job['link'])
                await asyncio.sleep(2)
                await page.wait_for_selector("text='Submit a proposal'", timeout=5000)
                await page.click("text='Submit a proposal'")
                await asyncio.sleep(3)
                print(f"[✅] Открыта форма подачи заявки")
                screenshot_path = (
                    f"screenshots/{profile_id}_{job['id']}_proposal.png"
                )
                os.makedirs("screenshots", exist_ok=True)
                await page.screenshot(path=screenshot_path)
                print(f"[📷] Скриншот формы: {screenshot_path}")
            except Exception as e:
                print(f"[⚠️] Ошибка при открытии {job['link']}: {e}")

        await asyncio.sleep(3)
        await context.close()
