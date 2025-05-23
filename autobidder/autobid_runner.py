import os
import json

# Пути к файлам
PROFILES_FILE = "profiles.json"
JOBS_FILE = "jobs.json"

# Загрузка профилей
def load_profiles():
    if not os.path.exists(PROFILES_FILE):
        return []
    with open(PROFILES_FILE) as f:
        return json.load(f)

# Загрузка джобов
def load_jobs():
    if not os.path.exists(JOBS_FILE):
        return []
    with open(JOBS_FILE) as f:
        return json.load(f)

# Проверка соответствия джоба фильтрам
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

    return min_budget <= budget <= max_budget

# Запуск автобиддера
def run_autobid():
    profiles = load_profiles()
    jobs = load_jobs()

    for profile in profiles:
        if not profile.get("autobid_enabled"):
            continue

        filters = profile.get("filters", {})
        print(f"\n👤 Профиль: {profile['name']}")

        matched = False
        for job in jobs:
            if job_matches_filters(job, filters):
                print(f"  ✅ Совпадение: {job['title']} — ${job.get('budget', '?')}")
                matched = True

        if not matched:
            print("  ❌ Нет подходящих джобов")

# Основной запуск
if __name__ == "__main__":
    run_autobid()
