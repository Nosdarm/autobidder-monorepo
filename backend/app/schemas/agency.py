from pydantic import BaseModel, EmailStr
from app.models.agency import AgencyRole  # Import the Enum
from app.schemas.user import UserOut  # For nesting user details


class AgencyProfileCreate(BaseModel):
    name: str
    autobid_enabled: bool = False


# Schemas for AgencyMember operations

class AgencyMemberInviteSchema(BaseModel):
    """Schema for inviting a user to an agency by email."""
    email: EmailStr
    role: AgencyRole = AgencyRole.MEMBER  # Default role for new invites


class AgencyMemberRoleUpdateSchema(BaseModel):
    """Schema for updating an agency member's role."""
    role: AgencyRole


class AgencyMemberResponseSchema(BaseModel):
    """Schema for returning agency member details."""
    id: int  # ID of the agency_member entry in the table
    agency_id: int  # User ID of the agency owner
    user_id: int  # User ID of the member
    role: AgencyRole
    user: UserOut  # Detailed information of the member user

    model_config = {"from_attributes": True}
