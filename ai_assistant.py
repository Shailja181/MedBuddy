import os
import json

try:
    from anthropic import Anthropic
    _client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", ""))
except Exception:
    _client = None

SYSTEM = """You are MedBuddy AI, a friendly health information assistant.
You help parse prescriptions, recommend personalized diet charts, suggest safe alternative medicines, and provide health guidance.

Rules:
- Answer clearly and concisely.
- Never diagnose independently.
- Always encourage medical professional consultation for severe symptoms.
- When speaking about medicines, use commonly known generic names.
"""


def answer_query(question: str, context: dict) -> str:
    if not os.environ.get("ANTHROPIC_API_KEY") or _client is None:
        return _fallback(question, context)
    try:
        msg = _client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=600,
            system=SYSTEM,
            messages=[{"role": "user", "content": f"CONTEXT:\n{context}\n\nQUESTION: {question}"}],
        )
        return msg.content[0].text
    except Exception as e:
        return _fallback(question, context)


def generate_diet_and_magnet(ocr_text: str, user_condition: str) -> dict:
    prompt = f"""
Based on this extracted prescription text:
"{ocr_text}"
And health condition: "{user_condition}"

Return ONLY a JSON object (no markdown, no code fences) with this shape:
{{
  "summary": "2 sentence prescription summary",
  "diet_chart": {{
    "breakfast": "Recommended breakfast options",
    "lunch": "Recommended lunch options",
    "dinner": "Recommended dinner options",
    "snacks": "Healthy snacks",
    "foods_to_avoid": "Specific foods to avoid"
  }},
  "fridge_magnet": {{
    "morning": "Morning schedule & meds",
    "afternoon": "Afternoon schedule & meds",
    "evening": "Evening schedule & meds",
    "night": "Bedtime routine & meds",
    "key_notes": "Important daily reminder"
  }}
}}
"""
    if not _client or not os.environ.get("ANTHROPIC_API_KEY"):
        return _fallback_diet(user_condition)
    try:
        res = _client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=800,
            system="Return raw JSON only. No markdown fences.",
            messages=[{"role": "user", "content": prompt}]
        )
        txt = res.content[0].text.strip()
        if txt.startswith("```"):
            txt = txt.split("```")[1]
            if txt.startswith("json"):
                txt = txt[4:]
        return json.loads(txt.strip())
    except Exception:
        return _fallback_diet(user_condition)


def ai_alternatives(medicine_name: str, allergies: list, rule_alternatives: list) -> dict:
    """Claude-enhanced alternative suggestions. Falls back to rule-based if AI is offline."""
    if not _client or not os.environ.get("ANTHROPIC_API_KEY"):
        return {
            "alternatives": rule_alternatives,
            "reasoning": "Rule-based suggestions (AI offline).",
            "source": "rules"
        }

    prompt = f"""
A patient with these allergies: {allergies}
Wants to know safe alternatives to: {medicine_name}

Rule-based suggestions already gave: {rule_alternatives}

Return ONLY a JSON object (no markdown) with:
{{
  "alternatives": ["drug name 1", "drug name 2", "drug name 3"],
  "reasoning": "One short sentence explaining why these are safer for this patient.",
  "warnings": "Any critical caveats they must know before switching."
}}

Keep alternatives to well-known generic names. Never suggest anything the patient is allergic to.
"""
    try:
        res = _client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=500,
            system="You are a clinical pharmacist assistant. Return raw JSON only.",
            messages=[{"role": "user", "content": prompt}]
        )
        txt = res.content[0].text.strip()
        if txt.startswith("```"):
            txt = txt.split("```")[1]
            if txt.startswith("json"):
                txt = txt[4:]
        result = json.loads(txt.strip())
        result["source"] = "ai"
        return result
    except Exception:
        return {
            "alternatives": rule_alternatives,
            "reasoning": "Rule-based fallback (AI parse failed).",
            "source": "rules"
        }


def _fallback_diet(condition: str) -> dict:
    return {
        "summary": f"Prescription uploaded for condition: {condition or 'General Health'}.",
        "diet_chart": {
            "breakfast": "Oatmeal with almonds, boiled egg white, warm lemon water.",
            "lunch": "Steamed vegetables, grilled chicken or tofu, brown rice, bowl of curd.",
            "dinner": "Light vegetable soup, whole wheat roti, cooked spinach.",
            "snacks": "Roasted chana, green tea, fresh seasonal fruit.",
            "foods_to_avoid": "Processed sugars, high-sodium snacks, excess caffeine."
        },
        "fridge_magnet": {
            "morning": "08:00 AM — Breakfast and prescribed morning doses.",
            "afternoon": "01:30 PM — Lunch and hydration check.",
            "evening": "06:00 PM — Light exercise or yoga asanas.",
            "night": "10:00 PM — Bedtime dosage and full rest.",
            "key_notes": "Drink 3 litres of water daily and record vitals."
        }
    }


def _fallback(q: str, ctx: dict) -> str:
    ql = q.lower()
    if "medicine" in ql or "medication" in ql:
        meds = ctx.get("medicines", [])
        if not meds: return "You have no active medicines saved."
        return "Your active medicines:\n" + "\n".join(f"• {m['name']} — {m.get('dosage','')}" for m in meds)
        
    if "allerg" in ql:
        allergies = ctx.get("allergies", [])
        if not allergies: return "You have no allergies recorded."
        return "Your recorded allergies:\n" + "\n".join(f"⚠ {a['name']} ({a.get('severity', 'moderate')})" for a in allergies)
        
    if "stress" in ql:
        return "Here are 4 tips to manage stress:\n\n1. Practice deep breathing exercises (try the 'Box Breathing' technique).\n2. Maintain a regular sleep schedule of 7-8 hours.\n3. Try a beginner Yoga flow (like the ones in your MedBuddy Exercises tab!).\n4. Reduce caffeine intake in the afternoon."
        
    if "blood pressure" in ql or "bp" in ql:
        return "A healthy blood pressure range for most adults is typically:\n\n• **Systolic**: Less than 120 mmHg\n• **Diastolic**: Less than 80 mmHg\n\n*(Note: 120-129 is considered elevated. Always consult your doctor for personalized targets.)*"
        
    return "MedBuddy AI is ready to help manage your health schedules, diets, and yoga practices. (Currently in demo offline mode - try asking about your medicines, allergies, stress, or BP!)"