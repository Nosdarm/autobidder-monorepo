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
# Using a default path for now, assuming `app` is the root for this path.
MODEL_PATH_STR = "app/ml_model/artifacts/model.joblib" # Relative to project root where FastAPI app runs

MODEL: Optional[Any] = None
MODEL_PATH = Path(MODEL_PATH_STR)
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO) # Ensure logger outputs messages

def load_model_on_startup():
    """
    Loads the serialized ML model from disk into the global MODEL variable.
    This function is intended to be called during FastAPI application startup.
    """
    global MODEL
    if MODEL_PATH.exists() and MODEL_PATH.is_file():
        try:
            MODEL = joblib.load(MODEL_PATH)
            logger.info(f"ML Model loaded successfully from {MODEL_PATH}")
        except Exception as e:
            logger.error(f"Error loading model from {MODEL_PATH}: {e}", exc_info=True)
            MODEL = None # Ensure model is None if loading fails
    else:
        logger.warning(f"Model file not found at {MODEL_PATH}. Prediction endpoint will be inactive.")
        MODEL = None

# Pydantic Schemas
class PredictionFeaturesInput(BaseModel):
    # Expects a flat dictionary of feature_name: value pairs.
    # The client must ensure all features used during training are provided.
    features: Dict[str, Any] 
    # Example for more specific typing, if known:
    # profile_experience_level: Optional[int] = None
    # job_emb_0: Optional[float] = None
    # ... and so on for all features

class PredictionResponse(BaseModel):
    success_probability: float
    model_info: Optional[str] = None

# Router Definition
router = APIRouter(
    prefix="/ml", 
    tags=["Machine Learning Predictions"] # Main tag for user-facing predictions
)

# Internal router for utility endpoints like model reload
internal_router = APIRouter(
    prefix="/ml/internal", # Differentiated prefix
    tags=["Machine Learning Internal Utilities"], # Separate tag
    include_in_schema=False # Hide from public OpenAPI docs
)

MODEL_RELOAD_SECRET = os.getenv("MODEL_RELOAD_SECRET", "your-super-secret-key") # Ensure this matches scheduler_setup.py

@internal_router.post("/reload_model", summary="Reloads the ML model")
async def reload_model_endpoint(request: Request):
    """
    Internal endpoint to trigger a reload of the ML model.
    Protected by a shared secret.
    """
    logger.info("Received request to reload ML model.")
    
    # Basic shared secret authentication
    actual_secret = request.headers.get("X-Reload-Secret")
    if not MODEL_RELOAD_SECRET or not actual_secret or actual_secret != MODEL_RELOAD_SECRET:
        logger.warning(f"Forbidden attempt to reload model. Secret mismatch or not provided. Provided: '{actual_secret}'")
        raise HTTPException(status_code=403, detail="Forbidden: Invalid or missing reload secret.")
    
    previous_model_load_status = "Loaded" if MODEL is not None else "Not loaded/Error"
    logger.info(f"Current model status before reload attempt: {previous_model_load_status}")
    
    load_model_on_startup() # Re-run the existing model loading logic
    
    current_model_load_status = "Loaded" if MODEL is not None else "Not loaded/Error"
    logger.info(f"Model status after reload attempt: {current_model_load_status}")
    
    return {"message": f"ML model reload triggered. Previous status: {previous_model_load_status}. Current status: {current_model_load_status}."}


@router.post("/autobid/predict_success_proba", response_model=PredictionResponse)
async def predict_success_proba(input_data: PredictionFeaturesInput):
    """
    Predicts the success probability for a bid based on input features.
    """
    global MODEL
    request_id = str(uuid.uuid4())
    logger.info(f"Request ID: {request_id} - Received prediction request.")

    if MODEL is None:
        logger.error(f"Request ID: {request_id} - Prediction attempt while model is not loaded.")
        raise HTTPException(status_code=503, detail="Model not loaded. Prediction service unavailable.")

    try:
        # Log a summary of input features
        try:
            features_json = json.dumps(input_data.features, sort_keys=True).encode('utf-8')
            features_hash = hashlib.sha256(features_json).hexdigest()
            logger.info(f"Request ID: {request_id} - Input features hash: {features_hash}. Number of features: {len(input_data.features)}")
        except Exception as e:
            logger.error(f"Request ID: {request_id} - Error generating features summary: {e}")
            # Continue without features summary if hashing fails, or handle as critical error

        # Convert input_data.features (dict) to DataFrame
        # Critical step: Feature names and order must match the training data.
        
        # If the model object (e.g., scikit-learn pipeline or XGBoost model) 
        # stores feature names used during training, use them for robust ordering.
        if hasattr(MODEL, 'feature_names_in_'):
            # Create a list of values in the order of feature_names_in_
            # Handles cases where input_data.features might have extra keys or wrong order.
            feature_values = []
            missing_features = []
            for name in MODEL.feature_names_in_:
                value = input_data.features.get(name)
                if value is None:
                    # This is a simple way to handle missing. Depending on the model,
                    # it might expect NaN (float types) or a specific placeholder.
                    # For now, if a feature expected by model is None in input, it's an issue.
                    missing_features.append(name)
                feature_values.append(value)
            
            if missing_features:
                logger.warning(f"Request ID: {request_id} - Missing required features in input: {missing_features} for model expecting {MODEL.feature_names_in_}. Imputing with 0.")
                # Impute with 0 for simplicity, assuming features are numeric.
                # This should align with how NaNs were handled pre-training or by the model itself.
                # A better approach might be to raise an error or use a pre-defined imputation strategy.
                for i, name in enumerate(MODEL.feature_names_in_):
                    if name in missing_features: # if feature_values[i] is None
                         feature_values[i] = 0 # Or np.nan if model handles it
                # raise HTTPException(status_code=400, detail=f"Missing required features: {missing_features}")

            df_input = pd.DataFrame([feature_values], columns=MODEL.feature_names_in_)
            logger.debug(f"Request ID: {request_id} - Input DataFrame for prediction (using feature_names_in_): \n{df_input.head()}")

        elif hasattr(MODEL, 'feature_names'): # Some models like older XGBoost might use this
            feature_values = [input_data.features.get(name) for name in MODEL.feature_names]
            if any(val is None for val in feature_values): # Simplified check
                 # As above, impute with 0 or handle more gracefully
                logger.warning(f"Request ID: {request_id} - Some features were None, filling with 0. Model features: {MODEL.feature_names}")
                feature_values = [0 if val is None else val for val in feature_values]
            df_input = pd.DataFrame([feature_values], columns=MODEL.feature_names)
            logger.debug(f"Request ID: {request_id} - Input DataFrame for prediction (using feature_names): \n{df_input.head()}")
            
        else:
            # Fallback: less robust, assumes input_data.features keys are in correct order
            # and match exactly what the model was trained on.
            # This path is taken if the model object doesn't store feature names.
            # It's recommended to save and load feature names separately in such cases.
            logger.warning(f"Request ID: {request_id} - Model does not have 'feature_names_in_' or 'feature_names'. Assuming input dict is correctly ordered.")
            df_input = pd.DataFrame([input_data.features])
            logger.debug(f"Request ID: {request_id} - Input DataFrame for prediction (direct from dict): \n{df_input.head()}")

        # Make prediction
        # predict_proba usually returns probabilities for each class [class_0_proba, class_1_proba]
        proba_array = MODEL.predict_proba(df_input)
        
        # Assuming class 1 is the 'success' class
        success_proba = float(proba_array[0, 1]) 
        
        logger.info(f"Request ID: {request_id} - Prediction successful. Success probability: {success_proba:.4f}")
        return PredictionResponse(
            success_probability=success_proba,
            model_info=f"Using model: {MODEL_PATH.name}" # Consider adding model version/timestamp if available
        )

    except Exception as e:
        logger.error(f"Request ID: {request_id} - Error during prediction: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")
