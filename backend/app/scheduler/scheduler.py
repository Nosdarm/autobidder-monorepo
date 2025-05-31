import logging # Added logging
from apscheduler.schedulers.background import BackgroundScheduler
# Assuming autobid_logic.run_autobid and upwork_profile_service.trigger_scheduled_upwork_profile_updates are compatible
# with BackgroundScheduler (e.g., they are synchronous or APScheduler handles async calls).
from autobidder.autobid_logic import run_autobid
from app.services.upwork_profile_service import trigger_scheduled_upwork_profile_updates
from app.services.upwork_job_service import trigger_scheduled_job_fetching # New import
import time

# Configure logger for this module
logger = logging.getLogger(__name__)
# Ensure basicConfig is called at least once in your application's entry point.
# If not, you can add a basicConfig here for standalone testing, but it's better to have it centralized.
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


scheduler = BackgroundScheduler()

def start_scheduler():
    # Uses the global scheduler instance
    try:
        scheduler.add_job(
            run_autobid,
            'interval',
            minutes=2,
            id='autobid_run', # Ensure IDs are unique and descriptive
            replace_existing=True,
            misfire_grace_time=60 # Default is 1s, good to set explicitly
        )
        logger.info("Autobid job scheduled.")

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
            logger.info("✅ Планировщик запущен.")
        else:
            logger.info("ℹ️ Планировщик уже запущен.")

    except Exception as e:
        logger.error(f"Ошибка при запуске планировщика или добавлении задач: {e}", exc_info=True)


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
