# app/auth/browser_login.py
import asyncio
import os
import json
import logging # Added logging
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError # Added PlaywrightTimeoutError
from app.config import settings # Added settings
from app.services.captcha_service import solve_captcha_task # Changed from solve_cloudflare

logger = logging.getLogger(__name__) # Added logger

AUTH_STATE_DIR = "auth_states"
USER_DATA_DIR = "user_data"

# TODO: CRITICAL - These selectors must be verified and updated for Upwork's current login page structure.
LOGIN_URL = "https://www.upwork.com/ab/account-security/login"
USERNAME_SELECTOR = "#login_username"
PASSWORD_SELECTOR = "#login_password"
LOGIN_BUTTON_SELECTOR = "button[type='submit']" # Example: might be more specific
CAPTCHA_IFRAME_SELECTOR = 'iframe[src*="hcaptcha.com"]' # For hCaptcha
SITEKEY_SELECTOR = 'div.h-captcha[data-sitekey]' # For hCaptcha sitekey
CAPTCHA_RESPONSE_TEXTAREA_H = '[name="h-captcha-response"]'
CAPTCHA_RESPONSE_TEXTAREA_G = '[name="g-recaptcha-response"]'
# TODO: CRITICAL - Selector for a reliable element that ONLY appears after successful login.
LOGGED_IN_INDICATOR_SELECTOR = "#nav-global-profile-image" # Example: User's profile image in nav
# TODO: CRITICAL - Selector for common login error messages (e.g., invalid credentials).
LOGIN_ERROR_SELECTOR = ".air3-banner-danger" # Example: General error banner

MAX_LOGIN_ATTEMPTS = 2 # Number of times to try logging in (e.g., initial attempt + 1 CAPTCHA attempt)

async def login_and_save_session(profile_id: str):
    os.makedirs(AUTH_STATE_DIR, exist_ok=True)
    os.makedirs(USER_DATA_DIR, exist_ok=True)
    profile_path = os.path.join(USER_DATA_DIR, profile_id)

    automated_login_successful = False

    async with async_playwright() as p:
        context = None # Define context here to ensure it's available in finally block
        try:
            context = await p.chromium.launch_persistent_context(
                user_data_dir=profile_path,
                headless=False, # Keep False for visibility during initial setup/debugging CAPTCHA
                # headless=True, # TODO: Change to True for production if CAPTCHA handling is robust
                viewport={"width": 1280, "height": 800},
                user_agent=settings.USER_AGENT if hasattr(settings, 'USER_AGENT') else "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
                args=[
                    "--start-maximized",
                    "--no-sandbox",
                    "--disable-blink-features=AutomationControlled"
                ]
            )
            page = await context.new_page()
            await page.set_extra_http_headers({"Accept-Language": "en-US,en;q=0.9"})

            logger.info(f"Navigating to Upwork login page: {LOGIN_URL} for profile {profile_id}")
            await page.goto(LOGIN_URL, wait_until="networkidle")

            if not settings.UPWORK_USERNAME or not settings.UPWORK_PASSWORD:
                logger.warning("Upwork username or password not set in settings. Falling back to manual login.")
            else:
                logger.info(f"Attempting automated login for profile {profile_id}...")
                for attempt in range(MAX_LOGIN_ATTEMPTS):
                    logger.info(f"Login attempt {attempt + 1}/{MAX_LOGIN_ATTEMPTS}")

                    if attempt > 0: # If it's a retry, refresh the page, could be due to failed CAPTCHA
                        logger.info("Refreshing page for new login attempt.")
                        await page.reload(wait_until="networkidle")

                    # Fill credentials (if not already filled or if page reloaded)
                    # Some sites might keep username filled after a failed CAPTCHA, adjust if needed.
                    try:
                        await page.wait_for_selector(USERNAME_SELECTOR, timeout=10000)
                        logger.info(f"Filling username field: {USERNAME_SELECTOR}")
                        await page.fill(USERNAME_SELECTOR, settings.UPWORK_USERNAME)

                        logger.info(f"Filling password field: {PASSWORD_SELECTOR}")
                        await page.fill(PASSWORD_SELECTOR, settings.UPWORK_PASSWORD)

                        logger.info(f"Clicking login button: {LOGIN_BUTTON_SELECTOR}")
                        await page.click(LOGIN_BUTTON_SELECTOR)
                        await page.wait_for_load_state("networkidle", timeout=15000) # Wait for page to react
                    except PlaywrightTimeoutError:
                        logger.error("Timeout waiting for login form fields or navigation after button click. Page might be stuck or selectors invalid.")
                        break # Break from attempts, proceed to manual fallback
                    except Exception as e:
                        logger.error(f"Error filling login form or clicking login button: {e}", exc_info=True)
                        break # Break from attempts

                    # Check for successful login
                    try:
                        await page.wait_for_selector(LOGGED_IN_INDICATOR_SELECTOR, timeout=10000)
                        logger.info(f"Successfully logged in for profile {profile_id}. Logged-in indicator found.")
                        automated_login_successful = True
                        break # Exit login attempts loop
                    except PlaywrightTimeoutError:
                        logger.info("Logged-in indicator not found. Checking for CAPTCHA or errors.")

                    # Check for CAPTCHA if not logged in
                    try:
                        logger.info(f"Looking for CAPTCHA iframe: {CAPTCHA_IFRAME_SELECTOR}")
                        # Ensure the frame is not just located, but actually visible/attached
                        captcha_frame_handle = page.frame_locator(CAPTCHA_IFRAME_SELECTOR).first
                        # Try to locate a known element within the iframe to confirm its presence and readiness
                        await captcha_frame_handle.locator("body").wait_for(timeout=7000) # Check if body inside iframe is ready

                        logger.info("CAPTCHA detected. Attempting to solve...")
                        page_url = page.url

                        # TODO: CRITICAL - Ensure SITEKEY_SELECTOR correctly targets the div containing data-sitekey
                        sitekey_element = page.locator(SITEKEY_SELECTOR).first
                        await sitekey_element.wait_for(timeout=5000) # Ensure sitekey element is present
                        sitekey = await sitekey_element.get_attribute('data-sitekey')

                        if not sitekey:
                            logger.error("Could not extract sitekey for CAPTCHA.")
                            break # Break attempts, move to manual

                        logger.info(f"Extracted sitekey: {sitekey} from URL: {page_url}")

                        captcha_type_on_page = "HCaptchaTaskProxyless" # Default, assuming hCaptcha
                        # TODO: Implement more robust CAPTCHA type detection here if needed.
                        # e.g., by checking unique elements of hCaptcha vs reCAPTCHA iframes/widgets.
                        # For now, CAPTCHA_IFRAME_SELECTOR is hCaptcha-specific.

                        logger.info(f"Attempting to solve CAPTCHA (type: {captcha_type_on_page}) via service...")
                        captcha_solved_successfully = False
                        try:
                            captcha_solution = await solve_captcha_task(
                                url=page_url,
                                sitekey=sitekey,
                                task_type=captcha_type_on_page
                            )
                            if captcha_solution:
                                logger.info("CAPTCHA solution received from service.")
                                captcha_solved_successfully = True
                            else:
                                # This case (solve_captcha_task returning None) might not happen if it raises exceptions instead.
                                logger.error("CAPTCHA service returned no solution (e.g., None).")
                        except (ValueError, RuntimeError, TimeoutError) as captcha_ex: # Catch specific errors from solve_captcha_task
                            logger.error(f"CAPTCHA solving service failed: {captcha_ex}", exc_info=True)
                        except Exception as captcha_ex_general: # Catch any other unexpected errors
                            logger.error(f"Unexpected error from CAPTCHA solving service: {captcha_ex_general}", exc_info=True)

                        if not captcha_solved_successfully:
                            logger.warning("Proceeding without CAPTCHA solution due to service failure. Login will likely fail if CAPTCHA is mandatory.")
                            break # Break from login attempts loop, will go to manual fallback.

                        logger.info("Submitting CAPTCHA solution...")

                        # TODO: CRITICAL - Verify if these textareas are in the main page or inside an iframe
                        # If inside an iframe, need to use frame_locator first.
                        # For hCaptcha, the 'h-captcha-response' textarea is usually in the main document.
                        submitted_to_h = False
                        if await page.locator(CAPTCHA_RESPONSE_TEXTAREA_H).is_visible():
                            await page.locator(CAPTCHA_RESPONSE_TEXTAREA_H).fill(captcha_solution)
                            submitted_to_h = True

                        submitted_to_g = False
                        if await page.locator(CAPTCHA_RESPONSE_TEXTAREA_G).is_visible():
                           await page.locator(CAPTCHA_RESPONSE_TEXTAREA_G).fill(captcha_solution)
                           submitted_to_g = True

                        if not submitted_to_h and not submitted_to_g:
                            logger.error("CAPTCHA response textarea not found on the page.")
                            break # Break attempts, move to manual

                        logger.info("CAPTCHA solution filled into response textarea.")

                        # Click login button again to submit with CAPTCHA solution
                        logger.info(f"Re-clicking login button: {LOGIN_BUTTON_SELECTOR} after CAPTCHA submission.")
                        await page.click(LOGIN_BUTTON_SELECTOR)
                        await page.wait_for_load_state("networkidle", timeout=15000)

                        # Re-check login success in the next iteration of the loop
                        # If login successful now, the next loop iteration will catch it.
                        # If another CAPTCHA or error, it will be handled.
                        continue # Continue to next login attempt (re-checks login success)

                    except PlaywrightTimeoutError: # This timeout is for CAPTCHA iframe/sitekey detection
                        logger.info("No CAPTCHA detected after login attempt (or timed out waiting for CAPTCHA elements).")
                        # This is a critical point: if login didn't succeed and no CAPTCHA found,
                        # it could be invalid credentials or other page errors.
                        try:
                            error_element = page.locator(LOGIN_ERROR_SELECTOR).first
                            # Use a shorter timeout for error messages as they should appear quickly if present
                            await error_element.wait_for(state="visible", timeout=3000)
                            error_text = await error_element.text_content()
                            logger.warning(f"Login error message detected on page: {error_text.strip()}")
                        except PlaywrightTimeoutError:
                            logger.info("No specific login error messages detected after failed login attempt and no CAPTCHA.")
                        # If it's the last attempt, this break will lead to manual fallback.
                        # If not, the loop continues, but it might be stuck if the page state isn't changing.
                        # Consider breaking here always if no CAPTCHA and login failed.
                        logger.warning("Login attempt failed, no CAPTCHA found. Aborting automated attempts.")
                        break # Break from login attempts loop, will go to manual fallback.
                    except Exception as e_captcha_handle: # Catch other errors during CAPTCHA detection/sitekey extraction
                        logger.error(f"Unexpected error during CAPTCHA detection or sitekey extraction: {e_captcha_handle}", exc_info=True)
                        break # Break from login attempts loop, will go to manual fallback.

            # Fallback to manual login if automated attempts failed
            if not automated_login_successful:
                if attempt == MAX_LOGIN_ATTEMPTS -1 : # Log specific message if all attempts exhausted
                    logger.info(f"All {MAX_LOGIN_ATTEMPTS} automated login attempts failed for profile {profile_id}.")
                logger.info(f"Automated login for profile {profile_id} failed or was skipped. Please log in manually in the browser.")
                logger.info("Ensure you are on the main Upwork page after login (e.g., your feed or dashboard).")
                input("After successfully logging in and landing on a main page, press Enter here to save the session...")

                # After manual login, verify again
                try:
                    await page.wait_for_selector(LOGGED_IN_INDICATOR_SELECTOR, timeout=10000) # Check if logged in now
                    logger.info(f"Manual login confirmed by user for profile {profile_id}.")
                    automated_login_successful = True # Consider it successful for saving state
                except PlaywrightTimeoutError:
                    logger.error(f"Still not detecting a logged-in state for profile {profile_id} after manual prompt. Session might not be valid.")
                    # Allow to proceed to save state anyway, as user confirmed.

            if automated_login_successful: # Or if manual login was confirmed
                state_path = os.path.join(AUTH_STATE_DIR, f"{profile_id}_auth.json")
                await context.storage_state(path=state_path)
                logger.info(f"[✅] Session saved for profile {profile_id} to: {state_path}")
            else:
                logger.error(f"Failed to confirm login for profile {profile_id}. Session not saved.")

        except Exception as e:
            logger.error(f"An unexpected error occurred during the login process for profile {profile_id}: {e}", exc_info=True)
        finally:
            if context:
                await context.close()
                logger.info(f"Browser context closed for profile {profile_id}.")


async def save_session_from_cookies(profile_id: str, cookies: str | list[dict]):
    os.makedirs(AUTH_STATE_DIR, exist_ok=True)
    # USER_DATA_DIR is not strictly needed here as we are not using persistent context,
    # but creating AUTH_STATE_DIR is good practice.

    if isinstance(cookies, str):
        try:
            parsed_cookies = json.loads(cookies)
        except json.JSONDecodeError:
            logger.error("[❌] Invalid JSON format for cookies.") # Changed print to logger
            return
    else:
        parsed_cookies = cookies

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True, # Changed to True for save_session_from_cookies as it's non-interactive
            args=[
                "--no-sandbox",
                "--disable-blink-features=AutomationControlled"
            ]
        )
        context = await browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent=settings.USER_AGENT if hasattr(settings, 'USER_AGENT') else "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            extra_http_headers={"Accept-Language": "en-US,en;q=0.9"}
        )

        try:
            await context.add_cookies(parsed_cookies)
            logger.info("[INFO] Cookies added to browser context.") # Changed print to logger
        except Exception as e:
            logger.error(f"[❌] Error adding cookies: {e}", exc_info=True) # Changed print to logger
            await browser.close()
            return

        page = await context.new_page()
        test_url = "https://www.upwork.com/ab/find-work/" # Standard Upwork feed URL
        logger.info(f"[INFO] Navigating to page: {test_url} to verify session...") # Changed print to logger

        try:
            await page.goto(test_url, wait_until="networkidle")

            current_url = page.url
            # More robust check: look for a specific element that only appears when logged in.
            # Using LOGGED_IN_INDICATOR_SELECTOR as a more robust check
            try:
                await page.wait_for_selector(LOGGED_IN_INDICATOR_SELECTOR, timeout=10000)
                logger.info(f"Logged-in indicator found at {current_url}. Session appears valid.")
                state_path = os.path.join(AUTH_STATE_DIR, f"{profile_id}_auth.json")
                await context.storage_state(path=state_path)
                logger.info(f"[✅] Session verified and saved from cookies: {state_path}") # Changed print to logger
            except PlaywrightTimeoutError:
                logger.error(f"[❌] Session validation failed. Logged-in indicator not found at {current_url}. URL may have redirected or cookies are invalid.") # Changed print to logger
                # Optionally, save a screenshot for debugging
                # screenshot_path = f"debug_cookie_login_fail_{profile_id}.png"
                # await page.screenshot(path=screenshot_path)
                # logger.info(f"[INFO] Debug screenshot saved: {screenshot_path}")

        except Exception as e:
            logger.error(f"[❌] Error during navigation or session check with cookies: {e}", exc_info=True) # Changed print to logger
            # screenshot_path = f"error_cookie_login_fail_{profile_id}.png"
            # await page.screenshot(path=screenshot_path)
            # logger.info(f"[INFO] Error screenshot saved: {screenshot_path}")
        finally:
            await browser.close()

if __name__ == "__main__":
    # Setup basic logging for the __main__ example if not configured elsewhere
    if not logging.getLogger().hasHandlers(): # Check if root logger has handlers
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    import sys
    if len(sys.argv) < 3:
        logger.error("Usage:") # Changed print to logger
        logger.error("  For automated/manual login: python app/auth/browser_login.py login <profile_id>") # Changed print to logger
        logger.error("  To save session from cookies (JSON string): python app/auth/browser_login.py cookies <profile_id> '<json_string_of_cookies>'") # Changed print to logger
        logger.error("  To save session from cookies (JSON file path): python app/auth/browser_login.py cookies <profile_id> \"path/to/cookies.json\"") # Changed print to logger
        sys.exit(1)

    command = sys.argv[1]
    profile_id_arg = sys.argv[2]

    if command == "login":
        if len(sys.argv) != 3:
            logger.error("Usage: python app/auth/browser_login.py login <profile_id>") # Changed print to logger
            sys.exit(1)
        logger.info(f"Attempting login for profile_id: {profile_id_arg}")
        asyncio.run(login_and_save_session(profile_id_arg))
    elif command == "cookies":
        if len(sys.argv) != 4:
            logger.error("Usage: python app/auth/browser_login.py cookies <profile_id> '<json_string_of_cookies_or_path_to_json_file>'") # Changed print to logger
            sys.exit(1)

        cookie_input_arg = sys.argv[3]
        cookies_data_arg = None

        if os.path.exists(cookie_input_arg):
            try:
                with open(cookie_input_arg, 'r') as f:
                    cookies_data_arg = json.load(f)
                logger.info(f"[INFO] Cookies loaded from file: {cookie_input_arg}") # Changed print to logger
            except Exception as e:
                logger.error(f"[❌] Error reading cookies file: {e}", exc_info=True) # Changed print to logger
                sys.exit(1)
        else:
            try:
                cookies_data_arg = json.loads(cookie_input_arg)
                logger.info("[INFO] Cookies loaded from JSON string.") # Changed print to logger
            except json.JSONDecodeError:
                logger.error("[❌] Error: Provided cookie input is not a valid JSON string and not a valid file path.") # Changed print to logger
                sys.exit(1)

        if cookies_data_arg:
            asyncio.run(save_session_from_cookies(profile_id_arg, cookies_data_arg))
        else:
            logger.error("[❌] Failed to load cookie data.") # Changed print to logger
            sys.exit(1)
    else:
        logger.error(f"Unknown command: {command}") # Changed print to logger
        sys.exit(1)
