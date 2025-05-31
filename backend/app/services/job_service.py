import uuid
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException, status

from app.models.job import Job
from app.schemas.job import JobCreate, JobUpdate

class JobService:
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def create_job(self, job_in: JobCreate) -> Job:
        if job_in.upwork_job_id:
            # Check for duplicates based on upwork_job_id
            existing_job_result = await self.db_session.execute(
                select(Job).filter(Job.upwork_job_id == job_in.upwork_job_id)
            )
            if existing_job_result.scalars().first():
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Job with this Upwork ID already exists."
                )

        # Here you would typically handle any specific business logic
        # before creating the job, e.g., validating description_embedding format if needed.
        job = Job(**job_in.model_dump())
        self.db_session.add(job)
        await self.db_session.commit()
        await self.db_session.refresh(job)
        return job

    async def get_job(self, job_id: uuid.UUID) -> Optional[Job]:
        result = await self.db_session.execute(
            select(Job).filter(Job.id == job_id)
        )
        return result.scalars().first()

    async def get_jobs(
        self,
        skip: int = 0,
        limit: int = 100,
        upwork_job_id: Optional[str] = None,
        title_contains: Optional[str] = None
    ) -> List[Job]:
        query = select(Job)

        if upwork_job_id:
            query = query.where(Job.upwork_job_id == upwork_job_id)

        if title_contains:
            query = query.where(Job.title.ilike(f"%{title_contains}%"))

        query = query.offset(skip).limit(limit)
        result = await self.db_session.execute(query)
        return result.scalars().all()

    async def update_job(self, job_id: uuid.UUID, job_in: JobUpdate) -> Optional[Job]:
        job = await self.get_job(job_id)
        if not job:
            return None
        
        update_data = job_in.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(job, key, value)
            
        await self.db_session.commit()
        await self.db_session.refresh(job)
        return job

    async def delete_job(self, job_id: uuid.UUID) -> bool:
        job = await self.get_job(job_id)
        if not job:
            return False
        
        await self.db_session.delete(job)
        await self.db_session.commit()
        return True

# Dependency provider for JobService
from app.database import get_db # Assuming get_db provides AsyncSession
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession # Ensure AsyncSession is imported

async def get_job_service(db: AsyncSession = Depends(get_db)) -> JobService:
    return JobService(db)
