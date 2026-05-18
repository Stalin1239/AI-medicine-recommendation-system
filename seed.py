import pandas as pd
from database import engine, session, Disease, Base

def seed_data():
    # 1. Wipe everything to start fresh
    print("Clearing old data...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    # 2. Load your master dataset
    df = pd.read_csv('healthos_master_dataset.csv')
    
    # 3. Carefully add each row
    for index, row in df.iterrows():
        item = Disease(
            name=row['name'],
            symptoms=row['symptoms'],
            severity=int(row['severity']),
            medicine_name=row['medicine_name'],
            base_dosage_mg=int(row['base_dosage_mg']),
            diet_to_eat=row['diet_to_eat'],
            diet_to_avoid=row['diet_to_avoid'],
            safe_tip=row['safe_tip'],
            dangerous_myth=row['dangerous_myth']
        )
        session.add(item)
    
    session.commit()
    print(f"Successfully loaded {len(df)} unique diseases.")

if __name__ == "__main__":
    seed_data()