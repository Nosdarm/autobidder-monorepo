# This file marks app/ml as a Python package and re-exports key components.

from . import feature_extraction

from .feature_extraction import (
    generate_job_description_embedding,
    generate_bid_text_embedding,
    generate_profile_features,
    generate_bid_temporal_features,
    get_profile_historical_features
)

__all__ = [
    "feature_extraction",
    "generate_job_description_embedding",
    "generate_bid_text_embedding",
    "generate_profile_features",
    "generate_bid_temporal_features",
    "get_profile_historical_features",
]
