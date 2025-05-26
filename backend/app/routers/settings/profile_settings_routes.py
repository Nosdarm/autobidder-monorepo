from fastapi import APIRouter
from app.schemas.auth import MessageResponse  # Import MessageResponse

router = APIRouter()


# Add response_model
@router.get("/profiles/test", response_model=MessageResponse)
def test_profile_settings():
    return {"message": "Profile settings API is working"}
