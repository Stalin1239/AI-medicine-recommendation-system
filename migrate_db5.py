import sqlite3

def migrate():
    conn = sqlite3.connect('health_app.db')
    cursor = conn.cursor()
    
    # Add created_at to prescription_schedules
    try:
        cursor.execute("ALTER TABLE prescription_schedules ADD COLUMN created_at DATETIME")
        print("Added created_at column to prescription_schedules")
    except sqlite3.OperationalError as e:
        print(f"created_at likely exists: {e}")
        
    conn.commit()
    conn.close()
    print("Migration 5 complete.")

if __name__ == '__main__':
    migrate()
