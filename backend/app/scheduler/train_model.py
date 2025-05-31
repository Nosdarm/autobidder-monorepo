import os
import sys

# Calculate the path to the 'backend' directory
# __file__ is backend/app/scheduler/train_model.py
# os.path.dirname(__file__) is backend/app/scheduler/
# os.path.dirname(os.path.dirname(__file__)) is backend/app/
# os.path.dirname(os.path.dirname(os.path.dirname(__file__))) is backend/
PROJECT_ROOT_BACKEND = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT_BACKEND not in sys.path:
    sys.path.insert(0, PROJECT_ROOT_BACKEND) # Insert at the beginning to ensure it's checked first

import json
import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.pipeline import make_pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import joblib
from app.config import settings # Added import

# Define DATA_DIR relative to PROJECT_ROOT_BACKEND
DATA_DIR = os.path.join(PROJECT_ROOT_BACKEND, "data")
PROFILES_FILE = os.path.join(DATA_DIR, "profiles.json")
JOBS_FILE = os.path.join(DATA_DIR, "jobs.json")
RESPONSES_FILE = os.path.join(DATA_DIR, "responses_log.json")
MODEL_FILE = settings.MODEL_PATH # This is already an absolute path from settings

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

    # Calculate class counts to determine if stratification is possible
    if y.empty:
        print("Error: Target variable 'y' is empty. Cannot proceed with training.")
        # This case should ideally be caught by `if df.empty:` check earlier.
        # If df is not empty but y is, it implies an issue in df construction or column naming.
        stratify_option = None
    else:
        try:
            y_counts = np.bincount(y) # Assumes y contains non-negative integers (0, 1)
            # Check if y_counts has at least two elements (for two classes)
            # and if the minimum count is less than 2 (needed for a binary split for train_test_split)
            # n_splits for StratifiedKFold (used internally by train_test_split for stratification) must be <= n_samples in each class.
            # Since test_size=0.2 implies a 5-fold split conceptually for the smaller set,
            # the smallest class must have at least 2 samples to allow 1 for test, 1 for train if split is 50/50.
            # More generally, if test_size = 0.2 (meaning 1/5th goes to test), then smallest class needs at least 2 members
            # for stratified split to be meaningful (one for test, one for train).
            # If smallest class has k members, test set gets ceil(0.2*k) and train gets floor(0.8*k) or vice-versa.
            # For stratification to work, each class must have at least n_splits members, where n_splits is
            # related to test_size (e.g., for test_size=0.2, n_splits is effectively 5).
            # A simpler check: if smallest class < 2, stratification is problematic for typical splits.
            if len(y_counts) < 2 or y_counts.min() < 2:
                min_class_count_val = y_counts.min() if len(y_counts) > 0 else 0
                print(f"Warning: The least populated class in y has only {min_class_count_val} member(s) (or y does not have at least two classes). Stratification will be disabled to prevent errors.")
                stratify_option = None
            else:
                stratify_option = y
        except Exception as e: # Catch potential errors with y that bincount might not like (e.g. non-integer, negative)
            print(f"Warning: Could not determine class counts for stratification due to: {e}. Stratification will be disabled.")
            stratify_option = None

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=stratify_option)

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
