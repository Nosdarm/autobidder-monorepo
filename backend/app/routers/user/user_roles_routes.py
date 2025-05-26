from fastapi import APIRouter, HTTPException, Depends
# BaseModel no longer needed here directly if RoleUpdateInput is imported
import json
import os
from app.auth.jwt import require_role
# from app.models.profile import Profile # Profile import is not used
from app.schemas.user import RoleUpdateInput, UserRoleUpdateResponse
# Import schemas

router = APIRouter()
USERS_FILE = "users.json"

# Local RoleUpdateInput removed


def load_users():
    if not os.path.exists(USERS_FILE):
        return []
    with open(USERS_FILE) as f:
        return json.load(f)


def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)

# 🔐 Обновить роль пользователя (только для супер-админа)


# Add response_model
@router.post("/admin/set-role", response_model=UserRoleUpdateResponse)
def set_user_role(
    data: RoleUpdateInput,  # Use imported RoleUpdateInput
    requester=Depends(require_role("superadmin"))
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
    return UserRoleUpdateResponse(
        status="role updated",
        user_id=data.user_id,
        new_role=data.role)
