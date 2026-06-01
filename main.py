from dotenv import load_dotenv
load_dotenv()
print("🤖 dotenv loaded")

import asyncio
import pickle
import json
from pathlib import Path
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, time
from typing import Optional

import numpy as np
from pydantic import BaseModel
from fastapi import FastAPI, Form, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, RedirectResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import func

from database import (
    engine,
    session,
    Disease,
    User,
    FamilyProfile,
    Reminder,
    Notification,
    TriageHistory,
    Doctor,
    ConsultationRequest,
    ConsultationHistory,
    DoctorAvailability,
    PrescriptionSchedule,
    PatientNotification,
    FollowUpRequest,
    hash_password,
    verify_password,
    create_tables,
    seed_diseases_from_csv,
    seed_default_doctors,
    seed_doctor_availability,
    AdminUpdateHistory,
)
import subprocess
from utils.validation_utils import validate_disease_data
from utils.csv_utils import append_disease_to_csv, update_disease_in_csv, delete_disease_from_csv

from dosage_engine import calculate_dosage
from ai_service import get_ai_recommendation
from logistics_service import get_nearest_medical_support
from report_service import generate_pdf_report, export_research_data, export_anonymized_json
from doctor_routing_service import (
    predict_specialty,
    get_available_doctors,
    get_alternative_specialists,
    create_consultation_request,
    update_consultation_status,
    complete_consultation,
    rate_consultation,
    update_doctor_status,
    update_doctor_queue,
    get_consultation_history,
    get_pending_consultations,
)

import os
import requests

AI_SERVICE_URL = os.getenv("AI_SERVICE_URL", "http://ai-service:5000")
CONFIDENCE_THRESHOLD = 0.15

def create_default_user():
    """Create a default user for testing if none exists"""
    existing_user = session.query(User).filter(User.email == "test@example.com").first()
    if not existing_user:
        default_user = User(
            full_name="Test User",
            email="test@example.com",
            hashed_password=hash_password("password123")
        )
        session.add(default_user)
        session.commit()
        print("✅ Created default user: test@example.com / password123")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # No more heavy in-memory pickle loads in API gateway!
    print("🚀 API Gateway: Booting microservice backend...")
    create_tables()
    seed_diseases_from_csv()
    seed_default_doctors()
    seed_doctor_availability()
    create_default_user()
    app.state.reminder_task = asyncio.create_task(reminder_background_worker())

    yield

    if getattr(app.state, "reminder_task", None):
        app.state.reminder_task.cancel()
    session.close()

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

if Path("static").exists():
    app.mount("/static", StaticFiles(directory="static"), name="static")

# --- AUTH MODELS & ROUTES ---

class SignupRequest(BaseModel):
    full_name: str
    email: str
    password: str

class LoginRequest(BaseModel):
    email: str
    password: str
    role: Optional[str] = "patient"

class UserUpdateRequest(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None

class FamilyMemberRequest(BaseModel):
    user_id: int
    name: str
    relation: str
    age: int
    chronic_conditions: Optional[str] = None
    notes: Optional[str] = None

class ReminderRequest(BaseModel):
    user_id: int
    medicine_name: str
    alarm_time: str
    note: Optional[str] = None

class ReminderUpdateRequest(BaseModel):
    active: bool

class DoctorPrescriptionRequest(BaseModel):
    triage_id: int
    action: str
    medicine_name: Optional[str] = None
    doctor_notes: Optional[str] = None

class DoctorPrescriptionUpdate(BaseModel):
    action: str
    medicine_name: Optional[str] = None
    doctor_notes: Optional[str] = None

class DoctorAnalyticsRequest(BaseModel):
    doctor_id: int

class DoctorPrescriptionAction(BaseModel):
    action: str  # "approve", "override", "complete"
    medicine_name: Optional[str] = None
    doctor_notes: Optional[str] = None


# --- DOCTOR ROUTING MODELS ---

class ConsultationRequestModel(BaseModel):
    patient_id: int
    disease_name: str
    symptoms: str
    severity: int
    priority: str = "normal"
    notes: Optional[str] = None
    triage_history_id: Optional[int] = None


class DoctorSelectionRequest(BaseModel):
    patient_id: int
    doctor_id: int
    disease_name: str
    symptoms: str
    severity: int
    priority: str = "normal"
    notes: Optional[str] = None
    triage_history_id: Optional[int] = None


class ConsultationStatusUpdate(BaseModel):
    consultation_id: int
    status: str
    comment: Optional[str] = None


class ConsultationCompletion(BaseModel):
    consultation_id: int
    diagnosis: str
    prescription: str
    recommendations: str
    duration_minutes: int = 30


class ConsultationRating(BaseModel):
    consultation_id: int
    rating: int
    feedback: Optional[str] = None


class DiagnosisDraft(BaseModel):
    actual_diagnosis: Optional[str] = None
    patient_symptoms: Optional[str] = None
    severity: Optional[int] = None
    precautions: Optional[str] = None
    treatment_notes: Optional[str] = None
    follow_up_instructions: Optional[str] = None
    prescription_data: Optional[str] = None


class DiagnosisFinalize(DiagnosisDraft):
    pass



class DoctorStatusUpdate(BaseModel):
    doctor_id: int
    is_online: bool


class DoctorQueueUpdate(BaseModel):
    doctor_id: int
    queue_size: int
    estimated_wait_minutes: int


def normalize_location(location: Optional[str]) -> str:
    if not location:
        return "Unknown"
    normalized = location.strip()
    return normalized if normalized else "Unknown"


def get_outbreak_alert(location: str, disease_name: str):
    if location.lower() == "unknown" or not disease_name:
        return None

    cutoff = datetime.now() - timedelta(days=7)
    matches = (
        session.query(
            TriageHistory.disease_name,
            func.count(TriageHistory.id).label("case_count"),
        )
        .filter(
            TriageHistory.location == location,
            TriageHistory.disease_name == disease_name,
            TriageHistory.created_at >= cutoff,
        )
        .group_by(TriageHistory.disease_name)
        .all()
    )

    for disease, count in matches:
        if count > 5:
            return {
                "area": location,
                "disease": disease,
                "case_count": count,
                "warning": "Regional Health Warning: multiple reports of the same disease in your area.",
            }
    return None


async def reminder_background_worker():
    while True:
        now = datetime.now()
        current_time = now.strftime("%H:%M")
        reminders = session.query(Reminder).filter(Reminder.active == True).all()

        for reminder in reminders:
            if reminder.alarm_time == current_time:
                last_alert = reminder.last_alerted_at
                if not last_alert or last_alert.strftime("%Y-%m-%d %H:%M") != now.strftime("%Y-%m-%d %H:%M"):
                    message = f"⏰ Reminder: Time to take {reminder.medicine_name}."
                    notification = Notification(
                        user_id=reminder.user_id,
                        message=message,
                        status="pending",
                        created_at=now,
                    )
                    session.add(notification)
                    reminder.last_alerted_at = now
        session.commit()
        await asyncio.sleep(60)


@app.get("/dashboard")
async def read_dashboard():
    return FileResponse(Path("static") / "dashboard.html")

@app.get("/doctor-dashboard")
async def read_doctor_dashboard():
    return FileResponse(Path("static") / "doctor-dashboard.html")

@app.get("/doctor/login")
async def read_doctor_login():
    return FileResponse(Path("static") / "doctor-login.html")

@app.get("/")
async def read_index():
    return RedirectResponse(url="/login")

@app.get("/login")
async def read_login():
    return FileResponse(Path("static") / "login.html")

@app.get("/signup")
async def read_signup():
    return FileResponse(Path("static") / "signup.html")

@app.post("/api/auth/signup")
async def signup(request: SignupRequest):
    existing_user = session.query(User).filter(User.email == request.email).first()
    if existing_user:
        return {"success": False, "message": "Email already registered"}
    try:
        new_user = User(full_name=request.full_name, email=request.email, hashed_password=hash_password(request.password))
        session.add(new_user)
        session.commit()
        return {"success": True, "message": "Account created"}
    except Exception as e:
        session.rollback()
        return {"success": False, "message": str(e)}

@app.post("/api/auth/login")
async def login(request: LoginRequest):
    if request.role == "doctor":
        doctor = session.query(Doctor).filter(Doctor.email == request.email).first()
        if not doctor or not verify_password(request.password, doctor.hashed_password):
            return {"success": False, "message": "Invalid email or password"}
        return {
            "success": True,
            "token": f"doctor_{doctor.id}",
            "role": "doctor",
            "user": {
                "id": doctor.id,
                "full_name": doctor.name,
                "email": doctor.email,
            },
        }
    elif request.role == "admin":
        if request.email == "admin@mediops.com" and request.password == "admin123":
            return {
                "success": True,
                "token": "admin_1",
                "role": "admin",
                "user": {"id": 1, "full_name": "System Admin", "email": "admin@mediops.com"}
            }
        return {"success": False, "message": "Invalid admin credentials"}
    else:
        user = session.query(User).filter(User.email == request.email).first()
        if not user or not verify_password(request.password, user.hashed_password):
            return {"success": False, "message": "Invalid email or password"}
        return {
            "success": True,
            "token": f"user_{user.id}",
            "role": "patient",
            "user": {
                "id": user.id,
                "full_name": user.full_name,
                "email": user.email,
            },
        }

@app.get("/api/user/{user_id}")
async def get_user(user_id: int):
    user = session.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {
        "success": True,
        "user": {
            "id": user.id,
            "full_name": user.full_name,
            "email": user.email,
        },
    }

@app.put("/api/user/{user_id}")
async def update_user(user_id: int, request: UserUpdateRequest):
    user = session.query(User).filter(User.id == user_id).first()
    if not user:
        return {"success": False, "message": "User not found"}

    if request.email:
        existing_email = session.query(User).filter(User.email == request.email, User.id != user_id).first()
        if existing_email:
            return {"success": False, "message": "Email already in use"}
        user.email = request.email
    if request.full_name:
        user.full_name = request.full_name

    session.commit()
    return {
        "success": True,
        "message": "Profile updated",
        "user": {
            "id": user.id,
            "full_name": user.full_name,
            "email": user.email,
        },
    }

# --- TRIAGE LOGIC ---

def classify_symptoms(text: str):
    normalized = text.strip()
    try:
        res = requests.post(f"{AI_SERVICE_URL}/predict", json={"symptoms": normalized}, timeout=8.0)
        if res.status_code == 200:
            data = res.json()
            return data["disease_name"], data["confidence"]
        else:
            raise HTTPException(status_code=res.status_code, detail=f"AI Service error: {res.text}")
    except Exception as e:
        print(f"⚠️ AI Service predicting connection error: {e}")
        raise HTTPException(status_code=503, detail=f"AI prediction service currently unreachable: {str(e)}")

@app.post("/triage")
async def triage_endpoint(
    symptoms: str = Form(...),
    age: int = Form(...),
    weight: float = Form(...),
    user_id: int = Form(0),
    location: str = Form("Unknown"),
    home_remedy: Optional[str] = Form(None),
    photo_url: Optional[str] = Form(None),
):
    prediction = None
    confidence = 0.0
    use_fallback = False

    # 1. Attempt AI model prediction from inference service
    try:
        prediction, confidence = classify_symptoms(symptoms)
    except Exception as e:
        print(f"⚠️ AI Service connection error, falling back to rule-based matcher: {e}")
        use_fallback = True

    # 2. Engage fallback if low confidence or missing predicted disease in database
    if not use_fallback and (confidence < CONFIDENCE_THRESHOLD or not prediction):
        use_fallback = True

    if not use_fallback:
        search_term = prediction.strip()
        disease = session.query(Disease).filter(Disease.name.ilike(f"%{search_term}%")).first()
        if not disease:
            print(f"⚠️ Predicted condition '{prediction}' not in database. Engaging fallback matcher.")
            use_fallback = True

    # 3. Fallback Predictor Route
    if use_fallback:
        try:
            from scripts.fallback_predict import predict_fallback
            fallback_res = predict_fallback(symptoms, age, weight)
            if fallback_res:
                print(f"🎯 Fallback Prediction Successful: {fallback_res['disease_name']} with {fallback_res['confidence']*100:.2f}% overlap")
                ai_insight = await get_ai_recommendation(symptoms, age, weight)

                triage_record = TriageHistory(
                    user_id=user_id,
                    disease_name=fallback_res["disease_name"],
                    symptoms=symptoms,
                    severity=fallback_res["local_verified_data"]["severity"],
                    location=location,
                    home_remedy=home_remedy,
                    photo_url=photo_url,
                    ai_insight=ai_insight,
                    recommended_medicine=fallback_res["recommended_medicine"],
                    dosage=fallback_res["dosage"],
                    doctor_status="pending",
                )
                session.add(triage_record)
                session.commit()

                medical_support = get_nearest_medical_support(fallback_res["local_verified_data"]["severity"], location)
                outbreak_alert = get_outbreak_alert(location, fallback_res["disease_name"])

                return {
                    "status": "Success",
                    "triage_id": triage_record.id,
                    "confidence": fallback_res["confidence"],
                    "local_verified_data": fallback_res["local_verified_data"],
                    "disease_name": fallback_res["disease_name"],
                    "recommended_medicine": fallback_res["recommended_medicine"],
                    "dosage": fallback_res["dosage"],
                    "safe_tip": fallback_res["safe_tip"],
                    "dangerous_myth": fallback_res["dangerous_myth"],
                    "medical_support": medical_support,
                    "outbreak_alert": outbreak_alert,
                    "ai_insight": ai_insight,
                    "is_fallback": True
                }
        except Exception as fe:
            print(f"❌ Fallback Prediction Error: {fe}")

    # 4. Standard Machine Learning Route
    search_term = prediction.strip()
    disease = session.query(Disease).filter(Disease.name.ilike(f"%{search_term}%")).first()
    ai_insight = await get_ai_recommendation(symptoms, age, weight)

    triage_record = TriageHistory(
        user_id=user_id,
        disease_name=prediction,
        symptoms=symptoms,
        severity=disease.severity if disease else 0,
        location=location,
        home_remedy=home_remedy,
        photo_url=photo_url,
        ai_insight=ai_insight,
        recommended_medicine=disease.medicine_name if disease else None,
        dosage=None,
        doctor_status="pending",
    )

    if confidence < CONFIDENCE_THRESHOLD:
        print("❌ Result: Confidence too low.")
        session.add(triage_record)
        session.commit()
        return {
            "status": "Success",
            "message": "Symptoms too vague, but you can still request a doctor.",
            "disease_name": prediction,
            "confidence": confidence,
            "ai_insight": ai_insight,
            "triage_id": triage_record.id,
            "is_verified": False
        }

    if not disease:
        print(f"❌ Result: Prediction '{prediction}' not found in Database.")
        session.add(triage_record)
        session.commit()
        return {
            "status": "Success",
            "message": "Condition not in local knowledge base, but you can consult a doctor.",
            "disease_name": prediction,
            "confidence": confidence,
            "ai_insight": ai_insight,
            "triage_id": triage_record.id,
            "is_verified": False
        }

    dosage = calculate_dosage(disease.base_dosage_mg, weight, age)
    medical_support = get_nearest_medical_support(disease.severity, location)
    outbreak_alert = get_outbreak_alert(location, disease.name)

    triage_record.disease_name = disease.name
    triage_record.severity = disease.severity
    triage_record.recommended_medicine = disease.medicine_name
    triage_record.dosage = str(dosage)

    session.add(triage_record)
    session.commit()

    print(f"✅ Result: Found {disease.name} in database.")
    local_data = {
        "disease_name": disease.name,
        "severity": disease.severity,
        "standard_medicine": disease.medicine_name,
        "calculated_dosage": dosage,
        "safe_tip": disease.safe_tip,
        "dangerous_myth": disease.dangerous_myth,
        "diet_tips": {"eat": disease.diet_to_eat, "avoid": disease.diet_to_avoid},
    }

    return {
        "status": "Success",
        "triage_id": triage_record.id,
        "confidence": confidence,
        "local_verified_data": local_data,
        "disease_name": local_data["disease_name"],
        "recommended_medicine": local_data.get("standard_medicine"),
        "dosage": str(local_data.get("calculated_dosage")),
        "safe_tip": local_data.get("safe_tip"),
        "dangerous_myth": local_data.get("dangerous_myth"),
        "medical_support": medical_support,
        "outbreak_alert": outbreak_alert,
        "ai_insight": ai_insight,
        "is_fallback": False
    }


@app.get("/api/mlops/status")
async def get_mlops_status():
    metadata_path = "models/version_metadata.json"
    status_data = {
        "retraining_pending": False,
        "fallback_active": True,
        "latest_version": "1.0.0",
        "latest_accuracy": 95.0,
        "sync_status": "synchronized",
        "last_sync_time": datetime.now().isoformat(),
        "total_diseases": session.query(Disease).count(),
        "average_severity": round(session.query(func.avg(Disease.severity)).scalar() or 0.0, 1)
    }

    if os.path.exists(metadata_path):
        try:
            with open(metadata_path, 'r') as f:
                meta = json.load(f)
            status_data["latest_version"] = meta.get("current_version", "1.0.0")
            status_data["latest_accuracy"] = round(meta.get("accuracy", 0.95) * 100, 2)
            status_data["sync_status"] = meta.get("sync_status", "synchronized")
            status_data["last_sync_time"] = meta.get("last_sync_time", status_data["last_sync_time"])
        except Exception:
            pass

    try:
        res = requests.get(f"{AI_SERVICE_URL}/", timeout=1.0)
        status_data["fallback_active"] = (res.status_code != 200)
    except Exception:
        status_data["fallback_active"] = True

    if status_data["sync_status"] == "pending":
        status_data["retraining_pending"] = True

    logs = []
    log_dir = "logs/training_logs"
    if os.path.exists(log_dir):
        try:
            files = sorted(os.listdir(log_dir), reverse=True)
            for file in files[:3]:
                with open(os.path.join(log_dir, file), "r", encoding="utf-8") as lf:
                    logs.append({"filename": file, "content": lf.read()})
        except Exception:
            pass

    status_data["training_logs"] = logs
    return status_data


@app.post("/api/patient/family")
async def create_family_member(member: FamilyMemberRequest):
    user = session.query(User).filter(User.id == member.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    profile = FamilyProfile(
        user_id=member.user_id,
        name=member.name,
        relation=member.relation,
        age=member.age,
        chronic_conditions=member.chronic_conditions,
        notes=member.notes,
    )
    session.add(profile)
    session.commit()
    return {"success": True, "family_member_id": profile.id}


@app.get("/api/patient/family")
async def list_family_members(user_id: int = Query(...)):
    members = session.query(FamilyProfile).filter(FamilyProfile.user_id == user_id).all()
    return {"family": [
        {
            "id": m.id,
            "name": m.name,
            "relation": m.relation,
            "age": m.age,
            "chronic_conditions": m.chronic_conditions,
            "notes": m.notes,
            "created_at": m.created_at.isoformat(),
        }
        for m in members
    ]}


@app.put("/api/patient/family/{member_id}")
async def update_family_member(member_id: int, member: FamilyMemberRequest):
    profile = session.query(FamilyProfile).filter(FamilyProfile.id == member_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Family member not found")
    profile.name = member.name
    profile.relation = member.relation
    profile.age = member.age
    profile.chronic_conditions = member.chronic_conditions
    profile.notes = member.notes
    session.commit()
    return {"success": True}


@app.delete("/api/patient/family/{member_id}")
async def delete_family_member(member_id: int):
    profile = session.query(FamilyProfile).filter(FamilyProfile.id == member_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Family member not found")
    session.delete(profile)
    session.commit()
    return {"success": True}


@app.post("/api/patient/reminders")
async def create_reminder(request: ReminderRequest):
    user = session.query(User).filter(User.id == request.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    try:
        datetime.strptime(request.alarm_time, "%H:%M")
    except ValueError:
        raise HTTPException(status_code=400, detail="alarm_time must be in HH:MM format")

    reminder = Reminder(
        user_id=request.user_id,
        medicine_name=request.medicine_name,
        alarm_time=request.alarm_time,
        note=request.note,
        active=True,
    )
    session.add(reminder)
    session.commit()
    return {"success": True, "reminder_id": reminder.id}


@app.get("/api/patient/reminders")
async def list_reminders(user_id: int = Query(...)):
    reminders = session.query(Reminder).filter(Reminder.user_id == user_id).all()
    return {"reminders": [
        {
            "id": r.id,
            "medicine_name": r.medicine_name,
            "alarm_time": r.alarm_time,
            "note": r.note,
            "active": r.active,
            "last_alerted_at": r.last_alerted_at.isoformat() if r.last_alerted_at else None,
            "created_at": r.created_at.isoformat(),
        }
        for r in reminders
    ]}


@app.patch("/api/patient/reminders/{reminder_id}")
async def update_reminder(reminder_id: int, request: ReminderUpdateRequest):
    reminder = session.query(Reminder).filter(Reminder.id == reminder_id).first()
    if not reminder:
        raise HTTPException(status_code=404, detail="Reminder not found")
    reminder.active = request.active
    session.commit()
    return {"success": True}


@app.delete("/api/patient/reminders/{reminder_id}")
async def delete_reminder(reminder_id: int):
    reminder = session.query(Reminder).filter(Reminder.id == reminder_id).first()
    if not reminder:
        raise HTTPException(status_code=404, detail="Reminder not found")
    session.delete(reminder)
    session.commit()
    return {"success": True}


@app.get("/api/patient/notifications")
async def list_notifications(user_id: int = Query(...)):
    notifications = session.query(Notification).filter(Notification.user_id == user_id).order_by(Notification.created_at.desc()).all()
    return {"notifications": [
        {
            "id": n.id,
            "message": n.message,
            "status": n.status,
            "created_at": n.created_at.isoformat(),
            "delivered_at": n.delivered_at.isoformat() if n.delivered_at else None,
        }
        for n in notifications
    ]}


@app.get("/api/patient/history")
async def patient_history(user_id: int = Query(...)):
    history = session.query(TriageHistory).filter(TriageHistory.user_id == user_id).order_by(TriageHistory.created_at.desc()).all()
    return {"history": [
        {
            "id": h.id,
            "disease_name": h.disease_name,
            "symptoms": h.symptoms,
            "severity": h.severity,
            "location": h.location,
            "home_remedy": h.home_remedy,
            "photo_url": h.photo_url,
            "recommended_medicine": h.recommended_medicine,
            "dosage": h.dosage,
            "doctor_status": h.doctor_status,
            "doctor_prescription": h.doctor_prescription,
            "doctor_comment": h.doctor_comment,
            "created_at": h.created_at.isoformat(),
        }
        for h in history
    ]}


@app.get("/api/alerts/outbreak")
async def outbreak_alert(location: str = Query(...), disease_name: str = Query(...)):
    alert = get_outbreak_alert(normalize_location(location), disease_name)
    return {"alert": alert}


@app.get("/api/doctor/dashboard")
async def default_doctor_dashboard():
    # For demo purposes, default to doctor ID 1
    return await doctor_dashboard(1)


@app.get("/api/doctor/{doctor_id}/dashboard")
async def doctor_dashboard(doctor_id: int):
    doctor = session.query(Doctor).filter(Doctor.id == doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")

    pending_consultations = session.query(ConsultationRequest).filter(
        ConsultationRequest.doctor_id == doctor_id,
        ConsultationRequest.status.in_(["pending", "accepted", "in_progress"])
    ).order_by(ConsultationRequest.created_at.asc()).all()

    completed_consultations = session.query(ConsultationRequest).filter(
        ConsultationRequest.doctor_id == doctor_id,
        ConsultationRequest.status == "completed"
    ).count()

    total_patients = session.query(func.count(func.distinct(ConsultationRequest.patient_id))).filter(
        ConsultationRequest.doctor_id == doctor_id
    ).scalar() or 0

    active_prescriptions = session.query(ConsultationHistory).filter(
        ConsultationHistory.doctor_id == doctor_id,
        ConsultationHistory.prescription != None
    ).count()

    emergency_cases = session.query(ConsultationRequest).filter(
        ConsultationRequest.doctor_id == doctor_id,
        ConsultationRequest.priority.in_(["urgent", "high"])
    ).count()

    cases = []
    for consultation in pending_consultations:
        patient = session.query(User).filter(User.id == consultation.patient_id).first()
        triage = None
        if consultation.triage_history_id:
            triage = session.query(TriageHistory).filter(TriageHistory.id == consultation.triage_history_id).first()

        cases.append({
            "consultation_id": consultation.id,
            "patient_id": patient.id if patient else None,
            "patient_name": patient.full_name if patient else "Unknown",
            "disease_name": consultation.disease_name,
            "predicted_specialty": consultation.predicted_specialty,
            "symptoms": consultation.patient_symptoms,
            "severity": consultation.severity,
            "priority": consultation.priority,
            "status": consultation.status,
            "created_at": consultation.created_at.isoformat(),
            "estimated_response_minutes": consultation.estimated_response_minutes,
            "photo_url": triage.photo_url if triage else None,
            "patient_location": triage.location if triage else None,
            "notes_from_patient": consultation.notes_from_patient,
            "triage_history_id": consultation.triage_history_id,
        })

    recent_activity = []
    recent_histories = session.query(ConsultationHistory).filter(
        ConsultationHistory.doctor_id == doctor_id
    ).order_by(ConsultationHistory.completed_at.desc()).limit(6).all()

    for history in recent_histories:
        patient = session.query(User).filter(User.id == history.patient_id).first()
        recent_activity.append({
            "type": "completed",
            "message": f"Completed consultation for {patient.full_name if patient else 'Unknown'} ({history.disease_name})",
            "timestamp": history.completed_at.isoformat() if history.completed_at else None,
            "patient_id": history.patient_id,
            "disease_name": history.disease_name,
            "prescription": history.prescription,
        })

    recent_requests = pending_consultations[-5:][::-1]
    for consultation in recent_requests:
        patient = session.query(User).filter(User.id == consultation.patient_id).first()
        recent_activity.append({
            "type": "pending",
            "message": f"New {consultation.priority.title()} case from {patient.full_name if patient else 'Unknown'}",
            "timestamp": consultation.created_at.isoformat(),
            "patient_id": consultation.patient_id,
            "disease_name": consultation.disease_name,
            "status": consultation.status,
        })

    notifications = session.query(Notification).filter(
        Notification.user_id == doctor_id
    ).order_by(Notification.created_at.desc()).limit(6).all()

    return {
        "success": True,
        "doctor": {
            "id": doctor.id,
            "name": doctor.name,
            "specialty": doctor.specialty,
            "hospital_affiliation": doctor.hospital_affiliation,
            "experience_years": doctor.experience_years,
        },
        "overview": {
            "total_patients": total_patients,
            "pending_cases": len(pending_consultations),
            "completed_consultations": completed_consultations,
            "active_prescriptions": active_prescriptions,
            "emergency_cases": emergency_cases,
        },
        "cases": cases,
        "recent_activity": recent_activity,
        "notifications": [
            {
                "id": n.id,
                "message": n.message,
                "status": n.status,
                "created_at": n.created_at.isoformat(),
            }
            for n in notifications
        ]
    }


@app.get("/api/doctor/patient/{patient_id}/history")
async def get_patient_history_for_doctor(patient_id: int):
    history = session.query(TriageHistory).filter(TriageHistory.user_id == patient_id).order_by(TriageHistory.created_at.desc()).all()
    return {
        "success": True,
        "history": [
            {
                "id": h.id,
                "disease_name": h.disease_name,
                "symptoms": h.symptoms,
                "severity": h.severity,
                "location": h.location,
                "photo_url": h.photo_url,
                "recommended_medicine": h.recommended_medicine,
                "doctor_prescription": h.doctor_prescription,
                "doctor_comment": h.doctor_comment,
                "created_at": h.created_at.isoformat(),
            }
            for h in history
        ]
    }


@app.get("/api/doctor/patient/{patient_id}/prescriptions")
async def get_patient_prescriptions_for_doctor(patient_id: int):
    prescriptions = session.query(TriageHistory).filter(
        TriageHistory.user_id == patient_id,
        TriageHistory.doctor_status != "pending"
    ).order_by(TriageHistory.created_at.desc()).all()
    
    # Also check ConsultationHistory
    consult_history = session.query(ConsultationHistory).filter(
        ConsultationHistory.patient_id == patient_id
    ).order_by(ConsultationHistory.completed_at.desc()).all()

    all_prescriptions = []
    for p in prescriptions:
        all_prescriptions.append({
            "source": "Triage",
            "date": p.created_at.isoformat(),
            "disease": p.disease_name,
            "medicine": p.doctor_prescription or p.recommended_medicine,
            "notes": p.doctor_comment
        })
    
    for c in consult_history:
        all_prescriptions.append({
            "source": "Consultation",
            "date": c.completed_at.isoformat() if c.completed_at else None,
            "disease": c.disease_name,
            "medicine": c.prescription,
            "notes": c.doctor_diagnosis
        })

    return {
        "success": True,
        "prescriptions": all_prescriptions
    }


@app.post("/api/doctor/prescription")
async def doctor_prescription_endpoint(request: DoctorPrescriptionRequest):
    # Find the triage record
    triage = session.query(TriageHistory).filter(TriageHistory.id == request.triage_id).first()
    if not triage:
        # Also check if it's a consultation ID
        consultation = session.query(ConsultationRequest).filter(ConsultationRequest.id == request.triage_id).first()
        if consultation:
            return await update_doctor_prescription(consultation.id, DoctorPrescriptionUpdate(
                action=request.action,
                medicine_name=request.medicine_name,
                doctor_notes=request.doctor_notes
            ))
        raise HTTPException(status_code=404, detail="Case not found")

    action = request.action.lower()
    triage.doctor_prescription = request.medicine_name
    triage.doctor_comment = request.doctor_notes
    triage.doctor_status = "completed" if action in ["approve", "override", "complete"] else "in_progress"
    
    # If there's an associated consultation request, update it too
    consultation = session.query(ConsultationRequest).filter(ConsultationRequest.triage_history_id == triage.id).first()
    if consultation:
        consultation.status = "completed" if action in ["approve", "override", "complete"] else "in_progress"
        if action in ["approve", "override", "complete"]:
            consultation.completed_at = datetime.utcnow()
            
            # Create ConsultationHistory entry
            history = ConsultationHistory(
                consultation_request_id=consultation.id,
                patient_id=consultation.patient_id,
                doctor_id=consultation.doctor_id,
                disease_name=consultation.disease_name,
                prescription=request.medicine_name,
                doctor_diagnosis=request.doctor_notes,
                completed_at=datetime.utcnow()
            )
            session.add(history)

    session.commit()
    return {"success": True, "message": "Prescription updated"}


@app.post("/api/doctor/consultations/{consultation_id}/prescription")
async def update_doctor_prescription(consultation_id: int, request: DoctorPrescriptionUpdate):
    consultation = session.query(ConsultationRequest).filter(
        ConsultationRequest.id == consultation_id
    ).first()
    if not consultation:
        raise HTTPException(status_code=404, detail="Consultation not found")

    action = request.action.lower()
    if action not in {"approve", "override", "in_progress", "complete"}:
        raise HTTPException(status_code=400, detail="Action must be approve, override, in_progress, or complete")

    if request.medicine_name and consultation.triage_history_id:
        triage = session.query(TriageHistory).filter(TriageHistory.id == consultation.triage_history_id).first()
        if triage:
            triage.doctor_prescription = request.medicine_name
            session.add(triage)

    if request.doctor_notes:
        consultation.notes_from_patient = request.doctor_notes

    if action == "approve":
        consultation.status = "accepted"
    elif action == "override":
        consultation.status = "in_progress"
    elif action == "in_progress":
        consultation.status = "in_progress"
    elif action == "complete":
        consultation.status = "completed"
        consultation.completed_at = datetime.utcnow()

    session.commit()

    return {
        "success": True,
        "consultation_id": consultation.id,
        "status": consultation.status,
        "medicine_name": request.medicine_name,
    }


@app.get("/api/doctor/{doctor_id}/notifications")
async def doctor_notifications(doctor_id: int):
    notifications = session.query(Notification).filter(Notification.user_id == doctor_id).order_by(Notification.created_at.desc()).all()
    return {
        "success": True,
        "notifications": [
            {
                "id": n.id,
                "message": n.message,
                "status": n.status,
                "created_at": n.created_at.isoformat(),
            }
            for n in notifications
        ]
    }


@app.get("/api/doctor/{doctor_id}/analytics")
async def doctor_analytics(doctor_id: int):
    """Get analytics data for doctor dashboard"""
    try:
        # Verify doctor exists
        doctor = session.query(Doctor).filter(Doctor.id == doctor_id).first()
        if not doctor:
            raise HTTPException(status_code=404, detail="Doctor not found")

        # Calculate metrics
        total_patients = session.query(func.count(func.distinct(ConsultationRequest.patient_id))).filter(
            ConsultationRequest.doctor_id == doctor_id
        ).scalar() or 0

        pending_cases = session.query(ConsultationRequest).filter(
            ConsultationRequest.doctor_id == doctor_id,
            ConsultationRequest.status.in_(["pending", "accepted", "in_progress"])
        ).count()

        completed_consultations = session.query(ConsultationRequest).filter(
            ConsultationRequest.doctor_id == doctor_id,
            ConsultationRequest.status == "completed"
        ).count()

        active_prescriptions = session.query(ConsultationHistory).filter(
            ConsultationHistory.doctor_id == doctor_id,
            ConsultationHistory.prescription != None
        ).count()

        emergency_cases = session.query(ConsultationRequest).filter(
            ConsultationRequest.doctor_id == doctor_id,
            ConsultationRequest.priority.in_(["urgent", "high"])
        ).count()

        return {
            "success": True,
            "analytics": {
                "total_patients": total_patients,
                "pending_cases": pending_cases,
                "completed_consultations": completed_consultations,
                "active_prescriptions": active_prescriptions,
                "emergency_cases": emergency_cases
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/api/doctor/prescriptions")
async def handle_doctor_prescription_action(request: DoctorPrescriptionAction, consultation_id: int = Query(...)):
    """Handle prescription actions from doctor dashboard"""
    try:
        # Get consultation
        consultation = session.query(ConsultationRequest).filter(
            ConsultationRequest.id == consultation_id
        ).first()

        if not consultation:
            raise HTTPException(status_code=404, detail="Consultation not found")

        # Update based on action
        if request.action == "approve":
            consultation.status = "completed"
            consultation.completed_at = datetime.utcnow()

            # Create consultation history
            history = ConsultationHistory(
                patient_id=consultation.patient_id,
                doctor_id=consultation.doctor_id,
                disease_name=consultation.disease_name,
                symptoms=consultation.patient_symptoms,
                prescription=request.medicine_name or consultation.disease_name,
                doctor_comment=request.doctor_notes,
                completed_at=datetime.utcnow()
            )
            session.add(history)

        elif request.action == "override":
            consultation.status = "completed"
            consultation.completed_at = datetime.utcnow()

            # Create consultation history with override
            history = ConsultationHistory(
                patient_id=consultation.patient_id,
                doctor_id=consultation.doctor_id,
                disease_name=consultation.disease_name,
                symptoms=consultation.patient_symptoms,
                prescription=request.medicine_name,
                doctor_comment=request.doctor_notes,
                completed_at=datetime.utcnow()
            )
            session.add(history)

        elif request.action == "complete":
            consultation.status = "completed"
            consultation.completed_at = datetime.utcnow()

        session.commit()

        return {
            "success": True,
            "consultation_id": consultation.id,
            "action": request.action,
            "status": consultation.status
        }
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        return {"success": False, "error": str(e)}


@app.get("/api/patient/prescriptions")
async def patient_prescriptions(user_id: int = Query(...)):
    prescriptions = session.query(TriageHistory).filter(
        TriageHistory.user_id == user_id,
        TriageHistory.doctor_status != "pending"
    ).order_by(TriageHistory.created_at.desc()).all()
    return {"prescriptions": [
        {
            "triage_id": p.id,
            "doctor_status": p.doctor_status,
            "doctor_prescription": p.doctor_prescription,
            "doctor_comment": p.doctor_comment,
            "recommended_medicine": p.recommended_medicine,
            "dosage": p.dosage,
            "created_at": p.created_at.isoformat(),
        }
        for p in prescriptions
    ]}


@app.get("/reports/export/anonymized")
async def export_anonymized():
    filepath = export_anonymized_json(engine)
    return FileResponse(filepath, media_type="application/json", filename=Path(filepath).name)


@app.get("/reports/export/csv")
async def export_anonymized_csv():
    filepath = export_research_data(engine)
    return FileResponse(filepath, media_type="text/csv", filename=Path(filepath).name)


@app.get("/reports/pdf/{triage_id}")
async def download_report(triage_id: int):
    history = session.query(TriageHistory).filter(TriageHistory.id == triage_id).first()
    if not history:
        raise HTTPException(status_code=404, detail="Triage record not found")

    disease = session.query(Disease).filter(Disease.name.ilike(f"%{history.disease_name}%")).first()
    report_data = {
        "name": f"user_{history.user_id}",
        "disease": history.disease_name,
        "dosage": history.dosage or "Not available",
        "safe_tip": disease.safe_tip if disease else "No safe tip available",
        "myth": disease.dangerous_myth if disease else "No myth data",
        "diet_eat": disease.diet_to_eat if disease else "Standard balanced diet",
        "diet_avoid": disease.diet_to_avoid if disease else "Standard avoid list",
    }
    filepath = generate_pdf_report(report_data)
    return FileResponse(filepath, media_type="application/pdf", filename=Path(filepath).name)


# --- DOCTOR ROUTING ENDPOINTS ---

@app.get("/consultation-request")
async def read_consultation_page():
    """Serve the consultation request HTML page"""
    return FileResponse(Path("static") / "consultation-request.html")


@app.get("/api/doctors/available")
async def get_doctors_for_disease(disease_name: str = Query(...)):
    """
    Get available doctors based on disease specialty prediction
    
    Returns:
    - Predicted specialty
    - List of available doctors for that specialty
    - Alternative specialists if primary specialty unavailable
    """
    try:
        # Predict specialty based on disease name
        predicted_specialty = predict_specialty(disease_name)
        
        # Get available doctors for this specialty
        available = get_available_doctors(predicted_specialty)
        
        # Get alternatives if no doctors available
        alternatives = []
        if not available:
            alternatives = get_alternative_specialists(predicted_specialty)
        
        return {
            "success": True,
            "disease_name": disease_name,
            "predicted_specialty": predicted_specialty,
            "available_doctors": available,
            "alternative_specialists": alternatives,
            "has_available": len(available) > 0
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/api/consultations/request")
async def request_consultation(request: DoctorSelectionRequest):
    """
    Patient selects a doctor and requests a consultation
    
    Creates a ConsultationRequest and assigns it to the selected doctor
    """
    try:
        # Verify patient exists
        patient = session.query(User).filter(User.id == request.patient_id).first()
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        # Verify doctor exists
        doctor = session.query(Doctor).filter(Doctor.id == request.doctor_id).first()
        if not doctor:
            raise HTTPException(status_code=404, detail="Doctor not found")
        
        # Get predicted specialty
        specialty = predict_specialty(request.disease_name)
        
        # Create consultation request
        consultation = create_consultation_request(
            patient_id=request.patient_id,
            doctor_id=request.doctor_id,
            disease_name=request.disease_name,
            predicted_specialty=specialty,
            symptoms=request.symptoms,
            severity=request.severity,
            priority=request.priority,
            notes=request.notes,
            triage_history_id=request.triage_history_id
        )
        
        if not consultation:
            raise HTTPException(status_code=500, detail="Failed to create consultation")
        
        # Create notification for doctor
        doctor_notification = Notification(
            user_id=doctor.id,
            message=f"New {request.priority.title()} consultation request from {patient.full_name} - {request.disease_name}",
            status="pending"
        )
        session.add(doctor_notification)
        
        # Create notification for patient
        patient_notification = Notification(
            user_id=request.patient_id,
            message=f"Your consultation request has been assigned to Dr. {doctor.name}. Estimated response: {consultation.estimated_response_minutes} minutes.",
            status="pending"
        )
        session.add(patient_notification)
        session.commit()
        
        return {
            "success": True,
            "consultation_id": consultation.id,
            "doctor_id": doctor.id,
            "doctor_name": doctor.name,
            "status": "pending",
            "estimated_response_minutes": consultation.estimated_response_minutes
        }
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        return {"success": False, "error": str(e)}


@app.get("/api/consultations/{consultation_id}")
async def get_consultation_details(consultation_id: int):
    """Get details of a specific consultation request"""
    try:
        consultation = session.query(ConsultationRequest).filter(
            ConsultationRequest.id == consultation_id
        ).first()
        
        if not consultation:
            raise HTTPException(status_code=404, detail="Consultation not found")
        
        doctor = session.query(Doctor).filter(Doctor.id == consultation.doctor_id).first()
        patient = session.query(User).filter(User.id == consultation.patient_id).first()
        
        return {
            "success": True,
            "id": consultation.id,
            "patient": {
                "id": patient.id,
                "name": patient.full_name
            },
            "doctor": {
                "id": doctor.id,
                "name": doctor.name,
                "specialty": doctor.specialty
            },
            "disease_name": consultation.disease_name,
            "symptoms": consultation.patient_symptoms,
            "severity": consultation.severity,
            "priority": consultation.priority,
            "status": consultation.status,
            "estimated_response_minutes": consultation.estimated_response_minutes,
            "created_at": consultation.created_at.isoformat(),
            "assigned_at": consultation.assigned_at.isoformat() if consultation.assigned_at else None,
            "accepted_at": consultation.accepted_at.isoformat() if consultation.accepted_at else None,
            "started_at": consultation.started_at.isoformat() if consultation.started_at else None,
            "completed_at": consultation.completed_at.isoformat() if consultation.completed_at else None,
        }
    except HTTPException:
        raise
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.get("/api/consultations/patient/{patient_id}")
async def get_patient_consultations(patient_id: int):
    """Get all consultations for a patient"""
    try:
        consultations = session.query(ConsultationRequest).filter(
            ConsultationRequest.patient_id == patient_id
        ).order_by(ConsultationRequest.created_at.desc()).all()
        
        result = []
        for consultation in consultations:
            doctor = session.query(Doctor).filter(Doctor.id == consultation.doctor_id).first()
            result.append({
                "id": consultation.id,
                "doctor_name": doctor.name,
                "specialty": doctor.specialty,
                "disease_name": consultation.disease_name,
                "status": consultation.status,
                "priority": consultation.priority,
                "created_at": consultation.created_at.isoformat(),
                "completed_at": consultation.completed_at.isoformat() if consultation.completed_at else None,
            })
        
        return {"success": True, "consultations": result}
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.patch("/api/consultations/{consultation_id}/status")
async def update_consultation_status_endpoint(
    consultation_id: int,
    status: str = Query(...),
    comment: Optional[str] = Query(None)
):
    """Update consultation status (pending -> accepted -> in_progress -> completed -> rejected)"""
    try:
        valid_statuses = ["pending", "accepted", "in_progress", "completed", "cancelled", "rejected"]
        if status not in valid_statuses:
            raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")
        
        success = update_consultation_status(consultation_id, status, comment)
        
        if not success:
            raise HTTPException(status_code=404, detail="Consultation not found")
        
        # Send notification to patient
        consultation = session.query(ConsultationRequest).filter(
            ConsultationRequest.id == consultation_id
        ).first()
        
        status_messages = {
            "accepted": "Your consultation has been accepted. The doctor will start shortly.",
            "in_progress": "Your consultation is now in progress.",
            "completed": "Your consultation has been completed.",
            "cancelled": "Your consultation has been cancelled.",
            "rejected": f"Your consultation was rejected by the specialist. Reason: {comment or 'None'}"
        }
        
        notification = Notification(
            user_id=consultation.patient_id,
            message=status_messages.get(status, f"Consultation status updated to {status}"),
            status="pending"
        )
        session.add(notification)
        session.commit()
        
        return {"success": True, "consultation_id": consultation_id, "new_status": status}
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        return {"success": False, "error": str(e)}


@app.post("/api/consultations/{consultation_id}/complete")
async def complete_consultation_endpoint(
    consultation_id: int,
    request: ConsultationCompletion
):
    """Complete a consultation and save diagnosis/prescription"""
    try:
        success = complete_consultation(
            consultation_id,
            request.diagnosis,
            request.prescription,
            request.recommendations,
            request.duration_minutes
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Consultation not found")
        
        consultation = session.query(ConsultationRequest).filter(
            ConsultationRequest.id == consultation_id
        ).first()
        
        # Send notification to patient
        notification = Notification(
            user_id=consultation.patient_id,
            message="Your consultation has been completed. Please review your prescription and recommendations.",
            status="pending"
        )
        session.add(notification)
        session.commit()
        
        return {"success": True, "consultation_id": consultation_id, "status": "completed"}
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        return {"success": False, "error": str(e)}


@app.post("/api/consultations/{consultation_id}/rate")
async def rate_consultation_endpoint(
    consultation_id: int,
    request: ConsultationRating
):
    """Rate and review a completed consultation"""
    try:
        if request.rating < 1 or request.rating > 5:
            raise HTTPException(status_code=400, detail="Rating must be between 1 and 5")
        
        success = rate_consultation(consultation_id, request.rating, request.feedback)
        
        if not success:
            raise HTTPException(status_code=404, detail="Consultation history not found")
        
        return {"success": True, "consultation_id": consultation_id, "rating": request.rating}
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        return {"success": False, "error": str(e)}


@app.get("/api/consultations/history/{patient_id}")
async def get_consultation_history_endpoint(patient_id: int):
    """Get patient's consultation history"""
    try:
        history = get_consultation_history(patient_id)
        return {"success": True, "history": history}
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.patch("/api/doctors/{doctor_id}/status")
async def update_doctor_status_endpoint(doctor_id: int, request: DoctorStatusUpdate):
    """Update doctor's online/offline status"""
    try:
        # Verify doctor exists
        doctor = session.query(Doctor).filter(Doctor.id == doctor_id).first()
        if not doctor:
            raise HTTPException(status_code=404, detail="Doctor not found")
        
        success = update_doctor_status(doctor_id, request.is_online)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update doctor status")
        
        return {
            "success": True,
            "doctor_id": doctor_id,
            "is_online": request.is_online
        }
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        return {"success": False, "error": str(e)}


@app.patch("/api/doctors/{doctor_id}/queue")
async def update_doctor_queue_endpoint(doctor_id: int, request: DoctorQueueUpdate):
    """Update doctor's queue size and estimated wait time"""
    try:
        # Verify doctor exists
        doctor = session.query(Doctor).filter(Doctor.id == doctor_id).first()
        if not doctor:
            raise HTTPException(status_code=404, detail="Doctor not found")
        
        success = update_doctor_queue(
            doctor_id,
            request.queue_size,
            request.estimated_wait_minutes
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update doctor queue")
        
        return {
            "success": True,
            "doctor_id": doctor_id,
            "queue_size": request.queue_size,
            "estimated_wait_minutes": request.estimated_wait_minutes
        }
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        return {"success": False, "error": str(e)}


@app.get("/api/doctors/{doctor_id}/pending")
async def get_doctor_pending_consultations(doctor_id: int):
    """Get pending consultations for a doctor"""
    try:
        # Verify doctor exists
        doctor = session.query(Doctor).filter(Doctor.id == doctor_id).first()
        if not doctor:
            raise HTTPException(status_code=404, detail="Doctor not found")
        
        pending = get_pending_consultations(doctor_id)
        return {"success": True, "pending": pending}
    except HTTPException:
        raise
    except Exception as e:
        return {"success": False, "error": str(e)}


# --- REAL-TIME STATUS UPDATES ---

@app.get("/api/consultations/{consultation_id}/stream")
async def stream_consultation_status(consultation_id: int):
    """
    Server-Sent Events (SSE) stream for real-time consultation status updates.
    Client can connect and receive updates when status changes.
    """
    async def event_generator():
        # Send initial status
        consultation = session.query(ConsultationRequest).filter(
            ConsultationRequest.id == consultation_id
        ).first()
        
        if not consultation:
            yield f"data: {json.dumps({'error': 'Consultation not found'})}\n\n"
            return
        
        # Keep track of last known status
        last_status = consultation.status
        last_update = consultation.updated_at if hasattr(consultation, 'updated_at') else datetime.utcnow()
        
        # Stream updates for 30 minutes
        start_time = datetime.utcnow()
        while (datetime.utcnow() - start_time).total_seconds() < 1800:
            try:
                # Check for status updates
                consultation = session.query(ConsultationRequest).filter(
                    ConsultationRequest.id == consultation_id
                ).first()
                
                if consultation and consultation.status != last_status:
                    doctor = session.query(Doctor).filter(Doctor.id == consultation.doctor_id).first()
                    
                    data = {
                        "consultation_id": consultation.id,
                        "status": consultation.status,
                        "doctor_name": doctor.name if doctor else "Unknown",
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    
                    yield f"data: {json.dumps(data)}\n\n"
                    last_status = consultation.status
                    
                    # Stop streaming if consultation is completed or cancelled
                    if consultation.status in ["completed", "cancelled"]:
                        break
                
                # Wait 5 seconds before checking again
                await asyncio.sleep(5)
            except Exception as e:
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
                break
    
    return StreamingResponse(event_generator(), media_type="text/event-stream")


# --- DIAGNOSIS MODULE ENDPOINTS ---

@app.get("/diagnosis/{consultation_id}")
async def read_diagnosis_interface(consultation_id: int):
    return FileResponse(Path("static") / "diagnosis-interface.html")


@app.get("/api/consultations/{consultation_id}/diagnosis")
async def get_diagnosis_draft(consultation_id: int):
    consultation = session.query(ConsultationRequest).filter(ConsultationRequest.id == consultation_id).first()
    if not consultation:
        raise HTTPException(status_code=404, detail="Consultation not found")
    
    patient = session.query(User).filter(User.id == consultation.patient_id).first()
    triage = None
    if consultation.triage_history_id:
        triage = session.query(TriageHistory).filter(TriageHistory.id == consultation.triage_history_id).first()

    return {
        "success": True,
        "data": {
            "consultation_id": consultation.id,
            "patient_id": consultation.patient_id,
            "doctor_id": consultation.doctor_id,
            "patient_name": patient.full_name if patient else "Unknown",
            "ai_predicted_disease": consultation.disease_name,
            "photo_url": triage.photo_url if triage else None,
            "patient_symptoms": consultation.patient_symptoms,
            "actual_diagnosis": consultation.actual_diagnosis,
            "severity": consultation.severity,
            "precautions": consultation.precautions,
            "treatment_notes": consultation.treatment_notes,
            "follow_up_instructions": consultation.follow_up_instructions,
            "prescription_data": consultation.prescription_data,
            "status": consultation.status,
            "created_at": consultation.created_at.isoformat()
        }
    }


@app.post("/api/consultations/{consultation_id}/diagnosis/auto-save")
async def auto_save_diagnosis(consultation_id: int, draft: DiagnosisDraft):
    consultation = session.query(ConsultationRequest).filter(ConsultationRequest.id == consultation_id).first()
    if not consultation:
        raise HTTPException(status_code=404, detail="Consultation not found")
    
    if draft.actual_diagnosis is not None: consultation.actual_diagnosis = draft.actual_diagnosis
    if draft.patient_symptoms is not None: consultation.patient_symptoms = draft.patient_symptoms
    if draft.severity is not None: consultation.severity = draft.severity
    if draft.precautions is not None: consultation.precautions = draft.precautions
    if draft.treatment_notes is not None: consultation.treatment_notes = draft.treatment_notes
    if draft.follow_up_instructions is not None: consultation.follow_up_instructions = draft.follow_up_instructions
    if draft.prescription_data is not None: consultation.prescription_data = draft.prescription_data
    
    if consultation.status == "pending":
        consultation.status = "under_review"
        
    session.commit()
    return {"success": True, "message": "Draft auto-saved"}


@app.post("/api/consultations/{consultation_id}/diagnosis/finalize")
async def finalize_diagnosis(consultation_id: int, draft: DiagnosisFinalize):
    consultation = session.query(ConsultationRequest).filter(ConsultationRequest.id == consultation_id).first()
    if not consultation:
        raise HTTPException(status_code=404, detail="Consultation not found")
    
    if draft.actual_diagnosis is not None: consultation.actual_diagnosis = draft.actual_diagnosis
    if draft.patient_symptoms is not None: consultation.patient_symptoms = draft.patient_symptoms
    if draft.severity is not None: consultation.severity = draft.severity
    if draft.precautions is not None: consultation.precautions = draft.precautions
    if draft.treatment_notes is not None: consultation.treatment_notes = draft.treatment_notes
    if draft.follow_up_instructions is not None: consultation.follow_up_instructions = draft.follow_up_instructions
    if draft.prescription_data is not None: consultation.prescription_data = draft.prescription_data
    
    consultation.status = "diagnosed"
    consultation.completed_at = datetime.utcnow()
    
    if draft.prescription_data:
        try:
            p_data = json.loads(draft.prescription_data)
            medicines = p_data.get("medicines", [])
            now = datetime.utcnow()
            import re
            
            timing_map = {
                "Morning": 8,
                "Afternoon": 13,
                "Evening": 18,
                "Night": 21
            }
            
            for med in medicines:
                duration_str = med.get("duration", "1")
                match = re.search(r'\d+', duration_str)
                days = int(match.group()) if match else 1
                
                timings = med.get("timings", [])
                for day in range(days):
                    base_date = now.date() + timedelta(days=day)
                    for t in timings:
                        hour = timing_map.get(t, 9)
                        sched_time = datetime.combine(base_date, time(hour=hour))
                        
                        sched = PrescriptionSchedule(
                            patient_id=consultation.patient_id,
                            consultation_id=consultation.id,
                            medicine_name=med.get("name"),
                            dosage=med.get("dosage"),
                            instructions=med.get("instructions"),
                            scheduled_time=sched_time,
                            status="pending"
                        )
                        session.add(sched)
        except Exception as e:
            print(f"Error generating schedules: {e}")
    
    history = ConsultationHistory(
        consultation_request_id=consultation.id,
        patient_id=consultation.patient_id,
        doctor_id=consultation.doctor_id,
        disease_name=draft.actual_diagnosis or consultation.disease_name,
        doctor_diagnosis=draft.treatment_notes,
        recommendations=draft.precautions,
        completed_at=datetime.utcnow()
    )
    session.add(history)
    session.commit()
    session.refresh(history)

    if draft.prescription_data:
        try:
            p_data = json.loads(draft.prescription_data)
            patient = session.query(User).filter(User.id == consultation.patient_id).first()
            doctor = session.query(Doctor).filter(Doctor.id == consultation.doctor_id).first()
            
            pdf_data = {
                "doctor_name": doctor.name if doctor else "Unknown",
                "doctor_specialty": doctor.specialty if doctor else "General",
                "patient_name": patient.full_name if patient else "Unknown",
                "patient_id": patient.id if patient else 0,
                "patient_age": getattr(patient, 'age', "N/A"),
                "patient_gender": getattr(patient, 'gender', "N/A"),
                "diagnosis": draft.actual_diagnosis or consultation.disease_name,
                "medicines": p_data.get("medicines", []),
                "lab_tests": p_data.get("lab_tests", ""),
                "diet_plan": p_data.get("diet_plan", ""),
                "exercise": p_data.get("exercise", ""),
                "prescription_id": f"RX-{history.id}-{datetime.utcnow().strftime('%M%S')}"
            }
            
            from report_service import generate_prescription_pdf
            pdf_path = generate_prescription_pdf(pdf_data)
            history.pdf_path = pdf_path
            session.commit()
        except Exception as e:
            print(f"Error generating prescription PDF: {e}")

    return {"success": True, "message": "Diagnosis finalized"}

class ConsultationSetup(BaseModel):
    consultation_type: str
    clinic_address: Optional[str] = None
    appointment_time: Optional[datetime] = None

@app.post("/api/consultations/{consultation_id}/setup")
async def setup_consultation(consultation_id: int, setup_data: ConsultationSetup):
    consultation = session.query(ConsultationRequest).filter(ConsultationRequest.id == consultation_id).first()
    if not consultation:
        raise HTTPException(status_code=404, detail="Consultation not found")
        
    consultation.consultation_type = setup_data.consultation_type
    
    if setup_data.consultation_type == "offline":
        consultation.clinic_address = setup_data.clinic_address
        consultation.appointment_time = setup_data.appointment_time
        import random, string
        token = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        consultation.token_number = token
        consultation.meeting_status = "scheduled"
    else:
        consultation.meeting_status = "in_progress"
        
    session.commit()
    return {"success": True, "token": getattr(consultation, 'token_number', None), "status": consultation.meeting_status}

# WebSocket Manager for Online Consultation
class ConnectionManager:
    def __init__(self):
        self.active_connections: dict = {}

    async def connect(self, websocket: WebSocket, room_id: str):
        await websocket.accept()
        if room_id not in self.active_connections:
            self.active_connections[room_id] = []
        self.active_connections[room_id].append(websocket)

    def disconnect(self, websocket: WebSocket, room_id: str):
        if room_id in self.active_connections:
            self.active_connections[room_id].remove(websocket)
            if not self.active_connections[room_id]:
                del self.active_connections[room_id]

    async def broadcast(self, message: str, room_id: str, exclude: WebSocket = None):
        if room_id in self.active_connections:
            for connection in self.active_connections[room_id]:
                if connection != exclude:
                    await connection.send_text(message)

manager = ConnectionManager()

@app.websocket("/ws/consultation/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str):
    await manager.connect(websocket, room_id)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.broadcast(data, room_id, exclude=websocket)
    except WebSocketDisconnect:
        manager.disconnect(websocket, room_id)

@app.get("/api/patient/{patient_id}/consultations")
async def get_patient_consultations(patient_id: int):
    consultations = session.query(ConsultationRequest).filter(
        ConsultationRequest.patient_id == patient_id,
        ConsultationRequest.status.in_(["pending", "under_review", "accepted", "in_progress"])
    ).order_by(ConsultationRequest.id.desc()).all()
    
    data = []
    for c in consultations:
        data.append({
            "id": c.id,
            "disease_name": c.disease_name,
            "status": c.status,
            "type": getattr(c, 'consultation_type', 'online'),
            "clinic_address": getattr(c, 'clinic_address', None),
            "appointment_time": getattr(c, 'appointment_time', None).isoformat() if getattr(c, 'appointment_time', None) else None,
            "token_number": getattr(c, 'token_number', None),
            "meeting_status": getattr(c, 'meeting_status', 'pending')
        })
    return {"success": True, "data": data}

@app.get("/api/patient/{patient_id}/dashboard")
async def get_patient_dashboard(patient_id: int):
    active_consultation = session.query(ConsultationRequest).filter(
        ConsultationRequest.patient_id == patient_id,
        ConsultationRequest.status.in_(["pending", "under_review", "accepted", "in_progress", "follow_up_required"])
    ).order_by(ConsultationRequest.id.desc()).first()
    
    cons_data = None
    if active_consultation:
        doctor = session.query(Doctor).filter(Doctor.id == active_consultation.doctor_id).first()
        cons_data = {
            "id": active_consultation.id,
            "disease_name": active_consultation.disease_name,
            "status": active_consultation.status,
            "doctor_name": doctor.name if doctor else "Unassigned",
            "doctor_specialty": doctor.specialty if doctor else "",
            "type": getattr(active_consultation, 'consultation_type', 'online'),
            "clinic_address": getattr(active_consultation, 'clinic_address', None),
            "appointment_time": getattr(active_consultation, 'appointment_time', None).isoformat() if getattr(active_consultation, 'appointment_time', None) else None,
            "token_number": getattr(active_consultation, 'token_number', None),
            "meeting_status": getattr(active_consultation, 'meeting_status', 'pending')
        }

    history = session.query(ConsultationHistory).filter(
        ConsultationHistory.patient_id == patient_id
    ).order_by(ConsultationHistory.id.desc()).first()
    
    rx_data = None
    if history:
        rx_data = {
            "disease_name": history.disease_name,
            "doctor_notes": history.doctor_diagnosis,
            "follow_up": history.recommendations,
            "pdf_path": history.id if history.pdf_path else None
        }

    today = datetime.utcnow().date()
    start_of_day = datetime.combine(today, datetime.min.time())
    end_of_day = datetime.combine(today, datetime.max.time())
    
    schedules = session.query(PrescriptionSchedule).filter(
        PrescriptionSchedule.patient_id == patient_id,
        PrescriptionSchedule.scheduled_time >= start_of_day,
        PrescriptionSchedule.scheduled_time <= end_of_day
    ).order_by(PrescriptionSchedule.scheduled_time.asc()).all()
    
    meds_data = []
    for s in schedules:
        meds_data.append({
            "id": s.id,
            "medicine_name": s.medicine_name,
            "dosage": s.dosage,
            "time": s.scheduled_time.strftime("%I:%M %p"),
            "status": s.status
        })

    notifications = session.query(PatientNotification).filter(
        PatientNotification.user_id == patient_id
    ).order_by(PatientNotification.id.desc()).limit(3).all()
    notifs_data = [{"message": n.message, "status": n.status} for n in notifications]

    return {
        "success": True,
        "active_consultation": cons_data,
        "latest_prescription": rx_data,
        "todays_medicines": meds_data,
        "recent_notifications": notifs_data
    }

@app.get("/reports/download/{history_id}")
async def download_prescription(history_id: int):
    import os
    history = session.query(ConsultationHistory).filter(ConsultationHistory.id == history_id).first()
    if not history or not history.pdf_path:
        raise HTTPException(status_code=404, detail="Prescription PDF not found")
        
    if not os.path.exists(history.pdf_path):
        raise HTTPException(status_code=404, detail="Prescription PDF not found")
        
    return FileResponse(
        history.pdf_path, 
        media_type='application/pdf',
        filename=f"Prescription_{history.disease_name}.pdf"
    )

class FollowUpCreate(BaseModel):
    consultation_id: int
    patient_id: int
    doctor_id: int
    follow_up_date: str
    notes: Optional[str] = None

@app.post("/api/follow-ups")
async def create_follow_up(data: FollowUpCreate):
    try:
        date_obj = datetime.fromisoformat(data.follow_up_date.replace("Z", "+00:00"))
        req = FollowUpRequest(
            consultation_id=data.consultation_id,
            patient_id=data.patient_id,
            doctor_id=data.doctor_id,
            follow_up_date=date_obj,
            notes=data.notes
        )
        session.add(req)
        
        notif = PatientNotification(
            user_id=data.patient_id,
            type="reminder",
            title="Follow-up Requested",
            message=f"Your doctor requested a follow-up on {date_obj.strftime('%Y-%m-%d')}.",
            action_link="#appointments"
        )
        session.add(notif)
        session.commit()
        return {"success": True}
    except Exception as e:
        session.rollback()
        return {"success": False, "error": str(e)}

@app.get("/api/patient/{patient_id}/follow-ups")
async def get_patient_follow_ups(patient_id: int):
    follow_ups = session.query(FollowUpRequest).filter(
        FollowUpRequest.patient_id == patient_id
    ).order_by(FollowUpRequest.follow_up_date.desc()).all()
    
    data = []
    for f in follow_ups:
        doc = session.query(Doctor).filter(Doctor.id == f.doctor_id).first()
        data.append({
            "id": f.id,
            "consultation_id": f.consultation_id,
            "doctor_name": doc.name if doc else "Doctor",
            "follow_up_date": f.follow_up_date.isoformat() if f.follow_up_date else None,
            "notes": f.notes,
            "status": f.status
        })
    return {"success": True, "data": data}

@app.get("/api/notifications/{user_id}")
async def get_notifications(user_id: int):
    notifs = session.query(PatientNotification).filter(
        PatientNotification.user_id == user_id
    ).order_by(PatientNotification.id.desc()).all()
    data = []
    for n in notifs:
        data.append({
            "id": n.id,
            "type": n.type,
            "title": n.title,
            "message": n.message,
            "is_read": n.is_read,
            "action_link": n.action_link,
            "created_at": n.created_at.isoformat() if n.created_at else None,
            "status": n.status
        })
    return {"success": True, "data": data}

@app.put("/api/notifications/{notification_id}/read")
async def mark_notification_read(notification_id: int):
    notif = session.query(PatientNotification).filter(PatientNotification.id == notification_id).first()
    if notif:
        notif.is_read = True
        notif.status = "read"
        session.commit()
        return {"success": True}
    return {"success": False, "error": "Not found"}

@app.put("/api/follow-ups/{follow_up_id}/{action}")
async def manage_follow_up(follow_up_id: int, action: str):
    req = session.query(FollowUpRequest).filter(FollowUpRequest.id == follow_up_id).first()
    if req:
        if action == "confirm":
            req.status = "confirmed"
        elif action == "reschedule":
            req.status = "rescheduled"
        session.commit()
        return {"success": True}
    return {"success": False}

@app.get("/api/medicines/search")
async def search_medicines(q: str = Query(..., min_length=1)):
    """Search for matching medicine names in the diseases table."""
    results = session.query(Disease.medicine_name).filter(Disease.medicine_name.ilike(f"%{q}%")).distinct().limit(10).all()
    # Handle possible empty or NaN values if any
    medicines = [row[0] for row in results if row[0] and str(row[0]).strip()]
    return {"success": True, "data": medicines}

class ScheduleAction(BaseModel):
    action: str

@app.get("/api/patient/{patient_id}/medication-schedule")
async def get_patient_medication_schedule(patient_id: int):
    now = datetime.utcnow()
    start_time = now - timedelta(days=1)
    
    schedules = session.query(PrescriptionSchedule).filter(
        PrescriptionSchedule.patient_id == patient_id,
        PrescriptionSchedule.scheduled_time >= start_time
    ).order_by(PrescriptionSchedule.scheduled_time).all()
    
    today_start = datetime.combine(now.date(), time(0,0))
    today_end = datetime.combine(now.date(), time(23,59,59))
    
    today_schedules = [s for s in schedules if today_start <= s.scheduled_time <= today_end]
    total_today = len(today_schedules)
    taken_today = len([s for s in today_schedules if s.status == "taken"])
    
    completion_percentage = int((taken_today / total_today) * 100) if total_today > 0 else 0
    
    data = []
    for s in schedules:
        data.append({
            "id": s.id,
            "medicine_name": s.medicine_name,
            "dosage": s.dosage,
            "instructions": s.instructions,
            "scheduled_time": s.scheduled_time.isoformat(),
            "status": s.status,
            "taken_at": s.taken_at.isoformat() if s.taken_at else None
        })
        
    return {
        "success": True, 
        "data": data,
        "analytics": {
            "total_today": total_today,
            "taken_today": taken_today,
            "completion_percentage": completion_percentage
        }
    }

@app.post("/api/schedule/{schedule_id}/action")
async def update_schedule_action(schedule_id: int, action_req: ScheduleAction):
    sched = session.query(PrescriptionSchedule).filter(PrescriptionSchedule.id == schedule_id).first()
    if not sched:
        raise HTTPException(status_code=404, detail="Schedule not found")
        
    if action_req.action == "take":
        sched.status = "taken"
        sched.taken_at = datetime.utcnow()
    elif action_req.action == "snooze":
        sched.status = "snoozed"
        sched.scheduled_time = sched.scheduled_time + timedelta(hours=1)
        
    session.commit()
    return {"success": True, "status": sched.status, "scheduled_time": sched.scheduled_time.isoformat()}

class DoctorAvailabilityUpdate(BaseModel):
    is_online: bool
    working_hours_start: Optional[str] = None
    working_hours_end: Optional[str] = None
    unavailable_dates: Optional[str] = None

@app.put("/api/doctor/{doctor_id}/availability")
async def update_doctor_availability(doctor_id: int, data: DoctorAvailabilityUpdate):
    try:
        avail = session.query(DoctorAvailability).filter(DoctorAvailability.doctor_id == doctor_id).first()
        if not avail:
            avail = DoctorAvailability(doctor_id=doctor_id)
            session.add(avail)
        
        avail.is_online = data.is_online
        if data.working_hours_start:
            avail.working_hours_start = data.working_hours_start
        if data.working_hours_end:
            avail.working_hours_end = data.working_hours_end
        if data.unavailable_dates is not None:
            avail.unavailable_dates = data.unavailable_dates
            
        avail.last_updated = datetime.utcnow()
        session.commit()
        return {"success": True}
    except Exception as e:
        session.rollback()
        return {"success": False, "error": str(e)}

@app.get("/api/doctor/{doctor_id}/availability")
async def get_doctor_availability(doctor_id: int):
    try:
        avail = session.query(DoctorAvailability).filter(DoctorAvailability.doctor_id == doctor_id).first()
        if not avail:
            avail = DoctorAvailability(doctor_id=doctor_id, is_online=False, working_hours_start="09:00", working_hours_end="17:00", unavailable_dates="")
            session.add(avail)
            session.commit()
        return {
            "success": True,
            "is_online": avail.is_online,
            "working_hours_start": avail.working_hours_start or "09:00",
            "working_hours_end": avail.working_hours_end or "17:00",
            "unavailable_dates": avail.unavailable_dates or ""
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/patient/{patient_id}/timeline")
async def get_patient_timeline(patient_id: int):
    try:
        events = []
        
        triages = session.query(TriageHistory).filter(TriageHistory.user_id == patient_id).all()
        for t in triages:
            events.append({
                "type": "triage",
                "icon": "fa-stethoscope",
                "color": "var(--primary)",
                "title": f"AI Triage: {t.disease_name}",
                "description": f"Reported symptoms: {t.symptoms[:50]}...",
                "timestamp": t.created_at
            })
            
        histories = session.query(ConsultationHistory).filter(ConsultationHistory.patient_id == patient_id).all()
        for h in histories:
            events.append({
                "type": "diagnosis",
                "icon": "fa-user-md",
                "color": "var(--success)",
                "title": f"Diagnosis: {h.disease_name}",
                "description": f"Doctor prescribed: {h.prescription}",
                "timestamp": h.completed_at
            })
            
        followups = session.query(FollowUpRequest).filter(FollowUpRequest.patient_id == patient_id).all()
        for f in followups:
            events.append({
                "type": "followup",
                "icon": "fa-calendar-plus",
                "color": "var(--warning)",
                "title": "Follow-Up Scheduled",
                "description": f"Status: {f.status}",
                "timestamp": f.created_at
            })
            
        events.sort(key=lambda x: x["timestamp"] if x["timestamp"] else datetime.min, reverse=True)
        
        for e in events:
            e["timestamp"] = e["timestamp"].isoformat() if e["timestamp"] else None
            
        return {"success": True, "timeline": events}
    except Exception as e:
        return {"success": False, "error": str(e)}

class DoctorCreateRequest(BaseModel):
    name: str
    email: str
    password: str
    specialty: str
    qualifications: str
    experience_years: int
    hospital_affiliation: str

@app.get("/admin")
async def read_admin_page():
    return FileResponse(Path("static") / "admin-panel.html")

@app.post("/api/admin/doctors")
async def create_doctor(request: DoctorCreateRequest):
    try:
        existing = session.query(Doctor).filter(Doctor.email == request.email).first()
        if existing:
            return {"success": False, "error": "Email already registered to a doctor"}
            
        hashed_pw = hash_password(request.password)
        
        new_doctor = Doctor(
            name=request.name,
            email=request.email,
            hashed_password=hashed_pw,
            specialty=request.specialty,
            qualifications=request.qualifications,
            experience_years=request.experience_years,
            hospital_affiliation=request.hospital_affiliation
        )
        session.add(new_doctor)
        session.commit()
        session.refresh(new_doctor)
        
        avail = DoctorAvailability(doctor_id=new_doctor.id)
        session.add(avail)
        session.commit()
        
        return {"success": True, "doctor_id": new_doctor.id}
    except Exception as e:
        session.rollback()
        return {"success": False, "error": str(e)}

@app.get("/api/admin/doctors")
async def get_all_doctors():
    try:
        doctors = session.query(Doctor).all()
        return {"success": True, "data": [{"id": d.id, "name": d.name, "specialty": d.specialty, "email": d.email, "is_active": d.is_active} for d in doctors]}
    except Exception as e:
        return {"success": False, "error": str(e)}


# --- ADMIN DISEASE DATASET MANAGEMENT & MLOPS RETRAINING ENDPOINTS ---

import sys

class DiseaseAdminRequest(BaseModel):
    name: str
    category: str
    symptoms: str
    severity: int
    diet_to_eat: str
    diet_to_avoid: str
    medicine_name: str
    safe_tip: str
    dangerous_myth: str
    base_dosage_mg: int

@app.get("/api/admin/diseases")
async def get_admin_diseases(search: Optional[str] = None, category: Optional[str] = None, severity: Optional[int] = None):
    try:
        query = session.query(Disease)
        if search:
            query = query.filter((Disease.name.ilike(f"%{search}%")) | (Disease.symptoms.ilike(f"%{search}%")))
        if category:
            query = query.filter(Disease.category == category)
        if severity:
            query = query.filter(Disease.severity == severity)
            
        diseases = query.order_by(Disease.name.asc()).all()
        return {
            "success": True,
            "data": [
                {
                    "id": d.id,
                    "name": d.name,
                    "category": d.category,
                    "symptoms": d.symptoms,
                    "severity": d.severity,
                    "diet_to_eat": d.diet_to_eat,
                    "diet_to_avoid": d.diet_to_avoid,
                    "medicine_name": d.medicine_name,
                    "safe_tip": d.safe_tip,
                    "dangerous_myth": d.dangerous_myth,
                    "base_dosage_mg": d.base_dosage_mg
                }
                for d in diseases
            ]
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/admin/diseases/{id}")
async def get_admin_disease_detail(id: int):
    try:
        disease = session.query(Disease).filter(Disease.id == id).first()
        if not disease:
            return {"success": False, "error": "Disease not found"}
        return {
            "success": True,
            "data": {
                "id": disease.id,
                "name": disease.name,
                "category": disease.category,
                "symptoms": disease.symptoms,
                "severity": disease.severity,
                "diet_to_eat": disease.diet_to_eat,
                "diet_to_avoid": disease.diet_to_avoid,
                "medicine_name": disease.medicine_name,
                "safe_tip": disease.safe_tip,
                "dangerous_myth": disease.dangerous_myth,
                "base_dosage_mg": disease.base_dosage_mg
            }
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/admin/diseases")
async def add_admin_disease(request: DiseaseAdminRequest):
    try:
        csv_path = "dataset_management/fedmedflow_accurate_dataset.csv"
        is_valid, errors = validate_disease_data(request.dict(), csv_path, db_session=session, is_edit=False)
        if not is_valid:
            return {"success": False, "error": " | ".join(errors)}
            
        new_disease = Disease(
            name=request.name,
            category=request.category,
            symptoms=request.symptoms,
            severity=request.severity,
            diet_to_eat=request.diet_to_eat,
            diet_to_avoid=request.diet_to_avoid,
            medicine_name=request.medicine_name,
            safe_tip=request.safe_tip,
            dangerous_myth=request.dangerous_myth,
            base_dosage_mg=request.base_dosage_mg
        )
        session.add(new_disease)
        session.commit()
        session.refresh(new_disease)
        
        # Update CSV dataset
        append_disease_to_csv(request.dict())
        
        # Log history
        history_entry = AdminUpdateHistory(
            action="ADD",
            disease_name=request.name,
            details=f"Added disease '{request.name}' with symptoms: {request.symptoms[:50]}..."
        )
        session.add(history_entry)
        session.commit()
        
        return {"success": True, "disease_id": new_disease.id}
    except Exception as e:
        session.rollback()
        return {"success": False, "error": str(e)}

@app.put("/api/admin/diseases/{id}")
async def edit_admin_disease(id: int, request: DiseaseAdminRequest):
    try:
        disease = session.query(Disease).filter(Disease.id == id).first()
        if not disease:
            return {"success": False, "error": "Disease not found"}
            
        old_name = disease.name
        csv_path = "dataset_management/fedmedflow_accurate_dataset.csv"
        is_valid, errors = validate_disease_data(request.dict(), csv_path, db_session=session, is_edit=True, original_name=old_name)
        if not is_valid:
            return {"success": False, "error": " | ".join(errors)}
            
        # Update DB fields
        disease.name = request.name
        disease.category = request.category
        disease.symptoms = request.symptoms
        disease.severity = request.severity
        disease.diet_to_eat = request.diet_to_eat
        disease.diet_to_avoid = request.diet_to_avoid
        disease.medicine_name = request.medicine_name
        disease.safe_tip = request.safe_tip
        disease.dangerous_myth = request.dangerous_myth
        disease.base_dosage_mg = request.base_dosage_mg
        session.commit()
        
        # Update CSV
        update_disease_in_csv(old_name, request.dict())
        
        # Log history
        history_entry = AdminUpdateHistory(
            action="EDIT",
            disease_name=request.name,
            details=f"Edited disease '{old_name}' (renamed to '{request.name}' if changed)."
        )
        session.add(history_entry)
        session.commit()
        
        return {"success": True, "disease_id": disease.id}
    except Exception as e:
        session.rollback()
        return {"success": False, "error": str(e)}

@app.delete("/api/admin/diseases/{id}")
async def delete_admin_disease(id: int):
    try:
        disease = session.query(Disease).filter(Disease.id == id).first()
        if not disease:
            return {"success": False, "error": "Disease not found"}
            
        disease_name = disease.name
        session.delete(disease)
        session.commit()
        
        # Delete from CSV
        delete_disease_from_csv(disease_name)
        
        # Log history
        history_entry = AdminUpdateHistory(
            action="DELETE",
            disease_name=disease_name,
            details=f"Deleted disease '{disease_name}' from DB and CSV."
        )
        session.add(history_entry)
        session.commit()
        
        return {"success": True, "message": f"Deleted {disease_name}"}
    except Exception as e:
        session.rollback()
        return {"success": False, "error": str(e)}

@app.get("/api/admin/diseases/history")
async def get_disease_update_history():
    try:
        logs = session.query(AdminUpdateHistory).order_by(AdminUpdateHistory.timestamp.desc()).all()
        return {
            "success": True,
            "data": [
                {
                    "id": log.id,
                    "action": log.action,
                    "disease_name": log.disease_name,
                    "details": log.details,
                    "timestamp": log.timestamp.strftime("%Y-%m-%d %H:%M:%S")
                }
                for log in logs
            ]
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/admin/retrain/status")
async def get_retrain_status():
    try:
        version = "1.0.0"
        build = 0
        meta_path = Path("models/version_metadata.json")
        if meta_path.exists():
            try:
                with meta_path.open("r", encoding='utf-8') as f:
                    meta_data = json.load(f)
                    version = meta_data.get("current_version", "1.0.0")
                    build = meta_data.get("build_number", 0)
            except Exception:
                pass

        accuracy = 0.95
        f1_score = 0.95
        report_dir = Path("logs/accuracy_reports")
        if report_dir.exists():
            reports = sorted(report_dir.glob("*.json"), key=os.path.getmtime)
            if reports:
                try:
                    with reports[-1].open("r", encoding='utf-8') as f:
                        metrics = json.load(f)
                        accuracy = metrics.get("accuracy", 0.95)
                        f1_score = metrics.get("f1_score", 0.95)
                except Exception:
                    pass

        health_score = 100
        dataset_path = Path("dataset/fedmedflow_accurate_dataset.csv")
        if not dataset_path.exists():
            dataset_path = Path("dataset_management/fedmedflow_accurate_dataset.csv")
        
        if dataset_path.exists():
            try:
                import pandas as pd
                df = pd.read_csv(dataset_path)
                missing = int(df.isna().sum().sum())
                duplicates = int(df.duplicated(subset=['name']).sum())
                health_score = max(30, 100 - (missing * 5) - (duplicates * 10))
            except Exception:
                pass

        return {
            "success": True,
            "version": version,
            "build": build,
            "accuracy": accuracy,
            "f1_score": f1_score,
            "health_score": health_score
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/admin/retrain/validate")
async def trigger_retrain_validate():
    try:
        script_path = "scripts/validate_dataset.py"
        res = subprocess.run([sys.executable, script_path], capture_output=True, text=True, encoding='utf-8')
        return {
            "success": res.returncode == 0,
            "stdout": res.stdout,
            "stderr": res.stderr
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/admin/retrain/run")
async def trigger_retrain_run():
    try:
        script_path = "scripts/retrain_model.py"
        res = subprocess.run([sys.executable, script_path], capture_output=True, text=True, encoding='utf-8')

        # Trigger dynamic reload of ML model inside AI Inference Service
        if res.returncode == 0:
            try:
                requests.post(f"{AI_SERVICE_URL}/reload", timeout=5.0)
                print("[OK] Dynamic ML model reload triggered to AI Service.")
            except Exception as e:
                print(f"[WARN] Failed to notify AI service to reload: {e}")

        # ---------------------------------------------------------------
        # AUTO GIT PUSH — triggers GitHub CI/CD without manual steps
        # Only runs if training succeeded
        # ---------------------------------------------------------------
        git_push_log = ""
        git_push_success = False

        if res.returncode == 0:
            try:
                # Stage the updated model, metadata, and CSV
                git_add = subprocess.run(
                    ["git", "add",
                     "health_model_v2.pkl",
                     "models/latest/health_model_v2.pkl",
                     "models/version_metadata.json",
                     "logs/training_logs/",
                     "fedmedflow_accurate_dataset.csv"],
                    capture_output=True, text=True, encoding='utf-8'
                )

                # Check if there's actually anything staged
                git_status = subprocess.run(
                    ["git", "diff", "--staged", "--quiet"],
                    capture_output=True
                )

                if git_status.returncode != 0:
                    # There are staged changes — commit and push
                    git_commit = subprocess.run(
                        ["git", "commit", "-m",
                         "Auto-MLOps: Admin retrained model locally — triggering CI/CD [skip validation]"],
                        capture_output=True, text=True, encoding='utf-8'
                    )

                    git_push = subprocess.run(
                        ["git", "push", "origin", "HEAD"],
                        capture_output=True, text=True, encoding='utf-8'
                    )

                    if git_push.returncode == 0:
                        git_push_success = True
                        git_push_log = "[OK] Pushed to GitHub. CI/CD pipeline will now start automatically."
                    else:
                        git_push_log = f"[WARN] Git push failed: {git_push.stderr.strip()}"
                else:
                    git_push_success = True
                    git_push_log = "[INFO] No model file changes detected — nothing to push."

            except Exception as git_err:
                git_push_log = f"[WARN] Git auto-push skipped: {git_err}"

        return {
            "success": res.returncode == 0,
            "stdout": res.stdout,
            "stderr": res.stderr,
            "git_push": git_push_success,
            "git_push_log": git_push_log
        }
    except Exception as e:
        return {"success": False, "error": str(e)}



@app.post("/api/admin/retrain/test")
async def trigger_retrain_test():
    try:
        script_path = "scripts/test_accuracy.py"
        res = subprocess.run([sys.executable, script_path], capture_output=True, text=True, encoding='utf-8')
        return {
            "success": res.returncode == 0,
            "stdout": res.stdout,
            "stderr": res.stderr
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


# --- GITHUB CI/CD TRIGGER ENDPOINTS ---

import urllib.request
import urllib.error

@app.post("/api/admin/retrain/github")
async def trigger_github_pipeline():
    """
    Triggers the full CI/CD retraining pipeline on GitHub Actions
    via the workflow_dispatch event on sync-model.yml.
    Requires GITHUB_TOKEN and GITHUB_REPO in .env
    """
    github_token = os.getenv("GITHUB_TOKEN", "")
    github_repo = os.getenv("GITHUB_REPO", "")  # e.g. "Stalin1239/AI-medicine-recommendation-system"
    branch = os.getenv("GITHUB_BRANCH", "main")

    if not github_token:
        return {
            "success": False,
            "error": "GITHUB_TOKEN not set in .env. Add it to trigger CI/CD from the admin panel."
        }
    if not github_repo:
        return {
            "success": False,
            "error": "GITHUB_REPO not set in .env. Example: Stalin1239/AI-medicine-recommendation-system"
        }

    # Trigger the master sync workflow (Step 4 — it runs validate → retrain → accuracy → push)
    workflow_file = "sync-model.yml"
    url = f"https://api.github.com/repos/{github_repo}/actions/workflows/{workflow_file}/dispatches"

    payload = json.dumps({"ref": branch}).encode("utf-8")
    headers = {
        "Authorization": f"Bearer {github_token}",
        "Accept": "application/vnd.github+json",
        "Content-Type": "application/json",
        "X-GitHub-Api-Version": "2022-11-28"
    }

    try:
        req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
        with urllib.request.urlopen(req) as response:
            # GitHub returns 204 No Content on success
            return {
                "success": True,
                "message": f"GitHub Actions pipeline triggered successfully on branch '{branch}'.",
                "workflow": workflow_file,
                "repo": github_repo
            }
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        return {
            "success": False,
            "error": f"GitHub API error {e.code}: {body}"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.get("/api/admin/retrain/github/status")
async def get_github_pipeline_status():
    """
    Returns the last 5 workflow runs for sync-model.yml from GitHub API.
    """
    github_token = os.getenv("GITHUB_TOKEN", "")
    github_repo = os.getenv("GITHUB_REPO", "")

    if not github_token or not github_repo:
        return {
            "success": False,
            "configured": False,
            "error": "GITHUB_TOKEN and GITHUB_REPO must be set in .env"
        }

    workflow_file = "sync-model.yml"
    url = f"https://api.github.com/repos/{github_repo}/actions/workflows/{workflow_file}/runs?per_page=5"
    headers = {
        "Authorization": f"Bearer {github_token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }

    try:
        req = urllib.request.Request(url, headers=headers, method="GET")
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode("utf-8"))
            runs = data.get("workflow_runs", [])
            return {
                "success": True,
                "configured": True,
                "repo": github_repo,
                "runs": [
                    {
                        "id": r["id"],
                        "status": r["status"],           # queued / in_progress / completed
                        "conclusion": r.get("conclusion"),  # success / failure / None
                        "created_at": r["created_at"],
                        "updated_at": r["updated_at"],
                        "html_url": r["html_url"]
                    }
                    for r in runs
                ]
            }
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        return {"success": False, "configured": True, "error": f"GitHub API {e.code}: {body}"}
    except Exception as e:
        return {"success": False, "configured": True, "error": str(e)}


# Clean transaction reset and uvicorn auto-reload trigger.

