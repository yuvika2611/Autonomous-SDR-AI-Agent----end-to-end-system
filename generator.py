# generator.py - PRODUCTION READY
import os
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

SYSTEM_PROMPT = "You are an efficient SDR assistant. Write concise, professional cold outreach emails. Return ONLY valid JSON, no markdown, no code blocks."


def clean_json_response(text: str) -> str:
    """Extract clean JSON from Groq response"""
    # Remove markdown code blocks (THIS was the bug)
    text = text.replace('```json', '').replace('```', '')
    
    # Find JSON object
    start = text.find('{')
    end = text.rfind('}') + 1
    
    if start >= 0 and end > start:
        return text[start:end]
    
    return text.strip()


def build_prompt(lead: dict, research: dict) -> str:
    return f"""
Write a short (3-5 sentences) personalized cold outreach email.

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

IMPORTANT: Return ONLY valid JSON, no markdown formatting, no code blocks.

Format:
{{ "subject": "...", "body": "...", "followups": ["follow-up 1", "follow-up 2"] }}
"""


def generate_outreach(
    lead: dict,
    research: dict,
    model: str = "llama-3.3-70b-versatile",
    temperature: float = 0.7,
    max_tokens: int = 500,
) -> dict:
    """
    Generate outreach email using Groq LLM.
    Always returns:
    {
        "subject": str,
        "body": str,
        "followups": list[str]
    }
    """

    api_key = os.getenv("GROQ_API_KEY")

    # ---------------- TEST MODE ----------------
    if not api_key:
        print("⚠️ TEST MODE — No GROQ_API_KEY found.")
        return {
            "subject": f"Quick chat about {lead.get('company', 'AI outreach')}",
            "body": f"Hey {lead.get('name','there')}, our AI system can help {lead.get('company','your team')} scale outreach. Open to a quick 15-min call? [CAL_LINK]",
            "followups": [
                "Following up — did you see my last message?",
                "Last check-in — happy to share a quick demo if helpful!",
            ],
        }

    # ---------------- REAL CALL ----------------
    try:
        client = Groq(api_key=api_key)
        prompt = build_prompt(lead, research)

        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )

        text = response.choices[0].message.content.strip()

        # ---------- Clean and parse JSON ----------
        try:
            json_text = clean_json_response(text)
            result = json.loads(json_text)
        except Exception:
            # Model returned plain text instead of JSON
            result = {
                "subject": f"Quick question, {lead.get('name','there')}",
                "body": text,
                "followups": [],
            }

        # ---------- ALWAYS enforce followups ----------
        if (
            "followups" not in result
            or not isinstance(result["followups"], list)
            or len(result["followups"]) == 0
        ):
            result["followups"] = [
                "Just checking in — did you get my previous message?",
                "Last follow-up — happy to send a quick demo if helpful!",
            ]

        return result

    # ---------------- FAILSAFE ----------------
    except Exception as e:
        print(f"⚠️ GROQ Error: {e}")
        return {
            "subject": "Let's talk about AI automation",
            "body": f"Hey {lead.get('name','there')}, I wanted to share how we help teams scale outreach using AI. [CAL_LINK]",
            "followups": [
                "Checking back in — did you see my last message?",
                "Last follow-up — can send a short demo if useful.",
            ],
        }