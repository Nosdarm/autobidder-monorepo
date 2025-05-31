import pytest
import pytest_asyncio
import uuid
from typing import Optional, List, AsyncGenerator
import datetime

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, AsyncEngine
from sqlalchemy.future import select
from fastapi import HTTPException

# Assuming Base is in app.db.base_class. Adjust if different.
from app.db.base_class import Base
from app.models.job import Job
from app.schemas.job import JobCreate, JobUpdate
from app.services.job_service import JobService

# Database URL for in-memory SQLite
DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest.fixture(scope="function") # Changed from session to function for better isolation if tests modify schema or have side effects
async def db_engine() -> AsyncGenerator[AsyncEngine, None]:
    """Fixture for an async SQLAlchemy engine."""
    engine = create_async_engine(DATABASE_URL)
    yield engine
    await engine.dispose()

async def _create_tables(engine: AsyncEngine):
    """Helper to create tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def _drop_tables(engine: AsyncEngine):
    """Helper to drop tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest_asyncio.fixture(scope="function")
async def db_session(db_engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    """Fixture for an async SQLAlchemy session with table setup/teardown."""
    await _create_tables(db_engine)
    async with AsyncSession(db_engine) as session:
        yield session
    # Tables are dropped after all tests in a session if scope is "session",
    # or after each test if scope is "function".
    # For SQLite in-memory, dropping might not be strictly necessary if engine is disposed,
    # but good practice for other DBs.
    await _drop_tables(db_engine)


@pytest.fixture(scope="function")
def job_service(db_session: AsyncSession) -> JobService:
    """Fixture for the JobService."""
    return JobService(db_session=db_session)


# --- Test Cases ---

@pytest.mark.asyncio
async def test_create_job_success(job_service: JobService, db_session: AsyncSession):
    job_create_data = JobCreate(
        title="Test Job",
        description="Test description",
        upwork_job_id="upwork123",
        url="http://example.com/job/upwork123",
        raw_data={"key": "value"},
        posted_time=datetime.datetime.now(datetime.timezone.utc)
    )
    created_job = await job_service.create_job(job_in=job_create_data)

    assert created_job is not None
    assert created_job.id is not None
    assert created_job.title == job_create_data.title
    assert created_job.upwork_job_id == job_create_data.upwork_job_id

    # Verify in DB
    fetched_job = await db_session.get(Job, created_job.id)
    assert fetched_job is not None
    assert fetched_job.title == job_create_data.title

@pytest.mark.asyncio
async def test_create_job_duplicate_upwork_id(job_service: JobService, db_session: AsyncSession):
    upwork_id = "duplicate_upwork_id_123"
    job1_data = JobCreate(
        title="First Job",
        description="Desc 1",
        upwork_job_id=upwork_id
    )
    await job_service.create_job(job_in=job1_data) # Create first job

    job2_data = JobCreate(
        title="Second Job",
        description="Desc 2",
        upwork_job_id=upwork_id # Same upwork_job_id
    )
    with pytest.raises(HTTPException) as exc_info:
        await job_service.create_job(job_in=job2_data)

    assert exc_info.value.status_code == 409
    assert "already exists" in exc_info.value.detail.lower()

@pytest.mark.asyncio
async def test_get_job_success(job_service: JobService, db_session: AsyncSession):
    job_data = Job(
        id=uuid.uuid4(),
        title="Pre-existing Job",
        upwork_job_id="upwork_pre_exist",
        description="Test"
    )
    db_session.add(job_data)
    await db_session.commit()

    fetched_job = await job_service.get_job(job_id=job_data.id)
    assert fetched_job is not None
    assert fetched_job.id == job_data.id
    assert fetched_job.title == job_data.title

@pytest.mark.asyncio
async def test_get_job_not_found(job_service: JobService):
    non_existent_uuid = uuid.uuid4()
    fetched_job = await job_service.get_job(job_id=non_existent_uuid)
    assert fetched_job is None

@pytest.mark.asyncio
async def test_get_jobs_empty(job_service: JobService):
    jobs = await job_service.get_jobs()
    assert jobs == []

@pytest.mark.asyncio
async def test_get_jobs_with_data_and_pagination(job_service: JobService, db_session: AsyncSession):
    # Create 3 jobs
    job1 = Job(id=uuid.uuid4(), title="Job 1", upwork_job_id="jp1", description="d1")
    job2 = Job(id=uuid.uuid4(), title="Job 2", upwork_job_id="jp2", description="d2")
    job3 = Job(id=uuid.uuid4(), title="Job 3", upwork_job_id="jp3", description="d3")
    db_session.add_all([job1, job2, job3])
    await db_session.commit()

    # Test limit
    jobs_limit_2 = await job_service.get_jobs(limit=2)
    assert len(jobs_limit_2) == 2

    # Test skip (offset)
    jobs_skip_1_limit_1 = await job_service.get_jobs(skip=1, limit=1)
    assert len(jobs_skip_1_limit_1) == 1
    # Ensure the correct job is skipped. Order by title for predictability if not otherwise ordered.
    # For SQLite in-memory, order might be insertion order if not specified.
    # Let's assume Job 2 or Job 3 could be returned depending on internal ordering.
    # To make this robust, we'd need to order results in get_jobs or know default order.
    # For now, we just check length. A more robust test would check content.
    # For example, if jobs are ordered by title by default (or if we add it to get_jobs):
    # assert jobs_skip_1_limit_1[0].title == "Job 2"

    all_jobs = await job_service.get_jobs(limit=10) # Get all to check skip logic

    jobs_skip_2 = await job_service.get_jobs(skip=2, limit=2)
    assert len(jobs_skip_2) == 1 # Only one job left after skipping 2
    if len(all_jobs) == 3: # Ensure this logic only runs if all 3 jobs were inserted
      assert jobs_skip_2[0].title == all_jobs[2].title # Check if the correct one is returned

@pytest.mark.asyncio
async def test_get_jobs_filter_by_upwork_id(job_service: JobService, db_session: AsyncSession):
    target_upwork_id = "filter_upwork_id_target"
    job1 = Job(id=uuid.uuid4(), title="Job Alpha", upwork_job_id="other_id_1", description="d")
    job2 = Job(id=uuid.uuid4(), title="Job Beta", upwork_job_id=target_upwork_id, description="d")
    job3 = Job(id=uuid.uuid4(), title="Job Gamma", upwork_job_id="other_id_2", description="d")
    db_session.add_all([job1, job2, job3])
    await db_session.commit()

    filtered_jobs = await job_service.get_jobs(upwork_job_id=target_upwork_id)
    assert len(filtered_jobs) == 1
    assert filtered_jobs[0].upwork_job_id == target_upwork_id
    assert filtered_jobs[0].title == "Job Beta"

@pytest.mark.asyncio
async def test_get_jobs_filter_by_title(job_service: JobService, db_session: AsyncSession):
    job1 = Job(id=uuid.uuid4(), title="Python Developer", upwork_job_id="title1", description="d")
    job2 = Job(id=uuid.uuid4(), title="Senior Pythonista", upwork_job_id="title2", description="d")
    job3 = Job(id=uuid.uuid4(), title="Java Developer", upwork_job_id="title3", description="d")
    db_session.add_all([job1, job2, job3])
    await db_session.commit()

    # Test case-insensitive title search
    filtered_jobs = await job_service.get_jobs(title_contains="python")
    assert len(filtered_jobs) == 2
    titles = {job.title for job in filtered_jobs}
    assert "Python Developer" in titles
    assert "Senior Pythonista" in titles

    filtered_jobs_exact = await job_service.get_jobs(title_contains="Python Developer")
    assert len(filtered_jobs_exact) == 1
    assert filtered_jobs_exact[0].title == "Python Developer"

    filtered_jobs_no_match = await job_service.get_jobs(title_contains="NoSuchTitle")
    assert len(filtered_jobs_no_match) == 0


@pytest.mark.asyncio
async def test_update_job_success(job_service: JobService, db_session: AsyncSession):
    original_job = Job(
        id=uuid.uuid4(),
        title="Original Title",
        description="Original Desc",
        upwork_job_id="update_test_1",
        url="http://original.url"
    )
    db_session.add(original_job)
    await db_session.commit()

    job_update_data = JobUpdate(title="Updated Title", url="http://updated.url", description="Updated Desc")

    updated_job = await job_service.update_job(job_id=original_job.id, job_in=job_update_data)
    assert updated_job is not None
    assert updated_job.id == original_job.id
    assert updated_job.title == "Updated Title"
    assert updated_job.description == "Updated Desc"
    assert updated_job.url == "http://updated.url"
    assert updated_job.upwork_job_id == "update_test_1" # Should not change if not in JobUpdate

    # Verify in DB
    refetched_job = await db_session.get(Job, original_job.id)
    assert refetched_job is not None
    assert refetched_job.title == "Updated Title"
    assert refetched_job.url == "http://updated.url"

@pytest.mark.asyncio
async def test_update_job_not_found(job_service: JobService):
    non_existent_uuid = uuid.uuid4()
    job_update_data = JobUpdate(title="Trying to update non-existent job")
    updated_job = await job_service.update_job(job_id=non_existent_uuid, job_in=job_update_data)
    assert updated_job is None

@pytest.mark.asyncio
async def test_delete_job_success(job_service: JobService, db_session: AsyncSession):
    job_to_delete = Job(
        id=uuid.uuid4(),
        title="Job To Delete",
        upwork_job_id="delete_me_1",
        description="Test"
    )
    db_session.add(job_to_delete)
    await db_session.commit()
    await db_session.refresh(job_to_delete) # Ensure it's fully loaded before delete

    delete_result = await job_service.delete_job(job_id=job_to_delete.id)
    assert delete_result is True

    # Verify in DB
    deleted_job_in_db = await db_session.get(Job, job_to_delete.id)
    assert deleted_job_in_db is None

@pytest.mark.asyncio
async def test_delete_job_not_found(job_service: JobService):
    non_existent_uuid = uuid.uuid4()
    delete_result = await job_service.delete_job(job_id=non_existent_uuid)
    assert delete_result is False

# --- Tests for update_jobs_with_predicted_scores ---
from unittest.mock import AsyncMock, MagicMock, patch

# Import the function to be tested and other necessary items
from backend.app.services.job_service import update_jobs_with_predicted_scores
from backend.app.schemas.ml import PredictionResponse # For mocking return value

@pytest.mark.asyncio
async def test_update_jobs_with_predicted_scores_success():
    # 1. Mock AsyncSession and its methods
    mock_db_session = AsyncMock(spec=AsyncSession)

    # Setup mock Job objects
    mock_job1 = Job(id=uuid.uuid4(), title="Job 1", description="Desc 1", predicted_score=None)
    mock_job2 = Job(id=uuid.uuid4(), title="Job 2", description="Desc 2", predicted_score=None)

    # Configure mock_db_session.execute chain
    # query(Job).filter(Job.predicted_score == None).all()
    # In SQLAlchemy 2.0 style with AsyncSession, this is:
    # result = await session.execute(select(Job).where(Job.predicted_score == None))
    # jobs_to_update = result.scalars().all()

    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [mock_job1, mock_job2]
    mock_db_session.execute.return_value = mock_result

    # 2. Mock predict_success_proba_service
    # This function is imported in job_service.py as:
    # from app.services.ml_service import predict_success_proba_service, MODEL
    # So we need to patch it there.
    mock_prediction_response = PredictionResponse(success_probability=0.9, score=90.0, model_info="test_model")

    with patch('backend.app.services.job_service.predict_success_proba_service', AsyncMock(return_value=mock_prediction_response)) as mock_predict_service, \
         patch('backend.app.services.job_service.MODEL', MagicMock()) as mock_model_global, \
         patch('backend.app.services.job_service.logger') as mock_logger: # Optional: mock logger

        # Ensure the global MODEL is not None so the function doesn't exit early
        # The MagicMock above for mock_model_global already ensures it's not None.

        # 3. Call the function
        await update_jobs_with_predicted_scores(db=mock_db_session)

        # 4. Assertions
        # Check if predict_success_proba_service was called for each job
        assert mock_predict_service.call_count == 2

        # Check if job objects were updated
        assert mock_job1.predicted_score == 90.0
        assert mock_job2.predicted_score == 90.0

        # Check if db.commit was called
        mock_db_session.commit.assert_called_once()

        # Optional: Check logging
        mock_logger.info.assert_any_call(f"Found 2 job(s) to update with predicted scores.")
        mock_logger.info.assert_any_call(f"Successfully updated job ID: {mock_job1.id} with predicted_score: 90.0")
        mock_logger.info.assert_any_call(f"Successfully updated job ID: {mock_job2.id} with predicted_score: 90.0")

@pytest.mark.asyncio
async def test_update_jobs_with_predicted_scores_no_jobs_to_update():
    mock_db_session = AsyncMock(spec=AsyncSession)
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [] # No jobs
    mock_db_session.execute.return_value = mock_result

    with patch('backend.app.services.job_service.predict_success_proba_service', AsyncMock()) as mock_predict_service, \
         patch('backend.app.services.job_service.MODEL', MagicMock()) as mock_model_global, \
         patch('backend.app.services.job_service.logger') as mock_logger:

        await update_jobs_with_predicted_scores(db=mock_db_session)

        mock_predict_service.assert_not_called()
        mock_db_session.commit.assert_not_called() # Should not commit if no jobs processed
        mock_logger.info.assert_any_call("No jobs found requiring predicted score updates.")


@pytest.mark.asyncio
async def test_update_jobs_with_predicted_scores_model_not_loaded():
    mock_db_session = AsyncMock(spec=AsyncSession)
    # Patch MODEL to be None
    with patch('backend.app.services.job_service.MODEL', None) as mock_model_global_none, \
         patch('backend.app.services.job_service.logger') as mock_logger:

        await update_jobs_with_predicted_scores(db=mock_db_session)

        mock_logger.error.assert_called_with("ML Model is not loaded. Cannot update job scores. Aborting.")
        mock_db_session.execute.assert_not_called() # Should not attempt to fetch jobs

@pytest.mark.asyncio
async def test_update_jobs_with_predicted_scores_prediction_fails_for_one_job():
    mock_db_session = AsyncMock(spec=AsyncSession)
    mock_job1 = Job(id=uuid.uuid4(), title="Job 1", description="Desc 1", predicted_score=None)
    mock_job2 = Job(id=uuid.uuid4(), title="Job 2", description="Desc 2", predicted_score=None) # Will fail
    mock_job3 = Job(id=uuid.uuid4(), title="Job 3", description="Desc 3", predicted_score=None)

    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [mock_job1, mock_job2, mock_job3]
    mock_db_session.execute.return_value = mock_result

    # Simulate prediction failure for job2
    async def side_effect_predict_service(input_data):
        # Assuming input_data.features["text_feature_for_pipeline"] contains title + " " + description
        if "Job 2 Desc 2" in input_data.features["text_feature_for_pipeline"]:
            raise Exception("Simulated prediction error")
        return PredictionResponse(success_probability=0.8, score=80.0, model_info="test_model")

    with patch('backend.app.services.job_service.predict_success_proba_service', AsyncMock(side_effect=side_effect_predict_service)) as mock_predict_service, \
         patch('backend.app.services.job_service.MODEL', MagicMock()) as mock_model_global, \
         patch('backend.app.services.job_service.logger') as mock_logger:

        await update_jobs_with_predicted_scores(db=mock_db_session)

        assert mock_predict_service.call_count == 3
        assert mock_job1.predicted_score == 80.0
        assert mock_job2.predicted_score is None # Failed prediction, score not set
        assert mock_job3.predicted_score == 80.0

        mock_db_session.commit.assert_called_once() # Should still commit successful updates
        mock_logger.error.assert_any_call(f"Error predicting score for job ID: {mock_job2.id}. Error: Simulated prediction error", exc_info=True)
