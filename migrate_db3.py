import sqlite3

def migrate():
    conn = sqlite3.connect('health_app.db')
    cursor = conn.cursor()
    
    # Create prescription_schedules table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS prescription_schedules (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id INTEGER,
        consultation_id INTEGER,
        medicine_name VARCHAR NOT NULL,
        dosage VARCHAR,
        instructions VARCHAR,
        scheduled_time DATETIME NOT NULL,
        status VARCHAR DEFAULT 'pending',
        taken_at DATETIME,
        FOREIGN KEY(patient_id) REFERENCES users(id),
        FOREIGN KEY(consultation_id) REFERENCES consultation_requests(id)
    )
    """)
    
    # Create indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_sched_patient ON prescription_schedules(patient_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_sched_consult ON prescription_schedules(consultation_id)")
    
    conn.commit()
    conn.close()
    print("Migration complete. prescription_schedules table created.")

if __name__ == '__main__':
    migrate()
