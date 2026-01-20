import os
import json
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

SYSTEM_PROMPT = "You are an efficient SDR assistant. Write concise, professional cold outreach emails."

def build_prompt(lead: dict) -> str:
    return f"""
Write a short (3-5 sentences) cold outreach email to {lead.get('name')} who is {lead.get('role')} at {lead.get('company')}.
We are offering: {lead.get('product','AI outreach automation')}.
Tone: helpful, professional, concise.
Include a single CTA asking to book a 15-minute call (place [CAL_LINK] as a placeholder).
Return only JSON with keys: subject, body, followups (array of 2 strings).
"""

def generate_outreach(lead: dict, model: str = "gpt-3.5-turbo", temperature: float = 0.2, max_tokens: int = 400) -> dict:
    prompt = build_prompt(lead)
    # Chat completion
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
    # Try to parse JSON if model returned JSON; otherwise return raw text
    try:
        parsed = json.loads(text)
        return parsed
    except Exception:
        return {"subject": f"Quick question, {lead.get('name')}", "body": text, "followups": []}
