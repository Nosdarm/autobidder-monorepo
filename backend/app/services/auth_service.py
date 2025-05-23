from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.auth import RegisterInput, LoginInput
from app.utils.auth import (
    get_password_hash,
    verify_password,
    create_access_token,
    decode_access_token,
)
from app.models.token_blacklist import TokenBlacklist
from app.services.email_service import send_verification_email  # ⬅️ подтверждение email


async def register_user_service(data: RegisterInput, db: Session):
    existing = db.query(User).filter(User.email == data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_password = get_password_hash(data.password)
    user = User(email=data.email, hashed_password=hashed_password)
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token({"sub": user.email})
    send_verification_email(user.email, token)

    return {"message": "Registration successful. Please check your email."}


def login_user_service(data: LoginInput, db: Session):
    user = db.query(User).filter(User.email == data.email).first()
    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({"sub": user.email})  # 👈 обязательно sub!
    return {"access_token": token, "token_type": "bearer"}


def verify_email_service(token: str, db: Session):
    try:
        payload = decode_access_token(token)
        email = payload.get("sub")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid token")

    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_verified = True
    db.commit()
    db.refresh(user)
    return {"message": "Email verified"}


def get_current_user_service(payload: dict, db: Session):
    email = payload.get("user_id")  # ← ключ!
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user



def logout_user_service(token: str):
    blacklist = TokenBlacklist(token=token)
    return {"message": "Logged out"}
