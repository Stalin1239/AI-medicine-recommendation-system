# 🏥 Doctor Routing System - Implementation Guide

## Overview

The Doctor Routing System is a professional healthcare platform that automatically routes patient consultation requests to appropriate specialists based on AI-predicted diseases/conditions.

## Key Features

### ✅ Implemented Features

1. **Automatic Specialty Detection**
   - AI predicts disease based on symptoms
   - System automatically determines required specialty (Dermatologist, Cardiologist, etc.)
   - Falls back to General Practitioner if no match found

2. **Smart Doctor Matching**
   - Displays available doctors sorted by:
     - Online/offline status (online first)
     - Estimated wait time
     - Queue size
     - Patient ratings
   - Shows alternative specialists if primary specialty unavailable

3. **Professional CTA Button**
   - "Request Medical Review" button appears after AI prediction
   - One-click integration from symptom analysis to doctor selection
   - Smooth navigation between patient dashboard and consultation booking

4. **Doctor Selection UI**
   - Modern healthcare card design with:
     - Doctor avatar and details
     - Real-time availability status
     - Experience and qualifications
     - Wait time estimates
     - Patient ratings (1-5 stars)
   - Responsive design works on mobile/tablet/desktop

5. **Comprehensive Consultation Form**
   - Symptom details
   - Severity level (Mild, Moderate, Severe, Critical)
   - Priority level (Low, Normal, High, Urgent)
   - Additional notes for doctor

6. **Database Models**
   - `Doctor` - Specialist information
   - `ConsultationRequest` - Active consultation requests
   - `ConsultationHistory` - Completed consultations with feedback
   - `DoctorAvailability` - Real-time doctor status

7. **Real-Time Status Updates**
   - Server-Sent Events (SSE) for real-time status streaming
   - Fallback to polling for SQLite compatibility
   - Status transitions: pending → accepted → in_progress → completed
   - Automatic notifications to patient at each status change

8. **Complete API Endpoints**
   - Doctor discovery and matching
   - Consultation request creation and management
   - Status updates and transitions
   - Consultation completion and feedback
   - History tracking and analytics

## System Architecture

### Database Schema

```
Users
├── Consultations (many-to-many)
└── ConsultationHistory

Doctors
├── Specialties
├── Availability
└── Ratings (from ConsultationHistory)

ConsultationRequest
├── patient_id (FK)
├── doctor_id (FK)
├── triage_history_id (FK)
├── status (pending/accepted/in_progress/completed)
├── priority
└── timestamps

ConsultationHistory
├── consultation_request_id (FK)
├── patient_id (FK)
├── doctor_id (FK)
├── diagnosis
├── prescription
├── patient_rating
└── feedback
```

### API Flow

```
Patient Dashboard (AI Prediction)
    ↓
"Request Medical Review" CTA Button
    ↓
GET /api/doctors/available?disease_name=X
    ↓
Display Available Doctors (sorted by availability)
    ↓
POST /api/consultations/request (Doctor selected)
    ↓
Consultation Request Created
    ↓
Real-time Status Updates via SSE/Polling
    ↓
PATCH /api/consultations/{id}/status (Doctor accepts/starts)
    ↓
POST /api/consultations/{id}/complete (Doctor completes)
    ↓
POST /api/consultations/{id}/rate (Patient rates)
    ↓
Consultation History Saved
```

## How to Use

### 1. Patient Workflow

**Step 1: Symptom Analysis**
- Patient enters symptoms in dashboard
- AI predicts disease and specialty needed
- "Request Medical Review" CTA button appears

**Step 2: Doctor Selection**
- Click "Request Medical Review"
- Navigate to consultation-request page
- Browse available specialists
- Select preferred doctor

**Step 3: Consultation Request**
- Fill in detailed symptoms and severity
- Choose priority level (if urgent)
- Add any additional notes
- Submit consultation request

**Step 4: Real-Time Tracking**
- See real-time status updates:
  - ⏳ Waiting for doctor acceptance
  - ✓ Doctor accepted
  - 📞 Consultation in progress
  - ✅ Consultation completed
- Receive notifications at each stage

**Step 5: Feedback**
- Rate consultation (1-5 stars)
- Add feedback for doctor
- View prescription and recommendations

### 2. Default Doctors (Pre-seeded)

The system comes with 10 default doctors across specialties:

**Dermatologists:**
- Dr. Sarah Johnson (City Medical Center, 12 yrs)
- Dr. Michael Chen (Central Hospital, 8 yrs)

**Cardiologists:**
- Dr. James Williams (Heart Care Institute, 15 yrs)
- Dr. Priya Patel (City Medical Center, 10 yrs)

**Psychiatrists:**
- Dr. Robert Martinez (Mental Health Center, 14 yrs)
- Dr. Lisa Anderson (Wellness Hospital, 9 yrs)

**Neurologist:**
- Dr. David Kumar (Brain & Spine Center, 11 yrs)

**Pulmonologist:**
- Dr. Emily Thompson (Lung Care Hospital, 10 yrs)

**Gastroenterologist:**
- Dr. Ahmed Hassan (Digestive Health Center, 12 yrs)

**General Practitioner:**
- Dr. Susan Lee (Primary Care Clinic, 13 yrs)

### 3. Adding New Doctors

Edit `database.py` and add to `seed_default_doctors()`:

```python
{
    "name": "Dr. Your Name",
    "email": "doctor@medclinic.com",
    "specialty": "Specialty Name",
    "qualifications": "MD, Specialization",
    "experience_years": 10,
    "hospital_affiliation": "Hospital Name"
}
```

Then reset the database to seed new doctors.

### 4. Specialty Mapping

Edit `doctor_routing_service.py` `SPECIALTY_MAPPING` to add disease → specialty mappings:

```python
SPECIALTY_MAPPING = {
    "diabetes": "Endocrinologist",
    "arthritis": "Rheumatologist",
    # Add more mappings...
}
```

## API Reference

### Get Available Doctors

```bash
GET /api/doctors/available?disease_name=Skin%20Disease
```

**Response:**
```json
{
  "success": true,
  "disease_name": "Skin Disease",
  "predicted_specialty": "Dermatologist",
  "available_doctors": [
    {
      "id": 1,
      "name": "Dr. Sarah Johnson",
      "specialty": "Dermatologist",
      "experience_years": 12,
      "hospital_affiliation": "City Medical Center",
      "is_online": true,
      "current_queue_size": 2,
      "estimated_wait_minutes": 15,
      "rating": 4.8
    }
  ],
  "alternative_specialists": []
}
```

### Request Consultation

```bash
POST /api/consultations/request
Content-Type: application/json

{
  "patient_id": 1,
  "doctor_id": 1,
  "disease_name": "Skin Disease",
  "symptoms": "Red rash on arms and legs",
  "severity": 2,
  "priority": "normal",
  "notes": "Started 3 days ago",
  "triage_history_id": 123
}
```

**Response:**
```json
{
  "success": true,
  "consultation_id": 5,
  "doctor_name": "Dr. Sarah Johnson",
  "status": "pending",
  "estimated_response_minutes": 15
}
```

### Update Consultation Status

```bash
PATCH /api/consultations/5/status?status=accepted
```

**Status Flow:**
- `pending` → `accepted` (doctor accepts)
- `accepted` → `in_progress` (doctor starts)
- `in_progress` → `completed` (doctor finishes)
- Any status → `cancelled` (cancel request)

### Complete Consultation

```bash
POST /api/consultations/5/complete
Content-Type: application/json

{
  "diagnosis": "Acute Dermatitis",
  "prescription": "Hydrocortisone 1% cream, twice daily",
  "recommendations": "Avoid allergens, keep skin moisturized",
  "duration_minutes": 20
}
```

### Rate Consultation

```bash
POST /api/consultations/5/rate
Content-Type: application/json

{
  "rating": 5,
  "feedback": "Dr. Johnson was very helpful and professional!"
}
```

### Get Consultation History

```bash
GET /api/consultations/history/1
```

### Real-Time Status Stream

```bash
GET /api/consultations/5/stream
```

Uses Server-Sent Events. Subscribe in JavaScript:
```javascript
const source = new EventSource('/api/consultations/5/stream');
source.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Status:', data.status);
};
```

## File Structure

```
mediops01/
├── main.py                           # FastAPI app with doctor routing endpoints
├── database.py                       # SQLAlchemy models for doctors/consultations
├── doctor_routing_service.py         # Business logic for routing
├── static/
│   ├── dashboard.html               # Updated with CTA button
│   ├── consultation-request.html    # Doctor selection & booking UI
│   └── ...
└── health_app.db                    # SQLite database
```

## UI/UX Features

### Modern Healthcare Design
- Gradient backgrounds with medical theme
- Smooth animations and transitions
- Professional color scheme (blues, purples)
- Accessibility-compliant design

### Responsive Layout
- Mobile-first approach
- Adapts to tablet/desktop screens
- Touch-friendly buttons and forms
- Optimized for slow networks

### Doctor Cards
- Doctor avatar with initials
- Name, specialty, and qualifications
- Experience years and hospital affiliation
- Online/offline status with animated indicator
- Patient rating with star display
- Current queue size and wait time
- "Select Doctor" button with visual feedback

### Status Indicators
- Online: Green dot with pulse animation
- Offline: Red dot
- Queue status shown in real-time
- Estimated wait times in minutes

### CTA Button Integration
- Appears immediately after AI prediction
- Professional button text ("Request Medical Review")
- Gradient styling to draw attention
- One-click navigation to doctor selection

## Integrations

### With Existing Systems

**AI Prediction:**
- Runs in existing `/triage` endpoint
- CTA button added to results display
- Data automatically passed to consultation system

**Notifications:**
- Doctor notification when request received
- Patient notification when status changes
- Uses existing Notification model

**History:**
- Consultation history saved in database
- Integrates with patient health history
- Enables analytics and follow-up

### External Services (Future)

- SMS/Email notifications
- Video consultation integration
- Payment processing
- Insurance verification

## Performance Considerations

### Database Optimization
- Indexes on frequently queried fields
- Efficient query patterns
- Connection pooling ready

### Real-Time Updates
- SSE (Server-Sent Events) for browsers that support it
- Fallback to polling (10-second intervals) for compatibility
- Automatic cleanup after 30 minutes

### Scalability
- Stateless API design
- Ready for horizontal scaling
- Can upgrade to PostgreSQL for production

## Security

### Authentication
- Uses existing user authentication
- Patient can only see own consultations
- Doctors see only assigned consultations

### Data Privacy
- Patient data encrypted in transit (HTTPS)
- Sensitive fields stored securely
- HIPAA-ready structure

### Input Validation
- All inputs sanitized
- Type checking on all endpoints
- Error handling and logging

## Testing the System

### Manual Testing Steps

1. **Start the server:**
   ```bash
   python main.py
   ```

2. **Login as patient:**
   - Navigate to http://localhost:8000/login
   - Use: test@example.com / password123

3. **Run symptom analysis:**
   - Go to Health Check tab
   - Enter symptoms (e.g., "red rash on arms")
   - Submit analysis

4. **Click CTA button:**
   - "Request Medical Review" button appears
   - Click to navigate to doctor selection

5. **Select doctor:**
   - Browse available specialists
   - Click "Select Doctor"

6. **Submit consultation:**
   - Fill form with details
   - Click "Request Consultation"

7. **View status:**
   - See real-time updates
   - Status changes as doctor responds

### API Testing with cURL

```bash
# Get available doctors
curl "http://localhost:8000/api/doctors/available?disease_name=Skin%20Disease"

# Request consultation
curl -X POST http://localhost:8000/api/consultations/request \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": 1,
    "doctor_id": 1,
    "disease_name": "Skin Disease",
    "symptoms": "Red rash",
    "severity": 2,
    "priority": "normal"
  }'

# Update status
curl -X PATCH "http://localhost:8000/api/consultations/1/status?status=accepted"
```

## Troubleshooting

### No Doctors Showing

1. Check that `seed_default_doctors()` was called
2. Verify database file exists at `health_app.db`
3. Check doctor specialty matches disease name

### Real-Time Updates Not Working

1. Check browser supports EventSource (SSE)
2. Verify server is running on same domain
3. Check network tab in DevTools for errors
4. Fallback to polling should still work

### Consultation Request Failing

1. Verify patient and doctor IDs are valid
2. Check all required fields are provided
3. Review server logs for error details
4. Ensure database hasn't run out of space

## Future Enhancements

- [ ] Video consultation integration (Zoom/Jitsi)
- [ ] Prescription management system
- [ ] Patient follow-up reminders
- [ ] Doctor performance analytics
- [ ] Insurance claim automation
- [ ] Multi-language support
- [ ] AI-powered doctor recommendation
- [ ] Wait time prediction ML model
- [ ] Appointment scheduling
- [ ] Telemedicine integration

## License

This system is part of the MediOps healthcare platform.

## Support

For issues or questions, check:
1. Server logs in terminal
2. Browser console (DevTools)
3. Database integrity with `sqlite3 health_app.db`
4. API endpoints documentation above
