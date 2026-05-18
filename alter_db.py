import sqlite3

def alter():
    conn = sqlite3.connect('health_app.db')
    cursor = conn.cursor()
    
    # Try adding each column, catch OperationalError if it already exists
    queries = [
        "ALTER TABLE doctor_availability ADD COLUMN working_hours_start VARCHAR DEFAULT '09:00';",
        "ALTER TABLE doctor_availability ADD COLUMN working_hours_end VARCHAR DEFAULT '17:00';",
        "ALTER TABLE doctor_availability ADD COLUMN unavailable_dates TEXT;"
    ]
    
    for q in queries:
        try:
            cursor.execute(q)
            print(f"Executed: {q}")
        except sqlite3.OperationalError as e:
            print(f"Skipped {q} because: {e}")
            
    conn.commit()
    conn.close()

if __name__ == '__main__':
    alter()
