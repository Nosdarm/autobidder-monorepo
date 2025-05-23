from fastapi import APIRouter, HTTPException, Depends, Path, Body
# EmailStr removed as it's not directly used here
from uuid import uuid4
import json
import os
from typing import List  # Import List

from app.auth.jwt import get_current_user
# verify_password is not used in this file
from app.utils.security import hash_password
from app.schemas.auth import RegisterInput, MessageResponse  # Import common schemas
from app.schemas.user import UserResponse, UserRegisterResponse
# Import user specific schemas

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

# Local RegisterInput removed, will use app.schemas.auth.RegisterInput


# Add response_model
@router.post("/register", response_model=UserRegisterResponse)
def register_user(data: RegisterInput = Body(...)):  # Use imported RegisterInput
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

    return UserRegisterResponse(
        message="User registered",
        id=new_user["id"]
    )


@router.get("/users", response_model=List[UserResponse])  # Add response_model
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
        raise HTTPException(
            status_code=400,
            detail="You can't delete yourself")

    filtered_users = [u for u in users if u["id"] != target_user_id]

    if len(filtered_users) == len(users):
        raise HTTPException(status_code=404, detail="User not found")

    save_users(filtered_users)
    return MessageResponse(message="User deleted")


@router.get("/me", response_model=UserResponse)  # Add response_model
def get_me(user_id: str = Depends(get_current_user)):
    users = load_users()
    user = next((u for u in users if u["id"] == user_id), None)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # FastAPI will automatically convert the parts of the user dict
    # that match UserResponse fields.
    return user

# ====================== ❌ Работа с профилями (удаление) ======================


@router.delete("/profiles/{profile_id}",
               response_model=MessageResponse)  # Add response_model
def delete_profile(
    profile_id: str = Path(...),
    user_id: str = Depends(get_current_user)
):
    profiles = load_profiles()
    updated_profiles = [p for p in profiles if not (
        p["id"] == profile_id and p["owner_id"] == user_id)]

    if len(updated_profiles) == len(profiles):
        raise HTTPException(status_code=404,
                            detail="Profile not found or not yours")

    save_profiles(updated_profiles)
    return MessageResponse(message="Profile deleted")
