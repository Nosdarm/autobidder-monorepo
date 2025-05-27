import logging
import httpx
from datetime import datetime, timedelta # Added timedelta
from typing import Dict, Any, Optional, List
import uuid # Added uuid

from sqlalchemy.orm import Session # Will change to AsyncSession
from sqlalchemy.exc import SQLAlchemyError # For DB error handling
from fastapi import HTTPException

# Assuming these are the correct paths in the consolidated structure
from app.database import SessionLocal # For creating new sessions if needed in standalone scripts/tasks
from app.models.autobid_settings import AutobidSettings
from app.models.profile import Profile
from app.models.job import Job
from app.models.profile_historical_stats import ProfileHistoricalStats
from app.models.bid import Bid # For placing mock bids
from app.models.autobid_log import AutobidLog # For logging attempts

from app.schemas.autobid import AutobidSettingsUpdate # For updating settings
# Schemas for ML prediction input/output will be handled by the ML service if called directly
# from app.schemas.ml import PredictionFeaturesInput, PredictionResponse # Example

# Assuming feature extraction utilities are now in app.ml.feature_extraction or similar
# These paths will need to be verified and corrected based on the actual consolidated structure.
# For now, direct import paths are assumed.
try:
    from app.ml.feature_extraction import (
        generate_profile_features,
        featurize_submission_time,
        featurize_bid_settings
    )
except ImportError:
    logger = logging.getLogger(__name__)
    logger.error("Failed to import feature extraction modules. Ensure they are in the correct path (e.g., app.ml.feature_extraction). Autobidder may not function correctly.")
    # Define dummy functions if import fails to allow service to load, but it won't work properly.
    def generate_profile_features(profile: Profile) -> Dict[str, Any]: return {}
    def featurize_submission_time(dt: datetime) -> Dict[str, Any]: return {}
    def featurize_bid_settings(settings_dict: Dict[str, Any]) -> Dict[str, Any]: return {}

from app.config import settings

# Configuration
ML_PREDICTION_ENDPOINT_URL = str(settings.ML_PREDICTION_ENDPOINT_URL) # Corrected path from ml_routes
ML_PROBABILITY_THRESHOLD = settings.ML_PROBABILITY_THRESHOLD

logger = logging.getLogger(__name__)
# Ensure logging is configured elsewhere in the app, or configure here if standalone
if not logger.hasHandlers():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(module)s - %(message)s')


# --- AutobidSettings Management (from original autobidder_service.py) ---
def get_settings_for_profile(profile_id: str, db: Session) -> Optional[AutobidSettings]:
    # This function was part of the original backend/app/services/autobidder_service.py
    # It's kept here as it's directly related to autobidder settings.
    # Note: The session management (db: Session) should be aligned with async practices if used in async contexts.
    settings = db.query(AutobidSettings).filter(AutobidSettings.profile_id == profile_id).first()
    if not settings:
        logger.info(f"No AutobidSettings found for profile {profile_id}, creating default settings.")
        settings = AutobidSettings(profile_id=profile_id) # Uses default values from model
        db.add(settings)
        try:
            db.commit()
            db.refresh(settings)
            logger.info(f"Default AutobidSettings created for profile {profile_id}.")
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Error creating default AutobidSettings for profile {profile_id}: {e}", exc_info=True)
            # Don't raise HTTPException from here if this can be called outside HTTP context.
            # Return None or re-raise a service-specific exception.
            return None 
    return settings

def update_settings_for_profile(profile_id: str, data: AutobidSettingsUpdate, db: Session) -> Optional[AutobidSettings]:
    # Also from original backend/app/services/autobidder_service.py
    settings = db.query(AutobidSettings).filter(AutobidSettings.profile_id == profile_id).first()
    if not settings:
        # Consistent with above, avoid HTTPException directly if possible.
        logger.warning(f"AutobidSettings not found for profile {profile_id} during update attempt.")
        return None 

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(settings, key, value)
    
    try:
        db.commit()
        db.refresh(settings)
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Error updating AutobidSettings for profile {profile_id}: {e}", exc_info=True)
        return None
    return settings

# --- ML Integration Logic (from app/services/ai_prompt_service.py) ---
async def _get_ml_prediction(features: Dict[str, Any]) -> Optional[float]:
    payload = {"features": features}
    logger.debug(f"Sending features to ML Prediction API: {list(features.keys())}")
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(ML_PREDICTION_ENDPOINT_URL, json=payload)
            response.raise_for_status()
            prediction_data = response.json()
            success_probability = prediction_data.get("success_probability")
            
            if success_probability is None:
                logger.error(f"ML API response missing 'success_probability'. Response: {prediction_data}")
                return None
            
            logger.info(f"Received success probability from ML API: {success_probability:.4f}")
            return float(success_probability)
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error calling ML Prediction API: {e.response.status_code} - {e.response.text}", exc_info=True)
        return None
    except httpx.RequestError as e:
        logger.error(f"Request error calling ML Prediction API: {e}", exc_info=True)
        return None
    except Exception as e:
        logger.error(f"Unexpected error in _get_ml_prediction: {e}", exc_info=True)
        return None

def _assemble_features_for_prediction(
    job_to_bid_on: Job, 
    active_profile: Profile, 
    db_for_historical: Session # Synchronous session for now
) -> Dict[str, Any]:
    prediction_input_features: Dict[str, Any] = {}

    # 1. Job Description Embedding
    job_emb_list = job_to_bid_on.description_embedding
    embedding_dim = 1536 # Standard for text-embedding-ada-002
    if job_emb_list is not None and len(job_emb_list) == embedding_dim:
        for i, val in enumerate(job_emb_list):
            prediction_input_features[f'job_emb_{i}'] = val
    else:
        if job_emb_list is not None: # Log if length is wrong
             logger.warning(f"Job ID {job_to_bid_on.id} has description embedding of unexpected length {len(job_emb_list)}. Expected {embedding_dim}. Filling with zeros.")
        else: # Log if missing
            logger.warning(f"Job ID {job_to_bid_on.id} has no precomputed description embedding. Filling with zeros.")
        for i in range(embedding_dim): 
            prediction_input_features[f'job_emb_{i}'] = 0.0

    # 2. Profile Features
    profile_feats = generate_profile_features(active_profile) # Assumes this function handles None values from profile
    if profile_feats:
        for key, value in profile_feats.items():
             prediction_input_features[f'profile_{key}'] = value if value is not None else 0.0

    # 3. Historical Features
    db_stats = db_for_historical.query(ProfileHistoricalStats).filter(
        ProfileHistoricalStats.profile_id == active_profile.id
    ).first()
    
    stats_max_age_days = 1.5 
    default_stat_value = 0.0
    historical_feats_dict: Dict[str, Any] = {
        "success_rate_7d": default_stat_value, "success_rate_30d": default_stat_value, "success_rate_90d": default_stat_value,
        "bid_frequency_7d": default_stat_value, "bid_frequency_30d": default_stat_value, "bid_frequency_90d": default_stat_value,
    }

    if db_stats:
        if (datetime.utcnow() - db_stats.last_updated_at).total_seconds() / (24 * 60 * 60) < stats_max_age_days:
            historical_feats_dict = {
                "success_rate_7d": db_stats.success_rate_7d, "success_rate_30d": db_stats.success_rate_30d,
                "success_rate_90d": db_stats.success_rate_90d, "bid_frequency_7d": db_stats.bid_frequency_7d,
                "bid_frequency_30d": db_stats.bid_frequency_30d, "bid_frequency_90d": db_stats.bid_frequency_90d,
            }
            logger.debug(f"Using historical stats for profile {active_profile.id}, last updated: {db_stats.last_updated_at}")
        else:
            logger.warning(f"Historical stats for profile {active_profile.id} are too old (last updated: {db_stats.last_updated_at}). Using defaults.")
    else:
        logger.warning(f"No historical stats found for profile {active_profile.id}. Using defaults.")

    for key, value in historical_feats_dict.items():
         prediction_input_features[f'hist_{key}'] = value if value is not None else default_stat_value

    # 4. Current Bid Temporal Features
    current_time = datetime.utcnow()
    submission_time_feats = featurize_submission_time(current_time)
    if submission_time_feats:
        for key, value in submission_time_feats.items():
            prediction_input_features[f'bid_temp_{key}'] = value if value is not None else -1 # -1 for time features if None

    # Bid Settings Features (using profile's autobid settings as a proxy or defaults)
    # This part needs careful review based on how bid settings are determined for new auto-bids.
    # For this example, we'll use defaults if not available on profile's autobid_settings.
    autobid_settings = get_settings_for_profile(active_profile.id, db_for_historical) # Re-fetch or pass if already available
    
    # Mock snapshot, ideally derived from actual bidding strategy for this profile/job
    mock_bid_settings_snapshot = {
        "budget": 100.0, # Default placeholder
        "duration_weeks": 4, # Default placeholder
        "is_fixed_price": False, # Default placeholder
    }
    # If settings are available, try to use more specific defaults
    if autobid_settings:
        # These fields (default_budget etc.) are not on AutobidSettings model currently.
        # This implies they might come from Profile or a more complex settings object.
        # For now, we stick to the simple mock_bid_settings_snapshot.
        pass 
        
    bid_settings_feats = featurize_bid_settings(mock_bid_settings_snapshot)
    if bid_settings_feats:
        for key, value in bid_settings_feats.items():
            prediction_input_features[f'bid_temp_{key}'] = value if value is not None else 0.0

    # Final check for None values
    for key, value in prediction_input_features.items():
        if value is None:
            logger.warning(f"Feature '{key}' is None after assembly, defaulting to 0.0. Check feature generation logic.")
            prediction_input_features[key] = 0.0
    return prediction_input_features

def _log_autobid_attempt(
    db: Session, profile_id: str, job_id: uuid.UUID, job_title: str, 
    status: str, success_proba: Optional[float] = None, 
    bid_text: Optional[str] = None, error_message: Optional[str] = None
):
    """Helper to log autobid attempts to AutobidLog table."""
    try:
        log_entry = AutobidLog(
            profile_id=profile_id,
            job_title=job_title,
            job_link=f"job_link_placeholder/{job_id}", # Placeholder, actual link might not be available
            bid_text=bid_text,
            status=status, # e.g., "bid_placed_ml", "skipped_ml_low_proba", "error_ml_prediction"
            score=success_proba, # Store ML score
            error_message=error_message,
            # created_at is default in model
        )
        db.add(log_entry)
        db.commit()
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Error logging autobid attempt for profile {profile_id}, job {job_id}: {e}", exc_info=True)


async def run_autobid_for_profile(profile_id: str):
    db: Optional[Session] = None
    try:
        db = SessionLocal() # Create a new synchronous session for this run
        active_profile = db.query(Profile).filter(Profile.id == profile_id).first()
        if not active_profile:
            logger.error(f"Profile {profile_id} not found. Skipping autobid run.")
            return
        
        autobid_settings = get_settings_for_profile(profile_id, db) # Use the function to get/create settings
        if not autobid_settings or not autobid_settings.enabled:
            logger.info(f"Autobidder is disabled for profile {profile_id}. Skipping.")
            return

        logger.info(f"Running autobidder for profile: {active_profile.name} ({profile_id})")

        potential_jobs: List[Job] = _discover_potential_jobs(db, active_profile)
        if not potential_jobs:
            logger.info(f"No potential jobs found for profile {profile_id}.")
            return
        
        logger.info(f"Found {len(potential_jobs)} potential jobs for profile {profile_id}.")

        bids_placed_count = 0
        daily_bid_limit = autobid_settings.daily_limit # From AutobidSettings model

        for job_to_bid_on in potential_jobs:
            if bids_placed_count >= daily_bid_limit:
                logger.info(f"Daily bid limit ({daily_bid_limit}) reached for profile {profile_id}. Stopping.")
                _log_autobid_attempt(db, profile_id, job_to_bid_on.id, job_to_bid_on.title, status="stopped_daily_limit")
                break

            logger.info(f"Processing job: {job_to_bid_on.title} (ID: {job_to_bid_on.id}) for profile {profile_id}")

            prediction_input_features = _assemble_features_for_prediction(job_to_bid_on, active_profile, db)
            success_proba = await _get_ml_prediction(prediction_input_features)

            decision_status = ""
            error_msg = None

            if success_proba is None:
                logger.warning(f"ML prediction failed for job {job_to_bid_on.id}. Skipping bid.")
                decision_status = "skipped_ml_failure"
                error_msg = "ML prediction service request failed or returned invalid data."
            elif success_proba >= ML_PROBABILITY_THRESHOLD:
                logger.info(f"ML prediction for job {job_to_bid_on.id}: {success_proba:.4f} (>= threshold {ML_PROBABILITY_THRESHOLD}). Proceeding with bid.")
                # Mock bid placement
                mock_bid_text = f"This is an auto-generated bid for {job_to_bid_on.title} by profile {active_profile.name}."
                # _place_bid(db, active_profile, job_to_bid_on, success_proba, mock_bid_text) # Actual bid placement
                
                # For now, just log the decision to place bid
                logger.info(f"MOCK_BID_PLACED: Job '{job_to_bid_on.title}', Profile '{active_profile.name}', Proba: {success_proba:.4f}")
                bids_placed_count += 1
                decision_status = "bid_placed_ml_approved"
            else:
                logger.info(f"ML prediction for job {job_to_bid_on.id}: {success_proba:.4f} (< threshold {ML_PROBABILITY_THRESHOLD}). Skipping bid.")
                decision_status = "skipped_ml_rejected"
            
            _log_autobid_attempt(db, profile_id, job_to_bid_on.id, job_to_bid_on.title, 
                                 status=decision_status, success_proba=success_proba, 
                                 bid_text=mock_bid_text if "bid_placed" in decision_status else None, 
                                 error_message=error_msg)

        logger.info(f"Autobidder run completed for profile {profile_id}. Bids placed: {bids_placed_count}")

    except Exception as e:
        logger.error(f"Unexpected error in run_autobid_for_profile for profile {profile_id}: {e}", exc_info=True)
        if db: # Log error to autobid_log if possible, even if general error
            _log_autobid_attempt(db, profile_id, uuid.uuid4(), "Unknown Job - Run Error", # job_id is fake here
                                 status="error_autobid_run", error_message=str(e))
    finally:
        if db:
            db.close()

# --- Mock/Placeholder Functions (to be replaced by actual implementation) ---
def _discover_potential_jobs(db: Session, profile: Profile) -> List[Job]:
    logger.warning("Using MOCKED job discovery. Replace with actual implementation.")
    try:
        # Fetch up to 5 jobs not yet bid on by this profile.
        # This is a placeholder. Real logic would involve keyword matching, filtering, etc.
        
        # Get IDs of jobs already bid on by this profile
        bid_on_job_ids = [bid.job_id for bid in db.query(Bid.job_id).filter(Bid.profile_id == profile.id).all()]
        
        jobs_query = db.query(Job)
        if bid_on_job_ids:
            jobs_query = jobs_query.filter(Job.id.notin_(bid_on_job_ids))
        
        jobs = jobs_query.limit(5).all()

        if not jobs and db.query(Job).count() == 0:
            logger.info("No jobs in DB, creating dummy jobs for autobidder testing.")
            # Use more specific UUIDs for dummy jobs if needed for consistency in tests
            dummy_job1_id = uuid.UUID("00000000-0000-0000-0000-000000000001")
            dummy_job2_id = uuid.UUID("00000000-0000-0000-0000-000000000002")
            
            # Check if dummy jobs exist before adding
            if not db.get(Job, dummy_job1_id):
                 db.add(Job(id=dummy_job1_id, title="Test Job 1 from Autobidder", description="Python FastAPI developer needed for a short project.", description_embedding=[0.1]*1536))
            if not db.get(Job, dummy_job2_id):
                 db.add(Job(id=dummy_job2_id, title="Test Job 2 from Autobidder", description="React frontend expert for web app.", description_embedding=[0.2]*1536))
            db.commit() # Commit dummy jobs
            # Re-query after adding
            jobs = db.query(Job).filter(Job.id.notin_(bid_on_job_ids)).limit(5).all()
            
        return jobs
    except SQLAlchemyError as e:
        logger.error(f"Error in MOCKED _discover_potential_jobs: {e}", exc_info=True)
        return []

# Note: _place_bid function was removed as its logic is now incorporated into logging within run_autobid_for_profile.
# If actual bid placement (e.g., creating a Bid record) is needed, it should be done there.

# This service is intended to be run as a background task (e.g., by a scheduler).
# If it needs to be exposed via an API endpoint (e.g., to trigger a run manually),
# that would be handled in a router, which would then call `run_autobid_for_profile`.
# The use of SessionLocal() here is for when this service is run independently.
# If called from an API route with a FastAPI Depends(get_db) session, that session should be passed down.
# For now, it's self-contained for background task execution.
# Consider refactoring to use AsyncSession if performance becomes an issue and underlying I/O can be async.
