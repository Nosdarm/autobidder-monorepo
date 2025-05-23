import json
import os

PROFILES_FILE = "profiles.json"

def load_profiles():
    if not os.path.exists(PROFILES_FILE):
        return []
    with open(PROFILES_FILE) as f:
        return json.load(f)

# 🔍 Проверка соответствия одного джоба фильтрам
def job_matches_filters(job, filters):
    title = job["title"].lower()
    desc = job["description"].lower()
    combined = title + " " + desc
    budget = job.get("budget", 0)

    includes = [kw.lower() for kw in filters.get("include_keywords", [])]
    excludes = [kw.lower() for kw in filters.get("exclude_keywords", [])]
    min_budget = filters.get("min_budget", 0)
    max_budget = filters.get("max_budget", float("inf"))

    if includes and not any(kw in combined for kw in includes):
        return False
    if excludes and any(kw in combined for kw in excludes):
        return False
    if budget < min_budget or budget > max_budget:
        return False

    return True

# 🧠 Запуск автобида
def run_autobid():
    job = {
        "title": "Figma dashboard for SaaS product",
        "description": "Looking for a UI/UX designer familiar with dashboards and Figma.",
        "budget": 300
    }

    profiles = load_profiles()
    for profile in profiles:
        if not profile.get("autobid_enabled"):
            print(f"⏭️  [{profile['name']}] Autobid выключен.")
            continue

        filters = profile.get("filters", {})
        print(f"\n🔍 Проверка профиля: {profile['name']}")
        print(f"   ➤ Фильтры: {filters}")
        if job_matches_filters(job, filters):
            print(f"✅ Подходит! Будем отправлять отклик.")
        else:
            print(f"❌ Не подходит. Пропускаем.")

# 💡 Для отладки
if __name__ == "__main__":
    run_autobid()
