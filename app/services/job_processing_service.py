import logging
from sqlalchemy.orm import Session
from typing import Optional

# Assuming 'app' is in PYTHONPATH
try:
    from app.models.job import Job
    from app.ml.feature_extraction.text_embeddings import generate_job_description_embedding
    from app.database import SessionLocal # For example usage
except ImportError as e:
    logging.error(f"Error importing modules in job_processing_service: {e}")
    # Define dummy classes for type hinting if models can't be imported
    class Job:
        id: Optional[str] = None
        title: Optional[str] = None
        description: Optional[str] = None
        description_embedding: Optional[list] = None
    
    def generate_job_description_embedding(job: Job) -> Optional[list]: # type: ignore
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

    In a real application, this would likely take a Pydantic schema for job data.
    """
    logger.info(f"Attempting to create job with ID: {job_id}, Title: {title}")
    
    # Check if job already exists (optional, depends on workflow)
    existing_job = db.query(Job).filter(Job.id == job_id).first()
    if existing_job:
        logger.warning(f"Job with ID {job_id} already exists. Skipping creation.")
        # Optionally, update description and re-calculate embedding if needed
        # For now, just return the existing job
        return existing_job

    # Create the new Job object
    db_job = Job(
        id=job_id, # Assuming job_id is provided (e.g., from external source like Upwork)
        title=title,
        description=description,
        description_embedding=None # Initialize with None
    )
    
    try:
        db.add(db_job)
        db.commit()
        db.refresh(db_job)
        logger.info(f"Successfully created job record for ID: {db_job.id}")

        # Now, generate and store the embedding
        if db_job.description:
            logger.info(f"Generating description embedding for job ID: {db_job.id}")
            embedding = generate_job_description_embedding(db_job) # This function takes a Job object
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

# Example Usage (illustrative, not part of the service typically)
if __name__ == "__main__":
    # This is for demonstration if running this file directly.
    # In a real app, db session would be managed by FastAPI Depends or similar.
    
    # Ensure PYTHONPATH includes project root to find 'app'
    # Example: export PYTHONPATH=/path/to/your/project:$PYTHONPATH
    
    logger.info("Running job_processing_service.py example...")
    example_db_session: Optional[Session] = None
    try:
        example_db_session = SessionLocal()
        
        # Example 1: Create a new job with a description
        job1_id = "test_job_id_embedding_001" # Replace with a real or unique ID for testing
        job1 = create_job_with_embedding(
            db=example_db_session,
            job_id=job1_id,
            title="Senior Python Developer for AI Project",
            description="We are looking for an experienced Python developer to work on an exciting AI project. Key skills include FastAPI, Pandas, and Scikit-learn."
        )
        if job1:
            logger.info(f"Example Job 1 created/retrieved: ID {job1.id}, Embedding type: {type(job1.description_embedding)}")
            if job1.description_embedding:
                 logger.info(f"Embedding preview (first 5 dims): {job1.description_embedding[:5]}")

        # Example 2: Create a job with no description
        job2_id = "test_job_id_embedding_002"
        job2 = create_job_with_embedding(
            db=example_db_session,
            job_id=job2_id,
            title="Quick Data Entry Task",
            description=None # No description
        )
        if job2:
            logger.info(f"Example Job 2 created/retrieved: ID {job2.id}, Embedding: {job2.description_embedding}")

    except Exception as e:
        logger.error(f"Error in example usage: {e}", exc_info=True)
    finally:
        if example_db_session:
            example_db_session.close()
            logger.info("Example DB session closed.")
