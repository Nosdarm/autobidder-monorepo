import uuid
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession # Ensure AsyncSession is imported
from sqlalchemy.future import select # Ensure select is imported
from fastapi import HTTPException, status

# Remove synchronous Session, use AsyncSession
from app.models.job import Job
from app.schemas.job import JobCreate, JobUpdate
from app.services.ml_service import predict_success_proba_service, MODEL # Added
from app.schemas.ml import PredictionFeaturesInput # Added
import logging # Added

# Setup logger for this service
logger = logging.getLogger(__name__)


async def update_jobs_with_predicted_scores(db: AsyncSession) -> None: # Changed Session to AsyncSession
    """
    Updates jobs with missing predicted_score by calling the ML service.
    Uses an asynchronous SQLAlchemy session.
    """
    if MODEL is None:
        logger.error("ML Model is not loaded. Cannot update job scores. Aborting.")
        return

    logger.info("Starting to update jobs with predicted scores.")

    try:
        # Fetch jobs where predicted_score is None using an asynchronous session
        result = await db.execute(select(Job).filter(Job.predicted_score == None))
        jobs_to_update = result.scalars().all()

        if not jobs_to_update:
            logger.info("No jobs found requiring predicted score updates.")
            return

        logger.info(f"Found {len(jobs_to_update)} job(s) to update with predicted scores.")

        for job in jobs_to_update:
            logger.info(f"Processing job ID: {job.id} (Upwork ID: {job.upwork_job_id})")
            if not job.title and not job.description:
                logger.warning(f"Job ID: {job.id} has no title or description. Skipping prediction.")
                continue

            job_text_features = (job.title or "") + " " + (job.description or "")
            features_dict = {"text_feature_for_pipeline": job_text_features}
            input_data = PredictionFeaturesInput(features=features_dict)

            try:
                logger.debug(f"Calling predict_success_proba_service for job ID: {job.id} with features: {job_text_features[:100]}...")
                prediction_response = await predict_success_proba_service(input_data)

                if prediction_response and prediction_response.score is not None:
                    job.predicted_score = prediction_response.score # This modification is in memory
                    logger.info(f"Successfully updated job ID: {job.id} with predicted_score: {job.predicted_score}")
                else:
                    logger.warning(f"Prediction for job ID: {job.id} did not return a score or response was None.")

            except HTTPException as http_exc:
                 logger.error(f"HTTPException during prediction for job ID: {job.id}. Detail: {http_exc.detail}. Status: {http_exc.status_code}")
            except Exception as e:
                logger.error(f"Error predicting score for job ID: {job.id}. Error: {str(e)}", exc_info=True)

        # After processing all jobs, add them to the session for update
        # and then commit.
        # Note: job objects are already part of the session if fetched from it.
        # Modifying them marks them as "dirty".
        await db.commit()
        logger.info("Successfully committed updates for job predicted scores.")

    except Exception as e:
        logger.error(f"An error occurred during the update_jobs_with_predicted_scores process: {str(e)}", exc_info=True)
        await db.rollback() # Rollback in case of error (async)
    # No db.close() needed for AsyncSession managed by FastAPI dependency injection

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
