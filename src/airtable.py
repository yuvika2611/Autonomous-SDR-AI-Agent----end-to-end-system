import os
from pyairtable import Table
from dotenv import load_dotenv
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
ENV_PATH = ROOT_DIR / '.env'

load_dotenv(ENV_PATH)

print("Loaded from:", ENV_PATH)
print("KEY:", os.getenv("AIRTABLE_API_KEY"))
print("BASE:", os.getenv("AIRTABLE_BASE_ID"))
print("TABLE:", os.getenv("AIRTABLE_TABLE_NAME"))


AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
AIRTABLE_TABLE_NAME = os.getenv("AIRTABLE_TABLE_NAME")

table = Table(AIRTABLE_API_KEY, AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME)

def get_active_leads():
    return table.all(formula = "{Status} != 'completed'")

def update_lead_status(record_id, new_status):
    table.update(record_id, {"Status" : new_status})
