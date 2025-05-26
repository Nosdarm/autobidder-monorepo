import json
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any

# Assuming 'app' is in PYTHONPATH and models are structured as app.models.<model_name>
try:
    from app.models.bid import Bid
except ImportError:
    logging.warning("Could not import Bid model directly from app.models. Ensure PYTHONPATH is set correctly or app is installed.")
    # Define dummy class for type hinting if Bid model can't be imported
    class Bid:
        bid_settings_snapshot: Optional[Any] = None
        submitted_at: Optional[datetime] = None

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Bid Settings Featurization ---
def featurize_bid_settings(settings_snapshot: Optional[Any]) -> Dict[str, Any]:
    """
    Featurizes the bid_settings_snapshot from a Bid object.
    Assumes a hypothetical structure: {"budget": float, "duration_weeks": int, "is_fixed_price": bool}

    Args:
        settings_snapshot: The bid_settings_snapshot field from a Bid object.
                           Expected to be a dictionary or a JSON string.

    Returns:
        A dictionary of extracted features.
    """
    features: Dict[str, Any] = {
        "setting_budget": 0.0,
        "setting_duration_weeks": 0,
        "setting_is_fixed_price": 0 # 0 for False/Not specified, 1 for True
    }

    if settings_snapshot is None:
        logging.debug("Bid settings snapshot is None.")
        return features

    data_to_parse = settings_snapshot
    if isinstance(settings_snapshot, str):
        try:
            data_to_parse = json.loads(settings_snapshot)
        except json.JSONDecodeError:
            logging.warning(f"Failed to parse bid_settings_snapshot JSON string: {settings_snapshot}")
            return features # Return default features if JSON is malformed

    if not isinstance(data_to_parse, dict):
        logging.warning(f"Bid settings snapshot is not a dictionary after potential parsing: {type(data_to_parse)}")
        return features

    features["setting_budget"] = float(data_to_parse.get("budget", 0.0))
    features["setting_duration_weeks"] = int(data_to_parse.get("duration_weeks", 0))
    features["setting_is_fixed_price"] = 1 if bool(data_to_parse.get("is_fixed_price", False)) else 0
    
    return features

# --- Submission Time Featurization ---
def featurize_submission_time(submitted_at: Optional[datetime]) -> Dict[str, int]:
    """
    Extracts temporal features from a bid's submission timestamp.

    Args:
        submitted_at: A datetime object representing when the bid was submitted.

    Returns:
        A dictionary of temporal features. Returns default/invalid values if submitted_at is None.
    """
    if submitted_at is None:
        logging.warning("Submitted_at timestamp is None. Returning default temporal features.")
        return {
            "time_hour_of_day": -1,
            "time_day_of_week": -1,
            "time_month": -1,
            "time_is_weekend": -1
        }

    return {
        "time_hour_of_day": submitted_at.hour,
        "time_day_of_week": submitted_at.weekday(),  # Monday=0, Sunday=6
        "time_month": submitted_at.month,
        "time_is_weekend": 1 if submitted_at.weekday() >= 5 else 0
    }

# --- Main Bid & Temporal Featurization Function ---
def generate_bid_temporal_features(bid: Bid) -> Dict[str, Any]:
    """
    Generates a dictionary of features for a given Bid object,
    combining bid settings and temporal features.

    Args:
        bid: A Bid object.

    Returns:
        A dictionary containing featurized bid and temporal data.
    """
    if not isinstance(bid, Bid): # Check if it's the actual model or dummy
        logging.warning("generate_bid_temporal_features received an object that is not a Bid instance.")
        # Return default/empty features structure
        bid_settings_features = featurize_bid_settings(None)
        temporal_features = featurize_submission_time(None)
    else:
        bid_settings_features = featurize_bid_settings(bid.bid_settings_snapshot)
        temporal_features = featurize_submission_time(bid.submitted_at)

    # Merge the dictionaries
    combined_features = {**bid_settings_features, **temporal_features}
    
    return combined_features
