# backend/scripts/run_scoring.py
import asyncio
import os
import sys

# Добавляем корневую директорию 'backend' в sys.path
PROJECT_ROOT_BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT_BACKEND not in sys.path:
    sys.path.insert(0, PROJECT_ROOT_BACKEND)

from app.db.session import SessionLocal
from app.services.job_service import update_jobs_with_predicted_scores
from app.services.ml_service import load_model_on_startup, MODEL
from app.config import settings

async def main():
    print("Attempting to load ML model...")
    if MODEL is None:
        print(f"ML Model not loaded. Attempting to load from: {settings.MODEL_PATH}")
        load_model_on_startup()
        if MODEL is None:
            print(f"Failed to load ML model from {settings.MODEL_PATH}. Please ensure the model file exists and settings are correct. Exiting.")
            return
    print("ML Model is loaded or was already loaded.")

    # SessionLocal должен быть async session factory
    async with SessionLocal() as db:
        try:
            print("Starting to update job scores...")
            await update_jobs_with_predicted_scores(db)
            print("Finished updating job scores.")
        except Exception as e:
            print(f"An error occurred during scoring: {e}")
            import traceback
            traceback.print_exc()
        # Сессия закроется автоматически благодаря 'async with'

if __name__ == "__main__":
    # Эти print помогут при отладке, если пути всё еще неверные
    print(f"Current working directory: {os.getcwd()}")
    print(f"PROJECT_ROOT_BACKEND calculated as: {PROJECT_ROOT_BACKEND}")
    # Можно раскомментировать для подробного просмотра sys.path во время выполнения
    # print(f"sys.path at execution: {sys.path}")

    asyncio.run(main())
