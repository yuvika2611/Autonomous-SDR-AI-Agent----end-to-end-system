import os
import json
from dotenv import load_dotenv

#Load .env
load_dotenv()
#print("DEBUG OPEN_API_KEY:", os.getenv("OPEN_API_KEY"))


from openai import OpenAI

SYSTEM_PROMPT = """
You are an AI SDR research assistant. 
Your job is to analyze the lead & produce insights that help write personalised outreach. "      
Return only JSON.
"""

def build_research_prompt(lead: dict) -> str:
    return f"""
Research the following lead & output structured JSON insights:

NAME : {lead.get("name")}
Role: {lead.get("role")}
Company: {lead.get("company")}
Notes: {lead.get("notes")}

Return JSON with these keys:
- company_summary: short description of the company
- role_insight: what this role cares about
- pain_points: array of 2-3 liekly challenges they face
- personalization: 1-2 sentence custom personalization to include in cold email
"""

def research_lead(lead: dict, model="gpt-4o-mini"):
    api_key = os.getenv("OPEN_API_KEY")

    #TEST MODE
    if not api_key:
        print("⚠️ Research agent running in TEST MODE.")
        return {
            "company_summary": f"{lead.get('company')} is likely a growing business focusing on scaling operations.",
            "role_insight": f"A {lead.get('role')} typically cares about efficiency and improving performance.",
            "pain_points": [
                "Too much manual workload",
                "Low reply rates in outreach",
                "Difficulty scaling leads pipeline"
            ],
            "personalization": (
                f"I noticed that {lead.get('company')} may be focusing on growth — "
                f"so AI-driven outreach could help {lead.get('role')} save time."
            )
        }
    #REAL MODE
    try:
        client = OpenAI(api_key=api_key)
        prompt = build_research_prompt(lead)

        resp = client.chat.completions.create(
            model = model,
            messages = [{"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": prompt}],
            max_tokens=350
        )
        text = resp.choices[0].message.content

        try:
            return json.loads(text)
        except Exception:
            print("⚠️ Invalid JSON from research model")
            return {
                "company_summary": "Unavailable",
                "role_insight": "Unavailable",
                "pain_points": [],
                "personalization": ""
            }

    except Exception as e:
        print("⚠️ Research agent failed:", e)
        return {
            "company_summary": "Company details unavailable.",
            "role_insight": "Role insights unavailable.",
            "pain_points": ["General outreach challenge"],
            "personalization": "Wanted to reach out with something helpful."
        }    
            
        