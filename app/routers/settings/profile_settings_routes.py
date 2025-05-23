from fastapi import APIRouter

router = APIRouter()

@router.get("/profiles/test")
def test_profile_settings():
    return {"message": "Profile settings API is working"}
