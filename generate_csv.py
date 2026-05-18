import pandas as pd
import random

medical_knowledge = {
    "Typhoid": ["High fever", "Rose spots", "Stomach pain", "Coated tongue"],
    "Bronchitis": ["Wheezing", "Chest congestion", "Persistent cough", "Shortness of breath"],
    "Acne": ["Oily skin", "Pimples", "Red bumps", "Blackheads"],
    "Dehydration": ["Extreme thirst", "Dry mouth", "Dark urine", "Dizziness"],
    "Common Cold": ["Runny nose", "Sneezing", "Sore throat", "Mild fever"],
    "Vitamin D Deficiency": ["Bone pain", "Muscle weakness", "Hair loss", "Mood changes"],
    "Acidity": ["Heartburn", "Sour burps", "Bloating", "Burning sensation in chest"],
    "Allergic Rhinitis": ["Watery eyes", "Itchy nose", "Constant sneezing", "Puffy eyelids"],
    "Influenza": ["High fever", "Chills", "Severe body ache", "Dry cough"],
    "Diarrhea": ["Loose stools", "Abdominal cramps", "Dehydration", "Urgency"],
    "Eczema": ["Dry skin", "Itchy patches", "Red inflammation", "Cracked skin"],
    "Gastritis": ["Upper stomach pain", "Nausea", "Indigestion", "Feeling full after small meal"],
    "Food Poisoning": ["Projectile vomiting", "Diarrhea", "Fever", "Abdominal cramps"],
    "Sinusitis": ["Facial pressure", "Stuffed nose", "Thick yellow mucus", "Headache"],
    "Anemia": ["Pale skin", "Cold hands", "Extreme fatigue", "Brittle nails"],
    "Sunburn": ["Red painful skin", "Peeling skin", "Blisters", "Hot to touch"],
    "Fungal Infection": ["Ring-shaped rash", "Itching between toes", "Discolored nails", "Scaly skin"],
    "Amoebiasis": ["Bloody stools", "Tenesmus", "Stomach cramps", "Weight loss"],
    "Dengue": ["Retro-orbital pain", "High fever", "Bleeding gums", "Joint pain"],
    "Heat Rash": ["Prickly heat", "Small red bumps", "Itching in sweat areas", "Mild swelling"],
    "Asthma": ["Chest tightness", "Difficulty breathing", "Wheezing sounds", "Night cough"],
    "Heat Stroke": ["No sweating", "Rapid pulse", "Confusion", "Body temp above 104F"],
    "Chickenpox": ["Fluid-filled blisters", "Intense itching", "Fever", "Loss of appetite"],
    "Malaria": ["Shivering chills", "Profuse sweating", "Cyclical fever", "Splenomegaly"]
}

def create_final_csv():
    df = pd.read_csv('cleaned_healthos_dataset.csv')
    
    def apply_signature(name):
        # Match base name to medical knowledge
        base_name = name.split(' (')[0].strip()
        if base_name in medical_knowledge:
            signature = medical_knowledge[base_name]
            # Pick 3-4 symptoms and shuffle them
            selected = random.sample(signature, random.randint(3, 4))
            return ", ".join(selected)
        return "Fever, Fatigue"

    df['symptoms'] = df['name'].apply(apply_signature)
    df.to_csv('fedmedflow_final_dataset.csv', index=False)
    print("✅ Created fedmedflow_final_dataset.csv with unique medical signatures.")

if __name__ == "__main__":
    create_final_csv()