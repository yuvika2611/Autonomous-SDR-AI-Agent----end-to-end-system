from db import init_db, add_lead, get_unprocessed, mark_contacted, add_followup
from generator import generate_outreach
from researcher import research_lead
from outreach import send_email
import os
from datetime import datetime, timezone, timedelta

init_db()

def seed_sample():
    rows = get_unprocessed(limit=1)
    if not rows:
        sample = {
            "name": "Rohit Sharma",
            "email": "rohit@example.com",
            "role": "Head of Marketing",
            "company": "BrightTech",
            "notes": "Interested in automation"
        }
        add_lead(sample)
        print("Seeded one sample lead.")

def run_one_cycle():
    leads = get_unprocessed(limit=5)
    if not leads:
        print("No unprocessed leads. Add leads to DB or run seed_sample().")
        return

    for lead in leads:
        print(f"Processing lead: {lead['name']} ({lead['email']})")
        lead['product'] = "AI-powered outreach automation to boost reply rates"
        research = research_lead(lead)
        out = generate_outreach(lead, research)

        subject = out.get("subject") if isinstance(out, dict) else "Quick question"
        body = out.get("body") if isinstance(out, dict) else str(out)
        followups = out.get("followups") if isinstance(out, dict) else []

        ok = send_email(lead['email'], subject, body)
        if ok:
            mark_contacted(lead['id'], body)
            print(f"Lead {lead['name']} marked as contacted.")

            # Schedule follow-ups
            demo_mode = os.getenv("FOLLOWUP_DEMO_MINUTES")
            for idx, fu_text in enumerate(followups):
                if demo_mode:
                    delay_minutes = int(demo_mode) * (idx + 1)
                    due = datetime.now(timezone.utc) + timedelta(minutes=delay_minutes)
                else:
                    delays_days = [3, 7]
                    days = delays_days[idx] if idx < len(delays_days) else (7 + idx*7)
                    due = datetime.now(timezone.utc) + timedelta(days=days)
                due_iso = due.strftime("%Y-%m-%d %H:%M:%S")
                add_followup(lead['id'], fu_text, due_iso)
                print(f"➡️ Scheduled follow-up #{idx+1} for {lead['name']} on {due_iso}")


if __name__ == "__main__":
    seed_sample()
    run_one_cycle()
