import pandas as pd
import re

def clean_and_prepare_data():
    print("--- Cleaning Dataset for FedMedFlow ---")
    df = pd.read_csv('healthos_master_dataset.csv')

    # 1. CLEAN NAMES: Group "Typhoid (Variant 1)" and "Typhoid (Variant 3)" into just "Typhoid"
    def strip_variant(name):
        return re.sub(r'\s*\(Variant\s+\d+\)', '', name).strip()

    df['name'] = df['name'].apply(strip_variant)

    # 2. CLEAN SYMPTOMS: Standardize text
    # This ensures "Fever, Cough" and "cough, fever" are treated similarly
    def standardize_symptoms(s):
        parts = [p.strip().lower() for p in str(s).split(',')]
        parts.sort() # Sorting helps the model see the combination, not the order
        return ", ".join(parts)

    df['symptoms'] = df['symptoms'].apply(standardize_symptoms)

    # 3. Save the Cleaned Version
    df.to_csv('cleaned_healthos_dataset.csv', index=False)
    
    print(f"✅ Success! Reduced unique labels from 1000 down to {df['name'].nunique()}.")
    print("Now use 'cleaned_healthos_dataset.csv' in your train_model.py script.")

if __name__ == "__main__":
    clean_and_prepare_data()