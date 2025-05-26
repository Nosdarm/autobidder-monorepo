import time
from backend.autobidder.autobid_logic import run_autobid

def run_periodically(interval_seconds: int = 60):
    while True:
        print("🚀 Запуск авто-бидера...")
        run_autobid()
        print("🕒 Ожидание следующего запуска...\n")
        time.sleep(interval_seconds)

if __name__ == "__main__":
    run_periodically(60)  # запуская каждые 60 секунд
