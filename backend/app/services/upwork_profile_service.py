import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from playwright.async_api import async_playwright, Playwright, Page, BrowserContext # Added Page, BrowserContext
import os
import logging
from app.models.profile import Profile
from sqlalchemy import select
from app.database import AsyncSessionLocal

# Configure logger for this service
logger = logging.getLogger(__name__)

# USER_DATA_DIR should ideally be sourced from a centralized configuration.
# For now, keeping it as a local constant for consistency with the original file.
USER_DATA_DIR = "user_data"

class UpworkProfileFetcher:
    """
    Handles fetching and parsing profile data from Upwork for a specific profile.
    """
    def __init__(self, profile_id: str, db: AsyncSession):
        self.profile_id = str(profile_id) # Ensure profile_id is a string
        self.db = db
        self.profile_dir = os.path.join(USER_DATA_DIR, self.profile_id)
        # Ensure the profile directory for user data exists for Playwright's persistent context
        os.makedirs(self.profile_dir, exist_ok=True)


    async def _launch_browser(self, p: Playwright) -> tuple[Optional[Page], Optional[BrowserContext]]:
        """
        Launches a Playwright browser with a persistent context.
        Uses headless=True for background operations.
        """
        logger.info(f"Attempting to launch browser for profile {self.profile_id} using user data dir: {self.profile_dir}")
        try:
            context = await p.chromium.launch_persistent_context(
                self.profile_dir,
                headless=True, # Essential for background tasks
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
                args=[
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage", # Common for Docker/CI environments
                    "--disable-blink-features=AutomationControlled",
                    "--disable-gpu", # Often useful in headless environments
                    # "--single-process" # Can sometimes help in resource-constrained environments, but use with caution
                ],
                # slow_mo=50 # Uncomment for debugging if needed
            )
            page = await context.new_page()
            logger.info(f"Browser launched successfully for profile {self.profile_id}.")
            return page, context
        except Exception as e:
            logger.error(f"Error launching browser for profile {self.profile_id}: {e}", exc_info=True)
            return None, None

    async def _navigate_to_profile(self, page: Optional[Page]):
        """
        Navigates to the user's Upwork profile page.
        This might involve multiple steps depending on Upwork's current UI.
        """
        if not page:
            logger.warning(f"Page object not available for profile {self.profile_id}, skipping navigation.")
            return

        profile_url = "https://www.upwork.com/profile/me" # A more direct URL if available after login
        # Fallback, more generic start page if direct profile URL doesn't work or session is iffy
        # find_work_url = "https://www.upwork.com/ab/find-work/"

        logger.info(f"Navigating to Upwork profile page for profile {self.profile_id}. Target URL: {profile_url}")
        try:
            await page.goto(profile_url, wait_until="domcontentloaded", timeout=30000) # 30s timeout
            logger.info(f"Successfully navigated to initial page for profile {self.profile_id}. Current URL: {page.url}")

            # TODO: CRITICAL - The following click is a placeholder strategy.
            # This needs to be verified and updated based on the actual page structure after logging in
            # and navigating to `profile_url`. It's possible no click is needed if `profile_url` lands directly.
            # If a click is needed to e.g. "View Profile" or "Edit Profile":
            # view_profile_selector = "a[href*='/freelancers/']" # Example, highly likely to be incorrect
            # logger.info(f"Attempting to click 'View Profile' link using selector: {view_profile_selector} for profile {self.profile_id}")
            # try:
            #     await page.click(view_profile_selector, timeout=10000)
            #     await page.wait_for_load_state("domcontentloaded", timeout=15000)
            #     logger.info(f"Clicked 'View Profile'. Current URL for profile {self.profile_id}: {page.url}")
            # except Exception as e:
            #     logger.warning(f"Could not click 'View Profile' link or page did not load as expected for profile {self.profile_id}: {e}. Current URL: {page.url}")
            #     # Consider taking a screenshot here for debugging if navigation fails:
            #     # await page.screenshot(path=f"debug_navigate_profile_{self.profile_id}.png")

        except Exception as e:
            logger.error(f"Error during navigation for profile {self.profile_id}: {e}. Current URL: {page.url}", exc_info=True)
            # await page.screenshot(path=f"error_navigate_profile_{self.profile_id}.png")


    async def _parse_profile_data(self, page: Optional[Page]) -> dict:
        """
        Parses various pieces of information from the Upwork profile page.
        Selectors are placeholders and MUST be updated.
        """
        profile_data = {
            'name': "Name not found", # Default placeholder
            'title': "Title not found", # Default placeholder
            'overview': "Overview not found", # Default placeholder
            'skills': [] # Default to empty list
        }
        if not page:
            logger.warning(f"Page object not available for profile {self.profile_id}, skipping parsing.")
            return profile_data

        logger.info(f"Attempting to parse profile data from page: {page.url} for profile {self.profile_id}")

        # Name
        # TODO: CRITICAL - Replace with the correct Playwright selector for Name
        name_selector = "div.user-profile-name h1" # Placeholder
        try:
            name_content = await page.locator(name_selector).text_content(timeout=5000)
            if name_content:
                profile_data['name'] = name_content.strip()
                logger.info(f"Parsed name for profile {self.profile_id}: {profile_data['name']}")
            else:
                logger.warning(f"Name selector '{name_selector}' found, but content was empty for profile {self.profile_id}.")
        except Exception as e:
            logger.error(f"Could not parse name for profile {self.profile_id} using selector '{name_selector}': {e}")

        # Title/Headline
        # TODO: CRITICAL - Replace with the correct Playwright selector for Title/Headline
        title_selector = "div.user-profile-title span" # Placeholder
        try:
            title_content = await page.locator(title_selector).text_content(timeout=5000)
            if title_content:
                profile_data['title'] = title_content.strip()
                logger.info(f"Parsed title for profile {self.profile_id}: {profile_data['title']}")
            else:
                logger.warning(f"Title selector '{title_selector}' found, but content was empty for profile {self.profile_id}.")
        except Exception as e:
            logger.error(f"Could not parse title for profile {self.profile_id} using selector '{title_selector}': {e}")

        # Overview/Summary
        # TODO: CRITICAL - Replace with the correct Playwright selector for Overview/Summary
        overview_selector = "div.profile-overview-section p" # Placeholder
        try:
            # This might need to join text from multiple paragraphs or handle complex structures
            overview_elements = await page.locator(overview_selector).all_text_contents()
            if overview_elements:
                profile_data['overview'] = "\n".join([text.strip() for text in overview_elements if text.strip()])
                logger.info(f"Parsed overview for profile {self.profile_id} (length: {len(profile_data['overview'])} chars).")
            else:
                logger.warning(f"Overview selector '{overview_selector}' found, but content was empty for profile {self.profile_id}.")
        except Exception as e:
            logger.error(f"Could not parse overview for profile {self.profile_id} using selector '{overview_selector}': {e}")

        # Skills
        # TODO: CRITICAL - Replace with the correct Playwright selector for individual Skill items
        skills_selector = "div.skills-section span.skill-item" # Placeholder
        try:
            skills_elements = await page.locator(skills_selector).all()
            if skills_elements:
                parsed_skills = []
                for el in skills_elements:
                    skill_text = await el.text_content(timeout=1000) # Short timeout per skill
                    if skill_text:
                        parsed_skills.append(skill_text.strip())
                profile_data['skills'] = [s for s in parsed_skills if s] # Filter out any empty strings
                logger.info(f"Parsed {len(profile_data['skills'])} skills for profile {self.profile_id}: {profile_data['skills']}")
            else:
                logger.info(f"Skills elements not found for profile {self.profile_id} using selector '{skills_selector}'.")
        except Exception as e:
            logger.error(f"Could not parse skills for profile {self.profile_id} using selector '{skills_selector}': {e}")

        logger.info(f"Finished parsing for profile {self.profile_id}. "
                    f"Name: {'Found' if profile_data['name'] != 'Name not found' else 'Not found'}, "
                    f"Title: {'Found' if profile_data['title'] != 'Title not found' else 'Not found'}, "
                    f"Overview: {'Found' if profile_data['overview'] != 'Overview not found' else 'Not found'}, "
                    f"Skills: {len(profile_data['skills'])}.")
        return profile_data

    async def _update_local_profile(self, upwork_data: dict):
        """
        Updates the local Profile record in the database with data fetched from Upwork.
        Only updates fields if new, valid data is found.
        """
        if not upwork_data:
            logger.warning(f"No Upwork data provided for profile {self.profile_id}, skipping update.")
            return

        logger.info(f"Attempting to update local profile {self.profile_id} with fetched data.")
        try:
            result = await self.db.execute(
                select(Profile).where(Profile.id == self.profile_id) # self.profile_id is already str
            )
            local_profile = result.scalars().first()

            if not local_profile:
                logger.error(f"Local profile with ID {self.profile_id} not found in the database. Cannot update.")
                return

            updated_fields = []

            # Update name if new data is valid and different
            new_name = upwork_data.get('name')
            if new_name and new_name != "Name not found" and local_profile.name != new_name:
                local_profile.name = new_name
                updated_fields.append("name")

            # Update title if new data is valid and different
            new_title = upwork_data.get('title')
            if new_title and new_title != "Title not found" and local_profile.title != new_title:
                local_profile.title = new_title
                updated_fields.append("title")

            # Update overview if new data is valid and different
            new_overview = upwork_data.get('overview')
            if new_overview and new_overview != "Overview not found" and local_profile.overview != new_overview:
                local_profile.overview = new_overview
                updated_fields.append("overview")

            # Update skills if new data is a list and different
            new_skills = upwork_data.get('skills')
            # Ensure new_skills is a list; it defaults to [] if parsing fails.
            # Check if it's different from current skills (assumes DB stores skills as list or comparable type)
            if isinstance(new_skills, list) and local_profile.skills != new_skills:
                 # Check if new_skills is not just an empty list IF local_profile.skills is also empty/None.
                 # This avoids an update if both are effectively "no skills".
                if new_skills or local_profile.skills: # Proceed if either has content
                    local_profile.skills = new_skills
                    updated_fields.append("skills")

            if updated_fields:
                logger.info(f"Updating fields {', '.join(updated_fields)} for profile {self.profile_id}.")
                await self.db.commit()
                await self.db.refresh(local_profile)
                logger.info(f"Successfully updated and refreshed local profile {self.profile_id}.")
            else:
                logger.info(f"No changes detected or new data was invalid/placeholder for local profile {self.profile_id}.")

        except Exception as e:
            logger.error(f"Error updating local profile {self.profile_id}: {e}", exc_info=True)
            try:
                await self.db.rollback()
                logger.info(f"Database rolled back for profile {self.profile_id} due to update error.")
            except Exception as rb_exc:
                logger.error(f"Error during rollback for profile {self.profile_id}: {rb_exc}", exc_info=True)


async def fetch_and_update_upwork_profile(profile_id: str, db: AsyncSession):
    """
    Orchestrates the fetching of profile data from Upwork for the given profile_id
    and updates the local database record.
    """
    logger.info(f"Starting Upwork profile fetch and update process for profile_id: {profile_id}")

    # Profile directory check (user_data_dir for persistent context)
    profile_user_data_dir = os.path.join(USER_DATA_DIR, str(profile_id))
    if not os.path.exists(profile_user_data_dir):
        # This check is crucial because launch_persistent_context might behave unexpectedly
        # or create an empty profile if the dir is missing, instead of using an existing one.
        # However, launch_persistent_context *will* create the directory if it doesn't exist.
        # The key is that a *saved session* must be in that directory for this to be useful.
        # For this function, we assume the dir should exist if a session was previously saved.
        logger.warning(f"Profile user data directory not found: {profile_user_data_dir}. "
                       f"A new profile might be created by Playwright if no existing session data is loaded. "
                       f"Ensure user has logged in and session was saved via browser_login.py for profile {profile_id}.")
        # os.makedirs(profile_user_data_dir, exist_ok=True) # launch_persistent_context does this

    fetcher = UpworkProfileFetcher(profile_id=profile_id, db=db)
    playwright_manager: Optional[Playwright] = None
    context: Optional[BrowserContext] = None
    status_payload = {"status": "unknown", "message": "Process did not complete."}


    try:
        playwright_manager = await async_playwright().start()
        page, context = await fetcher._launch_browser(playwright_manager)

        if page and context:
            await fetcher._navigate_to_profile(page)
            # Add a check here: if page.url is a login page, then session is invalid.
            if "login" in page.url or "upwork.com/ab/account-security/login" in page.url :
                 logger.error(f"Failed to load profile for {profile_id}: Session seems invalid, redirected to login page ({page.url}).")
                 status_payload = {"status": "error", "message": f"Session for profile {profile_id} is invalid or expired."}
            else:
                upwork_data = await fetcher._parse_profile_data(page)
                await fetcher._update_local_profile(upwork_data)
                # Provide a more specific summary
                summary_fields = {k: v for k, v in upwork_data.items() if k != 'skills'}
                summary_fields['skills_count'] = len(upwork_data.get('skills', []))
                status_payload = {"status": "success", "data_summary": summary_fields}
        else:
            logger.error(f"Failed to launch browser for profile {profile_id}. Cannot fetch profile data.")
            status_payload = {"status": "error", "message": f"Failed to launch browser for profile {profile_id}."}

    except Exception as e:
        logger.error(f"Major error during Upwork profile fetch for {profile_id}: {e}", exc_info=True)
        status_payload = {"status": "error", "message": f"An unexpected error occurred: {str(e)}"}
    finally:
        if context:
            try:
                await context.close()
                logger.info(f"Browser context closed for profile {profile_id}")
            except Exception as e:
                logger.error(f"Error closing browser context for profile {profile_id}: {e}", exc_info=True)
        if playwright_manager:
            try:
                # Playwright's stop() is synchronous, ensure it's not blocking if called from async code
                # However, async_playwright().start() returns an AsyncPlaywright manager, which should have an async stop
                # Based on Playwright docs, the manager from `async_playwright()` doesn't have a `stop()`.
                # The browser contexts and pages are closed, and Playwright exits when the `async with async_playwright() as p:` block ends.
                # If `playwright_manager` is the result of `async_playwright().start()`, it's an `AsyncPlaywright` object.
                # It doesn't need an explicit stop. It's managed by the Python process.
                logger.info(f"Playwright resources managed for profile {profile_id}.")
            except Exception as e:
                logger.error(f"Error managing Playwright resources for profile {profile_id}: {e}", exc_info=True)

    logger.info(f"Finished Upwork profile fetch for profile_id: {profile_id}. Result: {status_payload}")
    return status_payload

if __name__ == "__main__":
    # This __main__ block is for example and basic testing.
    # It requires a running asyncio event loop and proper database setup to function fully.

    # Setup basic logging for the __main__ example if not configured elsewhere
    if not logging.getLogger().hasHandlers():
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    async def main_test_profile_fetch():
        logger.info("Running __main__ test for UpworkProfileFetcher...")

        # Mock DB session for local testing to avoid real DB dependency for this example
        class MockAsyncSession:
            async def execute(self, query):
                logger.debug(f"Mock DB Execute: {query}")
                class MockResult:
                    def scalars(self): return self
                    def first(self): return None # Simulate profile not found or return mock Profile
                return MockResult()
            async def commit(self): logger.debug("Mock DB Commit")
            async def refresh(self, obj): logger.debug(f"Mock DB Refresh: {obj}")
            async def rollback(self): logger.debug("Mock DB Rollback")
            async def close(self): logger.debug("Mock DB Close")

        mock_db_session = MockAsyncSession()

        test_profile_id_main = "test_profile_for_main"

        # Ensure the user_data_dir for the test profile exists to simulate a previously saved session
        test_profile_user_data_dir = os.path.join(USER_DATA_DIR, test_profile_id_main)
        if not os.path.exists(test_profile_user_data_dir):
             os.makedirs(test_profile_user_data_dir, exist_ok=True)
             logger.info(f"Created dummy user data directory for profile '{test_profile_id_main}' for __main__ example: {test_profile_user_data_dir}")

        logger.info(f"Starting test fetch for profile_id: {test_profile_id_main}")
        result = await fetch_and_update_upwork_profile(test_profile_id_main, mock_db_session)
        logger.info(f"Test run result for profile {test_profile_id_main}: {result}")

    # To run this example:
    # asyncio.run(main_test_profile_fetch())
    pass # Keep pass if direct execution is not intended for CI/automated runs


async def trigger_scheduled_upwork_profile_updates(db_override: Optional[AsyncSession] = None):
    """
    Scheduled task to iterate through profiles and update their Upwork data.
    """
    logger.info("Scheduler: Starting scheduled Upwork profile updates...")

    db_session_is_managed_locally = False
    if db_override:
        db = db_override
    else:
        db = AsyncSessionLocal()
        db_session_is_managed_locally = True
        logger.info("Scheduler: Created new local DB session.")

    try:
        # Fetch all profiles to update.
        # Consider filtering for active profiles or those requiring an update based on some logic.
        # For example: .where(Profile.is_active == True) or .where(Profile.needs_upwork_update == True)
        stmt = select(Profile) # Selecting all profiles for now
        result = await db.execute(stmt)
        profiles_to_update = result.scalars().all()

        if not profiles_to_update:
            logger.info("Scheduler: No profiles found to process for scheduled Upwork profile updates.")
            return

        logger.info(f"Scheduler: Found {len(profiles_to_update)} profiles to check for updates.")

        for profile_model in profiles_to_update:
            profile_id_str = str(profile_model.id)
            logger.info(f"Scheduler: Attempting to update profile_id: {profile_id_str} (User ID: {profile_model.user_id})")
            try:
                await fetch_and_update_upwork_profile(profile_id=profile_id_str, db=db)
                logger.info(f"Scheduler: Successfully processed profile_id: {profile_id_str}")
            except Exception as e: # Catch errors from fetch_and_update_upwork_profile
                logger.error(f"Scheduler: Error processing profile_id {profile_id_str}: {e}", exc_info=True)

            # Small delay to be respectful to Upwork servers and avoid rate limiting.
            await asyncio.sleep(5) # Increased delay to 5 seconds

        logger.info("Scheduler: Finished iteration for scheduled Upwork profile updates.")

    except Exception as e:
        logger.error(f"Scheduler: General error in trigger_scheduled_upwork_profile_updates: {e}", exc_info=True)
    finally:
        if db_session_is_managed_locally and db:
            try:
                await db.close()
                logger.info("Scheduler: Local DB session closed.")
            except Exception as e:
                logger.error(f"Scheduler: Error closing local database session: {e}", exc_info=True)
