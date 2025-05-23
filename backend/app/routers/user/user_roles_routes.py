from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import json
import os
from app.auth.jwt import require_role
from app.models.profile import Profile

router = APIRouter()
USERS_FILE = "users.json"

class RoleUpdateInput(BaseModel):
    user_id: str
    role: str

def load_users():
    if not os.path.exists(USERS_FILE):
        return []
    with open(USERS_FILE) as f:
        return json.load(f)

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)

# 🔐 Обновить роль пользователя (только для супер-админа)
@router.post("/admin/set-role")
def set_user_role(
    data: RoleUpdateInput,
    requester = Depends(require_role("superadmin"))
):
    users = load_users()
    found = False
    for u in users:
        if u["id"] == data.user_id:
            u["role"] = data.role
            found = True
            break

    if not found:
        raise HTTPException(status_code=404, detail="User not found")

    save_users(users)
    return {"status": "role updated", "user_id": data.user_id, "new_role": data.role}
