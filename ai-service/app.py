import os
import sys
import pickle
import numpy as np
from pathlib import Path
from contextlib import asynccontextmanager
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException

# Secure console output on Windows
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Paths to check for the trained model (Docker volume first, then local folders)
MODEL_PATHS = [
    Path("/models/latest/health_model_v2.pkl"),
    Path("retraining/models/latest/health_model_v2.pkl"),
    Path("health_model_v2.pkl"),
    Path("../retraining/models/latest/health_model_v2.pkl"),
    Path("../health_model_v2.pkl")
]
ml_model = None
active_model_path = None

def load_ml_model():
    global ml_model, active_model_path
    selected_path = None
    for path in MODEL_PATHS:
        if path.exists():
            selected_path = path
            break
            
    if selected_path:
        try:
            with selected_path.open("rb") as f:
                ml_model = pickle.load(f)
            active_model_path = selected_path
            print(f"[OK] AI Inference Engine: ML Model loaded successfully from {selected_path}")
            return True
        except Exception as e:
            print(f"[ERROR] AI Inference Engine: Error reading model file at {selected_path}: {e}")
            ml_model = None
            active_model_path = None
            return False
    else:
        paths_str = ", ".join(str(p) for p in MODEL_PATHS)
        print(f"[WARN] AI Inference Engine: Model file not found in any of: {paths_str}. Prediction service will be offline.")
        ml_model = None
        active_model_path = None
        return False

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load model on boot
    load_ml_model()
    yield

app = FastAPI(title="MediOps AI Inference Service", lifespan=lifespan)

class PredictionRequest(BaseModel):
    symptoms: str

@app.post("/predict")
async def predict_symptoms(request: PredictionRequest):
    global ml_model
    if not ml_model:
        # Try reloading once in case a new model just arrived
        if not load_ml_model():
            raise HTTPException(status_code=503, detail="AI prediction model is offline or has not been trained yet.")

    normalized = request.symptoms.strip().lower()
    try:
        probabilities = ml_model.predict_proba([normalized])[0]
        best_index = int(np.argmax(probabilities))
        disease_name = str(ml_model.classes_[best_index])
        confidence = float(probabilities[best_index])
        
        return {
            "success": True,
            "disease_name": disease_name,
            "confidence": confidence
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")

@app.post("/reload")
async def reload_model():
    success = load_ml_model()
    if success:
        return {"success": True, "message": "ML Model reloaded successfully in memory."}
    else:
        raise HTTPException(status_code=500, detail="Failed to reload model binary from disk.")

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "model_loaded": ml_model is not None,
        "model_path": str(active_model_path) if active_model_path else "None"
    }
