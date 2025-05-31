from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, AccountType # Import AccountType
from app.schemas.auth import RegisterInput, LoginInput
from app.schemas.user import UserOut # Added import
from app.models.profile import Profile
from app.schemas.profile import ProfileCreate # Corrected import path
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
    user_data = {
        "email": data.email,
        "hashed_password": hashed_password,
        "account_type": data.account_type
    }
    if data.account_type == AccountType.AGENCY:
        user_data["role"] = "super_admin"
    # If not AGENCY, the role will use the default "user" from the User model

    user = User(**user_data)
    db.add(user)
    await db.commit()
    await db.refresh(user)

    # Create a default profile
    profile_data = ProfileCreate(
        user_id=user.id,
        name="Default Profile",
        profile_type="personal", # Changed from "general" to "personal"
        skills=[],
        experience_level=None
    )
    profile = Profile(**profile_data.model_dump())
    db.add(profile)
    await db.commit()
    # await db.refresh(profile) # Optional: if you need to use the refreshed profile object

    # These two lines MUST be present
    token = create_access_token({"sub": user.email})
    send_verification_email(user.email, token)

    return user # Return the user object


async def login_user_service(data: LoginInput, db: AsyncSession):
    print(f"Login attempt for email: {data.email}") # Log 1

    user_result = await db.execute(select(User).where(User.email == data.email))
    user = user_result.scalars().first()

    if not user:
        print(f"Login failed: User not found for email: {data.email}") # Log 2 (failure case)
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    print(f"Login attempt: User found for email: {data.email}") # Log 2 (success case)
    print(f"Login attempt: Stored hashed password: {user.hashed_password}") # Log 3

    password_matches = verify_password(data.password, user.hashed_password)
    print(f"Login attempt: Password verification result for {data.email}: {password_matches}") # Log 4

    if not password_matches:
        print(f"Login failed: Password mismatch for email: {data.email}")
        raise HTTPException(status_code=401, detail="Invalid credentials")

    print(f"Login successful for email: {data.email}")
    token_data = {
        "sub": user.email,
        "role": user.role,
        "account_type": user.account_type.value  # Use .value for Enum serialization
    }
    token = create_access_token(token_data)
    
    # Explicitly create UserOut instance from the ORM user model
    # Assuming Pydantic v2+ usage with model_validate.
    # If Pydantic v1, it would be UserOut.from_orm(user).
    user_out_instance = UserOut.model_validate(user) 
    
    print(f"Login service: UserOut instance created: {user_out_instance.model_dump_json()}") # Add this log

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": user_out_instance, # Pass the Pydantic model instance
        "role": user.role,  # Add role to the response
        "account_type": user.account_type  # Add account_type to the response (Pydantic handles Enum)
    }


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
