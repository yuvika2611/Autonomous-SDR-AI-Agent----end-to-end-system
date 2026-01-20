import os
from dotenv import load_dotenv
import smtplib
from email.message import EmailMessage

load_dotenv()

DRY_RUN = True  # change to False to actually send (and set SMTP vars)

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 465))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS")

def send_email(to_email: str, subject: str, body: str) -> bool:
    """
    If DRY_RUN True, we will only print the message to terminal.
    To send for real: set DRY_RUN=False and provide SMTP_USER and SMTP_PASS in .env
    """
    print("---- DRY RUN: email to send ----")
    print("To:", to_email)
    print("Subject:", subject)
    print("Body:\n", body)
    print("--------------------------------")
    if DRY_RUN:
        return True

    if not SMTP_USER or not SMTP_PASS:
        raise RuntimeError("SMTP credentials missing in environment")

    msg = EmailMessage()
    msg["From"] = SMTP_USER
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content(body)

    with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT) as s:
        s.login(SMTP_USER, SMTP_PASS)
        s.send_message(msg)

    return True
