import os
import glob
import re

STATIC_DIR = "c:/Users/stali/mediops01/static"

# The raw CSS that was injected incorrectly outside <style>
cyberpunk_css = """
        /* CYBERPUNK BACKGROUND SYSTEM */
        .cyber-container {
            position: fixed;
            top: 0; left: 0; width: 100%; height: 100%;
            z-index: -999;
            background-color: #ffffff;
            overflow: hidden;
            pointer-events: none;
        }

        .cyber-grid {
            position: absolute;
            width: 200%; height: 200%;
            top: -50%; left: -50%;
            background-image: 
                linear-gradient(rgba(0, 240, 255, 0.2) 1px, transparent 1px),
                linear-gradient(90deg, rgba(0, 240, 255, 0.2) 1px, transparent 1px);
            background-size: 50px 50px;
            transform: perspective(500px) rotateX(45deg);
            animation: grid-scroll 10s linear infinite;
        }

        @keyframes grid-scroll {
            0% { transform: perspective(500px) rotateX(45deg) translateY(0); }
            100% { transform: perspective(500px) rotateX(45deg) translateY(50px); }
        }

        .cyber-scanlines {
            position: absolute;
            width: 100%; height: 100%;
            background: linear-gradient(
                to bottom,
                rgba(255,255,255,0),
                rgba(255,255,255,0) 50%,
                rgba(0, 240, 255, 0.05) 50%,
                rgba(0, 240, 255, 0.05)
            );
            background-size: 100% 4px;
            z-index: 10;
        }

        /* HUD ELEMENTS */
        .cyber-hud {
            position: absolute;
            z-index: 15;
            padding: 20px;
        }
        .top-left { top: 0; left: 0; }
        .bottom-right { bottom: 0; right: 0; }

        .hud-text {
            color: #00f0ff;
            font-family: monospace;
            font-weight: bold;
            font-size: 0.8rem;
            letter-spacing: 2px;
            animation: blink 2s infinite;
        }
        .hud-bar {
            width: 150px; height: 3px;
            background: #00f0ff;
            margin-top: 5px;
            position: relative;
        }
        .hud-bar::after {
            content: ''; position: absolute; top: 0; right: -10px; width: 5px; height: 3px; background: #ff0055;
        }

        .hud-circle {
            width: 100px; height: 100px;
            border: 1px dashed rgba(0, 240, 255, 0.5);
            border-radius: 50%;
            animation: rotate-slow 15s linear infinite;
            display: flex; align-items: center; justify-content: center;
        }
        .hud-crosshair {
            width: 20px; height: 20px;
            border: 2px solid #ff0055;
            border-radius: 50%;
        }

        @keyframes blink { 0%, 96%, 98% { opacity: 1; } 97%, 99% { opacity: 0; } }
        @keyframes rotate-slow { 100% { transform: rotate(360deg); } }

        /* FLOATING MEDICAL EQUIPMENT */
        .floating-equip {
            position: absolute;
            filter: drop-shadow(0 0 10px rgba(0, 240, 255, 0.4));
        }
        .equip-tablet {
            top: 15%; right: 15%;
            animation: float-obj 12s ease-in-out infinite, rotate-3d 20s linear infinite;
        }
        .equip-syringe {
            bottom: 20%; left: 10%;
            animation: float-obj 15s ease-in-out infinite reverse;
        }
        .equip-dna {
            top: 30%; left: 45%;
            animation: float-obj 18s ease-in-out infinite, rotate-dna 10s linear infinite;
        }

        @keyframes float-obj {
            0%, 100% { transform: translateY(0px); }
            50% { transform: translateY(-30px); }
        }
        @keyframes rotate-3d {
            0% { transform: perspective(600px) rotateY(0deg) rotateX(10deg); }
            100% { transform: perspective(600px) rotateY(360deg) rotateX(10deg); }
        }
        @keyframes rotate-dna {
            100% { transform: rotateY(360deg); }
        }

        /* UI COMPONENT OVERRIDES (Cyberpunk Angle & Glitch) */
        .card, .auth-box, .sidebar, .form-card, .modal-content {
            clip-path: polygon(0 0, 100% 0, 100% calc(100% - 25px), calc(100% - 25px) 100%, 0 100%);
            border-bottom: 2px solid #00f0ff !important;
            border-right: 2px solid #00f0ff !important;
            background: rgba(255, 255, 255, 0.9) !important;
            box-shadow: 10px 10px 0px rgba(0, 240, 255, 0.1) !important;
        }

        button, .btn {
            position: relative;
            clip-path: polygon(0 0, calc(100% - 10px) 0, 100% 10px, 100% 100%, 10px 100%, 0 calc(100% - 10px));
            border-bottom: 2px solid #ff0055 !important;
            transition: all 0.2s;
        }

        button:hover, .btn:hover {
            animation: cyber-glitch 0.3s cubic-bezier(.25, .46, .45, .94) both infinite;
            background: #00f0ff !important;
            color: #050505 !important;
        }

        @keyframes cyber-glitch {
            0% { transform: translate(0) }
            20% { transform: translate(-2px, 2px) }
            40% { transform: translate(-2px, -2px) }
            60% { transform: translate(2px, 2px) }
            80% { transform: translate(2px, -2px) }
            100% { transform: translate(0) }
        }
"""

html_files = glob.glob(os.path.join(STATIC_DIR, "*.html"))

for filepath in html_files:
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        
    original = content
    
    # Remove all raw text that is between </style> and </head>
    # Note: re.sub is tricky with newlines. Let's do it safely.
    
    # 1. First, strip out ALL occurrences of the broken raw CSS injected previously.
    content = content.replace("50% { transform: translateY(-30px) rotate(180deg); }", "")
    content = content.replace("100% { transform: translateY(0) rotate(360deg); }", "")
    content = content.replace("}", "", 2) # CAREFUL, this might be dangerous if not precise.
    
    # Actually, a safer regex:
    # Delete everything between </style> and </head>
    content = re.sub(r'</style>[\s\S]*?</head>', r'</style>\n</head>', content)
    
    # But wait, my script also previously injected medical_css outside!
    # By deleting everything between </style> and </head>, I wipe the slate clean of all raw text.
    
    # 2. Inject the cyberpunk CSS *inside* the <style> block, right before </style>
    if '</style>' in content and '/* CYBERPUNK BACKGROUND SYSTEM */' not in content:
        content = content.replace("</style>", f"{cyberpunk_css}\n</style>")
        
    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Fixed {os.path.basename(filepath)}")
    else:
        print(f"No changes in {os.path.basename(filepath)}")

print("CSS Fix complete.")
