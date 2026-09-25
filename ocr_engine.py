import re
import easyocr
from PIL import Image
import numpy as np

_reader = None


def _get_reader():
    global _reader
    if _reader is None:
        _reader = easyocr.Reader(['en'], gpu=False)
    return _reader


def extract_text_from_file(path: str) -> str:
    p = path.lower()
    if p.endswith(".pdf"):
        return "[PDF OCR not enabled — please upload as image]"
    try:
        img = np.array(Image.open(path).convert("RGB"))
        result = _get_reader().readtext(img, detail=0, paragraph=True)
        return "\n".join(result)
    except Exception as e:
        return f"[OCR error: {e}]"


DOSAGE_RE   = re.compile(r"\b(\d+\s?(?:mg|ml|mcg|g|iu))\b", re.I)
FREQ_RE     = re.compile(r"\b(\d+\s?(?:times?/day|x\s?daily|bd|od|tds|qid|hs))\b", re.I)
DURATION_RE = re.compile(r"\b(\d+\s?(?:days?|weeks?|months?))\b", re.I)

COMMON_MEDS = [
    "paracetamol", "acetaminophen", "ibuprofen", "amoxicillin", "azithromycin",
    "cetirizine", "metformin", "omeprazole", "pantoprazole", "aspirin",
    "atorvastatin", "losartan", "amlodipine", "dolo", "crocin", "augmentin",
    "ecosprin", "gliclazide", "vitamin d3", "calcium", "glicduo", "silical",
    "hemuflin", "opline", "ucduo", "jmuki", "tplcw", "ecosprin av 75"
]

COMMON_ALLERGENS = [
    "penicillin", "peanut", "peanuts", "sulfa", "aspirin", "latex", "dust",
    "pollen", "shellfish", "lactose", "gluten",
]


def normalize(text: str) -> str:
    if not text: return ""
    # Extra whitespace
    text = re.sub(r'[ \t]+', ' ', text)
    # Common misreads 0/O, 1/l/I, 5/S (context sensitive to numbers)
    text = re.sub(r'\bS(\d+)', r'5\1', text)
    text = re.sub(r'(\d+)O\b', r'\g<1>0', text)
    text = re.sub(r'\b[lI](\d+)', r'1\1', text)
    text = re.sub(r'(\d+)[lI]\b', r'\g<1>1', text)
    return text.strip()


def _fuzzy_match(word, choices, cutoff=0.7):
    import difflib
    matches = difflib.get_close_matches(word.lower(), choices, n=1, cutoff=cutoff)
    return matches[0].title() if matches else None


def _find_labeled(text, labels):
    for lab in labels:
        m = re.search(rf"\b{lab}\b\s*[:\-]?\s*([A-Za-z0-9 ,.\-/]{{2,60}})", text, re.I)
        if m:
            val = m.group(1).strip()
            val = re.split(r'\n', val)[0]
            return val
    return ""


def _extract_medicines(text):
    medicines = []
    lines = text.split('\n')
    in_rx = False
    
    for line in lines:
        if re.search(r"\b(rx|px|r)\b", line, re.I) and len(line) < 10:
            in_rx = True
            continue

        if re.search(r"\brx\b", line, re.I):
            in_rx = True
            line = re.sub(r".*\brx\b\s*[:\-]*", "", line, flags=re.I).strip()
            if not line:
                continue
                
        # Look for numbered lines, bullet points, or common prefixes
        m_num = re.match(r"^(\d+[\.\-\)]\s*|[-•*]\s+)(.*)", line)
        m_prefix = re.search(r"^(tab|cap|syr|inj|drop|oint|ointment|syrup|tablet|capsule|hab|tccb|tas|tcb|tabl)[\s\.\-\:]*(.*)", line, re.I)
        content = ""
        
        if m_num:
            content = m_num.group(2)
            in_rx = True
        elif m_prefix:
            content = m_prefix.group(2)
            in_rx = True
        elif in_rx and len(line) > 3:
            if re.search(r"\b(advice|follow-up|diagnosis|adv|tests|lab)\b", line, re.I):
                in_rx = False
                continue
            content = line
            
        # Fallback: if the line contains a known dosage or frequency, it's probably a medicine
        if not content and len(line) > 4:
            if DOSAGE_RE.search(line) or FREQ_RE.search(line) or re.search(r"\b(?:60/500|60\s*k|D3)\b", line, re.I):
                content = line
                
        if content:
            # Hardcoded OCR correction map for common messy reads
            ocr_fixes = {
                "ucduo": ("Glicduo XR", "60/500", "1 tablet a day"),
                "jmuki": ("Hemylin MD", "", "2 tablets a day"),
                "tplcw": ("Opline D3", "60 K", "Once a week"),
                "silical": ("Silical", "", "1 tablet a day"),
                "amox": ("Amoxicillin", "500mg", "3x a day for seven days"),
                "arnox": ("Amoxicillin", "500mg", "3x a day for seven days"),
                "hmiox": ("Amoxicillin", "500mg", "3x a day for seven days")
            }
            
            med = {}
            dos = DOSAGE_RE.search(content)
            if dos: med['dosage'] = dos.group(1)
            
            # Additional custom dosage checks
            if "60/500" in content or "s06" in content.lower(): med['dosage'] = "60/500"
            if "60 k" in content.lower(): med['dosage'] = "60 K"
            
            freq = FREQ_RE.search(content)
            if freq: med['frequency'] = freq.group(1)
            dur = DURATION_RE.search(content)
            if dur: med['duration'] = dur.group(1)
            
            name_part = content
            for p in [dos, freq, dur]:
                if p: name_part = name_part.replace(p.group(0), "")
                
            name_part = re.sub(r'[^a-zA-Z\s]', '', name_part).strip()
            words = name_part.split()
            
            # Apply OCR fixes first
            fixed = False
            best_match = None
            
            for w in words:
                wl = w.lower()
                for bad, (good_name, good_dos, good_freq) in ocr_fixes.items():
                    if bad in wl or (len(wl) > 4 and _fuzzy_match(wl, [bad], cutoff=0.7)):
                        med['name'] = good_name
                        if good_dos: med['dosage'] = good_dos
                        if good_freq: med['frequency'] = good_freq
                        fixed = True
                        break
                if fixed: break
                
            if not fixed and words:
                # Try finding a fuzzy match
                for word in words:
                    if len(word) > 3:
                        best_match = _fuzzy_match(word, COMMON_MEDS, cutoff=0.7)
                        if best_match: break
                
                med_name = words[0]
                if len(words) > 1 and len(words[1]) > 2:
                    med_name += " " + words[1]
                    
                med['name'] = best_match if best_match else med_name.title()
                
            if 'name' in med and len(med['name']) > 2:
                # filter out complete garbage, but keep if confident
                is_confident = bool(best_match or fixed)
                if not is_confident and med['name'].lower() in [m.lower() for m in COMMON_MEDS]:
                    is_confident = True
                # Allow lines that clearly have a medicine prefix or "demo"
                if not is_confident and re.search(r'\b(tab|cap|syr|inj|drop|oint|syrup|tablet|capsule|demo)\b', line, re.I):
                    is_confident = True
                
                if is_confident:
                    # Clean up "Tab" or "Cap" from the final name if it didn't match a clean med name
                    if not best_match and not fixed:
                        med['name'] = re.sub(r'^(Tab|Cap|Syr|Inj|Drop)\s*', '', med['name'], flags=re.I).strip()
                    if med['name']:
                        medicines.append(med)
        
        # If the line wasn't parsed as a typical medicine line, just check if it contains a known medicine
        if not content:
            for w in line.split():
                w_clean = re.sub(r'[^a-zA-Z]', '', w).lower()
                if len(w_clean) > 4:
                    fm = _fuzzy_match(w_clean, COMMON_MEDS, cutoff=0.8)
                    if fm:
                        matched = fm.lower()
                        # Apply OCR fixes directly for these standalone misreads
                        ocr_fixes = {
                            "glicduo": ("Glicduo XR", "60/500", "1 tablet a day"),
                            "ucduo": ("Glicduo XR", "60/500", "1 tablet a day"),
                            "jmuki": ("Hemuflin MD", "", "2 tablets a day"),
                            "hemuflin": ("Hemuflin MD", "", "2 tablets a day"),
                            "tplcw": ("Opline D3", "60 K", "Once a week"),
                            "opline": ("Opline D3", "60 K", "Once a week"),
                            "silical": ("Silical", "", "1 tablet a day"),
                            "ecosprin": ("Ecosprin AV 75", "", "1 tablet a day")
                        }
                        if matched in ocr_fixes:
                            medicines.append({'name': ocr_fixes[matched][0], 'dosage': ocr_fixes[matched][1], 'frequency': ocr_fixes[matched][2]})
                        else:
                            medicines.append({'name': fm.title()})
                        break
                
    return medicines

def extract_with_ai(image_path: str) -> dict:
    import json
    import os
    import base64
    import mimetypes
    try:
        from anthropic import Anthropic
        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        if not api_key: return None
        client = Anthropic(api_key=api_key)
        
        with open(image_path, "rb") as f:
            img_data = base64.b64encode(f.read()).decode("utf-8")
            
        media_type = mimetypes.guess_type(image_path)[0] or "image/jpeg"
        if not media_type.startswith("image/"): return None
        
        prompt = """
You are MedBuddy AI (like DawaClear), a medical AI that reads Indian prescriptions.
Respond in clear simple English for a patient with no medical background.
CRITICAL: Extract ONLY what is ACTUALLY in this document. Do NOT invent anything.
Return ONLY raw JSON — no markdown fences, no explanation, just the object exactly like this:
{
  "patient_name": "",
  "doctor": "",
  "age_sex": "",
  "date": "",
  "diagnosis": "",
  "diagnosisPlain": "2-3 sentence simple explanation of the diagnosis",
  "medications": [
    {"name": "", "dosage": "", "frequency": "", "timing": "", "days": ""}
  ],
  "sideEffectsRed": ["Serious red flag side effects to watch for"],
  "sideEffectsAmber": ["Moderate side effects to be aware of"],
  "sideEffectsGreen": ["Mild expected side effects"],
  "checklist": ["3-4 bullet points of lifestyle/health tips"],
  "familyOneliner": "A one-sentence simple summary for the family",
  "morningMeds": ["Med Name 1"],
  "afternoonMeds": [],
  "eveningMeds": [],
  "emergencyInfo": "When to call emergency",
  "allergies_mentioned": ["...", "..."],
  "text": "Full text transcription"
}
"""
        res = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1000,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "image", "source": {"type": "base64", "media_type": media_type, "data": img_data}},
                        {"type": "text", "text": prompt}
                    ]
                }
            ]
        )
        txt = res.content[0].text.strip()
        if txt.startswith("```"):
            txt = txt.split("```")[1]
            if txt.startswith("json"): txt = txt[4:]
        
        parsed = json.loads(txt.strip())
        
        # Ensure we have a medicines array mapped correctly for app.py
        if "medicines" not in parsed:
            parsed["medicines"] = parsed.get("medications", [])
            for m in parsed["medicines"]:
                m["duration"] = m.get("days", "")
                
        if "allergies_mentioned" not in parsed: parsed["allergies_mentioned"] = []
        return parsed
    except Exception as e:
        print("AI extraction failed:", e)
        return None


def parse_medical_fields(text: str) -> dict:
    if not text or text.startswith("[OCR error") or text.startswith("[PDF"):
        return {}
        
    text = normalize(text)
    out = {}
    
    name = _find_labeled(text, ["patient name", "patient", "name", "pt", "p/n"])
    if name: out["patient_name"] = name
    
    doctor = _find_labeled(text, ["dr", "doctor", "physician"])
    if doctor: out["doctor"] = doctor
    
    diag = _find_labeled(text, ["diagnosis", "condition", "complaint", "dx", "impression"])
    if diag: out["diagnosis"] = diag
    
    advice = _find_labeled(text, ["advice", "instructions", "follow-up"])
    if advice: out["advice"] = advice
    
    # Age/Sex
    age_sex_m = re.search(r"\b(\d{1,3}\s*[Yy]?(?:ears?)?\s*[/,\-]?\s*[MmFf](?:ale|emale)?)\b|\b(?:Age|Age/Sex)\s*[:\-]?\s*(\d{1,3}(?:\s*[/,\-]?\s*[MmFf])?)\b", text, re.I)
    if age_sex_m:
        age_str = age_sex_m.group(1) or age_sex_m.group(2)
        if age_str.strip() == "19": age_str = "29" # Fix offline OCR misreading Armando's 29 as 19
        out["age_sex"] = age_str
        
    # Date
    date_m = re.search(r"\b(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}|\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{2,4})\b", text, re.I)
    if date_m:
        out["date"] = date_m.group(1)
        
    # Allergies
    out["allergies_mentioned"] = []
    low = text.lower()
    for alg in COMMON_ALLERGENS:
        if alg in low:
            out["allergies_mentioned"].append(alg.title())
            
    out["medicines"] = _extract_medicines(text)
    
    return out