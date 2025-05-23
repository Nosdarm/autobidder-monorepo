from apscheduler.schedulers.background import BackgroundScheduler
from autobidder.autobid_logic import run_autobid
import time

def start_scheduler():
    scheduler = BackgroundScheduler()

    # Запуск каждые 2 минуты
    scheduler.add_job(run_autobid, 'interval', minutes=2)

    scheduler.start()
    print("✅ Автобидер по расписанию запущен.")

    try:
        while True:
            time.sleep(1)  # 💤 чтобы не завершался
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
