from app.services.keyword_profile_service import tokenize, get_top_keywords_for_profile
from sqlalchemy.orm import Session

def calculate_keyword_affinity_score(
    db: Session,
    profile_id: str,
    job_description: str,
    max_bonus: float = 2.0
) -> float:
    top_keywords = get_top_keywords_for_profile(db, profile_id)
    job_words = set(tokenize(job_description))

    if not top_keywords:
        return 0.0

    matches = sum(1 for word in top_keywords if word in job_words)
    score_per_match = max_bonus / len(top_keywords)

    return round(matches * score_per_match, 2)
