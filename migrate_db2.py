import sqlite3

def migrate():
    conn = sqlite3.connect('health_app.db')
    cursor = conn.cursor()
    
    # Add prescription_data
    try:
        cursor.execute("ALTER TABLE consultation_requests ADD COLUMN prescription_data TEXT")
        print("Added prescription_data column")
    except sqlite3.OperationalError as e:
        print(f"prescription_data likely exists: {e}")
        
    conn.commit()
    conn.close()
    print("Migration complete.")

if __name__ == '__main__':
    migrate()
