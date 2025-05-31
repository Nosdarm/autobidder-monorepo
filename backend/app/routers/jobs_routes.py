from typing import List, Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession # Changed from sqlalchemy.orm import Session

from app.database import get_db # get_db should provide AsyncSession
from app.schemas.job import Job as JobSchema, JobCreate, JobUpdate # Aliased Job to JobSchema
from app.services.job_service import JobService, get_job_service # Actual service and dependency
from app.models.user import User as UserModel # For current_user dependency
# Removed: from app.services.auth_service import get_current_active_user
from app.auth.jwt import get_current_user_with_role # New import
from app.services.auth_service import get_current_user_service # New import


router = APIRouter()

# New local dependency function for user authentication
async def get_current_user_dependency(
    payload: dict = Depends(get_current_user_with_role),
    db: AsyncSession = Depends(get_db),
) -> UserModel:
    email_from_token = payload.get("sub")
    if not email_from_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload (missing sub)",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Workaround for get_current_user_service expecting "user_id" to be an email
    service_payload = {"user_id": email_from_token}

    user = await get_current_user_service(service_payload, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # TODO: Add role checks here if necessary, e.g.
    # required_roles = ["admin", "user"] # Example
    # if payload.get("role") not in required_roles:
    #     raise HTTPException(
    #         status_code=status.HTTP_403_FORBIDDEN,
    #         detail="Operation not permitted for this user role",
    #     )
    return user


@router.post("/", response_model=JobSchema, status_code=status.HTTP_201_CREATED)
async def create_job_endpoint(
    job_in: JobCreate,
    job_service: JobService = Depends(get_job_service),
    current_user: UserModel = Depends(get_current_user_dependency) # Changed dependency
):
    """
    Create a new job.
    Requires authentication.
    """
    # The JobService.create_job method already handles HTTPException for duplicates
    return await job_service.create_job(job_in=job_in)

@router.get("/{job_id}", response_model=JobSchema)
async def read_job_endpoint(
    job_id: uuid.UUID,
    job_service: JobService = Depends(get_job_service)
):
    """
    Get a specific job by its internal ID.
    """
    job = await job_service.get_job(job_id=job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return job

@router.get("/", response_model=List[JobSchema])
async def read_jobs_endpoint(
    skip: int = 0,
    limit: int = 100,
    upwork_job_id: Optional[str] = None, # Added filter
    title_contains: Optional[str] = None, # Added filter
    job_service: JobService = Depends(get_job_service)
):
    """
    Retrieve a list of jobs with optional filters.
    Filters include `upwork_job_id` and `title_contains`.
    """
    jobs = await job_service.get_jobs(
        skip=skip,
        limit=limit,
        upwork_job_id=upwork_job_id,
        title_contains=title_contains
    )
    return jobs

@router.put("/{job_id}", response_model=JobSchema)
async def update_job_endpoint(
    job_id: uuid.UUID,
    job_in: JobUpdate,
    job_service: JobService = Depends(get_job_service),
    current_user: UserModel = Depends(get_current_user_dependency) # Changed dependency
):
    """
    Update an existing job.
    Requires authentication.
    """
    updated_job = await job_service.update_job(job_id=job_id, job_in=job_in)
    if not updated_job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return updated_job

@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_job_endpoint(
    job_id: uuid.UUID,
    job_service: JobService = Depends(get_job_service),
    current_user: UserModel = Depends(get_current_user_dependency) # Changed dependency
):
    """
    Delete a job by its internal ID.
    Requires authentication.
    """
    success = await job_service.delete_job(job_id=job_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    # No content returned for 204
