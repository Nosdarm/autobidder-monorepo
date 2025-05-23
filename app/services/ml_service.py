from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse
from app.auth.jwt import get_current_user

router = APIRouter()

@router.post("/ml/predict")
def predict(job: dict, user_id: str = Depends(get_current_user)):
    from app.services.ml_service import predict_job_success
    return predict_job_success(job)

@router.get("/ml/metrics")
def get_metrics(user_id: str = Depends(get_current_user)):
    from app.services.ml_service import get_model_metrics
    return get_model_metrics()

@router.get("/ml/metrics/plot", response_class=HTMLResponse)
def get_metrics_plot():
    from app.services.ml_service import get_metrics_plot_html
    return get_metrics_plot_html()# app/services/ml_service.py

def predict_job_success(job: dict):
    # Пример простой логики — ты можешь заменить на свою модель
    title = job.get("title", "").lower()
    budget = job.get("budget", 0)

    if "figma" in title and budget > 500:
        score = 0.9
    elif "dashboard" in title:
        score = 0.75
    else:
        score = 0.6

    return {
        "score": round(score, 2),
        "comment": "Оценка на основе заголовка и бюджета"
    }


def get_model_metrics():
    return {
        "accuracy": 0.92,
        "f1_score": 0.89,
        "recall": 0.91
    }

def get_metrics_plot_html():
    return "<html><body><h1>Metrics Plot</h1><p>График пока не готов 😄</p></body></html>"
