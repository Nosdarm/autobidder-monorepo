import json
import os
import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.pipeline import make_pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import joblib
from app.config import settings # Added import

PROFILES_FILE = "profiles.json"
JOBS_FILE = "jobs.json"
RESPONSES_FILE = "responses_log.json"
MODEL_FILE = settings.MODEL_PATH # Changed to use settings.MODEL_PATH

# 📥 Загрузка
def load_json(path):
    if not os.path.exists(path):
        return []
    with open(path) as f:
        return json.load(f)

def execute_training_logic():
    profiles = load_json(PROFILES_FILE)
    jobs = load_json(JOBS_FILE)
    responses = load_json(RESPONSES_FILE)

    # 🔄 Создание обучающего датасета
    rows = []
    for profile in profiles:
        for job in jobs:
            row = {
                "profile_id": profile["id"],
                "job_id": job["id"],
                "text": job["title"] + " " + job["description"],
                "budget": job.get("budget", 0),
                "keywords": " ".join(profile.get("filters", {}).get("include_keywords", [])),
                "label": 1 if any(r["profile_id"] == profile["id"] and r["job_id"] == job["id"] for r in responses) else 0
            }
            rows.append(row)

    df = pd.DataFrame(rows)
    if df.empty:
        print("❌ Нет данных для обучения")
        # Consider using return or sys.exit(0) if this function is meant to be a script entry point
        # For now, simple return to allow testing to proceed if df is empty with certain mock data.
        return

    # 🧠 Обучение модели
    X = df["keywords"] + " " + df["text"]
    y = df["label"]

    if len(y.unique()) < 2:
        print(f"⚠️ Only one class ({y.unique()}) present in labels before splitting. Model training might be ineffective or fail.")
        # If training requires at least two classes, you might return here or raise an error.
        # For this script, we'll let it proceed to train_test_split, which might also fail if y_train has <2 classes.
        if len(df) < 2 : # Cannot split if less than 2 samples
             print("❌ Not enough data to perform train/test split. Exiting training.")
             return


    pipeline = make_pipeline(
        CountVectorizer(),
        LogisticRegression(max_iter=1000, random_state=42)
    )

    # Ensure there's enough data to split and for y_train to potentially have two classes
    # A test_size of 0.2 needs at least 5 samples for train and test sets to be non-empty.
    # If len(X) is small, test_size might lead to issues.
    # E.g. if len(X) = 4, test_size=0.2 -> 0.8 for train, 0.2 for test.
    # (4*0.8=3.2 -> 3 train, 4*0.2=0.8 -> 1 test). This should be fine.
    # If len(X) = 1, it will fail. Script already checks if df.empty.
    # What if df has 2,3,4 rows?
    # 2 rows: 1 train, 1 test. y_train might have 1 class.
    # 3 rows: 2 train, 1 test. y_train might have 1 or 2 classes.
    # 4 rows: 3 train, 1 test.
    # The test data in test_train_model.py creates 4 rows, so 3 train, 1 test. y_train should be okay.

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y if len(y.unique()) > 1 else None)

    if len(y_train.unique()) < 2:
        print(f"⚠️ y_train has only {len(y_train.unique())} unique labels after splitting. LogisticRegression training may fail or be suboptimal.")
        # Optionally, handle this: e.g., don't train, or log a more severe warning.
        # For now, allow it to proceed. sklearn might handle it or warn.

    try:
        pipeline.fit(X_train, y_train)
    except ValueError as e:
        print(f"❌ Error during pipeline.fit: {e}. This might be due to too few samples or classes in y_train.")
        return # Stop if fitting fails

    # 📊 Отчёт
    # Ensure X_test is not empty before predicting
    if len(X_test) > 0:
        preds = pipeline.predict(X_test)
        print(classification_report(y_test, preds))
    else:
        print("⚠️ X_test is empty. Skipping classification report.")

    # 💾 Сохраняем модель
    model_dir = os.path.dirname(MODEL_FILE)
    if model_dir: # Ensure model_dir is not empty
        os.makedirs(model_dir, exist_ok=True)

    joblib.dump(pipeline, MODEL_FILE)
    print(f"✅ Модель сохранена в {MODEL_FILE}")

if __name__ == "__main__":
    execute_training_logic()
