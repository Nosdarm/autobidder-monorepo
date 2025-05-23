import json
import os
import uuid
from datetime import datetime, timezone
import pickle

PROFILES_FILE = "profiles.json"
JOBS_FILE = "jobs.json"
RESPONSES_FILE = "responses_log.json"
SENT_BIDS_FILE = "sent_bids.json"
FEATURES_FILE = "features_log.json"
MODEL_PATH = "model.pkl"

# 📁 Загрузка данных
def load_profiles():
    if not os.path.exists(PROFILES_FILE):
        return []
    with open(PROFILES_FILE) as f:
        return json.load(f)

def load_jobs():
    if not os.path.exists(JOBS_FILE):
        return []
    with open(JOBS_FILE) as f:
        return json.load(f)

def load_responses():
    if not os.path.exists(RESPONSES_FILE):
        return []
    with open(RESPONSES_FILE) as f:
        return json.load(f)

def load_sent_bids():
    if not os.path.exists(SENT_BIDS_FILE):
        return []
    with open(SENT_BIDS_FILE) as f:
        return json.load(f)

# 💾 Сохранение данных
def save_response(profile_id, job_id):
    responses = load_responses()
    responses.append({"profile_id": profile_id, "job_id": job_id})
    with open(RESPONSES_FILE, "w") as f:
        json.dump(responses, f, indent=2)

def save_sent_bid(profile_id, job_id, bid_text):
    sent_bids = load_sent_bids()
    sent_bids.append({
        "profile_id": profile_id,
        "job_id": job_id,
        "bid_text": bid_text
    })
    with open(SENT_BIDS_FILE, "w") as f:
        json.dump(sent_bids, f, indent=2)

def save_feature_data(feature_row):
    if not os.path.exists(FEATURES_FILE):
        all_data = []
    else:
        with open(FEATURES_FILE) as f:
            all_data = json.load(f)

    all_data.append(feature_row)
    with open(FEATURES_FILE, "w") as f:
        json.dump(all_data, f, indent=2)

# 📌 Проверка
def has_already_applied(profile_id, job_id):
    responses = load_responses()
    return any(r["profile_id"] == profile_id and r["job_id"] == job_id for r in responses)

# 🧠 Логика фильтрации
def job_matches_filters(job, filters):
    title = job["title"].lower()
    desc = job["description"].lower()
    combined = title + " " + desc
    budget = job.get("budget", 0)

    includes = [kw.lower() for kw in filters.get("include_keywords", [])]
    excludes = [kw.lower() for kw in filters.get("exclude_keywords", [])]

    if includes and not any(kw in combined for kw in includes):
        return False
    if excludes and any(kw in combined for kw in excludes):
        return False

    min_budget = filters.get("min_budget", 0)
    max_budget = filters.get("max_budget", float("inf"))

    if budget < min_budget or budget > max_budget:
        return False

    return True

# 🧠 Извлечение фичей
def extract_features(profile, job):
    title = job.get("title", "").lower()
    desc = job.get("description", "").lower()
    text = title + " " + desc
    budget = job.get("budget", 0)

    include_kw = profile.get("filters", {}).get("include_keywords", [])
    exclude_kw = profile.get("filters", {}).get("exclude_keywords", [])

    features = {
        "profile_id": profile["id"],
        "job_id": job["id"],
        "job_length": len(text),
        "has_figma": int("figma" in text),
        "has_wordpress": int("wordpress" in text),
        "has_dashboard": int("dashboard" in text),
        "budget": budget,
        "num_keywords_matched": sum(1 for kw in include_kw if kw.lower() in text),
        "num_keywords_blocked": sum(1 for kw in exclude_kw if kw.lower() in text),
        "include_kw_count": len(include_kw),
        "exclude_kw_count": len(exclude_kw),
        "job_created_hour": int(job.get("created_at", "")[11:13]) if "created_at" in job else 0,
        "profile_type": 1 if profile.get("type") == "agency" else 0,
        "applied": 1
    }
    return features

# 📝 Генерация текста отклика
def generate_bid_text(profile, job):
    return f"""Hi! I'm {profile['name']} and I specialize in {', '.join(profile.get('filters', {}).get('include_keywords', []))}.
I’ve reviewed your project: "{job['title']}" and would love to help. Let's discuss more details!
"""

# 📦 Моковые джобы
def fetch_mock_jobs():
    return [
        {
            "id": str(uuid.uuid4()),
            "title": "Figma dashboard for SaaS product",
            "description": "Looking for a UI/UX designer familiar with dashboards and Figma.",
            "budget": 300,
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": str(uuid.uuid4()),
            "title": "Logo for fashion brand",
            "description": "Need a stylish logo for a new clothing line.",
            "budget": 50,
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": str(uuid.uuid4()),
            "title": "WordPress site redesign",
            "description": "Redesign a WordPress site with Elementor.",
            "budget": 150,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
    ]

def save_jobs(jobs):
    with open(JOBS_FILE, "w") as f:
        json.dump(jobs, f, indent=2)

def auto_fetch_jobs():
    jobs = fetch_mock_jobs()
    save_jobs(jobs)
    print(f"📥 Обновлено {len(jobs)} джобов")

# 📊 Предсказание с использованием модели
def load_model():
    if not os.path.exists(MODEL_PATH):
        return None
    with open(MODEL_PATH, "rb") as f:
        return pickle.load(f)

def predict_score(job):
    model = load_model()
    if not model:
        return 1.0  # если модель не обучена — всегда подавать
    job_text = job["title"] + " " + job["description"]
    return model.predict_proba([job_text])[0][1]

# 🚀 Основной запуск
def run_autobid():
    auto_fetch_jobs()

    profiles = load_profiles()
    jobs = load_jobs()

    for profile in profiles:
        if not profile.get("autobid_enabled"):
            continue

        print(f"\n👤 Профиль: {profile['name']}")
        filters = profile.get("filters", {})

        matched = False
        for job in jobs:
            job_id = job.get("id")
            if has_already_applied(profile["id"], job_id):
                print(f"  🔁 Уже отправлено: {job['title']}")
                continue

            score = predict_score(job)
            if score < 0.5:
                print(f"  ⚪ Пропущено (score={score:.2f}): {job['title']}")
                continue

            if job_matches_filters(job, filters):
                bid_text = generate_bid_text(profile, job)
                print(f"  ✅ Отклик отправлен: {job['title']} (${job.get('budget', 0)})")
                print(f"     📤 Текст отклика:\n{bid_text.strip()}")

                save_response(profile["id"], job_id)
                save_sent_bid(profile["id"], job_id, bid_text)
                features = extract_features(profile, job)
                save_feature_data(features)

                matched = True
            else:
                print(f"  ❌ Не подходит: {job['title']}")

        if not matched:
            print("  ⚠️ Нет новых подходящих проектов")

# 🔧 Запуск вручную
if __name__ == "__main__":
    run_autobid()
