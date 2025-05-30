import enum
from sqlalchemy import Column, Integer, String, ForeignKey, Enum, UniqueConstraint
from sqlalchemy.orm import relationship
from app.db.base import Base
from app.models.user import User # Assuming User model is in app.models.user


class AgencyRole(enum.Enum):
    SUPER_ADMIN = "super_admin"  # Typically the agency creator
    ADMIN = "admin"          # Can manage members, settings
    MEMBER = "member"        # Standard member


class AgencyMember(Base):
    __tablename__ = "agency_members"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # This ForeignKey points to the User who OWNS the agency (i.e., User with account_type="agency")
    agency_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # This ForeignKey points to the User who IS a MEMBER of the agency
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    role = Column(Enum(AgencyRole), nullable=False, default=AgencyRole.MEMBER)

    # Relationships
    # 'agency' relationship links to the User record representing the agency itself
    # back_populates removed as User model isn't updated yet.
    agency = relationship("User", foreign_keys=[agency_id])
    
    # 'user' relationship (renamed from 'member') links to the User record of the agency member.
    # back_populates removed as User model isn't updated yet.
    # This relationship is now named 'user' to align with AgencyMemberResponseSchema.
    user = relationship("User", foreign_keys=[user_id])

    # Constraints
    __table_args__ = (
        UniqueConstraint('agency_id', 'user_id', name='uq_agency_user_membership'),
    )

    def __repr__(self):
        return f"<AgencyMember(agency_id={self.agency_id}, user_id={self.user_id}, role='{self.role.value}')>"