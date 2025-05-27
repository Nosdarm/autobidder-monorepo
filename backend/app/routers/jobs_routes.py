from typing import List, Any
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.job import Job, JobCreate, JobUpdate
# Placeholder for JobService - replace with actual service and dependency
# from app.services.job_service import JobService, get_job_service 

router = APIRouter()

# Placeholder for service dependency
# For now, operations will be direct or raise NotImplementedError

# @router.post("/", response_model=Job, status_code=status.HTTP_201_CREATED)
# async def create_job(
#     job_in: JobCreate, 
#     # job_service: JobService = Depends(get_job_service), # Uncomment when service is available
#     db: Session = Depends(get_db) # Keep db for now if service is not ready
# ):
#     """
#     Create a new job.
#     """
#     # return await job_service.create_job(db=db, job_in=job_in) # Uncomment when service is available
#     raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Job service not implemented")

@router.get("/{job_id}", response_model=Job)
async def read_job(
    job_id: uuid.UUID,
    # job_service: JobService = Depends(get_job_service), # Uncomment when service is available
    db: Session = Depends(get_db) # Keep db for now
):
    """
    Get a specific job by ID.
    """
    # job = await job_service.get_job(db=db, job_id=job_id) # Uncomment when service is available
    # if not job:
    #     raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    # return job
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Job service not implemented")

@router.get("/", response_model=List[Job])
async def read_jobs(
    skip: int = 0,
    limit: int = 100,
    # job_service: JobService = Depends(get_job_service), # Uncomment when service is available
    db: Session = Depends(get_db) # Keep db for now
):
    """
    Retrieve jobs.
    """
    # jobs = await job_service.get_jobs(db=db, skip=skip, limit=limit) # Uncomment when service is available
    # return jobs
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Job service not implemented")

# @router.put("/{job_id}", response_model=Job)
# async def update_job(
#     job_id: uuid.UUID,
#     job_in: JobUpdate,
#     # job_service: JobService = Depends(get_job_service), # Uncomment when service is available
#     db: Session = Depends(get_db) # Keep db for now
# ):
#     """
#     Update a job.
#     """
#     # updated_job = await job_service.update_job(db=db, job_id=job_id, job_in=job_in) # Uncomment when service is available
#     # if not updated_job:
#     #     raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
#     # return updated_job
#     raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Job service not implemented")

# @router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
# async def delete_job(
#     job_id: uuid.UUID,
#     # job_service: JobService = Depends(get_job_service), # Uncomment when service is available
#     db: Session = Depends(get_db) # Keep db for now
# ):
#     """
#     Delete a job.
#     """
#     # success = await job_service.delete_job(db=db, job_id=job_id) # Uncomment when service is available
#     # if not success:
#     #     raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
#     # return
#     raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Job service not implemented")

# Note: POST, PUT, DELETE endpoints are commented out as they typically require more complex service logic
# and are often the source of merge conflicts if not handled carefully during consolidation.
# For now, focusing on GET endpoints and placeholder structure.
