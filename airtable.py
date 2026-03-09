# airtable.py - FIXED VERSION
import os
from pyairtable import Table
from dotenv import load_dotenv
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
ENV_PATH = ROOT_DIR / '.env'

load_dotenv(ENV_PATH)

AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
AIRTABLE_TABLE_NAME = os.getenv("AIRTABLE_TABLE_NAME")

table = Table(AIRTABLE_API_KEY, AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME)

def get_active_leads():
    """Get leads that are not completed"""
    return table.all(formula="{Status} != 'Completed'")

def update_lead_status(record_id, new_status):
    """Update lead status in Airtable"""
    table.update(record_id, {"Status": new_status})

def clean_field(value):
    """
    Convert Airtable field to string for SQLite
    Handles arrays, objects, None, etc.
    """
    if value is None:
        return ""
    if isinstance(value, list):
        # Join array items with commas
        return ", ".join(str(v) for v in value)
    if isinstance(value, dict):
        # Convert dict to JSON string
        return str(value)
    # Convert everything else to string
    return str(value)

def sync_airtable_to_db():
    """Pull leads from Airtable and insert into SQLite"""
    from db import add_lead
    import sqlite3 as _sqlite3

    records = get_active_leads()
    synced = 0
    skipped = 0

    print(f"\n📥 Fetched {len(records)} records from Airtable\n")

    for record in records:
        fields = record["fields"]

        lead = {
            "name":    clean_field(fields.get("Lead Name", "Unknown")),
            "email":   clean_field(fields.get("Email", "")),
            "company": clean_field(fields.get("Company", "")),
            "role":    clean_field(fields.get("Industry", "")),
            "notes":   clean_field(fields.get("Problem Signal", "") or fields.get("Notes", ""))
        }

        if lead["email"] and "@" in lead["email"]:
            print(f"✓ Syncing: {lead['name']} ({lead['email']}) from {lead['company']}")
            try:
                # Try insert first
                add_lead(lead)

                # Always update name/company in case it was blank before
                conn = _sqlite3.connect("leads.db")
                c = conn.cursor()
                c.execute("""
                    UPDATE leads 
                    SET name = ?, company = ?, role = ?, notes = ?
                    WHERE email = ? AND (name = '' OR name = 'Unknown' OR name IS NULL)
                """, (
                    lead["name"],
                    lead["company"],
                    lead["role"],
                    lead["notes"],
                    lead["email"]
                ))
                conn.commit()
                conn.close()

                synced += 1
            except Exception as e:
                print(f"  ⚠️ Failed: {e}")
                skipped += 1
        else:
            print(f"✗ Skipping: {lead['name']} — No email")
            skipped += 1

    print(f"\n📊 Sync Summary:")
    print(f"   ✅ Synced:  {synced} leads")
    print(f"   ⚠️ Skipped: {skipped} leads\n")

    return synced