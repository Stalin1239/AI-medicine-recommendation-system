import sqlite3

def migrate():
    conn = sqlite3.connect('health_app.db')
    cursor = conn.cursor()
    
    # Add actual_diagnosis
    try:
        cursor.execute("ALTER TABLE consultation_requests ADD COLUMN actual_diagnosis VARCHAR")
        print("Added actual_diagnosis column")
    except sqlite3.OperationalError as e:
        print(f"actual_diagnosis likely exists: {e}")
        
    # Add precautions
    try:
        cursor.execute("ALTER TABLE consultation_requests ADD COLUMN precautions TEXT")
        print("Added precautions column")
    except sqlite3.OperationalError as e:
        print(f"precautions likely exists: {e}")
        
    # Add treatment_notes
    try:
        cursor.execute("ALTER TABLE consultation_requests ADD COLUMN treatment_notes TEXT")
        print("Added treatment_notes column")
    except sqlite3.OperationalError as e:
        print(f"treatment_notes likely exists: {e}")
        
    # Add follow_up_instructions
    try:
        cursor.execute("ALTER TABLE consultation_requests ADD COLUMN follow_up_instructions TEXT")
        print("Added follow_up_instructions column")
    except sqlite3.OperationalError as e:
        print(f"follow_up_instructions likely exists: {e}")
        
    conn.commit()
    conn.close()
    print("Migration complete.")

if __name__ == '__main__':
    migrate()
