from fastapi import APIRouter, HTTPException, Depends, Path, Body
from pydantic import BaseModel, EmailStr
from uuid import uuid4
import json
import os

from app.auth.jwt import get_current_user
from app.utils.security import hash_password, verify_password

router = APIRouter()

USERS_FILE = "users.json"
PROFILES_FILE = "profiles.json"

# ====================== 🔧 Работа с файлами ======================

def load_users():
    if not os.path.exists(USERS_FILE):
        return []
    with open(USERS_FILE) as f:
        return json.load(f)

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)

def load_profiles():
    if not os.path.exists(PROFILES_FILE):
        return []
    with open(PROFILES_FILE) as f:
        return json.load(f)

def save_profiles(profiles):
    with open(PROFILES_FILE, "w") as f:
        json.dump(profiles, f, indent=2)

# ====================== 👤 Работа с пользователями ======================

class RegisterInput(BaseModel):
    email: EmailStr
    password: str

@router.post("/register")
def register_user(data: RegisterInput = Body(...)):
    users = load_users()

    if any(u["email"] == data.email for u in users):
        raise HTTPException(status_code=400, detail="Email already registered")

    new_user = {
        "id": str(uuid4()),
        "email": data.email,
        "hashed_password": hash_password(data.password),
        "role": "user"
    }

    users.append(new_user)
    save_users(users)

    return {"message": "User registered", "id": new_user["id"]}

@router.get("/users")
def list_users(user_id: str = Depends(get_current_user)):
    users = load_users()
    current_user = next((u for u in users if u["id"] == user_id), None)

    if not current_user or current_user["role"] != "superadmin":
        raise HTTPException(status_code=403, detail="Access denied")

    return users

@router.delete("/users/{target_user_id}")
def delete_user(target_user_id: str, user_id: str = Depends(get_current_user)):
    users = load_users()
    current_user = next((u for u in users if u["id"] == user_id), None)

    if not current_user or current_user["role"] != "superadmin":
        raise HTTPException(status_code=403, detail="Access denied")

    if target_user_id == user_id:
        raise HTTPException(status_code=400, detail="You can't delete yourself")

    filtered_users = [u for u in users if u["id"] != target_user_id]

    if len(filtered_users) == len(users):
        raise HTTPException(status_code=404, detail="User not found")

    save_users(filtered_users)
    return {"message": "User deleted"}

@router.get("/me")
def get_me(user_id: str = Depends(get_current_user)):
    users = load_users()
    user = next((u for u in users if u["id"] == user_id), None)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "id": user["id"],
        "email": user["email"],
        "role": user["role"]
    }

# ====================== ❌ Работа с профилями (удаление) ======================

@router.delete("/profiles/{profile_id}")
def delete_profile(
    profile_id: str = Path(...),
    user_id: str = Depends(get_current_user)
):
    profiles = load_profiles()
    updated_profiles = [p for p in profiles if not (p["id"] == profile_id and p["owner_id"] == user_id)]

    if len(updated_profiles) == len(profiles):
        raise HTTPException(status_code=404, detail="Profile not found or not yours")

    save_profiles(updated_profiles)
    return {"message": "Profile deleted"}
