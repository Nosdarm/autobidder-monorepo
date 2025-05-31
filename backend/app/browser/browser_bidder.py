import os
import asyncio
import random
import logging # Added
from typing import Optional # Added

from playwright.async_api import async_playwright, Page, TimeoutError as PlaywrightTimeoutError # Added Page, PlaywrightTimeoutError
from sqlalchemy.ext.asyncio import AsyncSession # Added for type hinting

from app.services.captcha_service import solve_captcha_task # Changed from solve_cloudflare
from app.services.bid_generation_service import generate_bid_text_async
# from app.database import get_db # This will be passed as AsyncSession
from app.services.autobid_log_service import log_autobid_attempt # Assuming this can work with sync or async session based on its implementation
from app.services.score_helper import calculate_keyword_affinity_score # Assuming this can work with sync or async session
from app.config import settings # Added

logger = logging.getLogger(__name__) # Added

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

        token = None
        try:
            logger.info(f"Calling CAPTCHA solving service with task_type: {task_type_for_solver} for URL: {captcha_details['url']}")
            token = await solve_captcha_task(
                url=captcha_details["url"],
                sitekey=captcha_details["sitekey"],
                task_type=task_type_for_solver
            )
        except (ValueError, RuntimeError, TimeoutError) as e_solve: # Specific errors from solve_captcha_task
            logger.error(f"CAPTCHA solving service failed for {captcha_type} at {captcha_details['url']}: {e_solve}", exc_info=True)
        except Exception as e_solve_general: # Other unexpected errors
            logger.error(f"Unexpected error from CAPTCHA solving service for {captcha_type} at {captcha_details['url']}: {e_solve_general}", exc_info=True)

        if token:
            if await _submit_captcha_token(page, captcha_type, token): # Pass original captcha_type for textarea selection
                logger.info(f"{captcha_type.capitalize()} solved and token submitted successfully.")
                return True
            else:
                logger.error(f"Failed to submit solved {captcha_type} token to textarea.")
                # If submitting token fails, retrying solve might not help unless page state changes.
                # Allow retry if max_solve_retries not reached, as it might be a transient page issue.
        else:
            # This log occurs if solve_captcha_task returned None or raised an exception handled above.
            logger.warning("CAPTCHA solving service did not return a token or failed.")

        if attempt < max_solve_retries - 1:
            logger.warning(f"CAPTCHA handling attempt {attempt + 1} failed for {captcha_type}. Retrying after a delay...")
            await asyncio.sleep(random.uniform(3,5)) # Wait before full retry

    logger.error(f"Failed to handle {captcha_type} after {max_solve_retries} attempts.")
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

            initial_url = "https://www.upwork.com/ab/find-work/"
            logger.info(f"Navigating to initial page: {initial_url}")
            await page.goto(initial_url, wait_until="networkidle", timeout=GENERAL_PAGE_LOAD_TIMEOUT)

            logger.info("Initial page load complete. Checking for CAPTCHA...")
            await _handle_captcha_on_page(page) # Handle CAPTCHA if present on initial load

            # Current page might have changed if CAPTCHA was handled by reload (though current helper does not reload)
            # Re-verify or ensure navigation to find-work if needed.
            if "find-work" not in page.url:
                 logger.info(f"Not on find-work page after initial CAPTCHA check (current: {page.url}). Re-navigating.")
                 await page.goto(initial_url, wait_until="networkidle", timeout=GENERAL_PAGE_LOAD_TIMEOUT)
                 await _handle_captcha_on_page(page) # Check again

            # TODO: CRITICAL - Selector for job cards needs verification
            job_cards_selector = ".job-tile-title a"
            logger.info(f"Looking for job cards with selector: {job_cards_selector}")
            await page.wait_for_selector(job_cards_selector, timeout=GENERAL_PAGE_LOAD_TIMEOUT)
            job_cards = await page.locator(job_cards_selector).all()

            jobs_details_list = []
            if not job_cards:
                logger.warning("No job cards found on find-work page.")

            for job_card_locator in job_cards:
                title = await job_card_locator.inner_text()
                href = await job_card_locator.get_attribute("href")
                if title and href:
                    jobs_details_list.append({"title": title.strip(), "link": f"https://www.upwork.com{href.split('?')[0]}"}) # Clean link

            logger.info(f"Found {len(jobs_details_list)} jobs to process.")

            for job_data_from_feed in jobs_details_list[:1]: # Process only the first job for now as per original logic
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
                    log_autobid_attempt(db=db, profile_id=int(profile_id), job_title=job_title_from_feed, job_link=job_link, bid_text=bid_text, status="failed", error_message=f"Failed to fill cover letter: {str(e)}")
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
                        break # Exit retry loop

                    except PlaywrightTimeoutError: # This covers timeout for click or for waiting for PROPOSAL_SUCCESS_INDICATOR_SELECTOR
                        logger.warning(f"Timeout during proposal submission process for {job_title_from_feed}. Attempt {attempt + 1}.")
                        captcha_present_after_fail = await _is_captcha_present(page)
                        if captcha_present_after_fail:
                            logger.info(f"CAPTCHA ({captcha_present_after_fail}) detected after failed/timed-out submit attempt.")
                            captcha_handled_successfully = await _handle_captcha_on_page(page) # This has its own retries for solving
                            if captcha_handled_successfully:
                                logger.info("CAPTCHA handled after failed submission. Will retry submitting proposal.")
                                await asyncio.sleep(random.uniform(2,4)) # Wait a bit after CAPTCHA solve before retrying
                                continue # Retry submission in the next loop iteration
                            else:
                                logger.error(f"CAPTCHA was present after failed submission for '{job_title_from_feed}', but failed to solve it. Aborting bid.")
                                break # Abort MAX_SUBMIT_ATTEMPTS loop for this job
                        else: # No CAPTCHA detected after timeout, but submission also failed (no success indicator)
                            logger.info(f"No CAPTCHA detected for '{job_title_from_feed}' after failed/timed-out submit attempt.")
                            try: # Check for specific error messages on the page
                                error_banner = page.locator(PROPOSAL_ERROR_INDICATOR_SELECTOR).first
                                if await error_banner.is_visible(timeout=1000): # Quick check for error message
                                    error_text = await error_banner.text_content()
                                    logger.error(f"Proposal submission failed for '{job_title_from_feed}' with on-page error: {error_text.strip()}. Aborting bid.")
                                else: # No specific error message found
                                    logger.error(f"Proposal submission failed for '{job_title_from_feed}': No success indicator, no CAPTCHA, and no specific on-page error message detected. Aborting bid.")
                            except PlaywrightTimeoutError: # Timeout waiting for error banner itself
                                logger.error(f"Proposal submission failed for '{job_title_from_feed}': No success indicator, no CAPTCHA, and timeout checking for on-page error messages. Aborting bid.")
                            break # Abort MAX_SUBMIT_ATTEMPTS loop for this job
                    except Exception as e_submit:
                        logger.error(f"Unexpected error during proposal submission attempt {attempt + 1} for '{job_title_from_feed}': {e_submit}", exc_info=True)
                        break # Abort MAX_SUBMIT_ATTEMPTS loop for this job

                # Log final bid attempt status
                if submitted_successfully:
                    # Call logging for success
                    # score = calculate_keyword_affinity_score(db=db, profile_id=int(profile_id), job_description=job_description_text)
                    # log_autobid_attempt(db=db, profile_id=int(profile_id), job_title=job_title_from_feed, job_link=job_link, bid_text=bid_text, status="success", score=score)
                    logger.info(f"Successfully submitted proposal for job: {job_title_from_feed}")
                else:
                    # Call logging for failure, including if all attempts were exhausted
                    logger.error(f"Failed to submit proposal for job: {job_title_from_feed} after {MAX_SUBMIT_ATTEMPTS} attempts or due to critical error.")
                    # log_autobid_attempt(db=db, profile_id=int(profile_id), job_title=job_title_from_feed, job_link=job_link, bid_text=bid_text, status="failed", error_message=f"Failed after {MAX_SUBMIT_ATTEMPTS} attempts or CAPTCHA/other errors.")

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
