# backend/app/services/upwork_job_service.py
import asyncio
import os
import json
import logging
from typing import Optional, List, Dict, Tuple, Any

from playwright.async_api import (
    async_playwright,
    Playwright,
    Page,
    BrowserContext,
    Response as PlaywrightResponse
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from app.models.job import Job
# from app.schemas.job import JobCreate # Placeholder, if needed for validation before Job model creation
from app.database import AsyncSessionLocal
from app.models.profile import Profile # Added for trigger_scheduled_job_fetching
import datetime # For parsing dates

# Configure basic logging
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s') # Already configured, ensure it's at app level
# Re-get logger if basicConfig was called globally elsewhere, or ensure it's configured once.
# For service file, usually just getting the logger is enough if config is in main app entry.
logger = logging.getLogger(__name__)

USER_DATA_DIR = "user_data"
AUTH_STATE_DIR = "auth_states"

# Placeholder - this needs to be determined by inspecting Upwork's network traffic
# Common patterns might include '/api/', '/jobs/', '/search/'
# Using a list of patterns to be more flexible
UPWORK_JOB_API_PATTERNS = [
    "**/api/search/jobs**", # Example pattern 1
    "**/search/jobs/url**", # Example pattern 2
    "**/jobs/api/v1/search/jobs**", # Example pattern 3
    "**/graphql**" # Many modern sites use GraphQL
]

class UpworkJobFetcher:
    def __init__(self, profile_id: str, db_session: AsyncSession):
        self.profile_id = str(profile_id)
        self.db_session = db_session
        self.profile_dir = os.path.join(USER_DATA_DIR, self.profile_id)
        self.auth_file = os.path.join(AUTH_STATE_DIR, f"{self.profile_id}_auth.json")

        os.makedirs(USER_DATA_DIR, exist_ok=True)
        os.makedirs(AUTH_STATE_DIR, exist_ok=True)

    async def _launch_browser_with_session(self, p: Playwright) -> Tuple[Optional[Page], Optional[BrowserContext]]:
        if not os.path.exists(self.auth_file):
            logger.error(f"Authentication file not found for profile {self.profile_id} at {self.auth_file}")
            return None, None

        logger.info(f"Attempting to launch browser with session for profile {self.profile_id} using auth file: {self.auth_file}")
        try:
            context = await p.chromium.launch_persistent_context(
                user_data_dir=self.profile_dir, # Persistent context needs a user data directory
                headless=True, # Run headless for automation
                storage_state=self.auth_file,
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
                viewport={"width": 1280, "height": 800},
                args=[
                    "--no-sandbox",
                    "--disable-blink-features=AutomationControlled",
                    "--disable-dev-shm-usage" # Often recommended for Docker/CI environments
                ],
                # slow_mo=50 # Uncomment for debugging to see what's happening
            )
            page = await context.new_page()
            await page.set_extra_http_headers({"Accept-Language": "en-US,en;q=0.9"})
            logger.info(f"Browser launched successfully for profile {self.profile_id}.")
            return page, context
        except Exception as e:
            logger.error(f"Error launching browser with session for profile {self.profile_id}: {e}")
            return None, None

    async def fetch_jobs_from_feed(self, search_terms: Optional[str] = None) -> List[Dict[str, Any]]:
        job_api_responses: List[Dict[str, Any]] = [] # Store raw JSON responses

        async def handle_response(response: PlaywrightResponse):
            try:
                is_match = False
                for pattern in UPWORK_JOB_API_PATTERNS:
                    if pattern.startswith("**/") and pattern.endswith("/**"): # Glob pattern for path segments
                        if pattern[3:-3] in response.url:
                            is_match = True
                            break
                    elif pattern.startswith("**/"): # Glob pattern for prefix
                         if response.url.endswith(pattern[3:]):
                            is_match = True
                            break
                    elif pattern.endswith("/**"): # Glob pattern for suffix
                        if response.url.startswith(pattern[:-3]):
                            is_match = True
                            break
                    elif pattern in response.url: # Simple substring match
                        is_match = True
                        break

                if is_match:
                    logger.info(f"Intercepted API response from URL: {response.url}")
                    if response.ok:
                        try:
                            json_response = await response.json()
                            job_api_responses.append(json_response)
                            logger.info(f"Successfully parsed JSON from: {response.url}")
                        except json.JSONDecodeError:
                            logger.error(f"Failed to parse JSON from {response.url}. Body: {await response.text()}")
                        except Exception as e:
                            logger.error(f"Error parsing JSON from {response.url}: {e}")
                    else:
                        logger.warning(f"Non-OK response from {response.url}: Status {response.status} {response.status_text}")
                        # logger.warning(f"Response body: {await response.text()}") # Be cautious with logging large bodies
            except Exception as e:
                logger.error(f"Error processing response from {response.url}: {e}")

        async with async_playwright() as p:
            page, context = await self._launch_browser_with_session(p)
            if not page or not context:
                logger.error("Failed to launch browser, cannot fetch jobs.")
                return []

            page.on("response", handle_response)

            base_search_url = "https://www.upwork.com/nx/jobs/search/"
            if search_terms:
                # Ensure search_terms are URL-encoded if they contain special characters
                # For simplicity, Playwright's goto usually handles basic encoding for query params
                search_url = f"{base_search_url}?q={search_terms.replace(' ', '+')}"
            else:
                search_url = base_search_url # Default feed

            logger.info(f"Navigating to job search URL: {search_url}")
            try:
                await page.goto(search_url, wait_until="networkidle", timeout=60000) # Increased timeout
                logger.info(f"Successfully navigated to {search_url}. Waiting for dynamic content...")

                # Wait for a bit or perform actions to trigger API calls if jobs load dynamically
                await page.wait_for_timeout(10000) # Wait 10 seconds for API calls

                # Example: Scroll to bottom to trigger more job loads
                # logger.info("Scrolling page to trigger more job loads...")
                # await page.evaluate('window.scrollBy(0, document.body.scrollHeight)')
                # await page.wait_for_timeout(5000) # Wait after scroll

            except Exception as e:
                logger.error(f"Error during navigation or waiting on {search_url}: {e}")
                # Optionally take a screenshot for debugging
                # screenshot_path = f"error_screenshot_profile_{self.profile_id}.png"
                # await page.screenshot(path=screenshot_path)
                # logger.info(f"Screenshot saved to {screenshot_path}")
            finally:
                page.remove_listener("response", handle_response)
                if context:
                    await context.close()
                logger.info("Browser context closed.")

        # Process API responses to extract structured job data
        processed_jobs_data: List[Dict[str, Any]] = []
        processed_upwork_job_ids_in_current_fetch = set()

        for response_item in job_api_responses:
            if not response_item:
                continue

            jobs_list_in_response = []
            if isinstance(response_item, dict):
                # This part remains speculative and needs adjustment based on actual API response structure
                potential_job_keys = ['jobs', 'results', 'marketplaceJobs', 'data', 'records']
                for key in potential_job_keys:
                    if key in response_item and isinstance(response_item[key], list):
                        jobs_list_in_response = response_item[key]
                        break
                    # Handle nested structures like data.jobs or data.search.jobs
                    if key == 'data' and isinstance(response_item.get('data'), dict):
                        nested_data = response_item['data']
                        for nested_key in potential_job_keys: # Check common keys inside 'data'
                            if nested_key in nested_data and isinstance(nested_data[nested_key], list):
                                jobs_list_in_response = nested_data[nested_key]
                                break
                            # Deeper nesting, e.g. data.search.results
                            if isinstance(nested_data.get(nested_key), dict):
                                deeper_data = nested_data[nested_key]
                                for deeper_key in potential_job_keys:
                                    if deeper_key in deeper_data and isinstance(deeper_data[deeper_key], list):
                                        jobs_list_in_response = deeper_data[deeper_key]
                                        break
                                if jobs_list_in_response: break
                        if jobs_list_in_response: break

                if not jobs_list_in_response and isinstance(response_item.get('data'), list): # e.g. GraphQL returning { "data": [...] }
                    jobs_list_in_response = response_item['data']

            elif isinstance(response_item, list): # If the entire response is a list of jobs
                jobs_list_in_response = response_item

            if not jobs_list_in_response:
                logger.warning(f"Could not find a list of jobs in an API response. Keys: {list(response_item.keys()) if isinstance(response_item, dict) else 'Not a dict'}. URL: (not available here)")
                continue

            for job_raw in jobs_list_in_response:
                if not isinstance(job_raw, dict):
                    logger.warning(f"Skipping non-dictionary job item: {job_raw}")
                    continue

                # --- Refined Data Extraction ---
                upwork_job_id = job_raw.get('ciphertext') or job_raw.get('id') or job_raw.get('uid') or job_raw.get('legacyGATSJobID')
                if not upwork_job_id:
                    logger.warning(f"Skipping job due to missing ID. Raw keys: {list(job_raw.keys())}")
                    continue

                upwork_job_id = str(upwork_job_id) # Ensure it's a string

                if upwork_job_id in processed_upwork_job_ids_in_current_fetch:
                    logger.info(f"Skipping duplicate job ID {upwork_job_id} within current fetch batch.")
                    continue

                title = job_raw.get('title')
                # Description snippet often available, full description might need separate fetch
                description_snippet = job_raw.get('description') or job_raw.get('snippet') or job_raw.get('shortDescription')

                # Construct URL - this is a common pattern for Upwork job URLs
                job_url = f"https://www.upwork.com/jobs/{upwork_job_id}"
                if 'url' in job_raw: # If a direct URL is provided
                    job_url = job_raw['url']

                posted_time_str = job_raw.get('createdOn') or job_raw.get('postedTime') or job_raw.get('publicationTime') # Common keys for post time
                posted_time_dt = None
                if posted_time_str:
                    try:
                        # Try ISO format first, then attempt more general parsing if needed
                        if isinstance(posted_time_str, str):
                            posted_time_dt = datetime.datetime.fromisoformat(posted_time_str.replace("Z", "+00:00"))
                        elif isinstance(posted_time_str, (int, float)): # Handle Unix timestamps (ms or s)
                             # Assuming timestamp is in seconds or milliseconds
                            if posted_time_str > 1e12: # Likely milliseconds
                                posted_time_dt = datetime.datetime.fromtimestamp(posted_time_str / 1000, tz=datetime.timezone.utc)
                            else: # Likely seconds
                                posted_time_dt = datetime.datetime.fromtimestamp(posted_time_str, tz=datetime.timezone.utc)
                    except ValueError:
                        logger.warning(f"Could not parse date string '{posted_time_str}' for job {upwork_job_id}. Needs specific parser or format is unknown.")
                    except Exception as e:
                        logger.error(f"Error parsing date string '{posted_time_str}' for job {upwork_job_id}: {e}")

                job_data_for_db = {
                    "upwork_job_id": upwork_job_id,
                    "title": title,
                    "description": description_snippet, # Storing snippet as description for now
                    "url": job_url,
                    "posted_time": posted_time_dt,
                    "raw_data": job_raw, # Store the full JSON for this job
                    # description_embedding will be handled later
                }
                processed_jobs_data.append(job_data_for_db)
                processed_upwork_job_ids_in_current_fetch.add(upwork_job_id)

        logger.info(f"Extracted {len(processed_jobs_data)} unique jobs from API responses for profile {self.profile_id}.")

        if not processed_jobs_data and job_api_responses:
            logger.warning("API responses were captured but no jobs could be extracted. Check API response structure and job extraction logic.")
        elif not job_api_responses:
            logger.warning("No API responses matching the patterns were captured.")

        # Store jobs in DB
        if processed_jobs_data:
            added_count, skipped_count = await self._store_jobs(processed_jobs_data)
            logger.info(f"DB: Added {added_count} new jobs, skipped {skipped_count} existing jobs.")
            # The function is expected to return the raw data for now, but in future might return Job model instances or status
            return processed_jobs_data # Or just a success message/count

        return [] # Return empty list if no jobs processed or stored

    async def _store_jobs(self, jobs_data: List[Dict[str, Any]]) -> Tuple[int, int]:
        added_count = 0
        skipped_count = 0

        if not self.db_session:
            logger.error("Database session not available. Cannot store jobs.")
            return 0, len(jobs_data)

        for job_dict in jobs_data:
            upwork_job_id = job_dict.get("upwork_job_id")
            if not upwork_job_id:
                logger.error(f"Skipping job due to missing 'upwork_job_id' in prepared data: {job_dict.get('title')}")
                skipped_count +=1
                continue

            try:
                # Check if job already exists
                result = await self.db_session.execute(
                    select(Job).where(Job.upwork_job_id == upwork_job_id)
                )
                existing_job = result.scalars().first()

                if existing_job:
                    skipped_count += 1
                else:
                    # Ensure all required fields for Job model are present, others can be None
                    # 'description_embedding' is not set here, will be handled by another process
                    new_job = Job(
                        upwork_job_id=job_dict["upwork_job_id"],
                        title=job_dict.get("title"),
                        description=job_dict.get("description"),
                        url=job_dict.get("url"),
                        posted_time=job_dict.get("posted_time"),
                        raw_data=job_dict.get("raw_data"),
                        # id will be auto-generated (UUID)
                        # description_embedding will be None initially
                    )
                    self.db_session.add(new_job)
                    added_count += 1
            except Exception as e: # Catch broader exceptions during DB interaction for a single job
                logger.error(f"Error processing job {upwork_job_id} for DB: {e}")
                skipped_count +=1 # Consider it skipped if error during check/add pre-commit

        if added_count > 0:
            try:
                await self.db_session.commit()
                logger.info(f"Successfully committed {added_count} new jobs to the database.")
            except IntegrityError as e:
                await self.db_session.rollback()
                logger.error(f"Database integrity error: {e}. Rolled back session. Some jobs might not have been saved.")
                # This typically happens if a unique constraint is violated concurrently, though primary check should prevent it.
                # For simplicity, we'll count them as skipped, though some might have failed.
                # A more granular retry or error tracking per job could be added.
                added_count = 0 # Reset added_count as commit failed
                skipped_count = len(jobs_data) # Assume all failed to add in this batch due to rollback
            except Exception as e:
                await self.db_session.rollback()
                logger.error(f"General error committing jobs: {e}. Rolled back session.")
                added_count = 0
                skipped_count = len(jobs_data)

        return added_count, skipped_count


async def trigger_scheduled_job_fetching(db_override: Optional[AsyncSession] = None):
    """
    Scheduled task to fetch Upwork jobs for all active profiles.
    An active profile is assumed to be one with `autobid_enabled == True`.
    """
    logger.info("Starting scheduled job fetching for active profiles...")
    db_session_is_managed_locally = False
    if db_override:
        db = db_override
    else:
        db = AsyncSessionLocal()
        db_session_is_managed_locally = True

    try:
        stmt = select(Profile).where(Profile.autobid_enabled == True)
        result = await db.execute(stmt)
        profiles_to_process = result.scalars().all()

        if not profiles_to_process:
            logger.info("No active profiles found to process for scheduled job fetching.")
            return

        logger.info(f"Found {len(profiles_to_process)} active profiles for job fetching.")

        for profile in profiles_to_process:
            # Ensure profile.id is string as UpworkJobFetcher expects string profile_id
            profile_id_str = str(profile.id)
            logger.info(f"Processing profile ID: {profile_id_str} (Name: {profile.profile_name or 'N/A'})")

            # Check if auth file exists for this profile before proceeding
            auth_file = os.path.join(AUTH_STATE_DIR, f"{profile_id_str}_auth.json")
            if not os.path.exists(auth_file):
                logger.warning(f"Auth file not found for profile {profile_id_str} at {auth_file}. Skipping job fetching for this profile.")
                continue

            try:
                fetcher = UpworkJobFetcher(profile_id=profile_id_str, db_session=db)
                # For scheduled tasks, we usually fetch the general feed.
                # Specific search terms might be handled by user-triggered actions or more complex scheduling.
                search_terms = None
                await fetcher.fetch_jobs_from_feed(search_terms=search_terms)
                logger.info(f"Job fetching completed for profile ID: {profile_id_str}.")
            except Exception as e:
                logger.error(f"Error during job fetching for profile ID {profile_id_str}: {e}")

            await asyncio.sleep(2) # Small delay to avoid overwhelming the server or hitting rate limits rapidly.

        logger.info("Scheduled job fetching for active profiles completed.")

    except Exception as e:
        logger.error(f"Error in trigger_scheduled_job_fetching: {e}")
    finally:
        if db_session_is_managed_locally:
            await db.close()
            logger.info("Local DB session closed for scheduled job fetching.")


# Example usage (for testing purposes)
if __name__ == "__main__":
    # NOTE: This __main__ block is for basic testing.
    # For a real application, database initialization (e.g., creating tables via Alembic)
    # should be handled as part of your application startup or deployment process.
    # If you run this standalone and the 'jobs' table doesn't exist, it will fail.

    async def main():
        test_profile_id = "test_profile_main_01" # Replace with a profile_id that has an auth file

        auth_file_path = os.path.join(AUTH_STATE_DIR, f"{test_profile_id}_auth.json")
        if not os.path.exists(auth_file_path):
            logger.error(f"Auth file for profile '{test_profile_id}' not found at '{auth_file_path}'.")
            logger.error("Please run `python backend/app/auth/browser_login.py login <profile_id>` first.")
            logger.error("Or, use `python backend/app/auth/browser_login.py cookies <profile_id> \"<cookie_json_or_path>\"`.")
            return

        # Setup DB session
        async with AsyncSessionLocal() as session:
            fetcher = UpworkJobFetcher(profile_id=test_profile_id, db_session=session)

            logger.info(f"--- Fetching jobs for default feed for profile: {test_profile_id} ---")
            # The function now returns the processed data list, or empty if nothing stored/processed
            fetched_job_data_list = await fetcher.fetch_jobs_from_feed()
            if fetched_job_data_list:
                logger.info(f"Processed {len(fetched_job_data_list)} jobs from the feed for potential storage.")
                # Example: Print details of the first few jobs that were processed (not necessarily stored if already exist)
                for i, job_data in enumerate(fetched_job_data_list[:3]):
                    logger.info(f"Processed Job {i+1}: ID - {job_data.get('upwork_job_id', 'N/A')}, Title - {job_data.get('title', 'N/A')}")
            else:
                logger.info("No new jobs processed or found from the feed.")

            logger.info(f"\n--- Fetching jobs with search term 'python' for profile: {test_profile_id} ---")
            fetched_job_data_list_search = await fetcher.fetch_jobs_from_feed(search_terms="python")
            if fetched_job_data_list_search:
                logger.info(f"Processed {len(fetched_job_data_list_search)} jobs for 'python' for potential storage.")
                for i, job_data in enumerate(fetched_job_data_list_search[:3]):
                     logger.info(f"Processed Job {i+1}: ID - {job_data.get('upwork_job_id', 'N/A')}, Title - {job_data.get('title', 'N/A')}")
            else:
                logger.info("No new jobs processed or found for 'python'.")

    asyncio.run(main())
