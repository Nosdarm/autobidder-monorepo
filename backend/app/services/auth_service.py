from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.schemas.auth import RegisterInput, LoginInput
from app.utils.auth import (
    get_password_hash,
    verify_password,
    create_access_token,
    decode_access_token,
)
# from app.models.token_blacklist import TokenBlacklist # F401 - now unused
from app.services.email_service import send_verification_email
# ⬅️ подтверждение email


async def register_user_service(data: RegisterInput, db: AsyncSession):
    existing_result = await db.execute(select(User).where(User.email == data.email))
    existing = existing_result.scalars().first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_password = get_password_hash(data.password)
    user = User(email=data.email, hashed_password=hashed_password)
    db.add(user)
    await db.commit()
    await db.refresh(user)

    # These two lines MUST be present
    token = create_access_token({"sub": user.email})
    send_verification_email(user.email, token)

    return user # Return the user object


async def login_user_service(data: LoginInput, db: AsyncSession):
    user_result = await db.execute(select(User).where(User.email == data.email))
    user = user_result.scalars().first()
    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({"sub": user.email})  # 👈 обязательно sub!
    return {"access_token": token, "token_type": "bearer"}


async def verify_email_service(token: str, db: AsyncSession):
    try:
        payload = decode_access_token(token)
        email = payload.get("sub")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid token")

    user_result = await db.execute(select(User).where(User.email == email))
    user = user_result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_verified = True
    await db.commit()
    await db.refresh(user)
    return {"message": "Email verified"}


async def get_current_user_service(payload: dict, db: AsyncSession):
    user_result = await db.execute(select(User).where(User.email == payload.get("user_id")))
    user = user_result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


def logout_user_service(token: str):
    # blacklist = TokenBlacklist(token=token) # F841 Unused local variable
    # Assuming the intention was to add the token to a blacklist.
    # If TokenBlacklist is an ORM model, it needs a session and
    # db.add(), db.commit().
    # For now, just removing the unused variable as per task.
    # If blacklisting is actually needed, this function is incomplete.
    return {"message": "Logged out"}
