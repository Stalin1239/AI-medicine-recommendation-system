import sys
import os
import pandas as pd

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

def run_validation():
    print("=========================================")
    print("🔍 [MLOps] Scanning Dataset Schema Integrity...")
    print("=========================================")
    
    # Locate dataset (support container and local path)
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
        print(f"[ERROR] Dataset file not found in searched paths: {paths_to_try}")
        sys.exit(1)
        
    print(f"[INFO] Active Dataset Found at: {csv_path}")
    
    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        print(f"[ERROR] Could not read CSV file: {e}")
        sys.exit(1)
        
    total_records = len(df)
    print(f"[INFO] Total Records Loaded: {total_records}")
    print("-----------------------------------------")
    
    # 1. Check for duplicate disease names
    duplicate_names = df[df.duplicated(subset=['name'], keep=False)]['name'].unique()
    if len(duplicate_names) > 0:
        print(f"[WARN] Schema Warning: Duplicate diseases detected in name field: {duplicate_names}")
    
    # 2. Field check boundaries
    errors = []
    required_fields = ['name', 'category', 'symptoms', 'severity', 'diet_to_eat', 'diet_to_avoid', 'medicine_name', 'safe_tip', 'dangerous_myth', 'base_dosage_mg']
    
    for idx, row in df.iterrows():
        line_num = idx + 2 # 1-based index + header
        
        # Missing fields
        for field in required_fields:
            val = row.get(field)
            if pd.isna(val) or str(val).strip() == "":
                errors.append(f"Line {line_num}: Missing required field '{field}'")
                
        # Severity constraints
        severity = row.get('severity')
        if not pd.isna(severity):
            try:
                sev_val = int(severity)
                if sev_val < 1 or sev_val > 10:
                    errors.append(f"Line {line_num}: Severity {sev_val} out of bounds (1-10)")
            except ValueError:
                errors.append(f"Line {line_num}: Severity '{severity}' must be an integer")
                
        # Dosage constraints
        dosage = row.get('base_dosage_mg')
        if not pd.isna(dosage):
            try:
                dos_val = int(dosage)
                if dos_val <= 0:
                    errors.append(f"Line {line_num}: Base dosage {dos_val} must be positive")
            except ValueError:
                errors.append(f"Line {line_num}: Base dosage '{dosage}' must be an integer")
                
        # Symptoms format check
        symptoms = row.get('symptoms')
        if not pd.isna(symptoms) and str(symptoms).strip() != "":
            s_list = [s.strip() for s in str(symptoms).split(',')]
            if len(s_list) < 2:
                errors.append(f"Line {line_num}: Symptoms '{symptoms}' should have at least 2 comma-separated values")

    print("[INFO] Validating rows: OK")
    print("-----------------------------------------")
    
    # Write execution log
    log_dir = "logs/validation_logs"
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "validation.log")
    
    with open(log_file, "w", encoding="utf-8") as f:
        f.write("Dataset Validation Log\n")
        f.write(f"Total rows scanned: {total_records}\n")
        f.write(f"Duplicates: {list(duplicate_names)}\n")
        if errors:
            f.write(f"Status: FAILED with {len(errors)} errors:\n")
            for e in errors:
                f.write(f" - {e}\n")
        else:
            f.write("Status: SUCCESS\n")

    if len(errors) > 0:
        print(f"[ERROR] Dataset Validation FAILED with {len(errors)} errors:")
        for err in errors[:10]: # print first 10
            print(f"  - {err}")
        if len(errors) > 10:
            print(f"  ... and {len(errors) - 10} more errors.")
        sys.exit(1)
    else:
        print("[OK] Dataset Validation SUCCESSFUL! All records conform to production MLOps schema.")
        sys.exit(0)

if __name__ == "__main__":
    run_validation()
