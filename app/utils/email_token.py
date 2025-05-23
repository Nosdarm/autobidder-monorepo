from jose import jwt
from datetime import datetime, timedelta

SECRET_EMAIL_KEY = "your_secret_email_key"  # замени на .env
ALGORITHM = "HS256"

def create_email_token(user_id: str):
    expire = datetime.utcnow() + timedelta(hours=24)
    to_encode = {"user_id": user_id, "exp": expire}
    return jwt.encode(to_encode, SECRET_EMAIL_KEY, algorithm=ALGORITHM)

def verify_email_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_EMAIL_KEY, algorithms=[ALGORITHM])
        return payload.get("user_id")
    except Exception:
        return None
