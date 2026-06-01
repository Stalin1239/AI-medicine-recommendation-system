import sqlite3
from pathlib import Path

def migrate_payments():
    db_path = Path("health_app.db")
    if not db_path.exists():
        print(f"Error: Database {db_path} not found.")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Add payment fields to consultation_requests
        cursor.execute("ALTER TABLE consultation_requests ADD COLUMN payment_status VARCHAR DEFAULT 'pending'")
        cursor.execute("ALTER TABLE consultation_requests ADD COLUMN payment_amount FLOAT DEFAULT 500.0")
        cursor.execute("ALTER TABLE consultation_requests ADD COLUMN transaction_id VARCHAR")
        
        # Add payment fields to consultation_history
        cursor.execute("ALTER TABLE consultation_history ADD COLUMN payment_status VARCHAR DEFAULT 'pending'")
        cursor.execute("ALTER TABLE consultation_history ADD COLUMN payment_amount FLOAT DEFAULT 500.0")
        cursor.execute("ALTER TABLE consultation_history ADD COLUMN transaction_id VARCHAR")
        
        conn.commit()
        print("✅ Successfully added payment fields to consultation_requests and consultation_history.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            print("⚠️ Payment fields already exist. No migration needed.")
        else:
            print(f"❌ Error during migration: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_payments()
