import os
import glob
import re

STATIC_DIR = "c:/Users/stali/mediops01/static"

# Replace HealthOS with MediOps
def replace_branding(content):
    content = content.replace("HealthOS", "MediOps")
    return content

# Regex replacements for Cyberpunk styles
regex_replacements = [
    # Replace the light gradient back to a deep dark neon gradient
    (r"background: linear-gradient\(135deg, #f8fafc 0%, #e2e8f0 50%, #f1f5f9 100%\);", 
     r"background: linear-gradient(135deg, #050505 0%, #0a0a0a 25%, #051020 50%, #0a0515 75%, #050505 100%);"),
    (r"background: linear-gradient\(135deg, #f8fafc 0%, #f1f5f9 50%, #e2e8f0 100%\);", 
     r"background: linear-gradient(135deg, #050505 0%, #0a0a0a 25%, #051020 50%, #0a0515 75%, #050505 100%);"),

    # Auth Box glassmorphism (dark with glowing neon border)
    (r"background: rgba\(255, 255, 255, 0\.85\);\s*backdrop-filter: blur\(20px\);\s*border: 1px solid rgba\(0, 0, 0, 0\.05\);", 
     r"background: rgba(10, 10, 10, 0.8);\n            backdrop-filter: blur(15px);\n            border: 1px solid rgba(0, 240, 255, 0.4);"),
    (r"background: rgba\(255, 255, 255, 0\.9\);\s*backdrop-filter: blur\(15px\);\s*border: 1px solid rgba\(0, 0, 0, 0\.05\);", 
     r"background: rgba(10, 10, 10, 0.8);\n            backdrop-filter: blur(15px);\n            border: 1px solid rgba(0, 240, 255, 0.4);"),

    # Text Colors in auth pages
    (r"color: #0f172a;", r"color: #ffffff; text-shadow: 0 0 5px rgba(0, 240, 255, 0.3);"),
    (r"color: #334155;", r"color: #00f0ff;"),
    (r"color: #475569;", r"color: #b026ff;"),

    # Inputs: Fix visibility (black background, bright cyan border, white text)
    (r"background: #ffffff;\s*border: 1px solid rgba\(0, 0, 0, 0\.1\);", 
     r"background: #000000;\n            border: 1px solid rgba(0, 240, 255, 0.5);\n            color: #ffffff;"),
    (r"background: #ffffff;\s*border: 1px solid var\(--border\);", 
     r"background: #000000;\n            border: 1px solid rgba(0, 240, 255, 0.5);\n            color: #ffffff;"),
    (r"bg-white border border-slate-200", r"bg-black border border-cyan-500"),
    (r"text-slate-800", r"text-white"),
    (r"placeholder-slate-400", r"placeholder-cyan-700"),

    # Buttons
    (r"linear-gradient\(135deg, #2563eb, #3b82f6\)", r"linear-gradient(135deg, #00f0ff, #b026ff)"),
    (r"linear-gradient\(135deg, #2563eb, #0ea5e9\)", r"linear-gradient(135deg, #00f0ff, #b026ff)"),
    (r"box-shadow: 0 10px 20px rgba\(37, 99, 235, 0\.2\);", r"box-shadow: 0 0 20px rgba(0, 240, 255, 0.6);"),

    # Social / Demo Buttons
    (r"background: #ffffff;\s*border: 1px solid rgba\(0, 0, 0, 0\.1\);", 
     r"background: rgba(0, 240, 255, 0.05);\n            border: 1px solid rgba(0, 240, 255, 0.3);"),

    # Dashboard root variables
    (r"--primary: #2563eb;", r"--primary: #00f0ff;"),
    (r"--primary-glow: rgba\(37, 99, 235, 0\.2\);", r"--primary-glow: rgba(0, 240, 255, 0.5);"),
    (r"--secondary: #0ea5e9;", r"--secondary: #b026ff;"),
    (r"--bg-darker: #f8fafc;", r"--bg-darker: #050505;"),
    (r"--bg-dark: #ffffff;", r"--bg-dark: #0a0a0a;"),
    (r"--bg-card: rgba\(255, 255, 255, 0\.85\);", r"--bg-card: rgba(10, 15, 25, 0.85);"),
    (r"--text-main: #0f172a;", r"--text-main: #ffffff;"),
    (r"--text-dim: #64748b;", r"--text-dim: #00f0ff;"),
    (r"--border: rgba\(0, 0, 0, 0\.08\);", r"--border: rgba(0, 240, 255, 0.3);"),
    (r"--glass: rgba\(255, 255, 255, 0\.5\);", r"--glass: rgba(0, 240, 255, 0.1);"),

    # Dashboard Body gradient fix
    (r"rgba\(37, 99, 235, 0\.1\)", r"rgba(0, 240, 255, 0.15)"),
    (r"rgba\(14, 165, 233, 0\.1\)", r"rgba(176, 38, 255, 0.15)"),

    # Sidebar background
    (r"background: rgba\(255, 255, 255, 0\.85\);", r"background: rgba(5, 5, 5, 0.9);"),
    
    # Blobs animation color
    (r"rgba\(34, 197, 255, 0\.4\)", r"rgba(0, 240, 255, 0.5)"),
    (r"rgba\(14, 165, 233, 0\.1\)", r"rgba(0, 240, 255, 0.1)"),
    (r"rgba\(168, 85, 247, 0\.3\)", r"rgba(176, 38, 255, 0.5)"),
    (r"rgba\(109, 40, 217, 0\.1\)", r"rgba(176, 38, 255, 0.1)"),
    (r"rgba\(59, 130, 246, 0\.3\)", r"rgba(252, 238, 10, 0.4)"),
    (r"rgba\(29, 78, 216, 0\.1\)", r"rgba(252, 238, 10, 0.1)"),
]

html_files = glob.glob(os.path.join(STATIC_DIR, "*.html"))

for filepath in html_files:
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        
    original = content
    content = replace_branding(content)
    
    for pattern, new in regex_replacements:
        content = re.sub(pattern, new, content)
        
    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated {os.path.basename(filepath)}")
    else:
        print(f"No changes in {os.path.basename(filepath)}")

print("Cyberpunk redesign complete.")
