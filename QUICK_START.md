# 🚀 Quick Start Guide - Doctor Routing System

## 1. Start the Server

```bash
cd c:\Users\stali\mediops01
.\.venv\Scripts\Activate.ps1
python main.py
```

Server will start on `http://localhost:8000`

## 2. Login to Dashboard

- URL: `http://localhost:8000/dashboard`
- Email: `test@example.com`
- Password: `password123`

## 3. Test the Doctor Routing System

### Step 1: Run Symptom Analysis
1. Go to **Health Check** tab
2. Enter symptoms: `red rash on arms and legs`
3. Age: `25`
4. Weight: `70`
5. Click **Submit**

### Step 2: Click CTA Button
After analysis, you'll see **"Request Medical Review"** button
- Click it to proceed to doctor selection

### Step 3: Select Doctor
- Browse available dermatologists
- Sort by online status, wait time, and rating
- Click **"Select Doctor"** on preferred specialist

### Step 4: Request Consultation
- Fill in symptom details
- Select severity (e.g., "Moderate")
- Choose priority (e.g., "Normal")
- Submit consultation request

### Step 5: Watch Real-Time Updates
- See status change: pending → accepted → in_progress → completed
- Receive notifications at each stage

## 4. API Testing with cURL

### Get Available Doctors
```bash
curl "http://localhost:8000/api/doctors/available?disease_name=Skin%20Disease"
```

**Response includes:**
- List of available doctors
- Online status with animated indicator
- Experience, qualifications, hospital affiliation
- Current queue size & estimated wait time
- Patient ratings

### Request Consultation
```bash
curl -X POST http://localhost:8000/api/consultations/request \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": 1,
    "doctor_id": 1,
    "disease_name": "Skin Disease",
    "symptoms": "Red rash on arms",
    "severity": 2,
    "priority": "normal",
    "notes": "Started 3 days ago"
  }'
```

### Update Consultation Status
```bash
curl -X PATCH "http://localhost:8000/api/consultations/1/status?status=accepted"
```

**Status flow:**
1. `pending` - Initial state
2. `accepted` - Doctor accepts request
3. `in_progress` - Consultation started
4. `completed` - Consultation finished

### Complete Consultation
```bash
curl -X POST http://localhost:8000/api/consultations/1/complete \
  -H "Content-Type: application/json" \
  -d '{
    "diagnosis": "Acute Dermatitis",
    "prescription": "Hydrocortisone 1% cream, twice daily",
    "recommendations": "Avoid allergens, keep skin moisturized",
    "duration_minutes": 20
  }'
```

### Rate Consultation
```bash
curl -X POST http://localhost:8000/api/consultations/1/rate \
  -H "Content-Type: application/json" \
  -d '{
    "rating": 5,
    "feedback": "Excellent service!"
  }'
```

## 5. Pre-Seeded Specialists

### Dermatologists
- **Dr. Sarah Johnson** (12 years) - City Medical Center
- **Dr. Michael Chen** (8 years) - Central Hospital

### Cardiologists
- **Dr. James Williams** (15 years) - Heart Care Institute
- **Dr. Priya Patel** (10 years) - City Medical Center

### Psychiatrists
- **Dr. Robert Martinez** (14 years) - Mental Health Center
- **Dr. Lisa Anderson** (9 years) - Wellness Hospital

### Other Specialties
- **Dr. David Kumar** - Neurologist
- **Dr. Emily Thompson** - Pulmonologist
- **Dr. Ahmed Hassan** - Gastroenterologist
- **Dr. Susan Lee** - General Practitioner

## 6. Key Features

### ✅ Automatic Specialty Detection
- AI predicts disease based on symptoms
- System finds matching specialists automatically
- Falls back to General Practitioner if no match

### ✅ Smart Doctor Matching
- Sorted by online status (online first)
- Then by estimated wait time
- Then by queue size
- Shows patient ratings

### ✅ Real-Time Status Updates
- Server-Sent Events for live updates
- Fallback to polling if SSE unavailable
- Automatic notifications to patient
- Status visible on consultation page

### ✅ Complete Workflow
- Disease prediction → Doctor selection → Consultation request → Real-time tracking → Completion → Rating

### ✅ Professional UI
- Modern healthcare card design
- Responsive on mobile/tablet/desktop
- Smooth animations
- Professional color scheme

## 7. File Structure

```
mediops01/
├── main.py                          # FastAPI with 15 new endpoints
├── database.py                      # 4 new models + seeding
├── doctor_routing_service.py        # Business logic (440 lines)
├── static/
│   ├── consultation-request.html   # Doctor selection UI
│   ├── dashboard.html              # Updated with CTA button
│   └── ...
└── DOCTOR_ROUTING_SYSTEM.md        # Full documentation
└── IMPLEMENTATION_SUMMARY.md       # Implementation details
```

## 8. Database

### Consultation Status Flow
```
pending (initial)
   ↓
accepted (doctor accepts)
   ↓
in_progress (consultation starts)
   ↓
completed (finished with prescription)
```

### Real-Time Updates
- Via SSE: `/api/consultations/{id}/stream`
- Via Polling: Check every 10 seconds
- Automatic cleanup after 30 minutes

## 9. Specialty Mapping

Automatic disease → specialty mapping:

```
Skin issues       → Dermatologist
Heart issues      → Cardiologist
Mental health     → Psychiatrist
Neurological      → Neurologist
Respiratory       → Pulmonologist
Digestive issues  → Gastroenterologist
Other             → General Practitioner
```

## 10. Testing Checklist

- [ ] Server starts without errors
- [ ] Dashboard loads with default user
- [ ] Symptom analysis works
- [ ] "Request Medical Review" button appears
- [ ] Doctor selection page loads
- [ ] Doctor cards show all details
- [ ] Consultation request submits successfully
- [ ] Real-time status updates appear
- [ ] Consultation can be completed
- [ ] Rating system works
- [ ] API endpoints respond correctly

## 11. Troubleshooting

### Server won't start
```bash
# Check Python version (3.7+)
python --version

# Check virtual environment
.\.venv\Scripts\Activate.ps1
pip list | grep fastapi
```

### No doctors showing
- Check database exists: `ls health_app.db`
- Verify doctors were seeded: Check logs for "Seeded X doctors"
- Try refreshing page

### Real-time updates not working
- Check browser console for errors (F12)
- Ensure server is running
- Try clicking back and forth to refresh

### Database errors
- Reset database: `rm health_app.db` (will recreate on startup)
- Check database permissions

## 12. Next Steps

1. **Video Consultation**: Add Zoom/Jitsi integration
2. **Doctor Portal**: Create interface for doctors
3. **Analytics**: View consultation metrics
4. **Insurance**: Add insurance verification
5. **Payments**: Implement payment processing
6. **Multi-language**: Support multiple languages
7. **Mobile App**: Create native mobile app

---

For detailed documentation, see `DOCTOR_ROUTING_SYSTEM.md`

**Status**: ✅ Ready to Use
