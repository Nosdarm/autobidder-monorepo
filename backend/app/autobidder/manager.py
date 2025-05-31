# app/autobidder/manager.py
import asyncio
import logging
import random # Added random
from sqlalchemy.ext.asyncio import AsyncSession # Added AsyncSession for type hints
from app.database import AsyncSessionLocal # For creating a session
from app.services.autobidder_settings_service import get_enabled_autobid_settings # Import the refactored service
from app.browser.browser_bidder import run_browser_bidder_for_profile # Import the bidder function

logger = logging.getLogger(__name__) # Use module-level logger

# Old queue-based logic removed/commented out:
# queue = asyncio.Queue()
# async def enqueue_profiles(): ...
# async def worker(worker_id: int): ...
# async def start_autobidder_loop(): ...


async def trigger_autobid_for_active_profiles_task():
    """
    Task function to be called by APScheduler.
    Fetches active autobid profiles and runs the browser bidder for each.
    """
    logger.info("Starting scheduled autobid task for active profiles...")
    db: AsyncSession = AsyncSessionLocal()
    try:
        # get_enabled_autobid_settings is now async and takes AsyncSession
        active_settings_list = await get_enabled_autobid_settings(db)

        if not active_settings_list:
            logger.info("No active autobid profiles found.")
            return

        logger.info(f"Found {len(active_settings_list)} active autobid profile(s) to process.")

        for setting in active_settings_list:
            # Ensure profile_id is string if expected by run_browser_bidder_for_profile
            # The AutobidSettings model likely has profile_id as string or UUID.
            # run_browser_bidder_for_profile expects str.
            profile_id = str(setting.profile_id)

            logger.info(f"Processing autobid for profile_id: {profile_id}")
            try:
                # run_browser_bidder_for_profile now takes AsyncSession
                await run_browser_bidder_for_profile(profile_id=profile_id, db=db)
                logger.info(f"Successfully finished autobid processing for profile_id: {profile_id}")
            except Exception as e:
                logger.error(f"Error during autobid processing for profile_id {profile_id}: {e}", exc_info=True)

            # Optional: Short delay between profiles if running sequentially and there are multiple profiles
            if len(active_settings_list) > 1:
                sleep_duration = random.randint(5, 15)
                logger.info(f"Processed profile {profile_id}. Sleeping for {sleep_duration}s before next profile.")
                await asyncio.sleep(sleep_duration)

        logger.info("Finished processing all active autobid profiles.")

    except Exception as e:
        logger.error(f"Critical error in trigger_autobid_for_active_profiles_task: {e}", exc_info=True)
    finally:
        await db.close()
        logger.info("Database session closed for autobid task.")