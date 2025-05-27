from apscheduler.schedulers.background import BackgroundScheduler
from autobidder.autobid_logic import run_autobid
import time

scheduler = BackgroundScheduler()

def start_scheduler():
    # Uses the global scheduler instance
    scheduler.add_job(run_autobid, 'interval', minutes=2)
    scheduler.start()
    print("✅ Автобидер по расписанию запущен.")

def shutdown_scheduler():
    # Uses the global scheduler instance
    if scheduler.running: # Check if scheduler is running before shutting down
        scheduler.shutdown()
        print("🛑 Автобидер по расписанию остановлен.")
    else:
        print("ℹ️ Планировщик не был запущен.")
