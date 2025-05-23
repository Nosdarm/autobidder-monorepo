import json
import os
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.pipeline import make_pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import joblib

PROFILES_FILE = "profiles.json"
JOBS_FILE = "jobs.json"
RESPONSES_FILE = "responses_log.json"
MODEL_FILE = "model.pkl"

# 📥 Загрузка
def load_json(path):
    if not os.path.exists(path):
        return []
    with open(path) as f:
        return json.load(f)

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
    exit()

# 🧠 Обучение модели
X = df["keywords"] + " " + df["text"]
y = df["label"]

pipeline = make_pipeline(
    CountVectorizer(),
    RandomForestClassifier(n_estimators=100, random_state=42)
)

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
pipeline.fit(X_train, y_train)

# 📊 Отчёт
preds = pipeline.predict(X_test)
print(classification_report(y_test, preds))

# 💾 Сохраняем модель
joblib.dump(pipeline, MODEL_FILE)
print(f"✅ Модель сохранена в {MODEL_FILE}")
