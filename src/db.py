import sqlite3
sqlite3.enable_callback_tracebacks(True)
from typing import Dict, List, Optional
from datetime import datetime, timedelta

DB_PATH = "leads.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # leads table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            role TEXT,
            phone TEXT,
            company TEXT,
            position TEXT,
            notes TEXT,
            status TEXT DEFAULT 'unprocessed',
            outreach TEXT,
            last_contacted TEXT
        )
    ''')
    # followups table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS followups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lead_id INTEGER NOT NULL,
            body TEXT NOT NULL,
            decision_reason TEXT NOT NULL,       
            due_date TEXT NOT NULL,
            sent INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (lead_id) REFERENCES leads(id)
        )
    ''')
    conn.commit()
    conn.close()

def add_lead(lead: Dict[str, Optional[str]]) -> int:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR IGNORE INTO leads (name, email, role, phone, company, position, notes, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, 'unprocessed')
    ''', (
        lead.get("name"),
        lead.get("email"),
        lead.get("role"),
        lead.get("phone"),
        lead.get("company"),
        lead.get("position"),
        lead.get("notes")
    ))
    conn.commit()
    lead_id = cursor.lastrowid
    conn.close()
    return lead_id

def get_unprocessed(limit: int = 10) -> List[Dict]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("""
        SELECT id, name, email, role, company, notes, status, outreach
        FROM leads WHERE status = 'unprocessed'
        LIMIT ?
    """, (limit,))
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows

def mark_contacted(lead_id: int, outreach_text: str):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        UPDATE leads 
        SET status = 'contacted', 
            outreach = ?, 
            last_contacted = datetime('now') 
        WHERE id = ?
    """, (outreach_text, lead_id))
    conn.commit()
    conn.close()

# -------------------------
# Followups helper functions
# -------------------------
def add_followup(lead_id: int, body: str, due_date_iso: str) -> int:
    """Add a follow-up for a lead."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "INSERT INTO followups (lead_id, body, due_date) VALUES (?, ?, ?)",
        (lead_id, body, due_date_iso)
    )
    conn.commit()
    fid = c.lastrowid
    conn.close()
    return fid

def get_due_followups(now_iso: str, limit: int = 50) -> List[Dict]:
    """Return followups where due_date <= now and sent = 0"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("""
        SELECT f.id, f.lead_id, f.body, f.due_date, l.name, l.email
        FROM followups f
        JOIN leads l ON l.id = f.lead_id
        WHERE f.sent = 0 AND f.due_date <= ?
        ORDER BY f.due_date ASC
        LIMIT ?
    """, (now_iso, limit))
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows

def mark_followup_sent(followup_id: int):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE followups SET sent = 1 WHERE id = ?", (followup_id,))
    conn.commit()
    conn.close()

def schedule_followup(lead_id: int, body: str, days: int, decision_reason: str):
    due_date = (datetime.utcnow() + timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        INSERT INTO followups (lead_id, body, decision_reason, due_date)
        VALUES (?, ?, ?, ?)
    """, (lead_id, body, decision_reason, due_date))
    conn.commit()
    conn.close()
               
                      
