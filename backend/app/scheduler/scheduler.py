import logging # Added logging
from apscheduler.schedulers.background import BackgroundScheduler
# Assuming autobid_logic.run_autobid and upwork_profile_service.trigger_scheduled_upwork_profile_updates are compatible
# with BackgroundScheduler (e.g., they are synchronous or APScheduler handles async calls).
# from autobidder.autobid_logic import run_autobid # This will be removed
from app.autobidder.manager import trigger_autobid_for_active_profiles_task # New autobid task
from app.services.upwork_profile_service import trigger_scheduled_upwork_profile_updates
from app.services.upwork_job_service import trigger_scheduled_job_fetching
# import time # Removed unused import

# Configure logger for this module
logger = logging.getLogger(__name__)
# Ensure basicConfig is called at least once in your application's entry point.
# If not, you can add a basicConfig here for standalone testing, but it's better to have it centralized.
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


scheduler = BackgroundScheduler()

def start_scheduler():
    # Uses the global scheduler instance
    try:
        # Removed old autobid job:
        # scheduler.add_job(
        #     run_autobid,
        #     'interval',
        #     minutes=2,
        #     id='autobid_run',
        #     replace_existing=True,
        #     misfire_grace_time=60
        # )
        # logger.info("Old autobid job (run_autobid) removed.")

        # Add new autobid task
        scheduler.add_job(
            trigger_autobid_for_active_profiles_task,
            'interval',
            minutes=30,
            id='trigger_autobid_for_active_profiles_task',
            replace_existing=True,
            misfire_grace_time=300 # 5 minutes
        )
        logger.info("Autobid task (trigger_autobid_for_active_profiles_task) scheduled every 30 minutes.")

        scheduler.add_job(
            trigger_scheduled_upwork_profile_updates,
            'interval',
            hours=6,
            id='update_upwork_profiles',
            replace_existing=True,
            misfire_grace_time=300 # 5 minutes
        )
        logger.info("Upwork profile update job scheduled.")

        # New job for fetching Upwork jobs
        scheduler.add_job(
            trigger_scheduled_job_fetching,
            "interval",
            minutes=5, # As per requirement
            id="scheduled_fetch_upwork_jobs",
            replace_existing=True,
            misfire_grace_time=60 # 1 minute
        )
        logger.info("Upwork job fetching job scheduled.")

        if not scheduler.running:
            scheduler.start()
            logger.info("✅ Scheduler started with new autobid task, profile updates, and job fetching.")
        else:
            logger.info("ℹ️ Scheduler already running. Jobs (re)loaded with new autobid task.")

    except Exception as e:
        logger.error(f"Error starting scheduler or adding jobs: {e}", exc_info=True)


def shutdown_scheduler():
    # Uses the global scheduler instance
    if scheduler.running:
        try:
            scheduler.shutdown()
            logger.info("🛑 Планировщик остановлен.")
        except Exception as e:
            logger.error(f"Ошибка при остановке планировщика: {e}", exc_info=True)
    else:
        logger.info("ℹ️ Планировщик не был запущен.")
