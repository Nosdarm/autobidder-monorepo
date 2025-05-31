import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from playwright.async_api import async_playwright, Playwright
import os
from app.models.profile import Profile # Added import
from sqlalchemy import select # Added import

# Assuming USER_DATA_DIR is defined similarly elsewhere or should be configured
USER_DATA_DIR = "user_data" # Or fetch from a config file

class UpworkProfileFetcher:
    def __init__(self, profile_id: str, db: AsyncSession):
        self.profile_id = profile_id
        self.db = db
        self.profile_dir = os.path.join(USER_DATA_DIR, str(self.profile_id)) # Ensure profile_id is string for path

    async def _launch_browser(self, p: Playwright):
        try:
            # Using headless=True for background operation.
            context = await p.chromium.launch_persistent_context(
                self.profile_dir,
                headless=True,
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
                args=[
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-blink-features=AutomationControlled"
                ]
            )
            page = await context.new_page()
            print(f"Browser launched successfully for profile {self.profile_id} using {self.profile_dir}")
            return page, context
        except Exception as e:
            print(f"Error launching browser for profile {self.profile_id}: {e}")
            return None, None

    async def _navigate_to_profile(self, page):
        if not page:
            print("Page object not available, skipping navigation.")
            return

        try:
            print(f"Navigating to Upwork feed for profile {self.profile_id}...")
            await page.goto("https://www.upwork.com/ab/find-work/", wait_until="domcontentloaded")
            print("Successfully navigated to Upwork feed.")

            # Placeholder selector strategy - this will likely need refinement
            profile_link_selector = "nav li a[href*='/profile'], nav a:has-text('Profile')" # TODO: Refine selector
            print(f"Attempting to click profile link using selector: {profile_link_selector}")

            # Using a try-except for the click action itself, as it's a common point of failure
            try:
                await page.click(profile_link_selector, timeout=10000) # 10 second timeout
                print("Profile link clicked. Waiting for page to load...")
                await page.wait_for_load_state("domcontentloaded")
                print(f"Navigated to profile page, current URL: {page.url}")
            except Exception as e:
                print(f"Could not click profile link or page did not load as expected: {e}")
                print(f"Current URL after failed click attempt: {page.url}")
                # Optionally, attempt other selectors or strategies here if the first fails

        except Exception as e:
            print(f"Error during navigation for profile {self.profile_id}: {e}")
            print(f"Current page URL when error occurred: {page.url}")

    async def _parse_profile_data(self, page):
        profile_data = {
            'name': None,
            'title': None,
            'overview': None,
            'skills': []
        }
        if not page:
            print("Page object not available, skipping parsing.")
            return profile_data

        print(f"Attempting to parse profile data from page: {page.url} for profile {self.profile_id}")

        # Placeholder selector for Name
        try:
            # TODO: Replace with actual selector for Name
            name_selector = "div.user-profile-name h1"
            profile_data['name'] = await page.locator(name_selector).text_content(timeout=5000)
            print(f"Parsed name: {profile_data['name']}")
        except Exception as e:
            print(f"Could not parse name: {e}")
            profile_data['name'] = "Name not found"

        # Placeholder selector for Title/Headline
        try:
            # TODO: Replace with actual selector for Title
            title_selector = "div.user-profile-title span"
            profile_data['title'] = await page.locator(title_selector).text_content(timeout=5000)
            print(f"Parsed title: {profile_data['title']}")
        except Exception as e:
            print(f"Could not parse title: {e}")
            profile_data['title'] = "Title not found"

        # Placeholder selector for Overview/Summary
        try:
            # TODO: Replace with actual selector for Overview
            overview_selector = "div.profile-overview-section p"
            profile_data['overview'] = await page.locator(overview_selector).text_content(timeout=5000)
            print(f"Parsed overview: {profile_data['overview']}")
        except Exception as e:
            print(f"Could not parse overview: {e}")
            profile_data['overview'] = "Overview not found"

        # Placeholder selector for Skills
        try:
            # TODO: Replace with actual selector for Skills
            skills_selector = "div.skills-section span.skill-item"
            skills_elements = await page.locator(skills_selector).all()
            if skills_elements:
                parsed_skills = []
                for el in skills_elements:
                    skill_text = await el.text_content(timeout=1000)
                    if skill_text:
                        parsed_skills.append(skill_text.strip())
                profile_data['skills'] = parsed_skills
                print(f"Parsed skills: {profile_data['skills']}")
            else:
                print("Skills elements not found.")
                profile_data['skills'] = []
        except Exception as e:
            print(f"Could not parse skills: {e}")
            profile_data['skills'] = [] # Default to empty list on error

        print(f"Finished parsing. Profile data summary for {self.profile_id}: "
              f"Name: {'Yes' if profile_data['name'] else 'No'}, "
              f"Title: {'Yes' if profile_data['title'] else 'No'}, "
              f"Overview: {'Yes' if profile_data['overview'] else 'No'}, "
              f"Skills: {len(profile_data['skills'])} found.")

        return profile_data

    async def _update_local_profile(self, upwork_data: dict):
        if not upwork_data:
            print(f"No Upwork data provided for profile {self.profile_id}, skipping update.")
            return

        print(f"Attempting to update local profile {self.profile_id} with data: {upwork_data.get('name')}, {len(upwork_data.get('skills', []))} skills")

        try:
            result = await self.db.execute(
                select(Profile).where(Profile.id == str(self.profile_id)) # Ensure profile_id is str for query
            )
            local_profile = result.scalars().first()

            if local_profile:
                updated = False
                # Update name if new data is valid
                new_name = upwork_data.get('name')
                if new_name and new_name != "Name not found" and local_profile.name != new_name:
                    local_profile.name = new_name
                    print(f"Updating profile {self.profile_id} name to: {new_name}")
                    updated = True

                # Update skills if new data is valid (list of strings)
                new_skills = upwork_data.get('skills')
                if isinstance(new_skills, list) and local_profile.skills != new_skills:
                    local_profile.skills = new_skills # Assumes Profile.skills can take a list
                    print(f"Updating profile {self.profile_id} skills to: {new_skills}")
                    updated = True

                new_title = upwork_data.get('title')
                if new_title and new_title != "Title not found" and local_profile.title != new_title:
                    local_profile.title = new_title
                    print(f"Updating profile {self.profile_id} title to: {new_title}")
                    updated = True

                new_overview = upwork_data.get('overview')
                if new_overview and new_overview != "Overview not found" and local_profile.overview != new_overview:
                    local_profile.overview = new_overview
                    print(f"Updating profile {self.profile_id} overview to: {new_overview}")
                    updated = True

                if updated:
                    print(f"Fields updated for profile {self.profile_id}: name, skills, title, overview (if changed).")
                    await self.db.commit()
                    await self.db.refresh(local_profile)
                    print(f"Successfully updated local profile {self.profile_id}.")
                else:
                    print(f"No changes detected for local profile {self.profile_id}. Data might be the same or invalid.")
            else:
                print(f"Local profile with ID {self.profile_id} not found in the database.")

        except Exception as e:
            print(f"Error updating local profile {self.profile_id}: {e}")
            # Consider await self.db.rollback() here if an error occurs during transaction


async def fetch_and_update_upwork_profile(profile_id: str, db: AsyncSession):
    """
    Fetches profile data from Upwork for the given profile_id and updates the local database.
    """
    print(f"Starting Upwork profile fetch for profile_id: {profile_id}")

    profile_dir_path = os.path.join(USER_DATA_DIR, str(profile_id))
    if not os.path.exists(profile_dir_path):
        print(f"Profile directory not found: {profile_dir_path}. User might need to log in first via browser_login.py.")
        return {"status": "error", "message": "Profile directory not found. Please ensure session is saved."}

    fetcher = UpworkProfileFetcher(profile_id=profile_id, db=db)

    playwright_manager = None
    page = None
    context = None
    status_message = {}

    try:
        playwright_manager = await async_playwright().start()
        page, context = await fetcher._launch_browser(playwright_manager)

        if page and context:
            await fetcher._navigate_to_profile(page)
            upwork_data = await fetcher._parse_profile_data(page)
            await fetcher._update_local_profile(upwork_data)
            status_message = {"status": "success", "data_summary": f"Fetched {len(upwork_data)} fields."}
        else:
            # This branch means browser launch failed
            status_message = {"status": "error", "message": f"Failed to launch browser for profile {profile_id}."}

    except Exception as e:
        print(f"Error during Upwork profile fetch for {profile_id}: {e}")
        status_message = {"status": "error", "message": str(e)}
    finally:
        if context:
            try:
                await context.close()
                print(f"Browser context closed for profile {profile_id}")
            except Exception as e:
                print(f"Error closing browser context for profile {profile_id}: {e}")
        if playwright_manager:
            try:
                await playwright_manager.stop()
                print("Playwright manager stopped.")
            except Exception as e:
                print(f"Error stopping Playwright manager: {e}")

    print(f"Finished Upwork profile fetch for profile_id: {profile_id}. Result: {status_message}")
    return status_message

if __name__ == "__main__":
    # Example of how to run (requires a running event loop and DB setup)
    # This is just for illustration and won't run directly without more context
    async def main_test():
        # Mock DB session for local testing
        class MockAsyncSession:
            async def execute(self, query): return self
            def scalars(self): return self
            def first(self): return None
            async def commit(self): pass
            async def refresh(self, obj): pass

        mock_db = MockAsyncSession()
        # Replace "test_profile_id" with an actual profile ID that has a user_data dir
        # Ensure user_data/test_profile_id directory exists if not using placeholders fully
        if not os.path.exists(os.path.join(USER_DATA_DIR, "test_profile_id")):
             os.makedirs(os.path.join(USER_DATA_DIR, "test_profile_id"), exist_ok=True)
             print(f"Created dummy directory for test_profile_id for __main__ example")

        result = await fetch_and_update_upwork_profile("test_profile_id", mock_db)
        print(f"Test run result: {result}")

    # To run this example:
    # asyncio.run(main_test())
    pass
