import sys
import os
import sqlite3
import pandas as pd

# Reconfigure stdout/stderr to support UTF-8 on Windows terminals
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Add parent directory to path to allow importing dosage_engine
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
try:
    from dosage_engine import calculate_dosage
except ImportError:
    # Inline fallback for calculate_dosage if import fails
    def calculate_dosage(base_mg, weight_kg, age):
        if base_mg == 0: return "Consult Doctor"
        if age < 12 or weight_kg < 35:
            final_dose = (weight_kg / 70) * base_mg
            return f"{round(final_dose, 2)} mg (Pediatric Adjusted)"
        elif weight_kg > 90:
            return f"{base_mg} mg (Standard Adult Max - Monitor closely)"
        return f"{base_mg} mg (Standard Adult Dose)"

# Medical stop words to ignore during symptom tokenization
MEDICAL_STOP_WORDS = {
    'i', 'have', 'am', 'and', 'or', 'feel', 'symptom', 'symptoms', 'a', 'of', 
    'with', 'the', 'my', 'is', 'in', 'to', 'for', 'it', 'some', 'mild', 'severe', 
    'feeling', 'pain', 'bad', 'got', 'has', 'very', 'constant', 'starting'
}

def clean_tokens(text: str):
    """Normalize and tokenize text, filtering out stop words."""
    if not text or pd.isna(text):
        return set()
    cleaned = text.lower().replace(",", " ").replace(".", " ").replace(";", " ").replace("-", " ")
    words = cleaned.split()
    return set(w.strip() for w in words if w.strip() not in MEDICAL_STOP_WORDS and len(w.strip()) > 2)

def predict_fallback(symptoms_text: str, age: int = 30, weight: float = 70.0):
    """
    Scans the database or CSV dataset using a symptom overlap & keyword similarity algorithm.
    Weights overlaps by disease severity and checks for exact name matches.
    """
    input_tokens = clean_tokens(symptoms_text)
    if not input_tokens:
        return None

    # Try to load diseases from SQLite first, fallback to CSV
    diseases = []
    db_path = "health_app.db"
    
    if os.path.exists(db_path):
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            rows = cursor.execute("SELECT name, category, symptoms, severity, diet_to_eat, diet_to_avoid, medicine_name, safe_tip, dangerous_myth, base_dosage_mg FROM diseases").fetchall()
            for r in rows:
                diseases.append({
                    "name": r[0],
                    "category": r[1],
                    "symptoms": r[2],
                    "severity": int(r[3]),
                    "diet_to_eat": r[4],
                    "diet_to_avoid": r[5],
                    "medicine_name": r[6],
                    "safe_tip": r[7],
                    "dangerous_myth": r[8],
                    "base_dosage_mg": int(r[9])
                })
            conn.close()
        except Exception as e:
            print(f"[WARN] SQLite lookup failed during fallback prediction: {e}")
            diseases = []

    # Fallback to CSV if SQLite is empty or failed
    if not diseases:
        csv_paths = [
            "dataset_management/fedmedflow_accurate_dataset.csv",
            "fedmedflow_accurate_dataset.csv",
            "../dataset_management/fedmedflow_accurate_dataset.csv"
        ]
        csv_path = None
        for p in csv_paths:
            if os.path.exists(p):
                csv_path = p
                break
        
        if csv_path:
            try:
                df = pd.read_csv(csv_path)
                for _, row in df.iterrows():
                    diseases.append({
                        "name": row['name'],
                        "category": row['category'],
                        "symptoms": row['symptoms'],
                        "severity": int(row['severity']),
                        "diet_to_eat": row['diet_to_eat'],
                        "diet_to_avoid": row['diet_to_avoid'],
                        "medicine_name": row['medicine_name'],
                        "safe_tip": row['safe_tip'],
                        "dangerous_myth": row['dangerous_myth'],
                        "base_dosage_mg": int(row['base_dosage_mg'])
                    })
            except Exception as e:
                print(f"[ERROR] Failed to load fallback CSV: {e}")

    if not diseases:
        print("[ERROR] No disease data available for Fallback Prediction.")
        return None

    best_match = None
    max_score = -1.0

    # Normalization scoring loop
    for d in diseases:
        disease_tokens = clean_tokens(d["symptoms"])
        if not disease_tokens:
            continue
            
        intersection = input_tokens.intersection(disease_tokens)
        if not intersection:
            continue
            
        # 1. Base Jaccard Overlap
        overlap_score = len(intersection) / len(input_tokens.union(disease_tokens))
        
        # 2. Disease name match bonus
        name_lower = d["name"].lower()
        for token in input_tokens:
            if token in name_lower or name_lower in token:
                overlap_score += 0.25 # Significant boost for exact name mention
                
        # 3. Severity Weighting factor (favors higher-risk matches in tie-breakers)
        severity_factor = 1.0 + (d["severity"] / 100.0) # Up to 10% boost for severity
        final_score = overlap_score * severity_factor
        
        if final_score > max_score:
            max_score = final_score
            best_match = d

    if not best_match:
        return None

    # Calculate proportional dosage using Clark's rule
    calculated_dose = calculate_dosage(best_match["base_dosage_mg"], weight, age)
    
    # Cap confidence score in a realistic range for rule-based systems
    confidence = min(0.85, max(0.20, max_score))
    
    # Prepare standard response
    return {
        "status": "Success",
        "disease_name": best_match["name"],
        "confidence": confidence,
        "is_fallback": True,
        "recommended_medicine": best_match["medicine_name"],
        "dosage": calculated_dose,
        "safe_tip": best_match["safe_tip"],
        "dangerous_myth": best_match["dangerous_myth"],
        "local_verified_data": {
            "disease_name": best_match["name"],
            "severity": best_match["severity"],
            "standard_medicine": best_match["medicine_name"],
            "calculated_dosage": calculated_dose,
            "safe_tip": best_match["safe_tip"],
            "dangerous_myth": best_match["dangerous_myth"],
            "diet_tips": {
                "eat": best_match["diet_to_eat"],
                "avoid": best_match["diet_to_avoid"]
            }
        }
    }

if __name__ == "__main__":
    # Small test loop
    test_res = predict_fallback("cough, high fever, runny nose", age=25, weight=75)
    print("Fallback Prediction Result:")
    print(test_res)
