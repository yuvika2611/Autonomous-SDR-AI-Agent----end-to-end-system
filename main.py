from db import init_db, add_lead, get_unprocessed, mark_contacted
from generator import generate_outreach
from outreach import send_email
import os
import json

# initialize DB (creates file if missing)
init_db()

# OPTIONAL: Add a sample lead if DB is empty (safe to run multiple times)
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
        print("No unprocessed leads. Add leads to the DB or run seed_sample().")
        return

    for lead in leads:
        print(f"Processing lead: {lead['name']} ({lead['email']})")
        # attach product info to lead dict (optional)
        lead['product'] = "AI-powered outreach automation to boost reply rates"
        out = generate_outreach(lead)
        subject = out.get("subject") if isinstance(out, dict) else "Quick question"
        body = out.get("body") if isinstance(out, dict) else str(out)
        # send (dry-run by default)
        ok = send_email(lead['email'], subject, body)
        if ok:
            mark_contacted(lead['id'], body)
            print(f"Lead {lead['name']} marked as contacted.")
        else:
            print("Send failed for", lead['name'])

if __name__ == "__main__":
    seed_sample()
    run_one_cycle()
