import sys
import os
import json
import shutil
import pickle
from datetime import datetime

# Reconfigure stdout/stderr to support UTF-8 on Windows terminals
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

def run_sync():
    print("=========================================")
    print("🔄 [MLOps] Running Latest Model Synchronization...")
    print("=========================================")
    
    source_model = "models/latest/health_model_v2.pkl"
    active_model = "health_model_v2.pkl"
    backup_dir = "models/backups"
    log_dir = "logs/synchronization_logs"
    
    os.makedirs(backup_dir, exist_ok=True)
    os.makedirs(log_dir, exist_ok=True)
    
    log_file = os.path.join(log_dir, "sync.log")
    
    # 1. Verify source model exists
    if not os.path.exists(source_model):
        print(f"[ERROR] Source model not found at {source_model}. Sync cancelled.")
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now().isoformat()}] [ERROR] Source model not found at {source_model}. Sync cancelled.\n")
        sys.exit(1)
        
    # 2. Verify model integrity (unpickle check)
    try:
        with open(source_model, "rb") as f:
            pickle.load(f)
        print("[OK] Source model integrity verified successfully.")
    except Exception as e:
        print(f"[ERROR] Source model is corrupted or invalid: {e}. Sync cancelled.")
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now().isoformat()}] [ERROR] Source model is corrupted: {e}. Sync cancelled.\n")
        sys.exit(1)
        
    # 3. Create backup of active model if exists
    if os.path.exists(active_model):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = os.path.join(backup_dir, f"health_model_v2_backup_{timestamp}.pkl")
        try:
            shutil.copy2(active_model, backup_path)
            print(f"[OK] Created backup of current active model at: {backup_path}")
        except Exception as e:
            print(f"[WARN] Failed to create active model backup: {e}. Continuing sync...")
            
    # 4. Perform synchronization (copy to active path)
    try:
        shutil.copy2(source_model, active_model)
        print(f"[OK] Synchronized latest model to active path: {active_model}")
        
        # 5. Update synchronization status in metadata JSON
        metadata_path = "models/version_metadata.json"
        if os.path.exists(metadata_path):
            try:
                with open(metadata_path, 'r') as f:
                    meta = json.load(f)
                meta["sync_status"] = "synchronized"
                meta["last_sync_time"] = datetime.now().isoformat()
                with open(metadata_path, 'w') as f:
                    json.dump(meta, f, indent=4)
                print("[OK] Version metadata status successfully updated to 'synchronized'.")
            except Exception as e:
                print(f"[WARN] Failed to update version metadata: {e}")
                
        # 6. Log successful synchronization
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now().isoformat()}] [SUCCESS] Model synced. Version metadata updated.\n")
            
        print("🎉 Model Synchronization completed successfully!")
        sys.exit(0)
    except Exception as e:
        print(f"[ERROR] Synchronization failed: {e}")
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now().isoformat()}] [ERROR] Sync failed: {e}\n")
        sys.exit(1)

if __name__ == "__main__":
    run_sync()
