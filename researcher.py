import os
import json
from dotenv import load_dotenv

load_dotenv()

from groq_generator import research_lead_groq

SYSTEM_PROMPT = """
You are an AI SDR research assistant. 
Your job is to analyze the lead & produce insights that help write personalised outreach.
Return only JSON.
"""

def research_lead(lead: dict, model="gpt-4o-mini"):
    """
    Research lead using Groq (FREE)
    Model parameter is ignored - kept for compatibility
    """
    try:
        return research_lead_groq(lead)
    except Exception as e:
        print(f"⚠️ Research agent failed: {e}")
        # Return safe fallback
        return {
            "company_summary": f"{lead.get('company', 'The company')} is a growing business",
            "role_insight": f"Companies in {lead.get('role', 'this industry')} focus on efficiency",
            "pain_points": ["Manual work", "Low reply rates", "Scaling challenges"],
            "personalization": f"Wanted to reach out about {lead.get('company', 'your company')}"
        }
