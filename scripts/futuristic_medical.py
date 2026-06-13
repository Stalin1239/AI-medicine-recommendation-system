import os
import glob
import re

STATIC_DIR = "c:/Users/stali/mediops01/static"

medical_bg_html = """
    <div class="medical-bg">
        <i class="fa-solid fa-pills med-icon med-icon-1"></i>
        <i class="fa-solid fa-dna med-icon med-icon-2"></i>
        <i class="fa-solid fa-stethoscope med-icon med-icon-3"></i>
        <i class="fa-solid fa-heart-pulse med-icon med-icon-4"></i>
        <i class="fa-solid fa-syringe med-icon med-icon-5"></i>
        <i class="fa-solid fa-briefcase-medical med-icon med-icon-6"></i>
    </div>
"""

medical_css = """
        .medical-bg {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            z-index: -999;
            overflow: hidden;
            background: linear-gradient(135deg, #f8fafc 0%, #e0f2fe 50%, #f1f5f9 100%);
        }
        
        .med-icon {
            position: absolute;
            color: rgba(14, 165, 233, 0.12);
            font-size: 5rem;
            animation: float-med 20s infinite linear;
            filter: drop-shadow(0 10px 15px rgba(14, 165, 233, 0.15));
        }

        .med-icon-1 { top: 10%; left: 10%; font-size: 8rem; animation-duration: 25s; }
        .med-icon-2 { bottom: 15%; right: 10%; font-size: 12rem; animation-duration: 35s; animation-direction: reverse; color: rgba(37, 99, 235, 0.08); }
        .med-icon-3 { top: 40%; left: 80%; font-size: 6rem; animation-duration: 22s; }
        .med-icon-4 { bottom: 30%; left: 20%; font-size: 10rem; animation-duration: 30s; color: rgba(16, 185, 129, 0.08); }
        .med-icon-5 { top: 20%; left: 45%; font-size: 5rem; animation-duration: 18s; animation-direction: reverse; }
        .med-icon-6 { bottom: 10%; left: 50%; font-size: 7rem; animation-duration: 28s; }

        @keyframes float-med {
            0% { transform: translateY(0) rotate(0deg); }
            50% { transform: translateY(-30px) rotate(180deg); }
            100% { transform: translateY(0) rotate(360deg); }
        }
"""

regex_replacements = [
    # Clean up old animated blobs HTML
    (r'<div class="animated-bg">[\s\S]*?</div>', r''),
    # Clean up old blob CSS
    (r'\.animated-bg\s*\{[\s\S]*?\}', r''),
    (r'\.blob\s*\{[\s\S]*?\}', r''),
    (r'\.blob1\s*\{[\s\S]*?\}', r''),
    (r'\.blob2\s*\{[\s\S]*?\}', r''),
    (r'\.blob3\s*\{[\s\S]*?\}', r''),
    (r'@keyframes float\s*\{[\s\S]*?\}', r''),

    # Revert auth box to light glassmorphism
    (r"background: rgba\(10, 10, 10, 0\.8\);\s*backdrop-filter: blur\(15px\);\s*border: 1px solid rgba\(0, 240, 255, 0\.4\);", 
     r"background: rgba(255, 255, 255, 0.9);\n            backdrop-filter: blur(20px);\n            border: 1px solid rgba(14, 165, 233, 0.2);"),

    # Revert inputs to light
    (r"background: #000000;\s*border: 1px solid rgba\(0, 240, 255, 0\.5\);\s*color: #ffffff;", 
     r"background: #ffffff;\n            border: 1px solid rgba(14, 165, 233, 0.3);\n            color: #0f172a;"),
    (r"bg-black border border-cyan-500", r"bg-white border border-sky-200"),
    (r"text-white", r"text-slate-800"),
    (r"placeholder-cyan-700", r"placeholder-slate-400"),

    # Revert auth page body texts
    (r"color: #ffffff; text-shadow: 0 0 5px rgba\(0, 240, 255, 0\.3\);", r"color: #0f172a;"),
    (r"color: #00f0ff;", r"color: #0ea5e9;"),
    (r"color: #b026ff;", r"color: #475569;"),

    # Buttons
    (r"linear-gradient\(135deg, #00f0ff, #b026ff\)", r"linear-gradient(135deg, #0ea5e9, #3b82f6)"),
    (r"box-shadow: 0 0 20px rgba\(0, 240, 255, 0\.6\);", r"box-shadow: 0 10px 25px rgba(14, 165, 233, 0.2);"),

    # Dashboard root variables
    (r"--primary: #00f0ff;", r"--primary: #0ea5e9;"),
    (r"--primary-glow: rgba\(0, 240, 255, 0\.5\);", r"--primary-glow: rgba(14, 165, 233, 0.3);"),
    (r"--secondary: #b026ff;", r"--secondary: #3b82f6;"),
    (r"--bg-darker: #050505;", r"--bg-darker: #f8fafc;"),
    (r"--bg-dark: #0a0a0a;", r"--bg-dark: #ffffff;"),
    (r"--bg-card: rgba\(10, 15, 25, 0\.85\);", r"--bg-card: rgba(255, 255, 255, 0.95);"),
    (r"--text-main: #ffffff;", r"--text-main: #0f172a;"),
    (r"--text-dim: #00f0ff;", r"--text-dim: #64748b;"),
    (r"--border: rgba\(0, 240, 255, 0\.3\);", r"--border: rgba(14, 165, 233, 0.2);"),
    (r"--glass: rgba\(0, 240, 255, 0\.1\);", r"--glass: rgba(255, 255, 255, 0.8);"),

    # Sidebar background
    (r"background: rgba\(5, 5, 5, 0\.9\);", r"background: rgba(255, 255, 255, 0.95);"),

    # Dashboard body gradients - completely remove them and rely on medical-bg
    (r"background-image: radial-gradient[\s\S]*?transparent 50%\);", r"background: transparent;"),
    (r"background-color: var\(--bg-darker\);", r"background: transparent;"),
    
    # Auth Body gradients
    (r"background: linear-gradient\(135deg, #050505 0%, #0a0a0a 25%, #051020 50%, #0a0515 75%, #050505 100%\);", r"background: transparent;"),
]

html_files = glob.glob(os.path.join(STATIC_DIR, "*.html"))

for filepath in html_files:
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        
    original = content
    
    # Apply regex replacements
    for pattern, new in regex_replacements:
        content = re.sub(pattern, new, content)
        
    # Inject CSS before </head>
    if '<head>' in content and '</head>' in content and '.medical-bg' not in content:
        content = content.replace("</head>", f"{medical_css}\n</head>")
        
    # Inject Medical HTML right after <body>
    if '<body>' in content and 'medical-bg' not in content:
        content = content.replace("<body>", f"<body>\n{medical_bg_html}")
        
    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated {os.path.basename(filepath)}")
    else:
        print(f"No changes in {os.path.basename(filepath)}")

print("Futuristic Medical redesign complete.")
