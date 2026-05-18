import os
import shutil
import pandas as pd
from typing import Dict

# Paths to synchronize
PRIMARY_CSV = "dataset_management/fedmedflow_accurate_dataset.csv"
FALLBACK_CSV = "fedmedflow_accurate_dataset.csv"

def sync_csv_files():
    """Synchronizes primary CSV to backup locations to maintain backward compatibility."""
    if os.path.exists(PRIMARY_CSV):
        shutil.copy2(PRIMARY_CSV, FALLBACK_CSV)

def load_csv() -> pd.DataFrame:
    """Loads the primary CSV dataset as a pandas DataFrame."""
    if not os.path.exists(PRIMARY_CSV):
        if os.path.exists(FALLBACK_CSV):
            # Restore from fallback if primary got deleted
            os.makedirs(os.path.dirname(PRIMARY_CSV), exist_ok=True)
            shutil.copy2(FALLBACK_CSV, PRIMARY_CSV)
        else:
            # Create an empty template
            df = pd.DataFrame(columns=[
                'name', 'category', 'symptoms', 'severity', 
                'diet_to_eat', 'diet_to_avoid', 'medicine_name', 
                'safe_tip', 'dangerous_myth', 'base_dosage_mg'
            ])
            df.to_csv(PRIMARY_CSV, index=False)
            return df
            
    return pd.read_csv(PRIMARY_CSV)

def append_disease_to_csv(disease_dict: Dict) -> bool:
    """Appends a new disease record to the CSV file safely."""
    try:
        df = load_csv()
        new_row = pd.DataFrame([disease_dict])
        df = pd.concat([df, new_row], ignore_index=True)
        df.to_csv(PRIMARY_CSV, index=False)
        sync_csv_files()
        return True
    except Exception as e:
        print(f"❌ Error appending to CSV: {e}")
        return False

def update_disease_in_csv(old_name: str, updated_dict: Dict) -> bool:
    """Updates all rows in the CSV matching old_name with new fields."""
    try:
        df = load_csv()
        # Find matches (case-insensitive)
        matches = df['name'].str.lower() == old_name.lower()
        
        if not matches.any():
            # If no matches, append as new row
            return append_disease_to_csv(updated_dict)
            
        # Update matching columns
        for key, value in updated_dict.items():
            if key in df.columns:
                df.loc[matches, key] = value
                
        df.to_csv(PRIMARY_CSV, index=False)
        sync_csv_files()
        return True
    except Exception as e:
        print(f"❌ Error updating CSV: {e}")
        return False

def delete_disease_from_csv(disease_name: str) -> bool:
    """Removes all rows from the CSV matching the disease name."""
    try:
        df = load_csv()
        original_len = len(df)
        df = df[df['name'].str.lower() != disease_name.lower()]
        
        if len(df) == original_len:
            return False
            
        df.to_csv(PRIMARY_CSV, index=False)
        sync_csv_files()
        return True
    except Exception as e:
        print(f"❌ Error deleting from CSV: {e}")
        return False
