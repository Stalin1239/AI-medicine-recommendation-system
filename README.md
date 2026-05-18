# 🏥 MediOps: Advanced Healthcare Intelligence Platform

MediOps is a state-of-the-art local medical diagnostic, triage routing, and data management platform. It features AI disease prediction models, clinical symptom submissions, dynamic dose calculations, and a fully integrated **Admin Dataset Command Center & MLOps retraining pipeline**.

---

## 🛠️ System Features

1. **Patient Portal**: Clinical symptom submission, automated triage scoring, and dosage suggestion engines.
2. **Physician Queue**: Live patient list, real-time diagnostic workspace, prescription writing, and video consultations.
3. **Futuristic Admin Command Center**:
   - Board-certified doctor registrations.
   - Comprehensive **Disease Dataset Management** (dynamic CSV updates, schema validation, duplicate protection, immediate availability).
   - **Local MLOps Retraining Hub** containing validation tools, TF-IDF + Random Forest model retraining, and split-evaluation accuracy metrics with a real-time console.

---

## 🚀 Quick Start Guide (Local Setup)

### 1. Requirements & Prerequisites
Ensure you have **Python 3.11** installed.

### 2. Install Virtual Environment
```bash
# Create the environment
python -m venv .venv

# Activate on Windows
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Setup Secrets
Copy `.env.example` into a new file named `.env`:
```bash
cp .env.example .env
```
Populate `GROQ_API_KEY` with your active cloud credential to enable LLM diagnostic insights.

### 4. Boot the Platform
```bash
uvicorn main:app --reload
```
Open **`http://localhost:8000/login`** in your browser!

---

## 🎛️ Admin Dataset Command Center

Access the admin dashboard at **`http://localhost:8000/admin`**.

Here, you can:
- **Add / Edit Diseases**: Instantly saved to `health_app.db` and updated in `dataset_management/fedmedflow_accurate_dataset.csv`. Modifying records immediately impacts search capability, doctor mappings, and triage scoring!
- **Dataset Validation**: Automatically checks format structure, severity scale (1-10), symptom commas, and dosage constraints.
- **Model Retraining**: Trains the local Random Forest Pipeline on recent CSV additions and **reloads the model instantly in-memory** without resetting the server.
- **Accuracy Diagnostics**: Measures weighted F1-Scores and Precision metrics.

---

## 📊 Local MLOps Suite (Manual Scripts)

For command-line execution, the scripts are located in `retraining/` and can be run manually:

1. **Verify CSV Schema Integrity**:
   ```bash
   python retraining/validate.py
   ```
2. **Retrain ML Predictor Pipeline**:
   ```bash
   python retraining/train.py
   ```
3. **Run Split-Evaluation Accuracy Metric**:
   ```bash
   python retraining/test_accuracy.py
   ```

---

## 🔒 Git & GitHub Security Best Practices

To protect patient information, database keys, and API secrets, **strictly adhere to the following rules before pushing to GitHub**:

### 🚫 Files That MUST NOT Be Pushed (Ignored in `.gitignore`):
- **`.env`**: Contains raw API secret keys. (Only push `.env.example`).
- **`*.db` / `health_app.db`**: Contains private user logins, registered doctor hashes, and clinical patient triage records.
- **`*.pkl`**: Avoid committing large binary ML models directly into Git to prevent branch bloat. Store model files in a registry/external storage.
- **`reports/` / `exports/`**: Contains PDF patient prescriptions and outbreak spreadsheets.
