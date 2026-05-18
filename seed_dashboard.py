from database import session, User, Doctor, TriageHistory, ConsultationRequest, Disease
from datetime import datetime, timedelta
import random

def seed_dashboard_data():
    doctor = session.query(Doctor).filter(Doctor.id == 1).first()
    if not doctor:
        print("Doctor ID 1 not found. Make sure seed_default_doctors() ran.")
        return

    # Create a few users if they don't exist
    users = session.query(User).limit(5).all()
    if len(users) < 3:
        for i in range(3):
            user = User(full_name=f"Patient {i+1}", email=f"patient{i+1}@example.com", hashed_password="hashed")
            session.add(user)
        session.commit()
        users = session.query(User).limit(5).all()

    # Get some diseases
    diseases = session.query(Disease).limit(5).all()
    if not diseases:
        print("No diseases found. Syncing from CSV...")
        from database import sync_data_from_csv
        sync_data_from_csv()
        diseases = session.query(Disease).limit(5).all()

    # Create Triage History and Consultation Requests
    priorities = ["urgent", "high", "normal"]
    statuses = ["pending", "accepted", "in_progress", "completed"]

    for i in range(10):
        patient = random.choice(users)
        disease = random.choice(diseases)
        
        triage = TriageHistory(
            user_id=patient.id,
            disease_name=disease.name,
            symptoms=f"Sample symptoms for {disease.name}: {disease.symptoms[:50]}...",
            severity=disease.severity,
            location="New York, NY",
            doctor_status="pending",
            created_at=datetime.utcnow() - timedelta(hours=random.randint(1, 48))
        )
        session.add(triage)
        session.flush()

        request = ConsultationRequest(
            patient_id=patient.id,
            doctor_id=doctor.id,
            triage_history_id=triage.id,
            disease_name=disease.name,
            predicted_specialty=doctor.specialty,
            patient_symptoms=triage.symptoms,
            severity=triage.severity,
            status=random.choice(statuses),
            priority=random.choice(priorities),
            created_at=triage.created_at
        )
        session.add(request)

    session.commit()
    print("[OK] Seeded 10 sample cases for Dr. Sarah Johnson.")

if __name__ == "__main__":
    seed_dashboard_data()
