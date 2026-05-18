import sqlite3

def migrate():
    conn = sqlite3.connect('health_app.db')
    cursor = conn.cursor()
    
    # Add pdf_path to consultation_history
    try:
        cursor.execute("ALTER TABLE consultation_history ADD COLUMN pdf_path TEXT")
        print("Added pdf_path column to consultation_history")
    except sqlite3.OperationalError as e:
        print(f"pdf_path likely exists: {e}")
        
    conn.commit()
    conn.close()
    print("Migration complete.")

if __name__ == '__main__':
    migrate()
