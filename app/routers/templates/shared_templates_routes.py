from fastapi import APIRouter, HTTPException, Request, Depends, Body
from pydantic import BaseModel
from typing import List, Dict
import os
import json
from app.auth.jwt import get_current_user



router = APIRouter()
TEMPLATES_FILE = "shared_templates.json"

# 🔸 Pydantic-модель
class Template(BaseModel):
    name: str
    value: Dict
    owner_id: str

# 📄 Получение всех шаблонов
@router.get("/shared-templates")
def list_templates(request: Request, user_id: str = Depends(get_current_user)):
    role = request.headers.get("x-user-role", "user")

    if not os.path.exists(TEMPLATES_FILE):
        return []

    with open(TEMPLATES_FILE) as f:
        all_templates = json.load(f)

    if role == "superadmin":
        return all_templates
    else:
        return [t for t in all_templates if t.get("owner_id") == user_id]

# 💾 Сохранение шаблона
@router.post("/templates")
def save_template(template: Template, user_id: str = Depends(get_current_user)):
    if not os.path.exists(TEMPLATES_FILE):
        all_templates = []
    else:
        with open(TEMPLATES_FILE) as f:
            all_templates = json.load(f)

    # Принудительно указываем владельца
    template_dict = template.dict()
    template_dict["owner_id"] = user_id

    # Удалим предыдущий с таким же именем
    all_templates = [t for t in all_templates if t["name"] != template.name or t["owner_id"] != user_id]
    all_templates.append(template_dict)

    with open(TEMPLATES_FILE, "w") as f:
        json.dump(all_templates, f, indent=2)

    return {"status": "saved"}

# ♻️ Обновление шаблона
@router.patch("/templates/{name}")
def update_template(name: str, updated_value: Dict = Body(...), user_id: str = Depends(get_current_user)):
    if not os.path.exists(TEMPLATES_FILE):
        raise HTTPException(status_code=404, detail="No templates found")

    with open(TEMPLATES_FILE) as f:
        all_templates = json.load(f)

    found = False
    for template in all_templates:
        if template["name"] == name and template["owner_id"] == user_id:
            template["value"] = updated_value
            found = True
            break

    if not found:
        raise HTTPException(status_code=404, detail="Template not found or not yours")

    with open(TEMPLATES_FILE, "w") as f:
        json.dump(all_templates, f, indent=2)

    return {"status": "updated"}

# ❌ Удаление шаблона
@router.delete("/templates/{name}")
def delete_template(name: str, user_id: str = Depends(get_current_user), request: Request = None):
    role = request.headers.get("x-user-role", "user")

    if role != "admin" and role != "superadmin":
        raise HTTPException(status_code=403, detail="Only admins can delete templates")

    if not os.path.exists(TEMPLATES_FILE):
        raise HTTPException(status_code=404, detail="No templates found")

    with open(TEMPLATES_FILE) as f:
        all_templates = json.load(f)

    filtered = [t for t in all_templates if t["name"] != name or t["owner_id"] != user_id]

    if len(filtered) == len(all_templates):
        raise HTTPException(status_code=404, detail="Template not found")

    with open(TEMPLATES_FILE, "w") as f:
        json.dump(filtered, f, indent=2)

    return {"status": "deleted"}
