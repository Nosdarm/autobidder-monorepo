import os
import asyncio
import random
import logging
from typing import Optional, List # Added List
import urllib.parse # Added urllib

from playwright.async_api import async_playwright, Page, TimeoutError as PlaywrightTimeoutError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select # Added select
# from sqlalchemy.orm import Session as SyncSession # Removed SyncSession import

from app.services.captcha_service import solve_captcha_task
from app.services.bid_generation_service import generate_bid_text_async
# from app.database import SessionLocal # Removed SessionLocal import
from app.services.autobid_log_service import log_autobid_attempt
from app.services.score_helper import calculate_keyword_affinity_score
from app.config import settings
from app.models.autobid_settings import AutobidSettings # Added
from app.models.profile import Profile # Added

logger = logging.getLogger(__name__)

USER_DATA_DIR = "user_data" # TODO: Ideally from settings

# --- CAPTCHA Related Selectors (Placeholders - Need Verification) ---
# TODO: CRITICAL - Verify and update all selectors below
HCAPTCHA_IFRAME_SELECTOR = 'iframe[src*="hcaptcha.com"]'
RECAPTCHA_IFRAME_SELECTOR = 'iframe[src*="google.com/recaptcha"]'
HCAPTCHA_ELEMENT_SELECTOR = "div.h-captcha[data-sitekey]" # For hCaptcha sitekey
RECAPTCHA_ELEMENT_SELECTOR = ".g-recaptcha[data-sitekey]" # For reCAPTCHA sitekey
HCAPTCHA_RESPONSE_TEXTAREA_SELECTOR = '[name="h-captcha-response"]'
RECAPTCHA_RESPONSE_TEXTAREA_SELECTOR = '[name="g-recaptcha-response"]'

# --- Proposal Submission Selectors (Placeholders - Need Verification) ---
# TODO: CRITICAL - Verify and update all selectors below
SUBMIT_PROPOSAL_BUTTON_SELECTOR = "button:has-text('Submit Proposal'), button:has-text('Send for * connects')" # Example, might need adjustment
PROPOSAL_SUCCESS_INDICATOR_SELECTOR = "text=Your proposal was submitted" # Or a specific element/URL change
PROPOSAL_ERROR_INDICATOR_SELECTOR = ".air3-banner-danger" # General error banner

# --- Timeouts and Limits ---
MAX_SUBMIT_ATTEMPTS = 3
GENERAL_PAGE_LOAD_TIMEOUT = 30000  # ms
CAPTCHA_DETECTION_TIMEOUT = 7000   # ms
CAPTCHA_SOLVE_RETRY_MAX = 2
SUBMIT_CLICK_TIMEOUT = 15000       # ms
SUCCESS_INDICATOR_TIMEOUT = 10000  # ms


async def _is_captcha_present(page: Page) -> Optional[str]:
    """Checks if a known CAPTCHA iframe is visible on the page."""
    try:
        hcaptcha_iframe = page.frame_locator(HCAPTCHA_IFRAME_SELECTOR).first
        await hcaptcha_iframe.locator("body").wait_for(timeout=CAPTCHA_DETECTION_TIMEOUT / 2)
        logger.info("hCaptcha iframe detected.")
        return "hcaptcha"
    except PlaywrightTimeoutError:
        logger.debug("hCaptcha iframe not detected or not ready.")

    try:
        recaptcha_iframe = page.frame_locator(RECAPTCHA_IFRAME_SELECTOR).first
        await recaptcha_iframe.locator("body").wait_for(timeout=CAPTCHA_DETECTION_TIMEOUT / 2)
        logger.info("reCAPTCHA iframe detected.")
        return "recaptcha"
    except PlaywrightTimeoutError:
        logger.debug("reCAPTCHA iframe not detected or not ready.")

    logger.debug("No known CAPTCHA detected.")
    return None

async def _get_captcha_details(page: Page, captcha_type: str) -> Optional[dict]:
    """Extracts sitekey and URL for the detected CAPTCHA."""
    sitekey_selector = HCAPTCHA_ELEMENT_SELECTOR if captcha_type == "hcaptcha" else RECAPTCHA_ELEMENT_SELECTOR
    logger.info(f"Attempting to extract sitekey using selector: {sitekey_selector}")
    try:
        # Ensure element is visible before trying to get attribute
        sitekey_element = page.locator(sitekey_selector).first
        await sitekey_element.wait_for(state="visible", timeout=5000)
        sitekey = await sitekey_element.get_attribute("data-sitekey")
        if sitekey:
            logger.info(f"Extracted sitekey: {sitekey} for {captcha_type} at {page.url}")
            return {"sitekey": sitekey, "url": page.url}
        else:
            logger.error(f"Could not extract data-sitekey for {captcha_type} using selector: {sitekey_selector}")
            return None
    except PlaywrightTimeoutError:
        logger.error(f"Timeout waiting for sitekey element for {captcha_type} using selector: {sitekey_selector}")
        return None
    except Exception as e:
        logger.error(f"Error extracting sitekey for {captcha_type}: {e}", exc_info=True)
        return None

async def _submit_captcha_token(page: Page, captcha_type: str, token: str) -> bool:
    """Fills the CAPTCHA response textarea with the solved token."""
    response_textarea_selector = HCAPTCHA_RESPONSE_TEXTAREA_SELECTOR if captcha_type == "hcaptcha" else RECAPTCHA_RESPONSE_TEXTAREA_SELECTOR
    logger.info(f"Attempting to fill CAPTCHA token into textarea: {response_textarea_selector}")
    try:
        # Some CAPTCHA implementations might require the textarea to be visible, others might not.
        # Ensure it exists, then fill.
        textarea = page.locator(response_textarea_selector).first
        await textarea.wait_for(timeout=5000) # Wait for textarea to be present
        await textarea.fill(token)
        logger.info(f"Successfully filled {captcha_type} token.")
        return True
    except PlaywrightTimeoutError:
        logger.error(f"Timeout waiting for CAPTCHA response textarea: {response_textarea_selector}")
        return False
    except Exception as e:
        logger.error(f"Error filling CAPTCHA token: {e}", exc_info=True)
        return False

async def _handle_captcha_on_page(page: Page, max_solve_retries: int = CAPTCHA_SOLVE_RETRY_MAX) -> bool:
    """
    Detects, solves, and submits CAPTCHA token if present on the page.
    Returns True if CAPTCHA was handled successfully, False otherwise.
    Does NOT perform actions like reload or re-clicking submit buttons.
    """
    logger.info(f"Checking for CAPTCHA on page: {page.url}")
    captcha_type = await _is_captcha_present(page)
    if not captcha_type:
        logger.info("No CAPTCHA detected on current page section.")
        return False

    logger.info(f"{captcha_type.capitalize()} detected. Attempting to solve.")

    for attempt in range(max_solve_retries):
        logger.info(f"CAPTCHA solve attempt {attempt + 1}/{max_solve_retries}")
        captcha_details = await _get_captcha_details(page, captcha_type)
        if not captcha_details:
            logger.error("Failed to get CAPTCHA details (sitekey/URL).")
            await asyncio.sleep(2) # Wait before retrying details extraction
            continue

        task_type_for_solver = "HCaptchaTaskProxyless" # Default
        if captcha_type == "hcaptcha":
            task_type_for_solver = "HCaptchaTaskProxyless"
        elif captcha_type == "recaptcha":
            # TODO: Distinguish between reCAPTCHA v2 and v3 if necessary.
            # Upwork more commonly uses hCaptcha or reCAPTCHA v2 checkbox type on interactive forms.
            # reCAPTCHA v3 is score-based and often invisible, requiring different handling if encountered.
            task_type_for_solver = "RecaptchaV2TaskProxyless"
        else:
            logger.warning(f"Unknown CAPTCHA type '{captcha_type}' detected by _is_captcha_present. Defaulting solver task type to HCaptchaTaskProxyless.")
            # Fallback or raise error if type is critical and unhandled

        token: Optional[str] = None # Ensure token is defined before try block
        captcha_solved_this_attempt = False
        try:
            logger.info(f"Calling CAPTCHA solving service with task_type: {task_type_for_solver} for URL: {captcha_details['url']} (Sitekey: {captcha_details['sitekey']})")
            token = await solve_captcha_task(
                url=captcha_details["url"],
                sitekey=captcha_details["sitekey"],
                task_type=task_type_for_solver
            )
            if token:
                logger.info(f"CAPTCHA token received for {captcha_type}.")
                if await _submit_captcha_token(page, captcha_type, token): # Pass original captcha_type for textarea selection
                    logger.info(f"{captcha_type.capitalize()} solved and token submitted successfully to page.")
                    captcha_solved_this_attempt = True # Mark as successfully handled for this attempt
                else:
                    logger.error(f"Failed to submit solved {captcha_type} token to textarea.")
                    # Token submission failed, likely a page issue. Retrying might help if page state is unstable.
            else:
                # solve_captcha_task itself logged that it didn't return a token.
                logger.warning(f"CAPTCHA service did not return a token for {captcha_type} at {captcha_details['url']}.")

        except (ValueError, RuntimeError, TimeoutError) as e_solve:
            logger.error(f"CAPTCHA solving service ({settings.CAPTCHA_PROVIDER_NAME}) failed for {captcha_type} at {captcha_details['url']} with error: {e_solve}", exc_info=False) # exc_info=False as service logs details
        except Exception as e_solve_general:
            logger.error(f"Unexpected error calling CAPTCHA solving service for {captcha_type} at {captcha_details['url']}: {e_solve_general}", exc_info=True)

        if captcha_solved_this_attempt:
            return True # CAPTCHA handled for this call of _handle_captcha_on_page

        # If token was not obtained, or not submitted successfully, and retries are left:
        if attempt < max_solve_retries - 1:
            logger.warning(f"CAPTCHA handling attempt {attempt + 1}/{max_solve_retries} failed for {captcha_type}. Retrying after a delay...")
            await asyncio.sleep(random.uniform(3,5))
        else: # All retries for this specific CAPTCHA instance failed
            logger.error(f"All {max_solve_retries} attempts to solve and submit {captcha_type} CAPTCHA failed for URL: {page.url}")

    # If loop finishes without returning True, it means all retries failed for this CAPTCHA instance
    logger.error(f"Failed to handle {captcha_type} after {max_solve_retries} attempts for URL: {page.url}")
    return False


async def fill_rate_increase_fields(page: Page): # Added type hint for page
    # TODO: CRITICAL - Verify these selectors
    try:
        await page.get_by_label("How often do you want a rate increase?").click(timeout=3000)
        await page.get_by_text("Every 3 months").click(timeout=3000)
    except Exception as e:
        logger.warning(f"Could not fill rate increase frequency: {e}")

    try:
        await page.get_by_label("How much of an increase do you want?").click(timeout=3000)
        await page.get_by_text("10%").click(timeout=3000)
    except Exception as e:
        logger.warning(f"Could not fill rate increase amount: {e}")

async def run_browser_bidder_for_profile(profile_id: str, db: AsyncSession): # Added db: AsyncSession
    logger.info(f"[▶️ START] Bidding process for profile {profile_id}")
    profile_dir = os.path.join(USER_DATA_DIR, profile_id)

    if not os.path.exists(profile_dir):
        logger.error(f"[❌] User data directory not found: {profile_dir}. Profile must log in and save session first.")
        return

    # db session is now passed as an argument, no need for `next(get_db())` here.
    # Ensure `log_autobid_attempt` and `calculate_keyword_affinity_score` are compatible with AsyncSession
    # or are run in a way that doesn't block the event loop if they are synchronous.

    logger.info(f"Fetching autobid settings and profile data for profile_id: {profile_id}")
    try:
        autobid_setting_stmt = select(AutobidSettings).where(AutobidSettings.profile_id == profile_id)
        autobid_setting_result = await db.execute(autobid_setting_stmt)
        autobid_setting: Optional[AutobidSettings] = autobid_setting_result.scalars().first()

        profile_stmt = select(Profile).where(Profile.id == profile_id) # Profile.id is usually UUID, ensure profile_id matches type
        profile_result = await db.execute(profile_stmt)
        profile_obj: Optional[Profile] = profile_result.scalars().first()

        if not autobid_setting or not profile_obj:
            logger.error(f"Autobid settings or profile object not found for profile_id: {profile_id}. Aborting bid run.")
            return
    except Exception as e_fetch:
        logger.error(f"Database error fetching settings/profile for {profile_id}: {e_fetch}", exc_info=True)
        return

    # TODO: Add a 'search_terms: Optional[List[str]] = Column(JSON, nullable=True)' field to the AutobidSettings model.
    # This field should be populated via API or other means.
    search_keywords: Optional[List[str]] = getattr(autobid_setting, 'search_terms', None)

    if not search_keywords and profile_obj.skills: # Assuming profile_obj.skills is List[str]
        logger.info(f"No specific search_terms found in AutobidSettings for profile {profile_id}. Using profile skills as fallback keywords: {profile_obj.skills}")
        search_keywords = profile_obj.skills
    elif not search_keywords:
        logger.warning(f"No search_terms in AutobidSettings and no skills in Profile for profile {profile_id}. Proceeding with general feed (Upwork's default algorithm).")

    job_search_url = "https://www.upwork.com/nx/jobs/search/" # New default Upwork job search URL
    if search_keywords and isinstance(search_keywords, list) and len(search_keywords) > 0:
        # Use up to 3 keywords, join them with space for Upwork query
        query_string = " ".join(search_keywords[:3])
        encoded_query = urllib.parse.quote_plus(query_string)
        job_search_url = f"https://www.upwork.com/nx/jobs/search/?q={encoded_query}&sort=recency" # Added sort by recency
        logger.info(f"Using targeted search URL for profile {profile_id}: {job_search_url}")
    else:
        logger.info(f"Using general job feed URL for profile {profile_id}: {job_search_url} (sorted by recency by default on Upwork, often)")
        # If no specific keywords, Upwork might use its own algorithm. Adding sort=recency might be good.
        if "?" not in job_search_url:
            job_search_url += "?sort=recency"
        else:
            job_search_url += "&sort=recency"


    async with async_playwright() as p:
        context = None
        try:
            context = await p.chromium.launch_persistent_context(
                user_data_dir=profile_dir,
                headless=True, # TODO: Set to False for debugging CAPTCHA/flow issues
                user_agent=settings.USER_AGENT if hasattr(settings, 'USER_AGENT') else "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
                args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-blink-features=AutomationControlled"]
            )
            page = await context.new_page()

            logger.info(f"Navigating to job search page: {job_search_url}")
            await page.goto(job_search_url, wait_until="networkidle", timeout=GENERAL_PAGE_LOAD_TIMEOUT)

            logger.info("Job search page load complete. Checking for CAPTCHA...")
            await _handle_captcha_on_page(page)

            # Verify current URL after potential CAPTCHA handling
            if urllib.parse.urlparse(page.url).path != urllib.parse.urlparse(job_search_url).path:
                 logger.info(f"URL changed after CAPTCHA check (current: {page.url}). Re-navigating to intended search URL: {job_search_url}")
                 await page.goto(job_search_url, wait_until="networkidle", timeout=GENERAL_PAGE_LOAD_TIMEOUT)
                 await _handle_captcha_on_page(page) # Check again

            # TODO: CRITICAL - Selector for job cards needs verification. This selector is for the 'Find Work' page.
            # The /nx/jobs/search/ page might have different selectors.
            job_cards_selector = "section[data-test='job-tile-list'] article.job-tile" # Example for /nx/jobs/search
            # Or more specific: job_cards_selector = "div[data-qa='job-tile']"
            # Need to find title link within this card.
            logger.info(f"Looking for job cards with selector: {job_cards_selector}")
            await page.wait_for_selector(job_cards_selector, timeout=GENERAL_PAGE_LOAD_TIMEOUT) # Wait for list container

            # TODO: CRITICAL - Selector for the title/link within each job card on /nx/jobs/search/ page
            # This example assumes a structure. This needs careful inspection.
            # Example: within each `article.job-tile`, find `h3 > a` or similar for title and link
            job_card_locators = await page.locator(job_cards_selector).all() # Get all cards

            jobs_details_list = []
            if not job_card_locators:
                logger.warning(f"No job cards found on job search page using selector: {job_cards_selector}")

            for card_locator in job_card_locators:
                # TODO: CRITICAL - Adjust these selectors for title and link within the card
                title_element = card_locator.locator("h3 > a").first # Example
                # Or: title_element = card_locator.locator("a[data-test='job-title-link']").first
                try:
                    await title_element.wait_for(state="visible", timeout=2000) # Short timeout per card
                    title = await title_element.inner_text()
                    href = await title_element.get_attribute("href")
                    if title and href:
                        # Links on /nx/jobs/search/ are usually relative, e.g., /jobs/xxxxxxxx
                        full_link = f"https://www.upwork.com{href.split('?')[0]}" if href.startswith("/jobs/") else href.split('?')[0]
                        jobs_details_list.append({"title": title.strip(), "link": full_link})
                except PlaywrightTimeoutError:
                    logger.warning("Could not find title/link in a job card, or it timed out.")
                except Exception as e_card:
                    logger.warning(f"Error processing a job card: {e_card}")

            logger.info(f"Found {len(jobs_details_list)} jobs to process from search results.")

            # TODO: Make the number of jobs to process configurable (e.g., via AutobidSettings.jobs_to_check_per_run)
            for job_data_from_feed in jobs_details_list[:1]:
                job_link = job_data_from_feed["link"]
                job_title_from_feed = job_data_from_feed["title"]
                logger.info(f"Processing job: {job_title_from_feed} - {job_link}")

                await page.goto(job_link, wait_until="networkidle", timeout=GENERAL_PAGE_LOAD_TIMEOUT)
                logger.info(f"Navigated to job page: {job_link}. Checking for CAPTCHA.")
                if await _handle_captcha_on_page(page): # Handle CAPTCHA if present on job page
                    logger.info("CAPTCHA handled on job page. Page might have reloaded or state changed.")
                    # Consider re-verifying elements or briefly waiting if needed.
                    await asyncio.sleep(2)


                # TODO: CRITICAL - Selector for "Submit a Proposal" button on job details page
                apply_button_selector = "button[data-test='apply-button'], button:has-text('Apply Now')"
                try:
                    logger.info(f"Looking for 'Apply Now' / 'Submit a Proposal' button using selector: {apply_button_selector}")
                    apply_button = page.locator(apply_button_selector).first
                    await apply_button.wait_for(state="visible", timeout=10000)
                    await apply_button.click()
                    await page.wait_for_load_state("networkidle", timeout=GENERAL_PAGE_LOAD_TIMEOUT)
                    logger.info("Clicked 'Apply Now'. Navigated to proposal submission page.")
                except PlaywrightTimeoutError:
                    logger.error(f"Could not find or click 'Apply Now' button for job {job_title_from_feed}. Skipping this job.")
                    # TODO: Log this attempt with a specific "apply_button_not_found" status if desired
                    continue # Skip to next job
                except Exception as e:
                    logger.error(f"Error clicking 'Apply Now' for job {job_title_from_feed}: {e}", exc_info=True)
                    continue

                # On proposal submission page, check for CAPTCHA again
                if await _handle_captcha_on_page(page):
                    logger.info("CAPTCHA handled on proposal page load.")
                    await asyncio.sleep(2)

                # TODO: CRITICAL - Selector for job description on proposal page
                description_selector_on_proposal_page = "div[data-test='job-description'], #job-details-description"
                job_description_text = "Description not found"
                try:
                    logger.info(f"Extracting job description using selector: {description_selector_on_proposal_page}")
                    desc_el = page.locator(description_selector_on_proposal_page).first
                    await desc_el.wait_for(state="visible", timeout=5000)
                    job_description_text = await desc_el.inner_text()
                    job_description_text = job_description_text.strip()
                except Exception as e:
                    logger.warning(f"Could not extract job description on proposal page: {e}")

                current_job_details = {
                    "title": job_title_from_feed, # Or extract title from this page if more accurate
                    "description": job_description_text
                }

                # TODO: CRITICAL - Selector for cover letter textarea
                cover_letter_selector = "textarea[name='coverLetter'], textarea[aria-label*='cover letter']"
                bid_text = await generate_bid_text_async(current_job_details, profile_id=profile_id, db=db)
                try:
                    logger.info(f"Filling cover letter using selector: {cover_letter_selector}")
                    await page.locator(cover_letter_selector).first.fill(bid_text, timeout=5000)
                except Exception as e:
                    logger.error(f"Failed to fill cover letter for {job_title_from_feed}: {e}. Skipping bid.")
                    # Log attempt as failed due to form interaction error
                    await log_autobid_attempt(db=db, profile_id=int(profile_id), job_title=job_title_from_feed, job_link=job_link, bid_text=bid_text, status="failed", error_message=f"Failed to fill cover letter: {str(e)}")
                    continue

                await fill_rate_increase_fields(page) # Assuming this is still relevant

                # --- Proposal Submission Loop with CAPTCHA Handling ---
                submitted_successfully = False
                for attempt in range(MAX_SUBMIT_ATTEMPTS):
                    logger.info(f"Proposal submission attempt {attempt + 1}/{MAX_SUBMIT_ATTEMPTS} for job: {job_title_from_feed}")

                    # Pre-emptive CAPTCHA check before clicking submit
                    if await _is_captcha_present(page):
                        logger.info("CAPTCHA detected before clicking submit proposal.")
                        if not await _handle_captcha_on_page(page):
                            logger.error("Pre-emptive CAPTCHA detected but could not be solved. Aborting bid for this job.")
                            break # Break from submit attempts
                        await asyncio.sleep(random.uniform(1,3)) # Brief pause after CAPTCHA solve

                    try:
                        logger.info(f"Clicking final submit proposal button using selector: {SUBMIT_PROPOSAL_BUTTON_SELECTOR}")
                        await page.click(SUBMIT_PROPOSAL_BUTTON_SELECTOR, timeout=SUBMIT_CLICK_TIMEOUT)

                        # Check for success indicator
                        logger.info(f"Waiting for proposal success indicator: {PROPOSAL_SUCCESS_INDICATOR_SELECTOR}")
                        await page.wait_for_selector(PROPOSAL_SUCCESS_INDICATOR_SELECTOR, timeout=SUCCESS_INDICATOR_TIMEOUT)
                        logger.info(f"Proposal submitted successfully for: {job_title_from_feed}")
                        submitted_successfully = True
                        break # Exit SUBMIT_ATTEMPTS loop

                    except PlaywrightTimeoutError:
                        logger.warning(f"Timeout during proposal submission process for '{job_title_from_feed}'. Attempt {attempt + 1}/{MAX_SUBMIT_ATTEMPTS}.")
                        captcha_present_after_fail = await _is_captcha_present(page)
                        if captcha_present_after_fail:
                            logger.info(f"CAPTCHA ({captcha_present_after_fail}) detected after failed/timed-out submit for '{job_title_from_feed}'.")
                            captcha_handled_successfully = await _handle_captcha_on_page(page)
                            if captcha_handled_successfully:
                                logger.info(f"CAPTCHA handled for '{job_title_from_feed}'. Will retry submitting proposal.")
                                await asyncio.sleep(random.uniform(2,4))
                                continue # Retry submission (next iteration of MAX_SUBMIT_ATTEMPTS loop)
                            else: # _handle_captcha_on_page returned False
                                logger.error(f"CAPTCHA was present for '{job_title_from_feed}', but failed to solve it after its internal retries. Aborting bid for this job.")
                                break # Abort MAX_SUBMIT_ATTEMPTS loop for this job
                        else:
                            logger.info(f"No CAPTCHA detected for '{job_title_from_feed}' after failed/timed-out submit attempt.")
                            try:
                                error_banner = page.locator(PROPOSAL_ERROR_INDICATOR_SELECTOR).first
                                if await error_banner.is_visible(timeout=1000):
                                    error_text = await error_banner.text_content()
                                    logger.error(f"Proposal submission for '{job_title_from_feed}' failed with on-page error: {error_text.strip()}. Aborting bid.")
                                else:
                                    logger.error(f"Proposal submission for '{job_title_from_feed}' failed: No success indicator, no CAPTCHA, and no specific on-page error message detected. Aborting bid.")
                            except PlaywrightTimeoutError:
                                logger.error(f"Proposal submission for '{job_title_from_feed}' failed: No success indicator, no CAPTCHA, and timeout checking for on-page error messages. Aborting bid.")
                            break # Abort MAX_SUBMIT_ATTEMPTS loop for this job
                    except Exception as e_submit: # Catch any other non-timeout errors during submission
                        logger.error(f"Unexpected error during proposal submission attempt {attempt + 1} for '{job_title_from_feed}': {e_submit}", exc_info=True)
                        break # Abort MAX_SUBMIT_ATTEMPTS loop for this job

                if not submitted_successfully and attempt == MAX_SUBMIT_ATTEMPTS - 1:
                    logger.error(f"All {MAX_SUBMIT_ATTEMPTS} attempts to submit proposal for '{job_title_from_feed}' failed.")

                # Log final bid attempt status
                if submitted_successfully:
                    score_value: Optional[float] = None
                    # sync_db_for_log_score: Optional[SyncSession] = None # Removed
                    try:
                        # sync_db_for_log_score = SessionLocal() # Removed
                        logger.info(f"Calculating score for job '{job_title_from_feed}' in separate thread.")
                        score_value = await asyncio.to_thread(
                            calculate_keyword_affinity_score, int(profile_id), job_description_text
                            # TODO: calculate_keyword_affinity_score needs to be refactored to manage its own sync DB session
                            # if it's run in a thread and needs DB access.
                        )
                    except Exception as e_score:
                        logger.error(f"Error calculating score for '{job_title_from_feed}': {e_score}", exc_info=True)
                    # finally: # Finally block no longer needed for sync_db_for_log_score here
                        # if sync_db_for_log_score:
                            # sync_db_for_log_score.close()

                    await log_autobid_attempt(db=db, profile_id=int(profile_id), job_title=job_title_from_feed, job_link=job_link, bid_text=bid_text, status="success", score=score_value)
                    logger.info(f"Successfully submitted proposal and logged for job: {job_title_from_feed}")
                else:
                    logger.error(f"Failed to submit proposal for job: {job_title_from_feed} (Loop completed or broke due to error). Logging failure.")
                    await log_autobid_attempt(db=db, profile_id=int(profile_id), job_title=job_title_from_feed, job_link=job_link, bid_text=bid_text, status="failed", error_message=f"Failed after {MAX_SUBMIT_ATTEMPTS} attempts or CAPTCHA/other errors.")

                await asyncio.sleep(random.uniform(3,5)) # Delay before processing next job

            # Screenshot is now taken after all jobs are processed (or just the first one in this loop)
            # Consider moving screenshot logic inside the loop if needed per job.
            logger.info("Taking final screenshot of the page.")
            screenshot_path = f"screenshots/{profile_id}_find_work_or_last_page.png"
            os.makedirs("screenshots", exist_ok=True)
            await page.screenshot(path=screenshot_path)

        except Exception as e:
            logger.error(f"An error occurred during the browser bidding process for profile {profile_id}: {e}", exc_info=True)
        finally:
            if context:
                await context.close()
                logger.info(f"Browser context closed for profile {profile_id}")
            # db session should be closed by the caller if it was passed in.
    logger.info(f"[🏁 END] Bidding process for profile {profile_id}")
