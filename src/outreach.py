import os
import json
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv
import smtplib
from email.message import EmailMessage

load_dotenv()

DRY_RUN = True  # change to False to send real emails

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


# --------------------------------------------------------
#  FOLLOW-UP SCHEDULER HELPERS
# --------------------------------------------------------
def load_followups():
    if not os.path.exists(FOLLOWUP_DB):
        return []
    with open(FOLLOWUP_DB, "r") as f:
        return json.load(f)


def save_followups(data):
    with open(FOLLOWUP_DB, "w") as f:
        json.dump(data, f, indent=2)


# --------------------------------------------------------
#  SCHEDULE A FOLLOW-UP
# --------------------------------------------------------
def schedule_followup(email: str, subject: str, body: str, delay_hours: int):
    followups = load_followups()

    follow_time = datetime.now() + timedelta(hours=delay_hours)
    followups.append({
        "email": email,
        "subject": subject,
        "body": body,
        "send_at": follow_time.isoformat(),
        "sent": False
    })

    save_followups(followups)

    print(f"[✓] Follow-up scheduled for {email} at {follow_time}")
    return True


# --------------------------------------------------------
#  RUN SCHEDULER LOOP
# --------------------------------------------------------
def run_followup_scheduler():
    print("▶ Follow-up scheduler running...")

    while True:
        followups = load_followups()
        now = datetime.now()

        for item in followups:
            if item["sent"]:
                continue

            send_time = datetime.fromisoformat(item["send_at"])

            if now >= send_time:
                print(f"Sending follow-up to {item['email']} ...")
                ok = send_email(item["email"], item["subject"], item["body"])
                if ok:
                    item["sent"] = True
                    print(f"[✓] Follow-up sent to {item['email']}")

        save_followups(followups)
        time.sleep(30)  # check every 30 seconds


# --------------------------------------------------------
#  DEMO
# --------------------------------------------------------
if __name__ == "__main__":
    # quick test example
    schedule_followup(
        email="test@example.com",
        subject="Following up 🙂",
        body="Hey, just checking in!",
        delay_hours=1
    )
    run_followup_scheduler()
