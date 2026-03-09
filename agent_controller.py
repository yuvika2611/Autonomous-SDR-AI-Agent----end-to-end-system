from db import get_unprocessed, mark_contacted, schedule_followup
from generator import generate_outreach
from researcher import research_lead
from decision_engine import plan_followups

def process_leads(limit=5):
    leads = get_unprocessed(limit)

    if not leads:
        print("No new leads to process.")
        return

    for lead in leads:
        print(f"\nProcessing lead: {lead['name']} ({lead['email']})")

        # 1. Research
        research = research_lead(lead)

        # 2. Generate outreach (AI writer)
        outreach_result = generate_outreach(lead, research)

        subject = outreach_result["subject"]
        body = outreach_result["body"]

        # 3. Mark contacted
        mark_contacted(lead["id"], body)

        print("Primary outreach:")
        print(subject)
        print(body)

        # 4. Decision Intelligence (AI brain)
        followup_plans = plan_followups(
            lead=lead,
            research=research,
            outreach_result=outreach_result
        )

        # 5. Schedule follow-ups
        for plan in followup_plans:
            schedule_followup(
                lead_id=lead["id"],
                body=plan["message"],
                days=plan["delay_days"],
                decision_reason=plan["decision_reason"]
            )

            print(
                f"Follow-up scheduled → {plan['delay_days']} days | "
                f"Reason: {plan['decision_reason']}"
            )

if __name__ == "__main__":
    process_leads()
