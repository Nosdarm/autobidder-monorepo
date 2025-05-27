import os # Added for MODEL_RELOAD_SECRET
import logging
import joblib
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional
import uuid # Added for request_id
import hashlib # Added for feature hashing
import json # Added for feature hashing

from fastapi import APIRouter, HTTPException, Depends, Request # Added Request
from pydantic import BaseModel

# Assuming app.config.get_settings() is the way to get app settings
# This might need adjustment based on actual config management.
# For now, let's hardcode a default path and make a note to use settings.
# from app.config import get_settings # Example
# settings = get_settings()
# MODEL_PATH_FROM_CONFIG = settings.MODEL_PATH 

# Placeholder for model path - should come from config
# MODEL_PATH_STR = os.getenv("MODEL_PATH", "app/ml_model/artifacts/model.joblib")
import logging # Moved logging import
from fastapi import APIRouter, HTTPException, Depends, Request

# Import Pydantic Schemas from app.schemas.ml
from app.schemas.ml import PredictionFeaturesInput, PredictionResponse, MetricsResponse # Added MetricsResponse
# Import the service functions
from app.services.ml_service import (
    load_model_on_startup, # Can be called from main.py or here on app startup
    predict_success_proba_service,
    get_model_metrics as get_model_metrics_service, # Renamed to avoid conflict
    get_metrics_plot_html as get_metrics_plot_html_service # Renamed
)
from app.auth.jwt import get_current_user # For protected routes

logger = logging.getLogger(__name__)
# logging.basicConfig should be configured in main.py or a logging config file.
# logging.basicConfig(level=logging.INFO)

# Main router for ML predictions
router = APIRouter(
    prefix="/ml",
    tags=["Machine Learning Predictions"]
)

# Internal router for model management (e.g., reload)
internal_router = APIRouter(
    prefix="/ml/internal",
    tags=["Machine Learning Internal Utilities"],
    include_in_schema=False # Typically hidden from public API docs
)

# Shared secret for sensitive operations like model reloading
MODEL_RELOAD_SECRET = os.getenv("MODEL_RELOAD_SECRET", "your-super-secret-key-for-model-reload")


@router.post("/predict_success_proba", response_model=PredictionResponse) # Changed path to be more generic if needed
async def predict_success_proba_endpoint(
    input_data: PredictionFeaturesInput,
    # current_user: str = Depends(get_current_user) # Optional: Protect endpoint
):
    """
    Predicts the success probability based on input features using the ML service.
    """
    logger.info(f"Received prediction request for features: {input_data.features.keys()}") # Basic logging
    try:
        # Call the service function to get the prediction
        prediction_result = await predict_success_proba_service(input_data=input_data)
        return prediction_result
    except HTTPException as e:
        # Re-raise HTTPException from the service (e.g., model not loaded, prediction error)
        raise e
    except Exception as e:
        # Catch any other unexpected errors
        logger.error(f"Unexpected error during prediction: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

@internal_router.post("/reload_model", summary="Reloads the ML model via service")
async def reload_model_endpoint(request: Request):
    """
    Internal endpoint to trigger a reload of the ML model.
    Protected by a shared secret.
    Calls the load_model_on_startup function from the service.
    """
    logger.info("Received request to reload ML model via internal endpoint.")
    
    actual_secret = request.headers.get("X-Reload-Secret")
    if not MODEL_RELOAD_SECRET or actual_secret != MODEL_RELOAD_SECRET:
        logger.warning("Forbidden attempt to reload model: Invalid or missing reload secret.")
        raise HTTPException(status_code=403, detail="Forbidden: Invalid or missing reload secret.")
    
    try:
        # Call the model loading function from the service
        # This assumes load_model_on_startup in the service updates the global MODEL state there.
        load_model_on_startup() 
        logger.info("ML model reload triggered successfully via service.")
        # Note: To get previous/current status, the service function would need to return it.
        return {"message": "ML model reload triggered via service."}
    except Exception as e:
        logger.error(f"Error during model reload via service: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to reload model via service: {str(e)}")

# Endpoints for metrics and plots, now calling service functions
@router.get("/metrics", response_model=MetricsResponse)
def get_metrics_endpoint(user_id: str = Depends(get_current_user)): # Protected
    logger.info(f"User {user_id} requesting model metrics.")
    try:
        metrics = get_model_metrics_service()
        return metrics
    except Exception as e:
        logger.error(f"Error fetching model metrics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Could not fetch model metrics.")

@router.get("/metrics/plot", response_class=HTMLResponse) # HTMLResponse from fastapi.responses
def get_metrics_plot_endpoint(user_id: str = Depends(get_current_user)): # Protected
    from fastapi.responses import HTMLResponse # Ensure HTMLResponse is imported
    logger.info(f"User {user_id} requesting metrics plot.")
    try:
        html_content = get_metrics_plot_html_service()
        return HTMLResponse(content=html_content)
    except Exception as e:
        logger.error(f"Error generating metrics plot: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Could not generate metrics plot.")

# Note: The original /ml/predict, /ml/metrics, /ml/metrics/plot routes from
# backend/app/routers/ml/ml_routes.py are now adapted to use the service.
# The /autobid/predict_success_proba path from the app/ version is used for the main prediction.
# If the older /ml/predict path is still needed, it can be added similarly,
# possibly calling a different service function or the same one with different input mapping.
