import os
from datetime import datetime, timezone
from apscheduler.schedulers.blocking import BlockingScheduler
from dotenv import load_dotenv
from db import get_due_followups, mark_followup_sent, init_db
from outreach import send_email

def log(msg: str):
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}")

load_dotenv()
init_db()

CHECK_INTERVAL_SECONDS = int(os.getenv("FOLLOWUP_CHECK_INTERVAL", "60"))

def send_followup_task():
    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    due = get_due_followups(now_iso)

    checked = len(due)
    sent = 0
    skipped = 0

    if not due:
        log("Scheduler alive | 0 follow-ups due")
        return

    for f in due:
        log(f"Evaluating follow-up #{f['id']} for {f['email']}")

        # Decision rule v1 (simple, clean)
        if f.get("sent"):
            skipped += 1
            log(f"Skipped #{f['id']} (already sent)")
            continue

        ok = send_email(
            f["email"],
            f"Following up — {f['name']}",
            f["body"]
        )

        if ok:
            mark_followup_sent(f["id"])
            sent += 1
            log(f"Sent follow-up #{f['id']}")
        else:
            skipped += 1
            log(f"Failed to send follow-up #{f['id']} (will retry)")

    log(
        f"Run summary | checked={checked} sent={sent} skipped={skipped}"
    )



def run_scheduler_blocking():
    scheduler = BlockingScheduler()
    scheduler.add_job(send_followup_task, "interval", seconds=CHECK_INTERVAL_SECONDS, max_instances=1)
    print(f"Follow-up scheduler started — checking every {CHECK_INTERVAL_SECONDS} seconds.")
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        print("Scheduler stopped.")

if __name__ == "__main__":
    run_scheduler_blocking()
