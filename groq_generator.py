import os
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()


def clean_json_response(text: str) -> str:
    """Extract clean JSON from Groq response"""
    # Remove markdown code blocks
    text = text.replace('```json', '').replace('```', '')
    
    # Find JSON object
    start = text.find('{')
    end = text.rfind('}') + 1
    
    if start >= 0 and end > start:
        return text[start:end]
    
    return text.strip()


def generate_outreach_groq(lead: dict, research: dict) -> dict:
    """Generate outreach email using Groq (FREE & FAST)"""
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    
    # Extract problem signal from notes if available
    problem_signal = lead.get('notes', '')
    
    prompt = f"""You are an expert SDR. Write a short, personalized cold outreach email.

Lead details:
- Name: {lead.get('name', 'there')}
- Company: {lead.get('company', 'your company')}
- Industry: {lead.get('role', 'their industry')}
- Problem Signal: {problem_signal}

Research insights:
- Company: {research.get('company_summary', 'Growing business')}
- Pain points: {', '.join(research.get('pain_points', ['scaling challenges']))}
- Hook: {research.get('personalization', 'Noticed your recent growth')}

Product: AI-powered outreach automation that boosts reply rates and saves 10+ hours/week

Write a 3-4 sentence email that:
1. References their specific problem/pain point if provided
2. Shows you understand their industry
3. Offers clear value
4. Includes [CAL_LINK] for calendar booking

Keep it natural and conversational. Don't sound like a salesperson.

IMPORTANT: Return ONLY valid JSON, no markdown formatting, no extra text.

Format:
{{"subject": "brief subject line", "body": "email body with [CAL_LINK] placeholder", "followups": ["follow-up 1", "follow-up 2"]}}"""

    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=500
        )
        
        text = completion.choices[0].message.content.strip()
        
        # Clean and extract JSON
        json_text = clean_json_response(text)
        result = json.loads(json_text)
        
        # Ensure required fields
        if "subject" not in result:
            result["subject"] = f"Quick question about {lead.get('company', 'AI automation')}"
        if "body" not in result:
            result["body"] = f"Hi {lead.get('name', 'there')}, wanted to reach out about AI automation. [CAL_LINK]"
        if "followups" not in result or not isinstance(result["followups"], list) or len(result["followups"]) == 0:
            result["followups"] = [
                "Just checking in — did you get my previous message?",
                "Last follow-up — happy to send a quick demo if helpful!"
            ]
        
        return result
        
    except json.JSONDecodeError as e:
        print(f"⚠️ JSON parsing failed. Raw response: {text[:200] if 'text' in locals() else 'N/A'}")
        print(f"   Error: {e}")
        # Return fallback
        return {
            "subject": f"Quick question about {lead.get('company', 'AI automation')}",
            "body": f"Hi {lead.get('name', 'there')},\n\nI help {lead.get('company', 'companies')} automate their outreach using AI. Our system personalizes at scale and boosts reply rates.\n\nWorth a quick 15-min chat? [CAL_LINK]\n\nBest,\nYour SDR Team",
            "followups": [
                "Following up on my message about AI outreach automation — would this be helpful?",
                "Last check-in before I pause outreach. Let me know if you'd like to see a demo!"
            ]
        }
    except Exception as e:
        print(f"⚠️ Groq generation failed: {e}")
        return {
            "subject": f"Quick question about {lead.get('company', 'AI automation')}",
            "body": f"Hi {lead.get('name', 'there')},\n\nI help companies automate outreach using AI. [CAL_LINK]",
            "followups": [
                "Following up — would this be helpful?",
                "Last check-in before I pause outreach."
            ]
        }


def research_lead_groq(lead: dict) -> dict:
    """Research lead using Groq"""
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    
    # Extract problem signal
    problem_signal = lead.get('notes', 'N/A')
    
    prompt = f"""Analyze this sales lead and provide insights.

Lead:
- Name: {lead.get('name', 'Unknown')}
- Industry: {lead.get('role', 'N/A')}
- Company: {lead.get('company', 'N/A')}
- Problem Signal: {problem_signal}

Based on the problem signal and industry, identify specific pain points and create a personalization hook.

IMPORTANT: Return ONLY valid JSON, no markdown formatting, no extra text.

Format:
{{"company_summary": "one sentence about the company", "role_insight": "what people in this industry care about", "pain_points": ["pain 1", "pain 2", "pain 3"], "personalization": "1-2 sentence hook that references their problem signal"}}"""

    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
            max_tokens=350
        )
        
        text = completion.choices[0].message.content.strip()
        
        # Clean and extract JSON
        json_text = clean_json_response(text)
        result = json.loads(json_text)
        
        # Validate structure
        required_keys = ["company_summary", "role_insight", "pain_points", "personalization"]
        for key in required_keys:
            if key not in result:
                raise ValueError(f"Missing required key: {key}")
        
        return result
        
    except Exception as e:
        print(f"⚠️ Groq research failed: {e}")
        # Fallback research
        return {
            "company_summary": f"{lead.get('company', 'The company')} is a growing business focusing on scaling operations",
            "role_insight": f"Companies in {lead.get('role', 'this industry')} typically focus on efficiency and ROI",
            "pain_points": [
                "Time-consuming manual outreach",
                "Low email reply rates",
                "Difficulty scaling sales pipeline"
            ],
            "personalization": f"I noticed {lead.get('company', 'your company')} might benefit from automating your outreach process"
        }