import os
import smtplib
from email.mime.text import MIMEText

MAILTRAP_HOST = os.getenv("MAILTRAP_HOST")
MAILTRAP_PORT = int(os.getenv("MAILTRAP_PORT", 2525))
MAILTRAP_USER = os.getenv("MAILTRAP_USER")
MAILTRAP_PASS = os.getenv("MAILTRAP_PASS")
MAILTRAP_FROM = os.getenv("MAILTRAP_FROM", "AutoBidder <noreply@example.com>")


def send_verification_email(to_email: str, token: str):
    verify_link = f"http://localhost:8000/auth/verify?token={token}"
    subject = "Verify your email"
    body = f"Click the link to verify your email:\n\n{verify_link}"

    msg = MIMEText(body, "plain")
    msg["Subject"] = subject
    msg["From"] = MAILTRAP_FROM
    msg["To"] = to_email

    with smtplib.SMTP(MAILTRAP_HOST, MAILTRAP_PORT) as server:
        server.login(MAILTRAP_USER, MAILTRAP_PASS)
        server.sendmail(MAILTRAP_FROM, to_email, msg.as_string())
