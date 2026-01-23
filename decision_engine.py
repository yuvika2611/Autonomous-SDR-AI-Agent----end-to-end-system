# decision_engine.py

def decide_followup(lead, research_summary, followup_index):
    """
    Returns follow-up timing and reasoning based on lead signals.
    """

    # Simple v1 rules (we'll make it smarter later)
    if "hiring" in research_summary.lower() or "scaling" in research_summary.lower():
        urgency = "high"
        days = 1
        reason = "Lead is in growth phase, high buying intent."
    elif "automation" in research_summary.lower():
        urgency = "medium"
        days = 2
        reason = "Lead expressed interest in automation, warm intent."
    else:
        urgency = "low"
        days = 3
        reason = "No strong buying signal, soft follow-up."

    # Space follow-ups logically
    days = days + followup_index

    return {
        "days": days,
        "urgency": urgency,
        "decision_reason": reason
    }
