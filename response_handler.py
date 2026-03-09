import imaplib
import email
import json
import os
from email.header import decode_header
from groq import Groq
from dotenv import load_dotenv
import sqlite3

load_dotenv()


def get_all_lead_emails() -> set:
    """Get set of all lead emails from database"""
    conn = sqlite3.connect("leads.db")
    c = conn.cursor()
    c.execute("SELECT email FROM leads")
    emails = {row[0].lower() for row in c.fetchall()}
    conn.close()
    return emails


def fetch_replies(since_hours: int = 24) -> list:
    """
    Fetch unread emails that are REPLIES from actual leads
    """
    IMAP_HOST = "imap.gmail.com"
    SMTP_USER = os.getenv("SMTP_USER")
    SMTP_PASS = os.getenv("SMTP_PASS")

    if not SMTP_USER or not SMTP_PASS:
        print("⚠️ No SMTP credentials — running in test mode")
        return []

    # Get list of valid lead emails
    valid_leads = get_all_lead_emails()
    print(f"📋 Monitoring {len(valid_leads)} leads in database")

    try:
        mail = imaplib.IMAP4_SSL(IMAP_HOST)
        mail.login(SMTP_USER, SMTP_PASS)
        mail.select("INBOX")

        # Only get recent emails
        from datetime import datetime, timedelta
        since_date = (datetime.now() - timedelta(hours=since_hours)).strftime("%d-%b-%Y")
        
        _, messages = mail.search(None, f'(UNSEEN SINCE {since_date})')
        email_ids = messages[0].split()

        print(f"📧 Found {len(email_ids)} unread emails in last {since_hours} hours")

        if not email_ids:
            mail.logout()
            return []

        replies = []
        processed = 0
        skipped = 0

        for eid in email_ids:
            try:
                _, msg_data = mail.fetch(eid, "(RFC822)")
                raw = msg_data[0][1]
                msg = email.message_from_bytes(raw)

                # Extract sender
                from_header = msg.get("From", "")
                sender_email = email.utils.parseaddr(from_header)[1].lower()

                # CRITICAL FILTER: Only process emails from known leads
                if sender_email not in valid_leads:
                    skipped += 1
                    continue

                # Skip noreply addresses
                if "noreply" in sender_email or "no-reply" in sender_email or "donotreply" in sender_email:
                    print(f"  ⏭️ Skipping noreply address: {sender_email}")
                    skipped += 1
                    continue

                processed += 1

                # Extract subject
                subject_raw = msg.get("Subject", "")
                subject, enc = decode_header(subject_raw)[0]
                if isinstance(subject, bytes):
                    subject = subject.decode(enc or "utf-8")

                # Extract body
                body = ""
                if msg.is_multipart():
                    for part in msg.walk():
                        if part.get_content_type() == "text/plain":
                            payload = part.get_payload(decode=True)
                            if payload:
                                body = payload.decode("utf-8", errors="ignore")
                                break
                else:
                    payload = msg.get_payload(decode=True)
                    if payload:
                        body = payload.decode("utf-8", errors="ignore")

                if sender_email and body:
                    replies.append({
                        "from_email": sender_email,
                        "subject": subject,
                        "body": body[:500]
                    })
                    print(f"  ✅ Found reply from lead: {sender_email}")

            except Exception as e:
                print(f"  ⚠️ Error reading email {eid}: {e}")
                continue

        mail.logout()
        
        print(f"\n📊 Email Processing Summary:")
        print(f"   Total unread: {len(email_ids)}")
        print(f"   From leads: {processed}")
        print(f"   Skipped (not leads): {skipped}")
        print(f"   Replies to process: {len(replies)}\n")
        
        return replies

    except Exception as e:
        print(f"⚠️ IMAP error: {e}")
        return []


def classify_reply(body: str) -> dict:
    """Uses Groq to classify the reply"""
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    
    prompt = f"""Classify this email reply from a sales prospect.
    
    Reply: "{body}"
    
    Return ONLY valid JSON (no markdown):
    {{
        "intent": "interested | not_interested | out_of_office | needs_info | wrong_person | unsubscribe",
        "sentiment": "positive | neutral | negative",
        "should_followup": true or false,
        "urgency": "high | medium | low",
        "suggested_action": "one sentence on what to do next"
    }}"""
    
    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=200
        )
        
        text = completion.choices[0].message.content.strip()
        
        # Clean JSON
        text = text.replace('```json', '').replace('```', '')
        start = text.find('{')
        end = text.rfind('}') + 1
        json_text = text[start:end]
        
        return json.loads(json_text)
        
    except Exception as e:
        print(f"⚠️ Classification error: {e}")
        return {
            "intent": "unknown",
            "sentiment": "neutral",
            "should_followup": False,
            "urgency": "low",
            "suggested_action": "Review manually"
        }


def handle_reply(sender_email: str, classification: dict, original_body: str):
    """Take action based on classified intent"""
    from outreach import send_email
    
    intent = classification["intent"]
    
    print(f"\n{'='*60}")
    print(f"📧 Reply from: {sender_email}")
    print(f"   Intent: {intent}")
    print(f"   Sentiment: {classification['sentiment']}")
    print(f"   Action: {classification['suggested_action']}")
    print(f"{'='*60}")
    
    if intent == "interested":
        # Send calendar link
        send_email(
            to_email=sender_email,
            subject="Let's connect — here's my calendar",
            body=f"""Hi,

Great to hear from you! I'd love to show you exactly how our AI SDR system works.

Here's my calendar to book a quick 15-minute call:
https://calendly.com/your-link-here

Looking forward to speaking with you!

Best Regards,
Yuvika Singh
AI SDR Solutions"""
        )
        update_lead_status_by_email(sender_email, "interested")
        print(f"✅ Sent meeting link to {sender_email}")
    
    elif intent == "needs_info":
        # AI generates helpful response
        response_body = generate_info_response(classification["suggested_action"], original_body)
        send_email(
            to_email=sender_email,
            subject="Re: Your question about AI SDR",
            body=response_body
        )
        print(f"📧 Sent info response to {sender_email}")
    
    elif intent == "not_interested":
        update_lead_status_by_email(sender_email, "not_interested")
        print(f"❌ Marked {sender_email} as not interested (no email sent)")
    
    elif intent == "unsubscribe":
        update_lead_status_by_email(sender_email, "unsubscribed")
        print(f"🚫 Unsubscribed {sender_email} (no further emails)")
    
    elif intent == "wrong_person":
        update_lead_status_by_email(sender_email, "wrong_person")
        print(f"🔄 Wrong person: {sender_email} (marked for review)")
    
    elif intent == "out_of_office":
        print(f"⏸️ Out of office: {sender_email} (pausing outreach)")
        # Don't change status, just pause follow-ups
    
    else:
        print(f"❓ Unknown intent: {sender_email} (manual review needed)")


def update_lead_status_by_email(email: str, status: str):
    """Update lead status in DB"""
    conn = sqlite3.connect("leads.db")
    c = conn.cursor()
    c.execute("UPDATE leads SET status = ? WHERE email = ?", (status, email.lower()))
    conn.commit()
    conn.close()


def generate_info_response(question_hint: str, original_body: str) -> str:
    """Generate helpful response to prospect's question"""
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    
    prompt = f"""Write a brief, helpful email response.

The prospect asked: {question_hint}

Their original message: {original_body[:200]}

Write a response that:
- Answers their question professionally
- Keeps it under 100 words
- Ends with calendar link: https://calendly.com/your-link-here

Return ONLY the email body text (no JSON, no subject line)."""
    
    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=200
        )
        return completion.choices[0].message.content.strip()
    except:
        return f"""Thanks for your question!

I'd be happy to provide more details. The best way would be a quick 15-minute call where I can answer all your questions and show you exactly how it works.

Here's my calendar: https://calendly.com/your-link-here

Best Regards,
Yuvika Singh"""


def process_all_replies():
    """Main function - call this from scheduler"""
    print("\n" + "="*60)
    print("📬 Checking for replies from leads...")
    print("="*60 + "\n")
    
    replies = fetch_replies()
    
    if not replies:
        print("✅ No new replies from leads found.\n")
        return
    
    for reply in replies:
        classification = classify_reply(reply["body"])
        handle_reply(reply["from_email"], classification, reply["body"])
    
    print("\n" + "="*60)
    print(f"✅ Processed {len(replies)} lead replies")
    print("="*60 + "\n")


if __name__ == "__main__":
    process_all_replies()