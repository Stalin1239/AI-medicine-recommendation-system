import sqlite3

def migrate():
    conn = sqlite3.connect('health_app.db')
    cursor = conn.cursor()
    
    # Create DoctorAvailability table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS doctor_availability (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        doctor_id INTEGER UNIQUE,
        is_online BOOLEAN DEFAULT 1,
        working_hours_start VARCHAR DEFAULT '09:00',
        working_hours_end VARCHAR DEFAULT '17:00',
        unavailable_dates TEXT,
        last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(doctor_id) REFERENCES doctors(id)
    )
    ''')
    
    conn.commit()
    conn.close()
    print("Migration 7 complete.")

if __name__ == '__main__':
    migrate()
