# main.py - UPDATED VERSION
from db import init_db, add_lead, get_unprocessed, mark_contacted
from generator import generate_outreach
from researcher import research_lead
from outreach import send_email
from airtable import sync_airtable_to_db
import os
from datetime import datetime, timezone, timedelta

init_db()

def seed_sample():
    """Add a sample lead if none exist"""
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
    """Process unprocessed leads"""
    
    # Sync from Airtable first
    sync_airtable_to_db()
    
    # Get unprocessed leads
    leads = get_unprocessed(limit=5)
    
    if not leads:
        print("✅ No unprocessed leads found.")
        print("   All leads have been contacted.")
        print("\nTo re-process leads, run:")
        print("   sqlite3 leads.db \"UPDATE leads SET status = 'unprocessed';\"")
        return

    for lead in leads:
        print(f"\n{'='*60}")
        print(f"Processing lead: {lead['name']} ({lead['email']})")
        print(f"{'='*60}\n")
        
        lead['product'] = "AI-powered outreach automation to boost reply rates"
        
        # Research
        research = research_lead(lead)
        
        # Generate outreach
        out = generate_outreach(lead, research)

        subject = out.get("subject") if isinstance(out, dict) else "Quick question"
        body = out.get("body") if isinstance(out, dict) else str(out)
        followups = out.get("followups") if isinstance(out, dict) else []

        print(f"Subject: {subject}")
        print(f"Body:\n{body}\n")

        # Send email
        ok = send_email(lead['email'], subject, body)
        
        if ok:
            mark_contacted(lead['id'], body)
            print(f"✅ Lead {lead['name']} marked as contacted.")

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
                
                from db import add_followup
                add_followup(lead['id'], fu_text, due_iso)
                print(f"➡️ Scheduled follow-up #{idx+1} for {lead['name']} on {due_iso}")
        else:
            print(f"❌ Failed to send email to {lead['name']}")

    print(f"\n{'='*60}")
    print(f"✅ Processed {len(leads)} leads")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    # Don't seed if we have Airtable data
    # seed_sample()
    run_one_cycle()