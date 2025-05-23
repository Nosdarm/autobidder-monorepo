from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse
from app.auth.jwt import get_current_user
from app.services.ml_service import (
    predict_job_success,
    get_model_metrics,
    get_metrics_plot_html
)

router = APIRouter()


@router.post("/ml/predict")
def predict(job: dict, user_id: str = Depends(get_current_user)):
    return predict_job_success(job)


@router.get("/ml/metrics")
def get_metrics(user_id: str = Depends(get_current_user)):
    return get_model_metrics()


@router.get("/ml/metrics/plot", response_class=HTMLResponse)
def get_metrics_plot():
    return get_metrics_plot_html()
