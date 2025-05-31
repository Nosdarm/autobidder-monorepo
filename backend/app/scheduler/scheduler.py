from apscheduler.schedulers.background import BackgroundScheduler
from autobidder.autobid_logic import run_autobid
from app.services.upwork_profile_service import trigger_scheduled_upwork_profile_updates # Added import
import time

scheduler = BackgroundScheduler()

def start_scheduler():
    # Uses the global scheduler instance
    scheduler.add_job(run_autobid, 'interval', minutes=2) # Existing job

    # New job for updating Upwork profiles
    scheduler.add_job(
        trigger_scheduled_upwork_profile_updates,
        'interval',
        hours=6,
        id='update_upwork_profiles',
        replace_existing=True
    )

    scheduler.start()
    print("✅ Планировщик запущен с автобиддером и обновлением профилей Upwork.")

def shutdown_scheduler():
    # Uses the global scheduler instance
    if scheduler.running: # Check if scheduler is running before shutting down
        scheduler.shutdown()
        print("🛑 Планировщик остановлен.")
    else:
        print("ℹ️ Планировщик не был запущен.")
