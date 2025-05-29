from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List

from app.database import get_db
from app.models.user import User, AccountType as UserAccountTypeEnum
from app.models.agency import AgencyMember, AgencyRole
from app.schemas.agency import (
    AgencyMemberInviteSchema,
    AgencyMemberRoleUpdateSchema,
    AgencyMemberResponseSchema,
)
from app.auth.jwt import get_current_user_with_role

router = APIRouter(prefix="/agency", tags=["Agency Management"])

# Dependency for super_admin access
async def get_current_active_agency_super_admin(
    token_payload: dict = Depends(get_current_user_with_role),
    db: AsyncSession = Depends(get_db)
) -> User:
    user_email = token_payload.get("user_id") # This is the email from token's 'sub'
    jwt_role = token_payload.get("role")
    # Ensure jwt_account_type is correctly handled if it's an Enum from token or string
    jwt_account_type_value = token_payload.get("account_type")
    
    # Convert string from token to Enum if necessary for comparison
    # Assuming AccountType enum values are strings like "individual", "agency"
    try:
        # If jwt_account_type_value is already an Enum, this direct comparison works.
        # If it's a string from JWT, it should have been converted to Enum in get_current_user_with_role.
        # For robustness, handle if it's still a string here.
        if isinstance(jwt_account_type_value, str):
            jwt_account_type = UserAccountTypeEnum(jwt_account_type_value)
        elif isinstance(jwt_account_type_value, UserAccountTypeEnum):
            jwt_account_type = jwt_account_type_value
        else: # Handle unexpected type
            jwt_account_type = None
    except ValueError: # Handle if string is not a valid UserAccountTypeEnum member
        jwt_account_type = None

    if not (jwt_account_type == UserAccountTypeEnum.AGENCY and jwt_role == "super_admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not an agency super_admin based on token claims."
        )

    result = await db.execute(select(User).where(User.email == user_email))
    agency_owner_user = result.scalars().first()

    if not agency_owner_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Agency super_admin user not found in DB.")
    
    if not (agency_owner_user.account_type == UserAccountTypeEnum.AGENCY and agency_owner_user.role == "super_admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User's current DB status does not confirm agency super_admin role."
        )
    return agency_owner_user

@router.post("/members/invite", response_model=AgencyMemberResponseSchema, status_code=status.HTTP_201_CREATED)
async def invite_agency_member(
    invite_data: AgencyMemberInviteSchema,
    agency_owner: User = Depends(get_current_active_agency_super_admin),
    db: AsyncSession = Depends(get_db)
):
    user_to_invite_result = await db.execute(select(User).where(User.email == invite_data.email))
    user_to_invite = user_to_invite_result.scalars().first()

    if not user_to_invite:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User to invite not found.")

    if user_to_invite.id == agency_owner.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Agency owner cannot invite themselves as a member.")

    existing_member_result = await db.execute(
        select(AgencyMember).where(AgencyMember.agency_id == agency_owner.id, AgencyMember.user_id == user_to_invite.id)
    )
    if existing_member_result.scalars().first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User is already a member of this agency.")

    new_member = AgencyMember(
        agency_id=agency_owner.id,
        user_id=user_to_invite.id,
        role=invite_data.role
    )
    db.add(new_member)
    await db.commit()
    
    # Retrieve the newly created member with the 'user' relationship loaded for the response
    # new_member.id will be populated after the commit.
    populated_member = await db.get(AgencyMember, new_member.id, options=[selectinload(AgencyMember.user)])
    if not populated_member:
         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve new member after creation.")
    return populated_member

@router.get("/members", response_model=List[AgencyMemberResponseSchema])
async def list_agency_members(
    agency_owner: User = Depends(get_current_active_agency_super_admin),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(AgencyMember)
        .where(AgencyMember.agency_id == agency_owner.id)
        .options(selectinload(AgencyMember.user)) # Eager load the 'user' relationship
    )
    members = result.scalars().all()
    return members

@router.delete("/members/{member_user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_agency_member(
    member_user_id: int,
    agency_owner: User = Depends(get_current_active_agency_super_admin),
    db: AsyncSession = Depends(get_db)
):
    if member_user_id == agency_owner.id:
         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Agency owner cannot remove themselves.")

    result = await db.execute(
        select(AgencyMember).where(AgencyMember.agency_id == agency_owner.id, AgencyMember.user_id == member_user_id)
    )
    member_to_delete = result.scalars().first()

    if not member_to_delete:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found in this agency.")
    
    await db.delete(member_to_delete)
    await db.commit()
    return None # For HTTP 204

@router.put("/members/{member_user_id}/role", response_model=AgencyMemberResponseSchema)
async def update_agency_member_role(
    member_user_id: int,
    role_update_data: AgencyMemberRoleUpdateSchema,
    agency_owner: User = Depends(get_current_active_agency_super_admin),
    db: AsyncSession = Depends(get_db)
):
    if member_user_id == agency_owner.id:
         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Agency owner's role cannot be changed via this endpoint.")

    if role_update_data.role == AgencyRole.SUPER_ADMIN: # Prevent assigning super_admin role
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot assign super_admin role to a member.")

    result = await db.execute(
        select(AgencyMember)
        .where(AgencyMember.agency_id == agency_owner.id, AgencyMember.user_id == member_user_id)
        # .options(selectinload(AgencyMember.user)) # Load for update if needed, but get will reload
    )
    member_to_update = result.scalars().first()

    if not member_to_update:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found in this agency.")

    member_to_update.role = role_update_data.role
    await db.commit()
    # await db.refresh(member_to_update, attribute_names=['role']) # Refresh specific attributes if needed

    # Retrieve the updated member with the 'user' relationship loaded for the response
    populated_member = await db.get(AgencyMember, member_to_update.id, options=[selectinload(AgencyMember.user)])
    if not populated_member:
         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve member after role update.")
    return populated_member

# Note: The `get_current_user_with_role` dependency in `app.auth.jwt` was updated in a previous step
# to return `account_type` as an `AccountType` enum object if possible, or None.
# The `get_current_active_agency_super_admin` dependency here handles potential string values
# from the token for `account_type` and converts to Enum for reliable comparison.
# This makes the dependency robust.
