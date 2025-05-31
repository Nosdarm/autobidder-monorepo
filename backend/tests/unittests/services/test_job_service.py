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
