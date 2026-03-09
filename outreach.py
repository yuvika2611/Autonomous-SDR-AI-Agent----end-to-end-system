import os
import json
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv
import smtplib
from email.message import EmailMessage

load_dotenv()

DRY_RUN = False  # change to False to send real emails

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 465))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS")

FOLLOWUP_DB = "followups.json"


# --------------------------------------------------------
#  EMAIL SENDING
# --------------------------------------------------------
def send_email(to_email: str, subject: str, body: str) -> bool:
    if DRY_RUN:
        print("---- DRY RUN: email to send ----")
        print(f"To: {to_email}")
        print(f"Subject: {subject}")
        print(f"Body:\n{body}")
        print("--------------------------------")
        return True

    if not SMTP_USER or not SMTP_PASS:
        raise RuntimeError("SMTP credentials missing in environment")

    msg = EmailMessage()
    msg["From"] = SMTP_USER
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content(body)

    try:
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT) as s:
            s.login(SMTP_USER, SMTP_PASS)
            s.send_message(msg)
        return True
    except Exception as e:
        print("Email sending failed:", e)
        return False
