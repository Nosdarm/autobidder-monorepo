import os
import logging
import httpx
from datetime import datetime
from typing import Dict, Any, Optional, List

from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.database import SessionLocal # For creating new sessions if needed
from app.models.autobid_settings import AutobidSettings
from app.models.profile import Profile
from app.models.job import Job # Assuming Job model exists and is relevant
from app.models.profile_historical_stats import ProfileHistoricalStats # Added import
# from app.models.bid import Bid # Bid model might be needed if constructing a hypothetical bid object for features

from app.schemas.autobid import AutobidSettingsUpdate
# Assuming PredictionFeaturesInput is defined in ml_predictions_api or a shared schema location.
# For now, we'll construct the dictionary directly.

from app.ml.feature_extraction import (
    # generate_job_description_embedding, # No longer called directly, using pre-computed
    # generate_bid_text_embedding, # Omitted for now as per instructions
    generate_profile_features,
    generate_bid_temporal_features, # This expects a Bid-like object or adapted input
    # get_profile_historical_features, # No longer called directly, using pre-computed table
    # Individual featurizers if needed for bid_temporal_features:
    featurize_submission_time,
    featurize_bid_settings
)

# Configuration
ML_PREDICTION_ENDPOINT_URL = os.getenv("ML_PREDICTION_ENDPOINT_URL", "http://localhost:8000/ml/autobid/predict_success_proba")
ML_PROBABILITY_THRESHOLD = float(os.getenv("ML_PROBABILITY_THRESHOLD", "0.5")) # Default threshold

logger = logging.getLogger(__name__)
# Ensure logging is configured elsewhere in the app, or configure here if standalone
if not logger.hasHandlers():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(module)s - %(message)s')


def get_settings_for_profile(profile_id: str, db: Session) -> Optional[AutobidSettings]:
    settings = db.query(AutobidSettings).filter(AutobidSettings.profile_id == profile_id).first()
    if not settings:
        logger.info(f"No AutobidSettings found for profile {profile_id}, creating default settings.")
        settings = AutobidSettings(profile_id=profile_id) # Uses default values from model
        db.add(settings)
        try:
            db.commit()
            db.refresh(settings)
            logger.info(f"Default AutobidSettings created for profile {profile_id}.")
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating default AutobidSettings for profile {profile_id}: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="Could not create default autobid settings.")
    return settings


def update_settings_for_profile(profile_id: str, data: AutobidSettingsUpdate, db: Session) -> AutobidSettings:
    settings = db.query(AutobidSettings).filter(AutobidSettings.profile_id == profile_id).first()
    if not settings:
        raise HTTPException(status_code=404, detail="Autobid settings not found for this profile.")

    update_data = data.model_dump(exclude_unset=True) # Pydantic v2
    # For Pydantic v1: update_data = data.dict(exclude_unset=True)
    
    for key, value in update_data.items():
        setattr(settings, key, value)
    
    try:
        db.commit()
        db.refresh(settings)
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating AutobidSettings for profile {profile_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Could not update autobid settings.")
    return settings

# --- New ML Integration Logic ---

async def _get_ml_prediction(features: Dict[str, Any]) -> Optional[float]:
    """
    Helper function to get success probability prediction from the ML API.
    """
    payload = {"features": features}
    logger.debug(f"Sending features to ML Prediction API: {list(features.keys())}") # Log keys to avoid overly verbose logs
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client: # Added timeout
            response = await client.post(ML_PREDICTION_ENDPOINT_URL, json=payload)
            response.raise_for_status()  # Raise an exception for 4XX or 5XX status codes
            
            prediction_data = response.json()
            success_probability = prediction_data.get("success_probability")
            
            if success_probability is None:
                logger.error(f"ML API response did not contain 'success_probability'. Response: {prediction_data}")
                return None
            
            logger.info(f"Received success probability from ML API: {success_probability:.4f}")
            return float(success_probability)
            
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error occurred while calling ML Prediction API: {e.response.status_code} - {e.response.text}", exc_info=True)
        return None
    except httpx.RequestError as e:
        logger.error(f"Request error occurred while calling ML Prediction API: {e}", exc_info=True)
        return None
    except Exception as e:
        logger.error(f"An unexpected error occurred in _get_ml_prediction: {e}", exc_info=True)
        return None


def _assemble_features_for_prediction(
    job_to_bid_on: Job, 
    active_profile: Profile, 
    db_for_historical: Session
) -> Dict[str, Any]:
    """
    Assembles all necessary features for a given job and profile,
    matching the structure expected by the ML model.
    """
    prediction_input_features: Dict[str, Any] = {}

    # 1. Job Description Embedding (use pre-computed)
    job_emb_list = job_to_bid_on.description_embedding
    if job_emb_list is not None:
        for i, val in enumerate(job_emb_list):
            prediction_input_features[f'job_emb_{i}'] = val
    else: # Handle missing pre-computed embedding
        # Assuming embedding size is known, e.g., 1536 for text-embedding-ada-002
        # This dimension should ideally come from a config or model artifact.
        embedding_dim = 1536 # Placeholder for actual dimension
        for i in range(embedding_dim): 
            prediction_input_features[f'job_emb_{i}'] = 0.0
        logger.warning(f"Job ID {job_to_bid_on.id} has no precomputed description embedding. Filled with zeros.")

    # 2. Profile Features
    profile_feats = generate_profile_features(active_profile)
    if profile_feats:
        for key, value in profile_feats.items():
             prediction_input_features[f'profile_{key}'] = value if value is not None else 0 # Or other imputation

    # 3. Historical Features (fetch from ProfileHistoricalStats table)
    db_stats = db_for_historical.query(ProfileHistoricalStats).filter(
        ProfileHistoricalStats.profile_id == active_profile.id
    ).first()

    historical_feats_dict: Dict[str, Any] = {}
    stats_max_age_days = 1.5 # Allow stats to be up to 1.5 days old given daily 00:30 update

    if db_stats and (datetime.utcnow() - db_stats.last_updated_at).days < stats_max_age_days:
        historical_feats_dict = {
            "success_rate_7d": db_stats.success_rate_7d,
            "success_rate_30d": db_stats.success_rate_30d,
            "success_rate_90d": db_stats.success_rate_90d,
            "bid_frequency_7d": db_stats.bid_frequency_7d,
            "bid_frequency_30d": db_stats.bid_frequency_30d,
            "bid_frequency_90d": db_stats.bid_frequency_90d,
        }
        logger.debug(f"Found and using historical stats for profile {active_profile.id} from DB, last_updated_at: {db_stats.last_updated_at}")
    else:
        if db_stats:
            logger.warning(f"Historical stats for profile {active_profile.id} are too old (last_updated_at: {db_stats.last_updated_at}). Using defaults.")
        else:
            logger.warning(f"No historical stats found for profile {active_profile.id}. Using defaults.")
        # Define default values if stats are missing or too old
        default_stat_value = 0.0 # Using 0.0 as a neutral default for rates and frequencies
        historical_feats_dict = {
            "success_rate_7d": default_stat_value, "success_rate_30d": default_stat_value, "success_rate_90d": default_stat_value,
            "bid_frequency_7d": default_stat_value, "bid_frequency_30d": default_stat_value, "bid_frequency_90d": default_stat_value,
        }

    # Add to main features dictionary, prefixed as in assemble_dataset.py
    for key, value in historical_feats_dict.items():
         prediction_input_features[f'hist_{key}'] = value if value is not None else 0.0


    # 4. Current Bid Temporal Features
    # This requires constructing a "hypothetical" Bid object or passing individual components.
    # We'll use individual components derived from current context.
    current_time = datetime.utcnow()
    submission_time_feats = featurize_submission_time(current_time)
    if submission_time_feats:
         # Matches `safely_add_features(features, bid_temporal_features_dict, 'bid_temp')`
         # and assumes generate_bid_temporal_features combines settings and time.
         # Here we are doing it more granularly.
        for key, value in submission_time_feats.items():
            # The keys from featurize_submission_time are like "time_hour_of_day"
            # In assemble_dataset, they were prefixed with "bid_temp_"
            prediction_input_features[f'bid_temp_{key}'] = value if value is not None else -1


    # Bid Settings Features (using profile's default autobid settings as a proxy)
    # This is a simplification. Actual bid settings might be determined later or dynamically.
    # For now, let's assume some defaults or fetch from profile's autobid_settings.
    # `featurize_bid_settings` expects a dict like {"budget": float, "duration_weeks": int, "is_fixed_price": bool}
    # This snapshot is part of the Bid model. If we don't have a Bid object yet, we use defaults.
    # Let's assume default settings for prediction if not otherwise specified.
    # The `active_profile.autobid_settings` (if available) might store some preferences.
    # For this example, let's use some placeholder default values.
    # This part is highly dependent on how `bid_settings_snapshot` is handled for new bids.
    # If the autobidder has its own logic for determining these, that should be used.
    # For now, we'll use some defaults that `featurize_bid_settings` can process.
    mock_bid_settings_snapshot = {
        "budget": active_profile.autobid_settings.default_budget if hasattr(active_profile, 'autobid_settings') and active_profile.autobid_settings else 100.0, # Example
        "duration_weeks": active_profile.autobid_settings.default_duration if hasattr(active_profile, 'autobid_settings') and active_profile.autobid_settings else 4, # Example
        "is_fixed_price": active_profile.autobid_settings.default_is_fixed if hasattr(active_profile, 'autobid_settings') and active_profile.autobid_settings else False, # Example
    }
    bid_settings_feats = featurize_bid_settings(mock_bid_settings_snapshot)
    if bid_settings_feats:
        for key, value in bid_settings_feats.items():
            # Keys are like "setting_budget". Prefixed with "bid_temp_" in assemble_dataset.py
            prediction_input_features[f'bid_temp_{key}'] = value if value is not None else 0


    # 5. Omitted: Bid Text Embedding (as per instructions for this iteration)

    # Final check for any None values that might have slipped through (e.g. from dict updates)
    # This is important for XGBoost which doesn't like None.
    for key, value in prediction_input_features.items():
        if value is None:
            logger.warning(f"Feature '{key}' is None after assembly, defaulting to 0. This might indicate an issue in feature generation.")
            prediction_input_features[key] = 0 # Or np.nan if all features are float and model handles NaN

    return prediction_input_features


async def run_autobid_for_profile(profile_id: str):
    """
    Main autobidder logic for a given profile.
    Fetches jobs, gets ML predictions, and decides on bids.
    """
    db: Optional[Session] = None
    try:
        db = SessionLocal()
        active_profile = db.query(Profile).filter(Profile.id == profile_id).first()
        if not active_profile:
            logger.error(f"Profile {profile_id} not found. Skipping autobid run.")
            return
        
        if not active_profile.autobid_settings or not active_profile.autobid_settings.enabled:
            logger.info(f"Autobidder is disabled for profile {profile_id}. Skipping.")
            return

        logger.info(f"Running autobidder for profile: {active_profile.name} ({profile_id})")

        # --- 1. Job Discovery (Simplified/Mocked) ---
        # In a real system, this would involve fetching jobs from a feed, API, or scraper.
        # For this example, let's assume we get a list of Job objects.
        # This mock function should ideally return Job objects that are in the DB
        # or are constructed in a way that feature extractors can use them.
        potential_jobs: List[Job] = _discover_potential_jobs(db, active_profile)
        if not potential_jobs:
            logger.info(f"No potential jobs found for profile {profile_id} based on criteria.")
            return
        
        logger.info(f"Found {len(potential_jobs)} potential jobs for profile {profile_id}.")

        # --- 2. Process Each Job ---
        bids_placed_count = 0
        daily_bid_limit = active_profile.autobid_settings.daily_limit or float('inf')


        for job_to_bid_on in potential_jobs:
            if bids_placed_count >= daily_bid_limit:
                logger.info(f"Daily bid limit ({daily_bid_limit}) reached for profile {profile_id}. Stopping.")
                break

            logger.info(f"Processing job: {job_to_bid_on.title} (ID: {job_to_bid_on.id}) for profile {profile_id}")

            # --- a. Feature Collection ---
            # Note: _assemble_features_for_prediction needs a db session for historical features.
            # If SessionLocal() creates a new session each time, ensure it's managed correctly.
            # Here, we pass the existing 'db' session.
            prediction_input_features = _assemble_features_for_prediction(job_to_bid_on, active_profile, db)
            
            # Log a sample of features for debugging (optional)
            # logger.debug(f"Sample of features for job {job_to_bid_on.id}: {{k: prediction_input_features[k] for k in list(prediction_input_features)[:5]}}")

            # --- b. Get Prediction ---
            success_proba = await _get_ml_prediction(prediction_input_features)

            # --- c. Decision Making ---
            if success_proba is None:
                logger.warning(f"ML prediction failed or unavailable for job {job_to_bid_on.id}. Proceeding with fallback logic (not bidding).")
                # Fallback: For now, skip bid if ML fails. More sophisticated fallback could be added.
                decision = "skipped_ml_failure"
            elif success_proba >= ML_PROBABILITY_THRESHOLD:
                logger.info(f"ML prediction for job {job_to_bid_on.id}: {success_proba:.4f} (>= threshold {ML_PROBABILITY_THRESHOLD}). Proceeding with bid.")
                # --- d. Bid Placement (Simplified/Mocked) ---
                # Actual bid placement logic would go here.
                # This could involve using profile-specific templates, etc.
                # For now, just log and increment counter.
                _place_bid(db, active_profile, job_to_bid_on, success_proba) # Placeholder
                bids_placed_count += 1
                decision = "bid_placed_ml_approved"
            else:
                logger.info(f"ML prediction for job {job_to_bid_on.id}: {success_proba:.4f} (< threshold {ML_PROBABILITY_THRESHOLD}). Skipping bid.")
                decision = "skipped_ml_rejected"
            
            # --- e. Logging Decision ---
            # This log entry could be more structured, e.g., to a database or specific log file.
            logger.info(f"Autobidder decision for profile {profile_id}, job {job_to_bid_on.id}: {decision}, proba: {success_proba if success_proba is not None else 'N/A'}")

        logger.info(f"Autobidder run completed for profile {profile_id}. Bids placed: {bids_placed_count}")

    except Exception as e:
        logger.error(f"An unexpected error occurred in run_autobid_for_profile for profile {profile_id}: {e}", exc_info=True)
    finally:
        if db:
            db.close()


# --- Mock/Placeholder Functions (to be replaced by actual implementation) ---
def _discover_potential_jobs(db: Session, profile: Profile) -> List[Job]:
    """
    Placeholder for job discovery logic.
    Should return a list of Job objects relevant to the profile.
    """
    logger.warning("Using MOCKED job discovery. Replace with actual implementation.")
    # Example: fetch first 2 jobs from DB for testing, that are not related to this profile yet
    # This is highly simplistic and needs proper job feed/filtering logic.
    try:
        # A real query would filter based on profile keywords, categories, exclude seen jobs etc.
        jobs = db.query(Job).limit(2).all()
        if not jobs:
            # Create dummy jobs if none exist for testing purposes
            if db.query(Job).count() == 0: # Only if Job table is empty
                logger.info("No jobs in DB, creating dummy jobs for autobidder testing.")
                dummy_job1 = Job(id=str(uuid.uuid4()), title="Test Job 1 from Autobidder", description="Python FastAPI developer needed for a short project.")
                dummy_job2 = Job(id=str(uuid.uuid4()), title="Test Job 2 from Autobidder", description="React frontend expert for web app.")
                db.add_all([dummy_job1, dummy_job2])
                db.commit()
                return [dummy_job1, dummy_job2]
            return []
        return jobs
    except Exception as e:
        logger.error(f"Error in MOCKED _discover_potential_jobs: {e}", exc_info=True)
        return []

import uuid # Add uuid for dummy job creation

def _place_bid(db: Session, profile: Profile, job: Job, success_proba: float):
    """
    Placeholder for actual bid placement logic.
    This would interact with the bidding platform or create a Bid record in the local DB.
    """
    # This is a MOCK function. In a real system, this would place a bid.
    # The actual outcome (is_success) would be known later and recorded.
    # For logging the link between prediction and outcome, that would typically happen
    # when the BidOutcome record is created or in an analysis step that joins Bid data (with stored proba)
    # and BidOutcome data.
    # For now, we log the information available at the time of deciding to bid.
    logger.info(
        f"AUTOBID_DECISION_LOG: ProfileID={profile.id}, JobID={job.id}, "
        f"Decision=BID_PLACED_BY_ML, ML_Success_Probability={success_proba:.4f}"
    )
    logger.debug(f"MOCK_BID_DETAIL: Placing bid for job '{job.title}' (ID: {job.id}) by profile '{profile.name}' (ID: {profile.id}) with predicted success_proba: {success_proba:.4f}")
    
    # Example: If Bid record creation happened here, you might store success_proba
    # from app.models.bid import Bid # Import if not already
    # new_bid = Bid(
    #     id=str(uuid.uuid4()),
    #     profile_id=profile.id,
    #     job_id=job.id,
    #     amount=100.0, # Example amount
    #     # ... other bid fields, including ML prediction related ones if stored
    #     generated_bid_text=f"This is an auto-generated bid for {job.title}.",
    #     external_signals_snapshot={"ml_success_probability": success_proba} # Store the prediction
    # )
    # db.add(new_bid)
    # db.commit()
    # logger.info(f"MOCK: Bid record created with ID {new_bid.id}")
    pass
