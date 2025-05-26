import smtplib # os removed as getenv calls are replaced
from email.mime.text import MIMEText
from app.config import settings # Import settings

# MAILTRAP_HOST = os.getenv("MAILTRAP_HOST") # Replaced
# MAILTRAP_PORT = int(os.getenv("MAILTRAP_PORT", 2525)) # Replaced
# MAILTRAP_USER = os.getenv("MAILTRAP_USER") # Replaced
# MAILTRAP_PASS = os.getenv("MAILTRAP_PASS") # Replaced
# MAILTRAP_FROM = os.getenv("MAILTRAP_FROM", "AutoBidder <noreply@example.com>") # Replaced


def send_verification_email(to_email: str, token: str):
    verify_link = f"{settings.EMAIL_VERIFICATION_HOST}/auth/verify?token={token}" # Use settings
    subject = "Verify your email"
    body = f"Click the link to verify your email:\n\n{verify_link}"

    msg = MIMEText(body, "plain")
    msg["Subject"] = subject
    msg["From"] = str(settings.MAILTRAP_FROM) # Use settings, ensure str if EmailStr
    msg["To"] = to_email

    # Ensure MAILTRAP_HOST and MAILTRAP_USER are not None before proceeding
    if not settings.MAILTRAP_HOST or not settings.MAILTRAP_USER:
        # Log an error or handle appropriately if email cannot be sent
        # due to missing configuration. For now, just preventing a runtime error.
        print("Mailtrap settings not fully configured. Email not sent.")
        return

    with smtplib.SMTP(settings.MAILTRAP_HOST, settings.MAILTRAP_PORT) as server: # Use settings
        server.login(settings.MAILTRAP_USER, settings.MAILTRAP_PASS) # Use settings
        server.sendmail(str(settings.MAILTRAP_FROM), to_email, msg.as_string()) # Use settings
