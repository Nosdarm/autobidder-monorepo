from pydantic import BaseModel, Field
from typing import Dict, Any, Optional # Added Dict, Any, Optional


# Schema for ML model prediction input
class PredictionFeaturesInput(BaseModel):
    features: Dict[str, Any]


class PredictionResponse(BaseModel):
    success_probability: Optional[float] = Field(None, description="Predicted success probability for the bid/job") # Made Optional
    score: Optional[float] = Field(None, description="Predicted score for the job success") # Made Optional
    comment: Optional[str] = Field(None, description="Comment or reason for the prediction") # Made Optional
    model_info: Optional[str] = Field(None, description="Information about the model used for prediction") # Added model_info


class MetricsResponse(BaseModel):
    accuracy: float = Field(..., description="Model accuracy")
    f1_score: float = Field(  # Using alias in case key has underscore
        ..., alias="f1_score", description="Model F1 score"
    )
    recall: float = Field(..., description="Model recall")

    # If these keys in the dictionary exactly match the field names
    # (e.g. "f1_score"), then `alias` is not strictly necessary but can be
    # good for explicitness.
    # Pydantic V2 uses model_config for from_attributes (ORM mode) but
    # these are from dicts. No specific config needed if field names
    # match dict keys.
    class Config:
        # For Pydantic V2, if we were converting from an object with
        # attributes that don't match field names, or need other specific
        # behaviors:
        # from_attributes = True # If it were from ORM
        # populate_by_name = True # To allow using field names even if
        # aliases are defined for serialization
        pass  # No special config needed for simple dicts with matching keys

# For GET /ml/charts/{chart_type}, if it were to return structured data:
# class ChartResponse(BaseModel):
#     chart_type: str
#     chart_data: dict # or a more specific Pydantic model for chart data
#     # or image_url: str
# However, the current implementation /ml/metrics/plot returns HTML directly.
