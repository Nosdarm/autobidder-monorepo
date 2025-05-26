import os
import sys
import logging
import subprocess
import httpx
from pathlib import Path
from typing import Optional
from datetime import datetime # Added for job timestamps

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

# Application specific imports for the new job
from app.database import SessionLocal
from app.models.profile import Profile
from app.models.profile_historical_stats import ProfileHistoricalStats
from app.ml.feature_extraction.historical_performance import get_profile_historical_features
from sqlalchemy.exc import SQLAlchemyError


# Assuming app.config.get_settings() or similar for centralized config is not yet fully integrated.
# For now, paths are derived relative to this file or use environment variables.

# 1. Setup Logging
logger = logging.getLogger(__name__)
# Ensure logging is configured elsewhere in the app (e.g., main.py) or configure here if needed.
if not logger.hasHandlers():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

# 2. Configuration
PYTHON_EXECUTABLE = sys.executable  # Path to the current Python interpreter
BASE_DIR = Path(__file__).resolve().parent.parent # This should be the project root if scheduler_setup.py is in app/
# If app/scheduler_setup.py, then BASE_DIR is the project root.
# If this file is app/scheduler/scheduler_setup.py, then Path(__file__).resolve().parent.parent.parent

# Adjust paths assuming this file is in 'app/scheduler_setup.py' and project root contains 'app/'
# If this file is in 'app/scheduler/scheduler_setup.py', then adjust accordingly
# For example, if this file is app/scheduler_setup.py:
# ASSEMBLE_SCRIPT_PATH = BASE_DIR / "app/ml_model/assemble_dataset.py"
# TRAIN_SCRIPT_PATH = BASE_DIR / "app/ml_model/train_model.py"
# DATA_OUTPUT_PATH = BASE_DIR / "app/ml_model/data/training_dataset.parquet"
# MODEL_ARTIFACTS_DIR = BASE_DIR / "app/ml_model/artifacts/"

# Let's assume the script is in app/scheduler_setup.py, and the project root is BASE_DIR
# and 'app' is a subdirectory of BASE_DIR.
# If script is 'app/scheduler/scheduler_setup.py', then BASE_DIR is 'app/', and project_root is BASE_DIR.parent
# For simplicity, let's assume this file is directly in `app/` directory.
# Or, better, define paths relative to the `app` directory for clarity if `BASE_DIR` is project root.
APP_DIR = Path(__file__).resolve().parent # This is `app/` if file is `app/scheduler_setup.py`

ASSEMBLE_SCRIPT_MODULE = "app.ml_model.assemble_dataset"
TRAIN_SCRIPT_MODULE = "app.ml_model.train_model"

# Using absolute paths for script outputs to avoid ambiguity when subprocess runs
# Ensure these directories exist or are created by the scripts.
DATA_OUTPUT_PATH = APP_DIR / "ml_model/data/training_dataset.parquet"
MODEL_ARTIFACTS_DIR = APP_DIR / "ml_model/artifacts/"

MODEL_RELOAD_URL = os.getenv("MODEL_RELOAD_URL", "http://localhost:8000/ml/internal/reload_model")
MODEL_RELOAD_SECRET = os.getenv("MODEL_RELOAD_SECRET", "your-super-secret-key") # Basic shared secret

# 3. Helper function to run scripts
def run_script(script_module_path: str, *args) -> bool:
    """
    Helper to run Python modules using subprocess.run.
    Using -m to run modules ensures they are run in the context of the project.
    Returns True on success, False on failure.
    """
    command = [PYTHON_EXECUTABLE, "-m", script_module_path] + list(args)
    logger.info(f"Executing command: {' '.join(command)}")
    try:
        # Ensure paths are strings for subprocess
        process = subprocess.run(
            [str(c) for c in command],
            capture_output=True,
            text=True,
            check=True, # Will raise CalledProcessError if script returns non-zero exit code
            cwd=BASE_DIR # Run from project root
        )
        logger.info(f"Script {script_module_path} STDOUT:\n{process.stdout}")
        if process.stderr:
            logger.warning(f"Script {script_module_path} STDERR:\n{process.stderr}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Error running script {script_module_path}: {e}")
        logger.error(f"STDOUT: {e.stdout}")
        logger.error(f"STDERR: {e.stderr}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error running script {script_module_path}: {e}", exc_info=True)
        return False

# 4. Function to trigger model reload
async def trigger_model_reload():
    """
    Makes an HTTP POST request to the model reload endpoint.
    """
    headers = {"X-Reload-Secret": MODEL_RELOAD_SECRET} # Simple shared secret authentication
    logger.info(f"Attempting to trigger model reload at: {MODEL_RELOAD_URL}")
    try:
        async with httpx.AsyncClient(timeout=30.0) as client: # Increased timeout for reload
            response = await client.post(MODEL_RELOAD_URL, headers=headers)
            response.raise_for_status() # Raise an exception for 4XX or 5XX status codes
            logger.info(f"Model reload endpoint responded: {response.status_code} - {response.json()}")
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error triggering model reload: {e.response.status_code} - {e.response.text}", exc_info=True)
    except httpx.RequestError as e:
        logger.error(f"Request error triggering model reload: {e}", exc_info=True)
    except Exception as e:
        logger.error(f"Unexpected error triggering model reload: {e}", exc_info=True)

# 5. Scheduled Job Definitions
async def assemble_data_job():
    """
    Scheduled job to run the dataset assembly script.
    """
    job_name = "Dataset Assembly"
    start_time = datetime.utcnow()
    logger.info(f"Scheduler: Starting job '{job_name}' at {start_time.isoformat()} UTC.")
    
    # Ensure directories for output exist (though script should also handle this)
    DATA_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    success = run_script(ASSEMBLE_SCRIPT_MODULE, "--output", str(DATA_OUTPUT_PATH))
    
    end_time = datetime.utcnow()
    duration = (end_time - start_time).total_seconds()
    status_message = "succeeded" if success else "failed"
    
    logger.info(
        f"Scheduler: Job '{job_name}' {status_message}. "
        f"Start: {start_time.isoformat()} UTC, End: {end_time.isoformat()} UTC, Duration: {duration:.2f}s. "
        f"Output dataset path: {DATA_OUTPUT_PATH if success else 'N/A'}"
    )
    if not success:
        logger.error(f"Scheduler: Job '{job_name}' detailed failure logged by run_script helper.")


async def train_model_job():
    """
    Scheduled job to run the model training script and then trigger reload.
    """
    job_name = "Model Training"
    start_time = datetime.utcnow()
    logger.info(f"Scheduler: Starting job '{job_name}' at {start_time.isoformat()} UTC.")
    
    # Ensure artifact directory exists
    MODEL_ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    
    success = run_script(
        TRAIN_SCRIPT_MODULE,
        "--input_path", str(DATA_OUTPUT_PATH),
        "--model_output_dir", str(MODEL_ARTIFACTS_DIR)
        # Add other training params if needed, e.g., from config or defaults
    )
    
    end_time = datetime.utcnow()
    duration = (end_time - start_time).total_seconds()
    status_message = "succeeded" if success else "failed"

    logger.info(
        f"Scheduler: Job '{job_name}' {status_message}. "
        f"Start: {start_time.isoformat()} UTC, End: {end_time.isoformat()} UTC, Duration: {duration:.2f}s. "
        f"Input dataset path: {DATA_OUTPUT_PATH}. Model artifacts dir: {MODEL_ARTIFACTS_DIR if success else 'N/A'}"
    )

    if success:
        logger.info(f"Scheduler: Job '{job_name}' completed successfully. Triggering model reload.")
        await trigger_model_reload()
    else:
        logger.error(f"Scheduler: Job '{job_name}' failed. Model reload not triggered. Detailed failure logged by run_script helper.")


async def update_historical_stats_job():
    """
    Scheduled job to update historical performance stats for all profiles.
    """
    job_name = "Update Profile Historical Stats"
    start_time = datetime.utcnow()
    logger.info(f"Scheduler: Starting job '{job_name}' at {start_time.isoformat()} UTC.")
    
    db: Optional[SessionLocal] = None # Type hint for db session
    updated_profiles_count = 0
    failed_profiles_count = 0

    try:
        db = SessionLocal()
        profiles_to_update = db.query(Profile.id).all()
        
        if not profiles_to_update:
            logger.info(f"Scheduler: Job '{job_name}' - No profiles found to update.")
        else:
            logger.info(f"Scheduler: Job '{job_name}' - Found {len(profiles_to_update)} profiles to update stats for.")

        for profile_id_tuple in profiles_to_update:
            profile_id = profile_id_tuple[0]
            try:
                logger.debug(f"Scheduler: Job '{job_name}' - Processing profile ID: {profile_id}")
                stats_dict = get_profile_historical_features(profile_id, db) # This function now calculates fresh stats
                
                # Prepare data for upsert, ensuring keys match ProfileHistoricalStats model columns
                stats_data_for_model = {
                    "profile_id": profile_id,
                    "success_rate_7d": stats_dict.get("success_rate_7d"),
                    "success_rate_30d": stats_dict.get("success_rate_30d"),
                    "success_rate_90d": stats_dict.get("success_rate_90d"),
                    "bid_frequency_7d": stats_dict.get("bid_frequency_7d"),
                    "bid_frequency_30d": stats_dict.get("bid_frequency_30d"),
                    "bid_frequency_90d": stats_dict.get("bid_frequency_90d"),
                    "last_updated_at": datetime.utcnow() # Set current timestamp
                }

                # Upsert logic: Get-then-update or create
                existing_stats = db.get(ProfileHistoricalStats, profile_id)
                if existing_stats:
                    logger.debug(f"Scheduler: Job '{job_name}' - Updating existing stats for profile ID: {profile_id}")
                    for key, value in stats_data_for_model.items():
                        setattr(existing_stats, key, value)
                else:
                    logger.debug(f"Scheduler: Job '{job_name}' - Creating new stats for profile ID: {profile_id}")
                    db.add(ProfileHistoricalStats(**stats_data_for_model))
                
                db.commit() # Commit per profile to avoid one failure rolling back all
                updated_profiles_count += 1
            except SQLAlchemyError as e_sql:
                db.rollback() # Rollback for the current profile
                logger.error(f"Scheduler: Job '{job_name}' - SQLAlchemyError processing profile ID {profile_id}: {e_sql}", exc_info=True)
                failed_profiles_count += 1
            except Exception as e_gen:
                db.rollback() # Rollback for the current profile
                logger.error(f"Scheduler: Job '{job_name}' - Generic error processing profile ID {profile_id}: {e_gen}", exc_info=True)
                failed_profiles_count += 1
                
    except Exception as e_outer:
        logger.error(f"Scheduler: Job '{job_name}' - Outer error during execution: {e_outer}", exc_info=True)
    finally:
        if db:
            db.close()

    end_time = datetime.utcnow()
    duration = (end_time - start_time).total_seconds()
    logger.info(
        f"Scheduler: Job '{job_name}' finished. "
        f"Start: {start_time.isoformat()} UTC, End: {end_time.isoformat()} UTC, Duration: {duration:.2f}s. "
        f"Profiles processed: {updated_profiles_count}, Profiles failed: {failed_profiles_count}"
    )


# 6. Scheduler Initialization and Job Scheduling
# Using AsyncIOScheduler as FastAPI is an async framework
scheduler = AsyncIOScheduler(timezone="UTC") # Or your preferred timezone string e.g., "Europe/Berlin"

# Define default cron schedules, can be overridden by environment variables
ASSEMBLE_CRON_HOUR = os.getenv("ASSEMBLE_CRON_HOUR", "1") # Default 1 AM UTC
ASSEMBLE_CRON_MINUTE = os.getenv("ASSEMBLE_CRON_MINUTE", "0")
TRAIN_CRON_HOUR = os.getenv("TRAIN_CRON_HOUR", "2") # Default 2 AM UTC
TRAIN_CRON_MINUTE = os.getenv("TRAIN_CRON_MINUTE", "0")
STATS_UPDATE_CRON_HOUR = os.getenv("STATS_UPDATE_CRON_HOUR", "0") # Default 00:30 AM UTC
STATS_UPDATE_CRON_MINUTE = os.getenv("STATS_UPDATE_CRON_MINUTE", "30")


try:
    scheduler.add_job(
        assemble_data_job,
        CronTrigger(hour=int(ASSEMBLE_CRON_HOUR), minute=int(ASSEMBLE_CRON_MINUTE)),
        id="assemble_data_job",
        name="Daily Dataset Assembly",
        replace_existing=True
    )
    logger.info(f"Scheduled dataset assembly job with cron: hour={ASSEMBLE_CRON_HOUR}, minute={ASSEMBLE_CRON_MINUTE} UTC.")

    scheduler.add_job(
        train_model_job,
        CronTrigger(hour=int(TRAIN_CRON_HOUR), minute=int(TRAIN_CRON_MINUTE)),
        id="train_model_job",
        name="Daily Model Training and Reload",
        replace_existing=True
    )
    logger.info(f"Scheduled model training job with cron: hour={TRAIN_CRON_HOUR}, minute={TRAIN_CRON_MINUTE} UTC.")

    scheduler.add_job(
        update_historical_stats_job,
        CronTrigger(hour=int(STATS_UPDATE_CRON_HOUR), minute=int(STATS_UPDATE_CRON_MINUTE)), # Daily at 00:30 AM UTC
        id="update_historical_stats_job",
        name="Daily Profile Historical Stats Update",
        replace_existing=True
    )
    logger.info(f"Scheduled profile historical stats update job with cron: hour={STATS_UPDATE_CRON_HOUR}, minute={STATS_UPDATE_CRON_MINUTE} UTC.")

except ValueError as e:
    logger.error(f"Error parsing cron parameters from environment variables: {e}. Using default schedules if possible.")
    # Fallback to default if env vars are invalid, though add_job might still fail if defaults also bad.
    # This part might need more robust error handling for cron string validation.
except Exception as e:
    logger.error(f"Error adding jobs to scheduler: {e}", exc_info=True)


def start_scheduler():
    if not scheduler.running:
        try:
            scheduler.start()
            logger.info("APScheduler started successfully.")
        except Exception as e:
            logger.error(f"Failed to start APScheduler: {e}", exc_info=True)
    else:
        logger.info("APScheduler is already running.")

def shutdown_scheduler(wait: bool = True):
    if scheduler.running:
        try:
            scheduler.shutdown(wait=wait)
            logger.info("APScheduler shut down successfully.")
        except Exception as e:
            logger.error(f"Failed to shut down APScheduler cleanly: {e}", exc_info=True)
    else:
        logger.info("APScheduler is not running.")
