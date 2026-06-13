import os
import glob
import re

STATIC_DIR = "c:/Users/stali/mediops01/static"

# Mapping of old dark variables to new light 2050 variables
var_replacements = {
    "--primary: #00f0ff;": "--primary: #2563eb;",
    "--primary-glow: rgba(0, 240, 255, 0.3);": "--primary-glow: rgba(37, 99, 235, 0.2);",
    "--secondary: #7000ff;": "--secondary: #0ea5e9;",
    "--bg-darker: #050811;": "--bg-darker: #f8fafc;",
    "--bg-dark: #0a0f1d;": "--bg-dark: #ffffff;",
    "--bg-card: rgba(16, 24, 48, 0.65);": "--bg-card: rgba(255, 255, 255, 0.85);",
    "--text-main: #f1f5f9;": "--text-main: #0f172a;",
    "--text-dim: #94a3b8;": "--text-dim: #64748b;",
    "--glass: rgba(255, 255, 255, 0.03);": "--glass: rgba(255, 255, 255, 0.5);",
    "--light: #f1f5f9;": "--light: #ffffff;"
}

# Regex replacements for hardcoded dark styles
regex_replacements = [
    # Auth Pages Background
    (r"background: linear-gradient\(135deg, #0f172a 0%, #1e293b 25%, #0f4c75 50%, #1a1a2e 75%, #16213e 100%\);", 
     r"background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 50%, #f1f5f9 100%); color: #0f172a;"),
    # Auth Box
    (r"background: rgba\(15, 23, 42, 0\.7\);", r"background: rgba(255, 255, 255, 0.85); border: 1px solid rgba(0,0,0,0.05);"),
    # Form Inputs
    (r"background: rgba\(30, 41, 59, 0\.8\);", r"background: #ffffff;"),
    (r"background: rgba\(30, 41, 59, 0\.95\);", r"background: #ffffff;"),
    (r"color: #f1f5f9;", r"color: #0f172a;"),
    (r"color: #e2e8f0;", r"color: #0f172a;"),
    (r"color: #cbd5e1;", r"color: #334155;"),
    (r"color: #94a3b8;", r"color: #475569;"),
    # Buttons
    (r"linear-gradient\(135deg, #22c55e, #16a34a\)", r"linear-gradient(135deg, #2563eb, #3b82f6)"),
    (r"linear-gradient\(135deg, #22c55e, #0ea5e9\)", r"linear-gradient(135deg, #2563eb, #0ea5e9)"),
    # Dashboard specific fixes
    (r"color: #fff;", r"color: var(--text-main);"),
    (r"color: rgba\(255,255,255,0\.5\);", r"color: var(--text-dim);"),
    (r"color: rgba\(255,255,255,0\.6\);", r"color: var(--text-dim);"),
    (r"color: rgba\(255,255,255,0\.7\);", r"color: var(--text-dim);"),
    # Dashboard body gradients
    (r"background-image: radial-gradient\(at 0% 0%, rgba\(112, 0, 255, 0\.15\) 0px, transparent 50%\), radial-gradient\(at 100% 100%, rgba\(0, 240, 255, 0\.1\) 0px, transparent 50%\);",
     r"background-image: radial-gradient(at 0% 0%, rgba(37, 99, 235, 0.1) 0px, transparent 50%), radial-gradient(at 100% 100%, rgba(14, 165, 233, 0.1) 0px, transparent 50%);"),
    (r"background: rgba\(10, 15, 29, 0\.85\);", r"background: rgba(255, 255, 255, 0.85);")
]

html_files = glob.glob(os.path.join(STATIC_DIR, "*.html"))

for filepath in html_files:
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        
    original = content
    
    for old, new in var_replacements.items():
        content = content.replace(old, new)
        
    for pattern, new in regex_replacements:
        content = re.sub(pattern, new, content)
        
    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated {os.path.basename(filepath)}")
    else:
        print(f"No changes in {os.path.basename(filepath)}")

print("Redesign complete.")
