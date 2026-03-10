import os
import json
from dotenv import load_dotenv

load_dotenv()

from openai import OpenAI

SYSTEM_PROMPT = "You are an efficient SDR assistant. Write concise, professional cold outreach emails."

def build_prompt(lead: dict, research: dict) -> str:
    return f"""
Write a short (3–5 sentences) personalized cold outreach email.

Lead details:
Name: {lead.get('name')}
Role: {lead.get('role')}
Company: {lead.get('company')}

Company insight:
{research.get('company_summary')}

Role insight:
{research.get('role_insight')}

Pain points:
{', '.join(research.get('pain_points', []))}

Personalization hook:
{research.get('personalization')}

Offer:
{lead.get('product', 'AI outreach automation')}

Tone: helpful, professional, concise.
Include one CTA to book a 15-minute call (use [CAL_LINK]).

Return ONLY JSON:
{{ "subject": "...", "body": "...", "followups": [] }}
"""

def generate_outreach(lead: dict, research: dict, model: str = "gpt-4o-mini", temperature: float = 0.2, max_tokens: int = 400) -> dict:
    api_key = os.getenv("OPEN_API_KEY")

    # Test mode
    if not api_key:
        print("⚠️ TEST MODE — No API key found.")
        return {
            "subject": f"Quick chat about {lead.get('company','AI outreach')}",
            "body": f"Hey {lead.get('name','there')}, our AI system can help {lead.get('company','your team')}. Open to a quick 15-min call? [CAL_LINK]",
            "followups": [
                "Following up — did you see my last message?",
                "Last check-in — happy to share a quick demo if helpful!"
            ]
        }

    try:
        client = OpenAI(api_key=api_key)
        prompt = build_prompt(lead, research)
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            temperature=temperature,
            max_tokens=max_tokens
        )

        text = resp.choices[0].message.content.strip()

        # Try to parse JSON
        try:
            result = json.loads(text)
        except Exception:
            # If GPT returns plain text instead of JSON
            result = {
                "subject": f"Quick question, {lead.get('name')}",
                "body": text,
                "followups": []
            }

        # 🔥 ALWAYS enforce followup list
        if (
            "followups" not in result
             or not isinstance(result["followups"], list)
             or len(result["followups"]) == 0
        ):
            result["followups"] = [
                "Just checking in — did you get my previous message?",
                "Last follow-up — happy to send a quick demo if helpful!"
            ]

        return result

    except Exception as e:
        print(f"⚠️ GPT Error: {e}")
        return {
            "subject": "Let's talk about AI automation",
            "body": f"Hey {lead.get('name','there')}, I wanted to share how we help teams scale outreach using AI. [CAL_LINK]",
            "followups": [
                "Checking back in — did you see my last message?",
                "Last follow-up — can send a short demo if useful."
            ]
        }
