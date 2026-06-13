"""
Doctor Routing Service
Handles intelligent routing of consultation requests to appropriate doctors
based on predicted specialty, availability, and other factors.
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict
from database import (
    session,
    Doctor,
    ConsultationRequest,
    ConsultationHistory,
    DoctorAvailability,
    User
)


# Specialty mapping - Map disease keywords to medical specialties
SPECIALTY_MAPPING = {
    # Dermatology
    "skin": "Dermatologist",
    "rash": "Dermatologist",
    "acne": "Dermatologist",
    "eczema": "Dermatologist",
    "psoriasis": "Dermatologist",
    "dermatitis": "Dermatologist",
    "fungal": "Dermatologist",
    
    # Cardiology
    "heart": "Cardiologist",
    "cardiac": "Cardiologist",
    "arrhythmia": "Cardiologist",
    "hypertension": "Cardiologist",
    "chest pain": "Cardiologist",
    "angina": "Cardiologist",
    "coronary": "Cardiologist",
    
    # Psychiatry
    "mental": "Psychiatrist",
    "depression": "Psychiatrist",
    "anxiety": "Psychiatrist",
    "stress": "Psychiatrist",
    "insomnia": "Psychiatrist",
    "bipolar": "Psychiatrist",
    "psychological": "Psychiatrist",
    
    # Neurology
    "neuro": "Neurologist",
    "seizure": "Neurologist",
    "migraine": "Neurologist",
    "headache": "Neurologist",
    "neurological": "Neurologist",
    "tremor": "Neurologist",
    "parkinsons": "Neurologist",
    
    # Pulmonology
    "lung": "Pulmonologist",
    "respiratory": "Pulmonologist",
    "asthma": "Pulmonologist",
    "bronchitis": "Pulmonologist",
    "pneumonia": "Pulmonologist",
    "cough": "Pulmonologist",
    "copd": "Pulmonologist",
    
    # Gastroenterology
    "stomach": "Gastroenterologist",
    "digestive": "Gastroenterologist",
    "gastric": "Gastroenterologist",
    "ulcer": "Gastroenterologist",
    "ibs": "Gastroenterologist",
    "crohn": "Gastroenterologist",
    "diarrhea": "Gastroenterologist",
}


def predict_specialty(disease_name: str) -> str:
    """
    Predict the appropriate medical specialty based on disease name.
    Falls back to "General Practitioner" if no specific match found.
    """
    disease_lower = disease_name.lower()
    
    for keyword, specialty in SPECIALTY_MAPPING.items():
        if keyword in disease_lower:
            return specialty
    
    # Default to General Practitioner
    return "General Practitioner"


def get_available_doctors(specialty: str) -> List[Dict]:
    """
    Get list of available doctors for a given specialty,
    sorted by estimated wait time and queue size.
    """
    # Find doctors with matching specialty
    if specialty in ["General Practitioner", "General Physician"]:
        specialties = ["General Practitioner", "General Physician"]
    else:
        specialties = [specialty]
        
    doctors = session.query(Doctor).filter(
        Doctor.specialty.in_(specialties),
        Doctor.is_active == True
    ).all()
    
    available_doctors = []
    
    for doctor in doctors:
        # Get doctor's availability
        availability = session.query(DoctorAvailability).filter(
            DoctorAvailability.doctor_id == doctor.id
        ).first()
        
        if availability:
            doctor_info = {
                "id": doctor.id,
                "name": doctor.name,
                "specialty": doctor.specialty,
                "experience_years": doctor.experience_years,
                "qualifications": doctor.qualifications,
                "hospital_affiliation": doctor.hospital_affiliation,
                "is_online": availability.is_online,
                "current_queue_size": availability.current_queue_size,
                "estimated_wait_minutes": availability.estimated_wait_minutes,
                "rating": calculate_doctor_rating(doctor.id)
            }
            available_doctors.append(doctor_info)
    
    # Sort by: online status first, then by wait time, then by queue size
    available_doctors.sort(key=lambda x: (
        not x["is_online"],  # Online doctors first
        x["estimated_wait_minutes"],  # Shorter wait times
        x["current_queue_size"]  # Smaller queue
    ))
    
    return available_doctors


def get_alternative_specialists(primary_specialty: str) -> List[Dict]:
    """
    Get alternative specialists if primary specialty is unavailable.
    """
    alternative_specialties = {
        "Cardiologist": ["General Practitioner"],
        "Dermatologist": ["General Practitioner"],
        "Psychiatrist": ["General Practitioner"],
        "Neurologist": ["General Practitioner"],
        "Pulmonologist": ["General Practitioner"],
        "Gastroenterologist": ["General Practitioner"],
    }
    
    alternatives = alternative_specialties.get(primary_specialty, [])
    all_doctors = []
    
    for specialty in alternatives:
        doctors = get_available_doctors(specialty)
        all_doctors.extend(doctors)
    
    return all_doctors[:3]  # Return top 3 alternatives


def create_consultation_request(
    patient_id: int,
    doctor_id: int,
    disease_name: str,
    predicted_specialty: str,
    symptoms: str,
    severity: int,
    priority: str = "normal",
    notes: str = None,
    triage_history_id: int = None
) -> Optional[ConsultationRequest]:
    """
    Create a new consultation request and assign to a doctor.
    """
    try:
        # Emergency Priority System
        if severity and severity >= 7:
            priority = "urgent"

        # Get estimated response time based on doctor's queue
        availability = session.query(DoctorAvailability).filter(
            DoctorAvailability.doctor_id == doctor_id
        ).first()
        
        estimated_wait = availability.estimated_wait_minutes if availability else 15
        
        consultation = ConsultationRequest(
            patient_id=patient_id,
            doctor_id=doctor_id,
            triage_history_id=triage_history_id,
            disease_name=disease_name,
            predicted_specialty=predicted_specialty,
            patient_symptoms=symptoms,
            severity=severity,
            priority=priority,
            notes_from_patient=notes,
            status="pending",
            estimated_response_minutes=estimated_wait,
            assigned_at=datetime.utcnow()
        )
        
        session.add(consultation)
        session.commit()
        
        # Update doctor's queue
        if availability:
            availability.current_queue_size += 1
            session.commit()
        
        return consultation
    except Exception as e:
        print(f"❌ Error creating consultation: {str(e)}")
        session.rollback()
        return None


def update_consultation_status(
    consultation_id: int,
    new_status: str,
    doctor_comment: str = None
) -> bool:
    """
    Update the status of a consultation request.
    Statuses: pending -> accepted -> in_progress -> completed
    """
    try:
        consultation = session.query(ConsultationRequest).filter(
            ConsultationRequest.id == consultation_id
        ).first()
        
        if not consultation:
            return False
        
        old_status = consultation.status
        consultation.status = new_status
        
        # Update timestamps based on status
        if new_status == "accepted":
            consultation.accepted_at = datetime.utcnow()
        elif new_status == "in_progress":
            consultation.started_at = datetime.utcnow()
        elif new_status == "completed":
            consultation.completed_at = datetime.utcnow()
            
            # Update doctor's queue
            availability = session.query(DoctorAvailability).filter(
                DoctorAvailability.doctor_id == consultation.doctor_id
            ).first()
            if availability and availability.current_queue_size > 0:
                availability.current_queue_size -= 1
        
        session.commit()
        return True
    except Exception as e:
        print(f"❌ Error updating consultation status: {str(e)}")
        session.rollback()
        return False


def complete_consultation(
    consultation_id: int,
    diagnosis: str,
    prescription: str,
    recommendations: str,
    duration_minutes: int = 30
) -> bool:
    """
    Complete a consultation and save history.
    """
    try:
        consultation = session.query(ConsultationRequest).filter(
            ConsultationRequest.id == consultation_id
        ).first()
        
        if not consultation:
            return False
        
        # Create consultation history record
        history = ConsultationHistory(
            consultation_request_id=consultation.id,
            patient_id=consultation.patient_id,
            doctor_id=consultation.doctor_id,
            disease_name=consultation.disease_name,
            doctor_diagnosis=diagnosis,
            prescription=prescription,
            recommendations=recommendations,
            duration_minutes=duration_minutes
        )
        
        session.add(history)
        consultation.status = "completed"
        consultation.completed_at = datetime.utcnow()
        session.commit()
        
        return True
    except Exception as e:
        print(f"❌ Error completing consultation: {str(e)}")
        session.rollback()
        return False


def rate_consultation(
    consultation_id: int,
    rating: int,
    feedback: str = None
) -> bool:
    """
    Add patient feedback and rating to consultation history.
    Rating: 1-5 stars
    """
    try:
        history = session.query(ConsultationHistory).filter(
            ConsultationHistory.consultation_request_id == consultation_id
        ).first()
        
        if not history:
            return False
        
        history.satisfaction_rating = rating
        history.patient_feedback = feedback
        session.commit()
        
        return True
    except Exception as e:
        print(f"❌ Error rating consultation: {str(e)}")
        session.rollback()
        return False


def update_doctor_status(doctor_id: int, is_online: bool) -> bool:
    """
    Update doctor's online/offline status.
    """
    try:
        availability = session.query(DoctorAvailability).filter(
            DoctorAvailability.doctor_id == doctor_id
        ).first()
        
        if availability:
            availability.is_online = is_online
            availability.last_updated = datetime.utcnow()
            session.commit()
            return True
        
        return False
    except Exception as e:
        print(f"❌ Error updating doctor status: {str(e)}")
        session.rollback()
        return False


def update_doctor_queue(doctor_id: int, queue_size: int, est_wait_minutes: int) -> bool:
    """
    Update doctor's queue information.
    """
    try:
        availability = session.query(DoctorAvailability).filter(
            DoctorAvailability.doctor_id == doctor_id
        ).first()
        
        if availability:
            availability.current_queue_size = max(0, queue_size)
            availability.estimated_wait_minutes = est_wait_minutes
            availability.last_updated = datetime.utcnow()
            session.commit()
            return True
        
        return False
    except Exception as e:
        print(f"❌ Error updating doctor queue: {str(e)}")
        session.rollback()
        return False


def calculate_doctor_rating(doctor_id: int) -> float:
    """
    Calculate average rating for a doctor based on consultation feedback.
    """
    ratings = session.query(ConsultationHistory).filter(
        ConsultationHistory.doctor_id == doctor_id,
        ConsultationHistory.satisfaction_rating != None
    ).all()
    
    if not ratings:
        return 5.0  # Default rating
    
    avg_rating = sum(r.satisfaction_rating for r in ratings) / len(ratings)
    return round(avg_rating, 1)


def get_consultation_history(patient_id: int) -> List[Dict]:
    """
    Get all consultation history for a patient.
    """
    consultations = session.query(ConsultationHistory).filter(
        ConsultationHistory.patient_id == patient_id
    ).order_by(ConsultationHistory.completed_at.desc()).all()
    
    history = []
    for consultation in consultations:
        doctor = session.query(Doctor).filter(
            Doctor.id == consultation.doctor_id
        ).first()
        
        history.append({
            "id": consultation.id,
            "doctor_name": doctor.name if doctor else "Unknown",
            "specialty": doctor.specialty if doctor else "Unknown",
            "disease": consultation.disease_name,
            "diagnosis": consultation.doctor_diagnosis,
            "rating": consultation.satisfaction_rating,
            "completed_at": consultation.completed_at.isoformat() if consultation.completed_at else None
        })
    
    return history


def get_pending_consultations(doctor_id: int) -> List[Dict]:
    """
    Get all pending consultations for a doctor.
    """
    consultations = session.query(ConsultationRequest).filter(
        ConsultationRequest.doctor_id == doctor_id,
        ConsultationRequest.status.in_(["pending", "accepted"])
    ).all()
    
    # Sort urgent first, then by created_at
    consultations.sort(key=lambda x: (x.priority != 'urgent', x.created_at))
    
    pending = []
    for consultation in consultations:
        patient = session.query(User).filter(
            User.id == consultation.patient_id
        ).first()
        
        pending.append({
            "id": consultation.id,
            "patient_name": patient.full_name if patient else "Unknown",
            "disease": consultation.disease_name,
            "symptoms": consultation.patient_symptoms,
            "severity": consultation.severity,
            "priority": consultation.priority,
            "status": consultation.status,
            "created_at": consultation.created_at.isoformat()
        })
    
    return pending
