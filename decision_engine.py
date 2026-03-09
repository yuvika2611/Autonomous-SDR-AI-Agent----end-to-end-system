def plan_followups(lead, research, outreach_result):
    """
    Decision Intelligence v1

    Inputs:
    - lead: dict
    - research: dict or string
    - outreach_result: dict returned by generate_outreach()

    Returns:
    - List of follow-up plans with:
        delay_days
        message
        decision_reason
    """

    plans = []

    research_text = ""
    if isinstance(research, dict):
        research_text = " ".join(map(str, research.values())).lower()
    else:
        research_text = str(research).lower()

    # Tone comes ONLY from generator output (not hardcoded)
    tone = outreach_result.get("tone", "cold")

    # -------------------------
    # HIGH INTENT
    # -------------------------
    if any(x in research_text for x in ["hiring", "scaling", "expanding"]):
        plans.extend([
            {
                "delay_days": 1,
                "message": "Just following up since you’re scaling — would love to help.",
                "decision_reason": "Company growth signals detected → high intent → fast follow-up."
            },
            {
                "delay_days": 3,
                "message": "Sharing one quick idea that could support your growth.",
                "decision_reason": "No reply after high-intent signal → reinforce relevance."
            }
        ])

    # -------------------------
    # MEDIUM INTENT
    # -------------------------
    elif "automation" in research_text or tone == "warm":
        plans.extend([
            {
                "delay_days": 2,
                "message": "Quick nudge to continue our conversation.",
                "decision_reason": "Automation interest or warm tone detected → maintain momentum."
            },
            {
                "delay_days": 5,
                "message": "Thought this might be useful for you.",
                "decision_reason": "Warm lead → trust-building follow-up."
            }
        ])

    # -------------------------
    # LOW INTENT
    # -------------------------
    else:
        plans.extend([
            {
                "delay_days": 3,
                "message": "Just circling back in case this is relevant.",
                "decision_reason": "Cold lead → allow space before re-engaging."
            },
            {
                "delay_days": 7,
                "message": "Last quick touch before I pause outreach.",
                "decision_reason": "No response → final attempt before dropping."
            }
        ])

    return plans
