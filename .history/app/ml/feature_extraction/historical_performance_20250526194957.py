import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, exc

# Assuming 'app' is in PYTHONPATH and models are structured as app.models.<model_name>
try:
    from app.models.bid import Bid
    from app.models.bid_outcome import BidOutcome
    # Profile model might be needed if we directly pass Profile objects or need profile-specific non-historical features here.
    # For now, only profile_id is used.
    # from app.models.profile import Profile
except ImportError:
    logging.warning("Could not import models directly from app.models. Ensure PYTHONPATH is set correctly or app is installed.")
    # Define dummy classes for type hinting if models can't be imported
    class Bid:
        id: Any = None
        profile_id: Any = None
        submitted_at: Any = None
    class BidOutcome:
        bid_id: Any = None
        is_success: Any = None

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def calculate_profile_success_rate(profile_id: str, db: Session, window_days: int = 30) -> Optional[float]:
    """
    Calculates the success rate for a given profile within a specified time window.

    Args:
        profile_id: The ID of the profile.
        db: SQLAlchemy Session object.
        window_days: The number of days to look back for calculating the success rate.

    Returns:
        The success rate as a float (e.g., 0.75 for 75%), or None if no bids were made
        or an error occurred.
    """
    if not isinstance(db, Session):
        logging.error(f"Invalid database session provided for profile_id: {profile_id}")
        return None

    start_date = datetime.utcnow() - timedelta(days=window_days)

    try:
        total_bids = db.query(func.count(Bid.id))\
                       .filter(Bid.profile_id == profile_id,
                               Bid.submitted_at >= start_date)\
                       .scalar()

        if total_bids is None: # Should be 0 if no records, but defensive check
            total_bids = 0
            
        if total_bids == 0:
            logging.info(f"No bids found for profile {profile_id} in the last {window_days} days. Success rate is None.")
            return None

        successful_bids = db.query(func.count(Bid.id))\
                            .join(BidOutcome, Bid.id == BidOutcome.bid_id)\
                            .filter(Bid.profile_id == profile_id,
                                    Bid.submitted_at >= start_date,
                                    BidOutcome.is_success == True)\
                            .scalar()
        
        if successful_bids is None: # Should be 0 if no records
             successful_bids = 0

        success_rate = successful_bids / total_bids
        logging.info(f"Profile {profile_id}, {window_days}d window: Total bids={total_bids}, Successful bids={successful_bids}, Success rate={success_rate:.2f}")
        return success_rate

    except exc.SQLAlchemyError as e:
        logging.error(f"Database error occurred while calculating success rate for profile {profile_id}: {e}")
        return None
    except Exception as e:
        logging.error(f"An unexpected error occurred while calculating success rate for profile {profile_id}: {e}")
        return None


def calculate_profile_bid_frequency(profile_id: str, db: Session, window_days: int = 30) -> Optional[int]:
    """
    Calculates the number of bids made by a profile within a specified time window.

    Args:
        profile_id: The ID of the profile.
        db: SQLAlchemy Session object.
        window_days: The number of days to look back.

    Returns:
        The total number of bids, or None if an error occurred.
    """
    if not isinstance(db, Session):
        logging.error(f"Invalid database session provided for profile_id: {profile_id} (bid frequency)")
        return None
        
    start_date = datetime.utcnow() - timedelta(days=window_days)
    try:
        total_bids = db.query(func.count(Bid.id))\
                       .filter(Bid.profile_id == profile_id,
                               Bid.submitted_at >= start_date)\
                       .scalar()
        
        logging.info(f"Profile {profile_id}, {window_days}d window: Total bids (frequency)={total_bids or 0}")
        return total_bids if total_bids is not None else 0

    except exc.SQLAlchemyError as e:
        logging.error(f"Database error occurred while calculating bid frequency for profile {profile_id}: {e}")
        return None
    except Exception as e:
        logging.error(f"An unexpected error occurred while calculating bid frequency for profile {profile_id}: {e}")
        return None


def get_profile_historical_features(profile_id: str, db: Session) -> Dict[str, Optional[float]]:
    """
    Generates a dictionary of historical performance features for a given profile.

    Args:
        profile_id: The ID of the profile.
        db: SQLAlchemy Session object.

    Returns:
        A dictionary containing historical features.
    """
    
    features: Dict[str, Optional[float]] = {
        "success_rate_7d": calculate_profile_success_rate(profile_id, db, window_days=7),
        "success_rate_30d": calculate_profile_success_rate(profile_id, db, window_days=30),
        "success_rate_90d": calculate_profile_success_rate(profile_id, db, window_days=90),
        "bid_frequency_7d": float(calculate_profile_bid_frequency(profile_id, db, window_days=7) or 0), # Cast to float for consistency
        "bid_frequency_30d": float(calculate_profile_bid_frequency(profile_id, db, window_days=30) or 0),
        "bid_frequency_90d": float(calculate_profile_bid_frequency(profile_id, db, window_days=90) or 0),
    }
    return features
