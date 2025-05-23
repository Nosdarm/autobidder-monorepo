import re
from collections import Counter
from sqlalchemy.orm import Session
from app.models.autobid_log import AutobidLog

# базовые стоп-слова — можно расширить
STOPWORDS = set(["the", "and", "for", "with", "you", "your", "this", "that", "are", "have", "need", "job", "project", "looking", "like"])

def tokenize(text: str) -> list[str]:
    tokens = re.findall(r'\b\w+\b', text.lower())
    return [t for t in tokens if t not in STOPWORDS and len(t) > 2]

def get_top_keywords_for_profile(db: Session, profile_id: str, limit: int = 10) -> list[str]:
    logs = db.query(AutobidLog).filter_by(profile_id=profile_id, status="success").all()

    all_words = []
    for log in logs:
        all_words += tokenize(log.job_title)
        all_words += tokenize(log.bid_text)

    counter = Counter(all_words)
    return [word for word, _ in counter.most_common(limit)]
