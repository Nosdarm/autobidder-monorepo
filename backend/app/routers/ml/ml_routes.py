from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse
from app.auth.jwt import get_current_user
from app.schemas.ml import PredictionResponse, MetricsResponse
# Import schemas
from app.services.ml_service import (
    predict_job_success,
    get_model_metrics,
    get_metrics_plot_html
)

router = APIRouter()


# Add response_model
@router.post("/ml/predict", response_model=PredictionResponse)
def predict(job: dict, user_id: str = Depends(get_current_user)):
    return predict_job_success(job)


# Add response_model
@router.get("/ml/metrics", response_model=MetricsResponse)
def get_metrics(user_id: str = Depends(get_current_user)):
    return get_model_metrics()


@router.get("/ml/metrics/plot", response_class=HTMLResponse)
def get_metrics_plot():
    return get_metrics_plot_html()
