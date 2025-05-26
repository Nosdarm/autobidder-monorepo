import os
import logging
import argparse
import pandas as pd
from sqlalchemy.orm import Session, joinedload
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta # Added for checking freshness of stats

# Assuming 'app' is in PYTHONPATH. Adjust if your project structure is different.
# This setup allows running the script as a module: python -m app.ml_model.assemble_dataset
try:
    from app.database import SessionLocal # Specific DB session provider
    from app.models.bid import Bid
    from app.models.job import Job
    from app.models.profile import Profile
    from app.models.bid_outcome import BidOutcome
    from app.models.profile_historical_stats import ProfileHistoricalStats # Added import
    from app.ml.feature_extraction import (
        # generate_job_description_embedding, # No longer called directly
        generate_bid_text_embedding,
        generate_profile_features,
        generate_bid_temporal_features,
        # get_profile_historical_features, # No longer called directly
        # Individual featurizers might be needed if combining features manually
        # get_text_embedding # If needed directly
    )
except ImportError as e:
    logging.error(f"Error importing application modules: {e}. Ensure PYTHONPATH is set correctly and all necessary modules exist.")
    # Fallback for local testing if script is not run as part of the 'app' package
    # This is not ideal for production but can help with isolated script development.
    # You might need to adjust sys.path or run `pip install -e .` in your project root.
    import sys
    sys.path.append(str(Path(__file__).resolve().parents[2])) # Add project root to path
    from app.database import SessionLocal
    from app.models.bid import Bid
    from app.models.job import Job
    from app.models.profile import Profile
    from app.models.bid_outcome import BidOutcome
    from app.models.profile_historical_stats import ProfileHistoricalStats # Added import
    from app.ml.feature_extraction import (
        # generate_job_description_embedding, # No longer called directly
        generate_bid_text_embedding,
        generate_profile_features,
        generate_bid_temporal_features,
        # get_profile_historical_features, # No longer called directly
    )


# 1. Setup Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


# 2. Fetch Data function
def fetch_data(db: Session) -> List[Bid]:
    """
    Queries the database to get a list of Bid objects with related data pre-loaded.
    Filters for bids that have at least one outcome.
    """
    logging.info("Fetching bids with outcomes from the database...")
    try:
        # Using joinedload for related objects to prevent N+1 queries.
        # Bid.outcomes is a list, so we filter for bids that have any outcomes.
        query = db.query(Bid).options(
            joinedload(Bid.job),
            joinedload(Bid.profile),
            joinedload(Bid.outcomes)  # Loads the list of outcomes for each bid
        ).filter(Bid.outcomes.any()) # Ensures only bids with at least one outcome are fetched

        bids = query.all()
        logging.info(f"Fetched {len(bids)} bids with outcomes.")
        return bids
    except Exception as e:
        logging.error(f"Error fetching data from database: {e}")
        return []


# 3. Process Bid to Features function
def process_bid_to_features(bid: Bid, db: Session) -> Optional[Dict[str, Any]]:
    """
    Processes a single Bid object into a flat dictionary of features.
    """
    if not bid.outcomes:
        logging.warning(f"Bid ID {bid.id} has no outcomes, skipping.")
        return None

    # Target Variable Logic: Assume the first outcome is the relevant one for simplicity.
    # In a real scenario, you might need more complex logic (e.g., latest outcome).
    outcome = bid.outcomes[0]
    target_is_success = int(outcome.is_success)

    # Feature Extraction
    # For embeddings, if they are pre-computed and stored, this would fetch them.
    job_embedding_list = bid.job.description_embedding # Use pre-computed embedding
    bid_text_embedding_list = generate_bid_text_embedding(bid) # This one is still generated on-the-fly
    
    profile_features_dict = generate_profile_features(bid.profile)
    bid_temporal_features_dict = generate_bid_temporal_features(bid)
    
    # Fetch historical features from ProfileHistoricalStats table
    db_stats = db.query(ProfileHistoricalStats).filter(
        ProfileHistoricalStats.profile_id == bid.profile_id
    ).first()

    historical_features_dict: Dict[str, Any] = {}
    stats_max_age_days = 1.5 # Consistent with autobidder_service.py

    if db_stats and (datetime.utcnow() - db_stats.last_updated_at).days < stats_max_age_days:
        historical_features_dict = {
            "success_rate_7d": db_stats.success_rate_7d,
            "success_rate_30d": db_stats.success_rate_30d,
            "success_rate_90d": db_stats.success_rate_90d,
            "bid_frequency_7d": db_stats.bid_frequency_7d,
            "bid_frequency_30d": db_stats.bid_frequency_30d,
            "bid_frequency_90d": db_stats.bid_frequency_90d,
        }
        logging.debug(f"Bid ID {bid.id}: Found and using historical stats for profile {bid.profile_id} from DB, last_updated_at: {db_stats.last_updated_at}")
    else:
        if db_stats: # Stats exist but are too old
            logging.warning(f"Bid ID {bid.id}: Historical stats for profile {bid.profile_id} are too old (last_updated_at: {db_stats.last_updated_at}). Using defaults.")
        else: # No stats found
            logging.warning(f"Bid ID {bid.id}: No historical stats found for profile {bid.profile_id}. Using defaults.")
        
        default_stat_value = 0.0 # Using 0.0 as a neutral default
        historical_features_dict = {
            "success_rate_7d": default_stat_value, "success_rate_30d": default_stat_value, "success_rate_90d": default_stat_value,
            "bid_frequency_7d": default_stat_value, "bid_frequency_30d": default_stat_value, "bid_frequency_90d": default_stat_value,
        }

    # Combine Features into a single flat dictionary
    features: Dict[str, Any] = {}

    # Embeddings (handle None and flatten)
    if job_embedding_list is not None:
        for i, val in enumerate(job_embedding_list):
            features[f'job_emb_{i}'] = val
    else: # Handle cases where pre-computed embedding might be None
        # Assuming embedding size is known, e.g., 1536 for text-embedding-ada-002
        # This dimension should ideally come from a config or model artifact.
        embedding_dim = 1536 # Placeholder for actual dimension
        for i in range(embedding_dim): 
            features[f'job_emb_{i}'] = 0.0
        logging.warning(f"Bid ID {bid.id}, Job ID {bid.job_id}: Job description_embedding is None. Filled with zeros.")

    if bid_text_embedding_list:
        for i, val in enumerate(bid_text_embedding_list):
            features[f'bid_emb_{i}'] = val
    else:
        pass

    # Other feature groups (handle None from group, or keys within group)
    def safely_add_features(base_dict, new_features_dict, prefix):
        if new_features_dict:
            for key, value in new_features_dict.items():
                base_dict[f'{prefix}_{key}'] = value if value is not None else None # or some other placeholder like 0 or -1
        else: # if the whole dict is None
             logging.warning(f"Feature group {prefix} is None for Bid ID {bid.id}")


    safely_add_features(features, profile_features_dict, 'profile')
    safely_add_features(features, bid_temporal_features_dict, 'bid_temp')
    safely_add_features(features, historical_features_dict, 'hist')
    
    # Add Bid ID and Profile ID for traceability if needed, though usually not for training
    features['bid_id_trace'] = bid.id 
    features['profile_id_trace'] = bid.profile_id

    # Add the target variable
    features['target_is_success'] = target_is_success
    
    return features


# 4. Main function
def main():
    """
    Main function to orchestrate dataset assembly.
    """
    # Argument Parser
    parser = argparse.ArgumentParser(description="Assemble dataset for ML model training.")
    parser.add_argument(
        "--output",
        type=str,
        required=True,
        help="Output file path for the dataset (e.g., data/training_dataset.parquet)"
    )
    # Add more arguments if needed (e.g., date ranges, specific profile IDs)
    # parser.add_argument("--start-date", type=str, help="Start date for bid data (YYYY-MM-DD)")
    # parser.add_argument("--end-date", type=str, help="End date for bid data (YYYY-MM-DD)")

    args = parser.parse_args()
    output_path = Path(args.output)

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    logging.info(f"Starting dataset assembly. Output will be saved to: {output_path}")

    db: Optional[Session] = None
    try:
        db = SessionLocal()
        bids_with_outcomes = fetch_data(db)

        if not bids_with_outcomes:
            logging.info("No bids with outcomes found. Exiting.")
            return

        all_features_list: List[Dict[str, Any]] = []
        for i, bid in enumerate(bids_with_outcomes):
            logging.info(f"Processing bid {i+1}/{len(bids_with_outcomes)}: ID {bid.id}")
            feature_dict = process_bid_to_features(bid, db)
            if feature_dict:
                all_features_list.append(feature_dict)
        
        if not all_features_list:
            logging.info("No features could be processed. Exiting.")
            return

        logging.info("Converting feature list to DataFrame...")
        df = pd.DataFrame(all_features_list)

        # Handle Missing Values in DataFrame (Post-assembly)
        # For embeddings, 0 is a common fillna value. For other features, -1 or mean/median might be better.
        # This is a simple strategy; more sophisticated imputation might be needed.
        # Example: Get embedding dimension (e.g. from a config or first valid embedding)
        # Determine expected embedding columns and fill only those with 0, others with -1.
        # For now, a general fillna(0) is used.
        logging.info(f"DataFrame shape before fillna: {df.shape}")
        df.fillna(0, inplace=True) # Fill all NaNs with 0 for simplicity.
        logging.info(f"DataFrame shape after fillna: {df.shape}")


        # Save DataFrame
        if output_path.suffix == ".parquet":
            df.to_parquet(output_path, index=False)
            logging.info(f"Dataset saved successfully to {output_path} (Parquet format).")
        elif output_path.suffix == ".csv":
            df.to_csv(output_path, index=False)
            logging.info(f"Dataset saved successfully to {output_path} (CSV format).")
        else:
            logging.error(f"Unsupported output file format: {output_path.suffix}. Please use .parquet or .csv.")
            return

    except Exception as e:
        logging.error(f"An error occurred during dataset assembly: {e}", exc_info=True)
    finally:
        if db:
            logging.info("Closing database session.")
            db.close()

if __name__ == "__main__":
    main()
