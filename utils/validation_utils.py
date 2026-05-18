import re
import pandas as pd
from typing import Dict, List, Tuple
from sqlalchemy.orm import Session
from database import Disease

def validate_disease_data(data: Dict, csv_path: str, db_session: Session = None, is_edit: bool = False, original_name: str = None) -> Tuple[bool, List[str]]:
    """
    Validates disease fields for completeness, proper syntax, ranges, and duplicates.
    
    Returns:
    - Tuple[bool, List[str]]: (is_valid, list_of_error_messages)
    """
    errors = []

    # 1. Check Missing/Required Fields
    required_fields = [
        'name', 'category', 'symptoms', 'severity', 
        'diet_to_eat', 'diet_to_avoid', 'medicine_name', 
        'safe_tip', 'dangerous_myth', 'base_dosage_mg'
    ]
    for field in required_fields:
        if field not in data or data[field] is None or str(data[field]).strip() == "":
            errors.append(f"Field '{field}' is required and cannot be empty.")

    if errors:
        return False, errors

    # 2. Extract and clean data values
    name = str(data['name']).strip()
    category = str(data['category']).strip()
    symptoms = str(data['symptoms']).strip()
    medicine = str(data['medicine_name']).strip()
    
    # 3. Validate Severity Range (1-10)
    try:
        severity = int(data['severity'])
        if severity < 1 or severity > 10:
            errors.append("Severity score must be an integer between 1 and 10.")
    except (ValueError, TypeError):
        errors.append("Severity must be a valid integer.")

    # 4. Validate Base Dosage
    try:
        dosage = int(data['base_dosage_mg'])
        if dosage <= 0:
            errors.append("Base dosage must be a positive integer (mg).")
    except (ValueError, TypeError):
        errors.append("Base dosage must be a valid integer.")

    # 5. Validate Symptoms Formatting
    # Should be a comma-separated list of symptoms. Each symptom should contain only characters/spaces.
    symptom_list = [s.strip() for s in symptoms.split(',')]
    if len(symptom_list) == 0 or (len(symptom_list) == 1 and symptom_list[0] == ""):
        errors.append("Symptoms must be a comma-separated list.")
    else:
        for idx, sym in enumerate(symptom_list):
            if not sym:
                errors.append(f"Symptom #{idx+1} is empty (check double commas).")
                continue
            if len(sym) < 2:
                errors.append(f"Symptom '{sym}' is too short (must be at least 2 characters).")
            # Allow alphabet, spaces, hyphens, and slashes (common in medical terms)
            if not re.match(r"^[a-zA-Z\s\-/()]+$", sym):
                errors.append(f"Symptom '{sym}' contains invalid characters. Only letters, spaces, hyphens, and parentheses are allowed.")

    # 6. Check Duplicate Entries
    if not is_edit or (is_edit and name.lower() != original_name.lower()):
        # Check SQLite DB
        if db_session:
            existing_db = db_session.query(Disease).filter(Disease.name.ilike(name)).first()
            if existing_db:
                errors.append(f"A disease with the name '{name}' already exists in the database.")

        # Check CSV Dataset
        try:
            df = pd.read_csv(csv_path)
            if 'name' in df.columns:
                existing_csv = df[df['name'].str.lower() == name.lower()]
                if not existing_csv.empty:
                    errors.append(f"A disease with the name '{name}' already exists in the CSV dataset.")
        except Exception as e:
            # If CSV doesn't exist or is unreadable, skip duplicate check for CSV but log error
            print(f"⚠️ Could not read CSV for duplicate check: {e}")

    return len(errors) == 0, errors
