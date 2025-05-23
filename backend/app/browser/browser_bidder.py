import os
import asyncio
import random

from playwright.async_api import async_playwright
from app.services.captcha_service import solve_cloudflare
from app.services.bid_generation_service import generate_bid_text_async
from app.database import get_db
from app.services.autobid_log_service import log_autobid_attempt
from app.services.score_helper import calculate_keyword_affinity_score

USER_DATA_DIR = "user_data"

async def fill_rate_increase_fields(page):
    try:
        await page.get_by_label("How often do you want a rate increase?").click()
        await page.get_by_text("Every 3 months").click()
    except:
        pass

    try:
        await page.get_by_label("How much of an increase do you want?").click()
        await page.get_by_text("10%").click()
    except:
        pass

async def run_browser_bidder_for_profile(profile_id: str):
    print(f"[▶️ START] Профиль {profile_id}")
    profile_dir = os.path.join(USER_DATA_DIR, profile_id)

    if not os.path.exists(profile_dir):
        print(f"[❌] user_data_dir не найден: {profile_dir}")
        return

    db = next(get_db())

    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir=profile_dir,
            headless=False
        )
        page = await context.new_page()
        await page.goto("https://www.upwork.com/")

        if await page.locator('[data-sitekey]').count() > 0:
            sitekey = await page.get_attribute('[data-sitekey]', 'data-sitekey')
            token = await solve_cloudflare("https://www.upwork.com/", sitekey)
            await page.evaluate("""document.querySelector('textarea[name="g-recaptcha-response"]').value = arguments[0];""", token)
            await page.reload()
            await asyncio.sleep(5)

        await page.mouse.move(200, 300)
        await asyncio.sleep(random.uniform(1, 2))
        await page.mouse.wheel(0, 1000)
        await asyncio.sleep(1)

        await page.goto("https://www.upwork.com/ab/find-work/")
        job_cards = await page.locator(".job-tile-title a").all()
        jobs = []
        for job in job_cards:
            title = await job.inner_text()
            href = await job.get_attribute("href")
            jobs.append({"title": title.strip(), "link": f"https://www.upwork.com{href}"})

        for job in jobs[:1]:
            await page.goto(job["link"])
            await asyncio.sleep(3)

            try:
                await page.click("text=Submit a Proposal", timeout=5000)
                await page.wait_for_load_state("networkidle")
            except:
                continue

            try:
                desc_el = await page.locator("div[data-test='job-description']").first
                description = await desc_el.inner_text()
            except:
                description = "Описание отсутствует"

            job_data = {
                "title": job["title"],
                "description": description.strip()
            }

            bid_text = await generate_bid_text_async(job_data, profile_id=profile_id, db=db)
            await page.fill("textarea[name='coverLetter']", bid_text)
            await fill_rate_increase_fields(page)

            try:
                await page.click("button:has-text('Submit Proposal')")
                await asyncio.sleep(2)

                score = calculate_keyword_affinity_score(
                    db=db,
                    profile_id=int(profile_id),
                    job_description=description
                )

                log_autobid_attempt(
                    db=db,
                    profile_id=int(profile_id),
                    job_title=job["title"],
                    job_link=job["link"],
                    bid_text=bid_text,
                    status="success",
                    score=score
                )
            except Exception as e:
                log_autobid_attempt(
                    db=db,
                    profile_id=int(profile_id),
                    job_title=job["title"],
                    job_link=job["link"],
                    bid_text=bid_text,
                    status="failed",
                    error_message=str(e)
                )

            await asyncio.sleep(3)

        screenshot_path = f"screenshots/{profile_id}_find_work.png"
        os.makedirs("screenshots", exist_ok=True)
        await page.screenshot(path=screenshot_path)
        await context.close()
