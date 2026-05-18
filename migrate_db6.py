import sqlite3

def migrate():
    conn = sqlite3.connect('health_app.db')
    cursor = conn.cursor()
    
    # Create PatientNotification table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS patient_notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        type VARCHAR,
        title VARCHAR,
        message TEXT,
        is_read BOOLEAN DEFAULT 0,
        action_link VARCHAR,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        status VARCHAR DEFAULT 'unread',
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
    ''')
    
    # Create FollowUpRequest table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS follow_up_requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        consultation_id INTEGER,
        patient_id INTEGER,
        doctor_id INTEGER,
        follow_up_date DATETIME,
        notes TEXT,
        status VARCHAR DEFAULT 'pending',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(consultation_id) REFERENCES consultation_requests(id),
        FOREIGN KEY(patient_id) REFERENCES users(id),
        FOREIGN KEY(doctor_id) REFERENCES doctors(id)
    )
    ''')
    
    conn.commit()
    conn.close()
    print("Migration 6 complete.")

if __name__ == '__main__':
    migrate()
