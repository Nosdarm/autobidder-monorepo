import pandas as pd
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import os
import json

RESPONSES_FILE = "responses_log.json"
MODEL_PATH = "model.pkl"
METRICS_FILE = "model_metrics.json"

def retrain_model():
    if not os.path.exists(RESPONSES_FILE):
        print("⚠️ Нет данных для обучения.")
        return

    df = pd.read_json(RESPONSES_FILE)

    if len(df) < 5:
        print("⚠️ Недостаточно данных для переобучения модели.")
        return

    # Преобразуем
    X = df[["job_length", "has_figma", "budget"]]
    y = df["applied"]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

    model = RandomForestClassifier()
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    report = classification_report(y_test, y_pred, output_dict=True)
    with open(METRICS_FILE, "w") as f:
        json.dump(report["weighted avg"], f, indent=2)

    joblib.dump(model, MODEL_PATH)
    print("✅ Модель переобучена и сохранена.")

if __name__ == "__main__":
    retrain_model()
