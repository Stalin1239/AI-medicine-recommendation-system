import sys
import pandas as pd
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Reconfigure stdout/stderr to support UTF-8 on Windows terminals
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')
from datetime import datetime
import hashlib
import secrets

# 1. DATABASE SETUP
# This creates/connects to health_app.db in your project folder
Base = declarative_base()
engine = create_engine('sqlite:///health_app.db', connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
session = SessionLocal()

# 2. USER MODEL DEFINITION
# For authentication
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

# 3. DISEASE MODEL DEFINITION
# This is the "blueprint" for your medicine data
class Disease(Base):
    __tablename__ = "diseases"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    category = Column(String)
    symptoms = Column(Text)
    severity = Column(Integer)
    diet_to_eat = Column(Text)
    diet_to_avoid = Column(Text)
    medicine_name = Column(String)
    safe_tip = Column(Text)
    dangerous_myth = Column(Text)
    base_dosage_mg = Column(Integer)


class AdminUpdateHistory(Base):
    __tablename__ = "admin_update_history"

    id = Column(Integer, primary_key=True, index=True)
    action = Column(String)  # 'ADD', 'EDIT', 'DELETE'
    disease_name = Column(String)
    details = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)


class FamilyProfile(Base):
    __tablename__ = "family_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    name = Column(String, nullable=False)
    relation = Column(String, nullable=False)
    age = Column(Integer, nullable=False)
    chronic_conditions = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Reminder(Base):
    __tablename__ = "reminders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    medicine_name = Column(String, nullable=False)
    alarm_time = Column(String, nullable=False)
    note = Column(Text, nullable=True)
    active = Column(Boolean, default=True)
    last_alerted_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    message = Column(Text, nullable=False)
    status = Column(String, default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)
    delivered_at = Column(DateTime, nullable=True)


class TriageHistory(Base):
    __tablename__ = "triage_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=True)
    disease_name = Column(String, index=True)
    symptoms = Column(Text)
    severity = Column(Integer)
    location = Column(String, default="Unknown")
    home_remedy = Column(Text, nullable=True)
    photo_url = Column(String, nullable=True)
    ai_insight = Column(Text, nullable=True)
    recommended_medicine = Column(String, nullable=True)
    dosage = Column(String, nullable=True)
    doctor_status = Column(String, default="pending")
    doctor_prescription = Column(String, nullable=True)
    doctor_comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


# 3A. DOCTOR MODEL
class Doctor(Base):
    __tablename__ = "doctors"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    specialty = Column(String, nullable=False, index=True)  # e.g., "Dermatologist", "Cardiologist"
    qualifications = Column(Text, nullable=True)  # e.g., "MD, Board Certified"
    experience_years = Column(Integer, default=0)
    hospital_affiliation = Column(String, nullable=True)
    photo_url = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


# 3B. CONSULTATION REQUEST MODEL
class ConsultationRequest(Base):
    __tablename__ = "consultation_requests"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("users.id"), index=True)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), index=True)
    triage_history_id = Column(Integer, ForeignKey("triage_history.id"), nullable=True)
    disease_name = Column(String, nullable=False)
    predicted_specialty = Column(String, nullable=False)
    patient_symptoms = Column(Text, nullable=True)
    severity = Column(Integer, nullable=True)
    status = Column(String, default="pending")  # pending, under_review, diagnosed, follow_up_required, emergency, accepted, in_progress, completed, cancelled
    priority = Column(String, default="normal")  # urgent, high, normal, low
    notes_from_patient = Column(Text, nullable=True)
    actual_diagnosis = Column(String, nullable=True)
    precautions = Column(Text, nullable=True)
    treatment_notes = Column(Text, nullable=True)
    follow_up_instructions = Column(Text, nullable=True)
    prescription_data = Column(Text, nullable=True)
    assigned_at = Column(DateTime, nullable=True)
    accepted_at = Column(DateTime, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    estimated_response_minutes = Column(Integer, default=15)
    
    # Consultation Management
    consultation_type = Column(String, default="online") # online, offline
    clinic_address = Column(Text, nullable=True)
    appointment_time = Column(DateTime, nullable=True)
    token_number = Column(String, nullable=True)
    meeting_status = Column(String, default="pending") # pending, scheduled, in_progress, ended
    
    created_at = Column(DateTime, default=datetime.utcnow)


# 3C. CONSULTATION HISTORY MODEL
class ConsultationHistory(Base):
    __tablename__ = "consultation_history"

    id = Column(Integer, primary_key=True, index=True)
    consultation_request_id = Column(Integer, ForeignKey("consultation_requests.id"))
    patient_id = Column(Integer, ForeignKey("users.id"))
    doctor_id = Column(Integer, ForeignKey("doctors.id"))
    disease_name = Column(String, nullable=False)
    doctor_diagnosis = Column(Text, nullable=True)
    prescription = Column(Text, nullable=True)
    recommendations = Column(Text, nullable=True)
    duration_minutes = Column(Integer, nullable=True)
    satisfaction_rating = Column(Integer, nullable=True)  # 1-5 stars
    patient_feedback = Column(Text, nullable=True)
    pdf_path = Column(String, nullable=True)
    completed_at = Column(DateTime, default=datetime.utcnow)

class PrescriptionSchedule(Base):
    __tablename__ = "prescription_schedules"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("users.id"), index=True)
    consultation_id = Column(Integer, ForeignKey("consultation_requests.id"), index=True)
    medicine_name = Column(String, nullable=False)
    dosage = Column(String, nullable=True)
    instructions = Column(String, nullable=True)
    scheduled_time = Column(DateTime, nullable=False)
    status = Column(String, default="pending") # pending, taken, missed, snoozed
    taken_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class PatientNotification(Base):
    __tablename__ = "patient_notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    type = Column(String, default="alert") # alert, reminder, message
    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    action_link = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="unread")

class FollowUpRequest(Base):
    __tablename__ = "follow_up_requests"

    id = Column(Integer, primary_key=True, index=True)
    consultation_id = Column(Integer, ForeignKey("consultation_requests.id"), index=True)
    patient_id = Column(Integer, ForeignKey("users.id"), index=True)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), index=True)
    follow_up_date = Column(DateTime, nullable=False)
    notes = Column(Text, nullable=True)
    status = Column(String, default="pending") # pending, confirmed, rescheduled, completed
    created_at = Column(DateTime, default=datetime.utcnow)


# 3D. DOCTOR AVAILABILITY MODEL
class DoctorAvailability(Base):
    __tablename__ = "doctor_availability"

    id = Column(Integer, primary_key=True, index=True)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), unique=True, index=True)
    is_online = Column(Boolean, default=False)
    working_hours_start = Column(String, default="09:00")
    working_hours_end = Column(String, default="17:00")
    unavailable_dates = Column(Text, nullable=True)
    current_queue_size = Column(Integer, default=0)
    estimated_wait_minutes = Column(Integer, default=15)
    last_updated = Column(DateTime, default=datetime.utcnow)


# 4. PASSWORD HELPER FUNCTIONS
def hash_password(password: str) -> str:
    # Use PBKDF2 with SHA256 for password hashing (no byte limit issues)
    salt = secrets.token_hex(32)
    pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)
    return f"{salt}${pwd_hash.hex()}"

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        salt, pwd_hash = hashed_password.split('$')
        new_hash = hashlib.pbkdf2_hmac('sha256', plain_password.encode('utf-8'), salt.encode('utf-8'), 100000)
        return new_hash.hex() == pwd_hash
    except:
        return False

# 5. HELPER FUNCTION: Sync CSV to Database

def get_disease_by_name_prefix(prediction: str):
    """Find the first disease matching the predicted label in the local knowledge base."""
    return session.query(Disease).filter(Disease.name.ilike(f"%{prediction}%") ).first()


def create_tables():
    """Create any missing database tables."""
    Base.metadata.create_all(bind=engine)


def is_disease_table_empty() -> bool:
    """Return True when the diseases table has no rows."""
    try:
        return session.query(Disease).count() == 0
    except Exception:
        return True


def seed_diseases_from_csv(csv_file: str = 'dataset_management/fedmedflow_accurate_dataset.csv'):
    """Seed the diseases table from CSV when the table is empty."""
    create_tables()
    if not is_disease_table_empty():
        return

    # Fallback to root CSV if needed during first-run
    if not os.path.exists(csv_file):
        fallback = 'fedmedflow_accurate_dataset.csv'
        if os.path.exists(fallback):
            csv_file = fallback
        else:
            print(f"⚠️ CSV file not found: {csv_file}. Database will remain empty until you run sync_data_from_csv.")
            return

    print("--- Seeding database with medical data ---")
    df = pd.read_csv(csv_file)
    unique_df = df.drop_duplicates(subset=['name'])
    for _, row in unique_df.iterrows():
        new_entry = Disease(
            name=row['name'],
            category=row['category'],
            symptoms=row['symptoms'],
            severity=int(row['severity']),
            diet_to_eat=row['diet_to_eat'],
            diet_to_avoid=row['diet_to_avoid'],
            medicine_name=row['medicine_name'],
            safe_tip=row['safe_tip'],
            dangerous_myth=row['dangerous_myth'],
            base_dosage_mg=int(row['base_dosage_mg'])
        )
        session.add(new_entry)

    session.commit()
    print(f"✅ Seeded {len(unique_df)} unique diseases into 'health_app.db'.")


def sync_data_from_csv(csv_file: str = 'dataset_management/fedmedflow_accurate_dataset.csv'):
    """Reads the CSV and pushes unique diseases into the SQLite DB."""
    if not os.path.exists(csv_file):
        fallback = 'fedmedflow_accurate_dataset.csv'
        if os.path.exists(fallback):
            csv_file = fallback
        else:
            print(f"❌ Error: {csv_file} not found. Please ensure the CSV is in the folder.")
            return

    print("--- Syncing Database with Medical Data ---")
    df = pd.read_csv(csv_file)

    # Safely clear the diseases table only to prevent losing users or doctors
    session.query(Disease).delete()
    session.commit()

    unique_df = df.drop_duplicates(subset=['name'])
    for _, row in unique_df.iterrows():
        new_entry = Disease(
            name=row['name'],
            category=row['category'],
            symptoms=row['symptoms'],
            severity=int(row['severity']),
            diet_to_eat=row['diet_to_eat'],
            diet_to_avoid=row['diet_to_avoid'],
            medicine_name=row['medicine_name'],
            safe_tip=row['safe_tip'],
            dangerous_myth=row['dangerous_myth'],
            base_dosage_mg=int(row['base_dosage_mg'])
        )
        session.add(new_entry)

    session.commit()
    print(f"✅ Success! {len(unique_df)} unique diseases added to 'health_app.db'.")


def seed_default_doctors():
    """Seed default doctors for each specialty."""
    # Check if doctors already exist
    if session.query(Doctor).count() > 0:
        return
    
    doctors_data = [
        # Dermatologists
        {
            "name": "Dr. Sarah Johnson",
            "email": "sarah.johnson@medclinic.com",
            "specialty": "Dermatologist",
            "qualifications": "MD, Board Certified Dermatology",
            "experience_years": 12,
            "hospital_affiliation": "City Medical Center"
        },
        {
            "name": "Dr. Michael Chen",
            "email": "michael.chen@medclinic.com",
            "specialty": "Dermatologist",
            "qualifications": "MD, Dermatology Specialist",
            "experience_years": 8,
            "hospital_affiliation": "Central Hospital"
        },
        # Cardiologists
        {
            "name": "Dr. James Williams",
            "email": "james.williams@medclinic.com",
            "specialty": "Cardiologist",
            "qualifications": "MD, Board Certified Cardiology",
            "experience_years": 15,
            "hospital_affiliation": "Heart Care Institute"
        },
        {
            "name": "Dr. Priya Patel",
            "email": "priya.patel@medclinic.com",
            "specialty": "Cardiologist",
            "qualifications": "MD, Cardiac Specialist",
            "experience_years": 10,
            "hospital_affiliation": "City Medical Center"
        },
        # Psychiatrists
        {
            "name": "Dr. Robert Martinez",
            "email": "robert.martinez@medclinic.com",
            "specialty": "Psychiatrist",
            "qualifications": "MD, Board Certified Psychiatry",
            "experience_years": 14,
            "hospital_affiliation": "Mental Health Center"
        },
        {
            "name": "Dr. Lisa Anderson",
            "email": "lisa.anderson@medclinic.com",
            "specialty": "Psychiatrist",
            "qualifications": "MD, Psychiatry Specialist",
            "experience_years": 9,
            "hospital_affiliation": "Wellness Hospital"
        },
        # Neurologists
        {
            "name": "Dr. David Kumar",
            "email": "david.kumar@medclinic.com",
            "specialty": "Neurologist",
            "qualifications": "MD, Board Certified Neurology",
            "experience_years": 11,
            "hospital_affiliation": "Brain & Spine Center"
        },
        # Pulmonologists
        {
            "name": "Dr. Emily Thompson",
            "email": "emily.thompson@medclinic.com",
            "specialty": "Pulmonologist",
            "qualifications": "MD, Respiratory Specialist",
            "experience_years": 10,
            "hospital_affiliation": "Lung Care Hospital"
        },
        # Gastroenterologists
        {
            "name": "Dr. Ahmed Hassan",
            "email": "ahmed.hassan@medclinic.com",
            "specialty": "Gastroenterologist",
            "qualifications": "MD, GI Specialist",
            "experience_years": 12,
            "hospital_affiliation": "Digestive Health Center"
        },
        # General Practitioners
        {
            "name": "Dr. Susan Lee",
            "email": "susan.lee@medclinic.com",
            "specialty": "General Practitioner",
            "qualifications": "MD, Family Medicine",
            "experience_years": 13,
            "hospital_affiliation": "Primary Care Clinic"
        },
    ]
    
    for doctor_data in doctors_data:
        doctor = Doctor(
            name=doctor_data["name"],
            email=doctor_data["email"],
            hashed_password=hash_password("doctor123"),  # Default password for demo
            specialty=doctor_data["specialty"],
            qualifications=doctor_data["qualifications"],
            experience_years=doctor_data["experience_years"],
            hospital_affiliation=doctor_data["hospital_affiliation"]
        )
        session.add(doctor)
    
    session.commit()
    print(f"✅ Seeded {len(doctors_data)} default doctors into database.")


def seed_doctor_availability():
    """Seed doctor availability statuses."""
    # Clear existing availability records
    session.query(DoctorAvailability).delete()
    
    doctors = session.query(Doctor).all()
    for doctor in doctors:
        availability = DoctorAvailability(
            doctor_id=doctor.id,
            is_online=True,  # Start all as online
            current_queue_size=0,
            estimated_wait_minutes=15
        )
        session.add(availability)
    
    session.commit()
    print(f"✅ Seeded availability for {len(doctors)} doctors.")


# 4. RUN THIS FILE DIRECTLY TO SETUP/SYNC
if __name__ == "__main__":
    sync_data_from_csv()
