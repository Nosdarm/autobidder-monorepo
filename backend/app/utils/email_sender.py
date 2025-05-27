import os
from email.message import EmailMessage
import aiosmtplib
from app.config import settings

async def send_email(to_email: str, subject: str, body: str):
    message = EmailMessage()
    message["From"] = str(settings.MAILTRAP_FROM)
    message["To"] = to_email
    message["Subject"] = subject
    message.set_content(body)

    await aiosmtplib.send(
        message,
        hostname=settings.MAILTRAP_HOST,
        port=settings.MAILTRAP_PORT,
        username=settings.MAILTRAP_USER,
        password=settings.MAILTRAP_PASS,
        use_tls=False,
    )
