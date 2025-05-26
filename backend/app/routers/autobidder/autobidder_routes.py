# backend/app/routers/autobidder/autobidder_routes.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.ai_prompt import AIPrompt
from app.schemas.ai_prompt import PreviewResponse  # Import the new schema
from app.services.bid_generation_service import generate_bid_text_async


router = APIRouter(
    prefix="/prompts",
    tags=["Autobidder"],
)


@router.post("/{prompt_id}/preview",
             response_model=PreviewResponse)  # Use the new schema
def preview_prompt(
    prompt_id: int,
    db: Session = Depends(get_db),
):
    # Ищем промт в базе
    prompt = db.query(AIPrompt).filter(AIPrompt.id == prompt_id).first()
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")

    # Фейковый job description для примера
    fake_job = {
        "description": (
            "Ищем UX/UI‑дизайнера для редизайна SaaS‑продукта. "
            "Требуется опыт с Figma и понимание user flow."
        )
    }

    # Генерация текста через ваш сервис
    preview_text = generate_bid_text_async(
        fake_job,
        profile_id=prompt.profile_id,
        db=db,
    )

    return {"preview": preview_text}
