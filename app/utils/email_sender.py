import os
from email.message import EmailMessage
import aiosmtplib
from dotenv import load_dotenv

load_dotenv()

async def send_email(to_email: str, subject: str, body: str):
    message = EmailMessage()
    message["From"] = os.getenv("MAILTRAP_FROM")
    message["To"] = to_email
    message["Subject"] = subject
    message.set_content(body)

    await aiosmtplib.send(
        message,
        hostname=os.getenv("MAILTRAP_HOST"),
        port=int(os.getenv("MAILTRAP_PORT")),
        username=os.getenv("MAILTRAP_USER"),
        password=os.getenv("MAILTRAP_PASS"),
        use_tls=False,
    )
