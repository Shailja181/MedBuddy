"""
MedBuddy Conflict Engine
Handles drug-drug interactions, cross-allergy checks, duplicate therapy detection,
and safe alternative suggestions.
"""

from typing import List, Dict, Any, Optional

# ==========================================
# KNOWLEDGE BASE & MAPPINGS
# ==========================================

# Cross-reactive drug classes for advanced allergy detection
DRUG_CLASSES = {
    "penicillins": ["penicillin", "amoxicillin", "ampicillin", "augmentin", "piperacillin"],
    "nsaids": ["ibuprofen", "aspirin", "naproxen", "diclofenac", "celecoxib", "meloxicam", "indomethacin"],
    "sulfa": ["sulfamethoxazole", "bactrim", "septra", "sulfasalazine"],
    "statins": ["atorvastatin", "rosuvastatin", "simvastatin", "pravastatin", "lovastatin"],
    "ace_inhibitors": ["lisinopril", "enalapril", "ramipril", "captopril", "benazepril"],
    "arbs": ["losartan", "valsartan", "candesartan", "irbesartan", "telmisartan"],
    "antihistamines": ["cetirizine", "loratadine", "fexofenadine", "levocetirizine", "diphenhydramine"],
    "ppi": ["omeprazole", "pantoprazole", "esomeprazole", "rabeprazole", "lansoprazole"],
    "anti_diabetic": ["glicduo", "metformin", "glimepiride"],
    "supplements": ["silical", "hemuflin md", "opline d3 60 k", "opline", "hemuflin"],
    "blood_thinners": ["ecosprin", "aspirin", "ecosprin av 75"]
}

# Major Drug-Drug Interactions (Pairwise)
DRUG_INTERACTIONS = [
    {
        "pair": {"aspirin", "warfarin"},
        "severity": "CRITICAL",
        "warning": "Severe risk of major bleeding when combining Aspirin and Warfarin."
    },
    {
        "pair": {"ibuprofen", "aspirin"},
        "severity": "WARNING",
        "warning": "Concomitant use may increase stomach ulcer risk and reduce antiplatelet efficacy of Aspirin."
    },
    {
        "pair": {"lisinopril", "spironolactone"},
        "severity": "CRITICAL",
        "warning": "High risk of hyperkalemia (dangerously high blood potassium levels)."
    },
    {
        "pair": {"sertraline", "tramadol"},
        "severity": "CRITICAL",
        "warning": "Risk of Serotonin Syndrome when taking SSRIs with Tramadol."
    },
    {
        "pair": {"atorvastatin", "clarithromycin"},
        "severity": "WARNING",
        "warning": "Clarithromycin increases statin concentrations, raising muscle toxicity/rhabdomyolysis risk."
    },
    {
        "pair": {"metformin", "contrast"},
        "severity": "WARNING",
        "warning": "Risk of lactic acidosis if taking Metformin prior to intravascular iodinated contrast procedures."
    }
]

# Alternative Medication Substitutes Database
SUBSTITUTES_DB = {
    "aspirin": ["Paracetamol", "Ibuprofen", "Acetaminophen"],
    "ibuprofen": ["Paracetamol", "Naproxen", "Acetaminophen"],
    "paracetamol": ["Ibuprofen", "Naproxen"],
    "acetaminophen": ["Ibuprofen", "Naproxen"],
    "amoxicillin": ["Azithromycin", "Ciprofloxacin", "Clarithromycin", "Erythromycin"],
    "penicillin": ["Erythromycin", "Azithromycin", "Clarithromycin"],
    "cetirizine": ["Loratadine", "Fexofenadine", "Levocetirizine"],
    "metformin": ["Glipizide", "Sitagliptin", "Empagliflozin", "Pioglitazone"],
    "atorvastatin": ["Rosuvastatin", "Simvastatin", "Pravastatin"],
    "omeprazole": ["Pantoprazole", "Esomeprazole", "Famotidine"],
    "lisinopril": ["Losartan", "Valsartan", "Amlodipine"],
    "glicduo xr": ["Glimepiride + Metformin", "Sitagliptin", "Gliclazide"],
    "glicduo": ["Glimepiride + Metformin", "Sitagliptin", "Gliclazide"],
    "silical": ["Calcimax", "Shelcal", "Gemcal"],
    "hemuflin md": ["Dexorange", "Orofer", "Tonoferon"],
    "hemuflin": ["Dexorange", "Orofer", "Tonoferon"],
    "hemylin": ["Dexorange", "Orofer", "Tonoferon"],
    "opline d3": ["UPRISE-D3", "Depura", "Calcirol"],
    "opline": ["UPRISE-D3", "Depura", "Calcirol"],
    "ecosprin av 75": ["Clopidogrel", "Prasugrel"],
    "ecosprin": ["Clopidogrel", "Prasugrel"]
}


# ==========================================
# CORE ENGINE FUNCTIONS
# ==========================================

def _clean_str(text: Optional[str]) -> str:
    """Helper to normalize text for comparison."""
    return (text or "").strip().lower()


def _get_drug_classes_for_med(med_name: str) -> List[str]:
    """Finds all drug class categories associated with a given medicine name."""
    clean_med = _clean_str(med_name)
    matched_classes = []
    for cls_name, members in DRUG_CLASSES.items():
        if any(member in clean_med or clean_med in member for member in members):
            matched_classes.append(cls_name)
    return matched_classes


def check_conflicts(medicine_name: str, user_allergies: List[str], user_medicines: List[str]) -> List[Dict[str, Any]]:
    """
    Comprehensive conflict checking for a target medicine against user allergies and current active medicines.
    
    Returns a list of structured warning objects containing message, severity, and type.
    """
    conflicts = []
    target_med = _clean_str(medicine_name)

    if not target_med:
        return conflicts

    # 1. Check Exact & Cross-Allergy Conflicts
    target_classes = _get_drug_classes_for_med(target_med)
    for allergy in user_allergies:
        allergy_clean = _clean_str(allergy)
        if not allergy_clean:
            continue

        # Exact substring allergy match
        if allergy_clean in target_med or target_med in allergy_clean:
            conflicts.append({
                "type": "ALLERGY",
                "severity": "CRITICAL",
                "message": f"Allergy Alert: Direct match found for '{allergy}'."
            })
            continue

        # Cross-allergy class check
        allergy_classes = _get_drug_classes_for_med(allergy_clean)
        shared_classes = set(target_classes).intersection(set(allergy_classes))
        if shared_classes or (allergy_clean in DRUG_CLASSES and target_classes and allergy_clean in target_classes):
            conflicts.append({
                "type": "CROSS_ALLERGY",
                "severity": "WARNING",
                "message": f"Cross-Allergy Risk: '{medicine_name}' belongs to the same class as your allergen '{allergy}'."
            })

    # 2. Check Duplicate Therapy
    for existing_med in user_medicines:
        existing_clean = _clean_str(existing_med)
        if existing_clean == target_med:
            conflicts.append({
                "type": "DUPLICATE",
                "severity": "WARNING",
                "message": f"Duplicate Therapy: You are already taking '{medicine_name}'."
            })

    # 3. Check Drug-Drug Interactions
    for existing_med in user_medicines:
        existing_clean = _clean_str(existing_med)
        for interaction in DRUG_INTERACTIONS:
            pair = interaction["pair"]
            # Check if target_med and existing_med match the interaction pair
            if any(p in target_med for p in pair) and any(p in existing_clean for p in pair):
                # Ensure it's two distinct matched drugs
                if not (target_med in existing_clean and existing_clean in target_med):
                    conflicts.append({
                        "type": "DRUG_INTERACTION",
                        "severity": interaction["severity"],
                        "message": f"Interaction with '{existing_med}': {interaction['warning']}"
                    })

    return conflicts


def suggest_alternatives(medicine_name: str, user_allergies: List[str] = None) -> Dict[str, Any]:
    """
    Recommends safe drug alternatives by filtering candidates against user allergens and drug classes.
    """
    if user_allergies is None:
        user_allergies = []

    target_med = _clean_str(medicine_name)
    raw_candidates = SUBSTITUTES_DB.get(target_med, [])

    safe_alternatives = []
    
    for candidate in raw_candidates:
        candidate_clean = _clean_str(candidate)
        candidate_classes = _get_drug_classes_for_med(candidate_clean)
        
        is_unsafe = False
        for allergy in user_allergies:
            allergy_clean = _clean_str(allergy)
            if not allergy_clean:
                continue

            # Check direct match
            if allergy_clean in candidate_clean or candidate_clean in allergy_clean:
                is_unsafe = True
                break

            # Check class match
            allergy_classes = _get_drug_classes_for_med(allergy_clean)
            if set(candidate_classes).intersection(set(allergy_classes)):
                is_unsafe = True
                break

        if not is_unsafe:
            safe_alternatives.append(candidate)

    return {
        "medicine": medicine_name,
        "alternatives": safe_alternatives if safe_alternatives else ["No safe automated substitutes found. Consult your physician."],
        "disclaimer": "Medical disclaimer: Consult a licensed healthcare provider before making any medication changes."
    }