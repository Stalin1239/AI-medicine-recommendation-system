import sys
import os
import json
import pickle
import shutil
from datetime import datetime
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline

# Reconfigure stdout/stderr to support UTF-8 on Windows terminals
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
if hasattr(sys.stderr, 'reconfigure'):
    try:
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

def get_next_version(metadata_path):
    default_meta = {
        "current_version": "1.0.0",
        "build_number": 0,
        "last_trained": "",
        "accuracy": 0.95,
        "fallback_active": False,
        "sync_status": "synchronized"
    }
    
    if not os.path.exists(metadata_path):
        os.makedirs(os.path.dirname(metadata_path), exist_ok=True)
        with open(metadata_path, 'w') as f:
            json.dump(default_meta, f, indent=4)
        return "1.0.0", 1
        
    try:
        with open(metadata_path, 'r') as f:
            meta = json.load(f)
    except Exception:
        meta = default_meta
        
    build = meta.get("build_number", 0) + 1
    version_parts = meta.get("current_version", "1.0.0").split('.')
    # Increment patch version
    patch = int(version_parts[2]) + 1
    new_version = f"{version_parts[0]}.{version_parts[1]}.{patch}"
    
    # Save back
    meta["current_version"] = new_version
    meta["build_number"] = build
    meta["last_trained"] = datetime.now().isoformat()
    meta["sync_status"] = "pending" # pending push back to repo
    
    with open(metadata_path, 'w') as f:
        json.dump(meta, f, indent=4)
        
    return new_version, build

def train_model():
    print("=========================================")
    print("🚀 [MLOps] Beginning AI Model Retraining Pipeline...")
    print("=========================================")
    
    paths_to_try = [
        "/app/dataset/fedmedflow_accurate_dataset.csv",
        os.path.abspath(os.path.join(os.path.dirname(__file__), "../dataset/fedmedflow_accurate_dataset.csv")),
        os.path.abspath(os.path.join(os.path.dirname(__file__), "../dataset_management/fedmedflow_accurate_dataset.csv")),
        "dataset_management/fedmedflow_accurate_dataset.csv",
        "fedmedflow_accurate_dataset.csv"
    ]
    
    csv_path = None
    for p in paths_to_try:
        if os.path.exists(p):
            csv_path = p
            break
            
    if not csv_path:
        print("[ERROR] Dataset file not found.")
        sys.exit(1)
        
    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        print(f"[ERROR] Could not read CSV file: {e}")
        sys.exit(1)
        
    if len(df) < 5:
        print("[ERROR] Not enough data rows in CSV to train model.")
        sys.exit(1)
        
    X = df['symptoms'].astype(str).str.lower()
    y = df['name']
    
    print(f"[INFO] Rows parsed: {len(df)} | Unique Diseases: {len(y.unique())}")
    
    # Train classification model pipeline
    pipeline = Pipeline([
        ('tfidf', TfidfVectorizer(analyzer='word', ngram_range=(1, 2))),
        ('clf', RandomForestClassifier(n_estimators=100, random_state=42))
    ])
    
    try:
        pipeline.fit(X, y)
        print("[OK] Model successfully trained!")
        
        # Versioning metadata
        metadata_path = "models/version_metadata.json"
        version, build = get_next_version(metadata_path)
        print(f"[INFO] Model Version assigned: v{version} (Build #{build})")
        
        # Targets
        version_dir = f"models/versions/v{version}"
        latest_dir = "models/latest"
        global_models_dir = "models/latest"
        
        os.makedirs(version_dir, exist_ok=True)
        os.makedirs(latest_dir, exist_ok=True)
        
        v_model_path = os.path.join(version_dir, "health_model_v2.pkl")
        l_model_path = os.path.join(latest_dir, "health_model_v2.pkl")
        fallback_root_path = "health_model_v2.pkl"
        
        # Save to version folder
        with open(v_model_path, 'wb') as f:
            pickle.dump(pipeline, f)
            
        # Copy to latest mounts
        shutil.copy2(v_model_path, l_model_path)
        shutil.copy2(v_model_path, fallback_root_path)
        
        print(f"[OK] Saved versioned artifact to: {v_model_path}")
        print(f"[OK] Dynamic active model promoted to: {l_model_path}")
        
        # Log generation
        log_dir = "logs/training_logs"
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, f"train_v{version}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
        
        with open(log_file, 'w', encoding='utf-8') as log:
            log.write("=========================================\n")
            log.write("MediOps MLOps Training Report\n")
            log.write("=========================================\n")
            log.write(f"Timestamp: {datetime.now().isoformat()}\n")
            log.write(f"Model Version: v{version}\n")
            log.write(f"Build Number: #{build}\n")
            log.write(f"Training Rows: {len(df)}\n")
            log.write(f"Classes: {len(y.unique())}\n")
            log.write("Classifier: Random Forest (100 estimators)\n")
            log.write(f"Saved Version File: {v_model_path}\n")
            log.write(f"Saved Latest File: {l_model_path}\n")
            log.write("=========================================\n")
            
        print(f"[OK] Training logs compiled at: {log_file}")
        sys.exit(0)
    except Exception as e:
        print(f"[ERROR] Error training ML model: {e}")
        sys.exit(1)

if __name__ == "__main__":
    train_model()
