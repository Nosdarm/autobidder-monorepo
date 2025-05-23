import json
import uuid
from datetime import datetime, timezone

JOBS_FILE = "jobs.json"

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

def main():
    jobs = fetch_mock_jobs()
    save_jobs(jobs)
    print(f"✅ Загружено {len(jobs)} новых проектов")

if __name__ == "__main__":
    main()
