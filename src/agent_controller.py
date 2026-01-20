from db import get_unprocessed, mark_contacted, schedule_followup
from generator import generate_outreach
from researcher import research_lead

def process_leads(limit=5):
    leads = get_unprocessed(limit)

    if not leads:
        print("No new leads to process.")
        return

    for lead in leads:
        print(f"Processing lead: {lead['name']} ({lead['email']})")

        # 1. Research
        research = research_lead(lead)

        # 2. Generate outreach
        result = generate_outreach(lead, research)

        subject = result["subject"]
        body = result["body"]
        followups = result.get("followups", [])

        # 3. Mark contacted
        mark_contacted(lead["id"], body)

        print("Primary outreach generated.")
        print(subject)
        print(body)

        # 4. Schedule follow-ups with reasoning
        for i, fu in enumerate(followups):
            decision_reason = f"Follow-up #{i+1} scheduled because no reply after initial outreach."

            schedule_followup(
                lead_id=lead["id"],
                body=fu,
                days=(i + 1) * 2,
                decision_reason=decision_reason
            )

            print(f"Follow-up {i+1} scheduled with reason: {decision_reason}")

if __name__ == "__main__":
    process_leads()

