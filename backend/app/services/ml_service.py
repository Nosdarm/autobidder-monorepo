import logging
import joblib
import pandas as pd
from pathlib import Path
from typing import Dict, Any, Optional
import uuid
import hashlib
import json

from fastapi import HTTPException

# Schemas are now imported from app.schemas.ml, but since this is a service,
# it will take Pydantic models (schemas) as input and return them, or ORM models.
from app.schemas.ml import PredictionFeaturesInput, PredictionResponse
from app.config import settings

# Global model variable and path (these should ideally be managed by a class or app state)
MODEL_PATH_STR = settings.MODEL_PATH # Ensure this path is correct relative to project root
MODEL: Optional[Any] = None
MODEL_PATH = Path(MODEL_PATH_STR)

logger = logging.getLogger(__name__)
# BasicConfig should be called once, preferably in main.py or a config module.
# logging.basicConfig(level=logging.INFO) # Comment out if configured elsewhere

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

async def predict_success_proba_service(input_data: PredictionFeaturesInput) -> PredictionResponse:
    """
    Predicts the success probability for a bid based on input features.
    (Moved from router, made async if any internal I/O becomes async)
    """
    global MODEL # Access the globally loaded model
    request_id = str(uuid.uuid4()) # For logging/tracing
    logger.info(f"Request ID: {request_id} - Received prediction request in service.")

    if MODEL is None:
        logger.error(f"Request ID: {request_id} - Prediction attempt while model is not loaded.")
        # Consider if reloading here is an option, or if it should strictly fail.
        # load_model_on_startup() # Potentially try to reload, but could be slow.
        # if MODEL is None: # Check again after trying to reload
        raise HTTPException(status_code=503, detail="Model not loaded. Prediction service unavailable.")

    try:
        # Log a summary of input features (optional, for debugging)
        try:
            features_json = json.dumps(input_data.features, sort_keys=True).encode('utf-8')
            features_hash = hashlib.sha256(features_json).hexdigest()
            logger.info(f"Request ID: {request_id} - Input features hash: {features_hash}. Number of features: {len(input_data.features)}")
        except Exception as e:
            logger.error(f"Request ID: {request_id} - Error generating features summary: {e}")

        # Convert input_data.features (dict) to DataFrame
        # This part is critical and depends heavily on the model's expected input format.
        if hasattr(MODEL, 'feature_names_in_'):
            feature_values = []
            missing_features = []
            for name in MODEL.feature_names_in_:
                value = input_data.features.get(name)
                if value is None:
                    missing_features.append(name)
                feature_values.append(value)
            
            if missing_features:
                logger.warning(f"Request ID: {request_id} - Missing required features: {missing_features}. Imputing with 0.")
                for i, name in enumerate(MODEL.feature_names_in_):
                    if name in missing_features:
                         feature_values[i] = 0 # Or np.nan, or other imputation
            df_input = pd.DataFrame([feature_values], columns=MODEL.feature_names_in_)
        elif hasattr(MODEL, 'feature_names'): # Older XGBoost, etc.
            feature_values = [input_data.features.get(name) for name in MODEL.feature_names]
            if any(val is None for val in feature_values):
                logger.warning(f"Request ID: {request_id} - Some features were None, filling with 0.")
                feature_values = [0 if val is None else val for val in feature_values]
            df_input = pd.DataFrame([feature_values], columns=MODEL.feature_names)
        else:
            logger.warning(f"Request ID: {request_id} - Model does not store feature names. Assuming input dict is correctly ordered.")
            df_input = pd.DataFrame([input_data.features])
        
        logger.debug(f"Request ID: {request_id} - Input DataFrame for prediction: \n{df_input.to_string()}")

        # Make prediction
        proba_array = MODEL.predict_proba(df_input)
        success_proba = float(proba_array[0, 1]) # Assuming class 1 is 'success'
        score = success_proba * 100
        
        logger.info(f"Request ID: {request_id} - Prediction successful. Success probability: {success_proba:.4f}, Score: {score:.2f}")
        
        return PredictionResponse(
            success_probability=success_proba,
            score=score,
            model_info=f"Using model: {MODEL_PATH.name}" # Or more detailed model versioning
        )

    except Exception as e:
        logger.error(f"Request ID: {request_id} - Error during prediction: {e}", exc_info=True)
        # Re-raise as HTTPException or a custom service exception
        raise HTTPException(status_code=500, detail=f"Prediction error in service: {str(e)}")

# Placeholder functions from the original ml_service.py, adapt as needed
def get_model_metrics(): # This would likely load metrics from a file or a monitoring system
    logger.info("Fetching model metrics (placeholder).")
    return {
        "accuracy": 0.92, # Example value
        "f1_score": 0.89,  # Example value
        "recall": 0.91    # Example value
    }

def get_metrics_plot_html(): # This could generate an HTML plot or return a pre-generated one
    logger.info("Generating metrics plot HTML (placeholder).")
    return "<html><body><h1>Metrics Plot</h1><p>График пока не готов 😄 (Service version)</p></body></html>"

# The reload_model logic is more of an operational endpoint, typically called by an admin or a scheduler.
# It might stay in the router (ml_routes.py internal_router) or be part_of a dedicated AdminService.
# For now, load_model_on_startup is the primary mechanism for the service to get the model.
# If the service itself needs to trigger reloads without an HTTP request, that's a different pattern.

# Example of how a service class structure might look (optional for this refactoring if not already used)
# class MLService:
#     def __init__(self, model_path: str = MODEL_PATH_STR):
#         self.model_path = Path(model_path)
#         self.model: Optional[Any] = None
#         self._load_model() # Load on instantiation

#     def _load_model(self):
#         # Similar to load_model_on_startup but assigns to self.model
#         if self.model_path.exists():
#             try:
#                 self.model = joblib.load(self.model_path)
#                 logger.info(f"MLService: Model loaded from {self.model_path}")
#             except Exception as e:
#                 logger.error(f"MLService: Error loading model: {e}")
#                 self.model = None
#         else:
#             logger.warning(f"MLService: Model file not found at {self.model_path}")
#             self.model = None
    
#     async def predict(self, input_data: PredictionFeaturesInput) -> PredictionResponse:
#         # Uses self.model instead of global MODEL
#         if self.model is None:
#             raise HTTPException(status_code=503, detail="MLService: Model not loaded.")
#         # ... rest of the prediction logic using self.model ...
#         # This async keyword here would be if, for example, feature fetching was async
        
#         # For now, let's assume the core prediction is CPU-bound and synchronous
#         # but can be called from an async route handler.
#         # If using a class, the method might not need to be async itself unless it does I/O.
#         pass


# Dependency provider for the service function (if not using a class)
# No database session needed for this version of predict_success_proba_service
# async def get_ml_prediction_service(): # This is a bit trivial if the service is just functions
#     return predict_success_proba_service # Returns the function itself

# If using a class-based service:
# ml_service_instance = MLService() # Global instance, or manage lifetime with FastAPI startup/shutdown
# async def get_ml_service() -> MLService:
#    return ml_service_instance
