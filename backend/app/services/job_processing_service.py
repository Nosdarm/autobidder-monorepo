import logging
from sqlalchemy.orm import Session # Will change to AsyncSession
from typing import Optional, List # Changed to List

# Assuming 'app' is in PYTHONPATH
try:
    from app.models.job import Job
    # This import might need adjustment based on where feature_extraction is moved
    from app.ml.feature_extraction.text_embeddings import generate_job_description_embedding 
    from app.database import SessionLocal # For example usage, should use Depends(get_db) in FastAPI routes
except ImportError as e:
    logging.error(f"Error importing modules in job_processing_service: {e}")
    # Define dummy classes for type hinting if models can't be imported
    class Job: # type: ignore
        id: Optional[str] = None
        title: Optional[str] = None
        description: Optional[str] = None
        description_embedding: Optional[List[float]] = None # Corrected type hint
    
    def generate_job_description_embedding(job: Job) -> Optional[List[float]]: # type: ignore
        return None
    
    class SessionLocal: # type: ignore
        def __call__(self): pass


logger = logging.getLogger(__name__)
if not logger.hasHandlers():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


def create_job_with_embedding(
    db: Session, 
    job_id: str, 
    title: Optional[str], 
    description: Optional[str]
) -> Optional[Job]:
    """
    Placeholder function to demonstrate creating a new Job record
    and then generating and storing its description embedding.
    """
    logger.info(f"Attempting to create job with ID: {job_id}, Title: {title}")
    
    existing_job = db.query(Job).filter(Job.id == job_id).first()
    if existing_job:
        logger.warning(f"Job with ID {job_id} already exists. Skipping creation.")
        return existing_job

    db_job = Job(
        id=job_id, 
        title=title,
        description=description,
        description_embedding=None 
    )
    
    try:
        db.add(db_job)
        db.commit()
        db.refresh(db_job)
        logger.info(f"Successfully created job record for ID: {db_job.id}")

        if db_job.description:
            logger.info(f"Generating description embedding for job ID: {db_job.id}")
            embedding = generate_job_description_embedding(db_job) 
            if embedding:
                db_job.description_embedding = embedding
                db.commit()
                db.refresh(db_job)
                logger.info(f"Successfully generated and stored description embedding for job ID: {db_job.id}")
            else:
                logger.warning(f"Failed to generate embedding for job ID: {db_job.id} (embedding was None).")
        else:
            logger.info(f"Job ID: {db_job.id} has no description. Skipping embedding generation.")
            
        return db_job

    except Exception as e:
        db.rollback()
        logger.error(f"Error creating job or its embedding for ID {job_id}: {e}", exc_info=True)
        return None

# Example Usage (illustrative)
# if __name__ == "__main__":
#     logger.info("Running job_processing_service.py example...")
#     example_db_session: Optional[Session] = None
#     try:
#         example_db_session = SessionLocal()
#         job1_id = "example_job_001"
#         job1 = create_job_with_embedding(
#             db=example_db_session,
#             job_id=job1_id,
#             title="Senior Python Developer for AI Project",
#             description="We are looking for an experienced Python developer..."
#         )
#         if job1:
#             logger.info(f"Example Job 1: ID {job1.id}, Embedding type: {type(job1.description_embedding)}")
#     except Exception as e:
#         logger.error(f"Error in example usage: {e}", exc_info=True)
#     finally:
#         if example_db_session:
#             example_db_session.close()
#             logger.info("Example DB session closed.")
