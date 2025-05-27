# app/services/template_service.py
import os
import json
from fastapi import HTTPException # APIRouter removed

TEMPLATE_DIR = "user_templates"
os.makedirs(TEMPLATE_DIR, exist_ok=True)
# router = APIRouter(prefix="/templates", tags=["Templates"]) # Router definition removed

# 📝 Путь к шаблону


def get_template_path(user_id: str):
    return os.path.join(TEMPLATE_DIR, f"{user_id}.json")

# ✅ Получить шаблон и промт


def get_user_template(user_id: str):
    path = get_template_path(user_id)
    if not os.path.exists(path):
        return {
            "prompt": (
                "Ты опытный специалист. Напиши отклик на вакансию "
                "профессионально."
            ),
            "template": (
                "Здравствуйте! Я увидел вашу задачу: {title}. У меня есть "
                "соответствующий опыт и я хотел бы обсудить детали."
            )
        }
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

# 💾 Обновить шаблон и промт


def update_user_template(user_id: str, data: dict):
    path = get_template_path(user_id)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return {"status": "updated"}

# 🔗 API-роуты (These should be in a router file, not the service file)
# @router.get("/{user_id}")
# def api_get_template(user_id: str):
#     return get_user_template(user_id)

# @router.post("/{user_id}")
# def api_update_template(user_id: str, data: dict):
#     if "prompt" not in data or "template" not in data:
#         raise HTTPException(status_code=400,
#                             detail="Missing 'prompt' or 'template'")
#     return update_user_template(user_id, data)
