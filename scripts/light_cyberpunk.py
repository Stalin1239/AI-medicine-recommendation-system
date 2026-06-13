import os
import glob
import re

STATIC_DIR = "c:/Users/stali/mediops01/static"

cyberpunk_html = """
    <div class="cyber-container">
        <div class="cyber-grid"></div>
        <div class="cyber-scanlines"></div>
        <div class="cyber-hud top-left">
            <div class="hud-text">MEDIOPS // SYS.ACTIVE // NEURAL_LINK: ONLINE</div>
            <div class="hud-bar"></div>
        </div>
        <div class="cyber-hud bottom-right">
            <div class="hud-circle">
                <div class="hud-crosshair"></div>
            </div>
        </div>
        
        <!-- Floating Cyber Medical Equipment -->
        <div class="floating-equip equip-tablet">
            <svg viewBox="0 0 100 140" width="120" height="160">
                <rect x="5" y="5" width="90" height="130" rx="10" fill="rgba(255,255,255,0.1)" stroke="#00f0ff" stroke-width="2"/>
                <rect x="15" y="15" width="70" height="100" fill="rgba(0,240,255,0.1)"/>
                <line x1="20" y1="30" x2="60" y2="30" stroke="#00f0ff" stroke-width="3" opacity="0.8"/>
                <line x1="20" y1="45" x2="80" y2="45" stroke="#00f0ff" stroke-width="2" opacity="0.5"/>
                <line x1="20" y1="60" x2="70" y2="60" stroke="#00f0ff" stroke-width="2" opacity="0.5"/>
                <circle cx="50" cy="122" r="4" fill="#00f0ff"/>
            </svg>
        </div>
        
        <div class="floating-equip equip-syringe">
            <svg viewBox="0 0 140 140" width="150" height="150">
                <g transform="rotate(45 70 70)">
                    <rect x="60" y="30" width="20" height="60" fill="none" stroke="#ff0055" stroke-width="2"/>
                    <rect x="60" y="50" width="20" height="35" fill="rgba(57, 255, 20, 0.6)"/> <!-- Glowing green liquid -->
                    <line x1="55" y1="30" x2="85" y2="30" stroke="#ff0055" stroke-width="3"/>
                    <line x1="70" y1="90" x2="70" y2="120" stroke="#ff0055" stroke-width="2"/> <!-- Needle -->
                    <rect x="65" y="10" width="10" height="20" fill="none" stroke="#ff0055" stroke-width="2"/> <!-- Plunger -->
                </g>
            </svg>
        </div>
        
        <div class="floating-equip equip-dna">
            <svg viewBox="0 0 100 200" width="120" height="220">
                <path d="M 30 20 Q 70 60 30 100 T 30 180" fill="none" stroke="#00f0ff" stroke-width="3" opacity="0.7"/>
                <path d="M 70 20 Q 30 60 70 100 T 70 180" fill="none" stroke="#39ff14" stroke-width="3" opacity="0.7"/>
                <!-- Rungs -->
                <line x1="35" y1="40" x2="65" y2="40" stroke="#00f0ff" stroke-width="2" opacity="0.6"/>
                <line x1="45" y1="60" x2="55" y2="60" stroke="#00f0ff" stroke-width="2" opacity="0.6"/>
                <line x1="35" y1="80" x2="65" y2="80" stroke="#39ff14" stroke-width="2" opacity="0.6"/>
                <line x1="30" y1="100" x2="70" y2="100" stroke="#39ff14" stroke-width="2" opacity="0.6"/>
                <line x1="35" y1="120" x2="65" y2="120" stroke="#00f0ff" stroke-width="2" opacity="0.6"/>
                <line x1="45" y1="140" x2="55" y2="140" stroke="#39ff14" stroke-width="2" opacity="0.6"/>
                <line x1="35" y1="160" x2="65" y2="160" stroke="#00f0ff" stroke-width="2" opacity="0.6"/>
            </svg>
        </div>
    </div>
"""

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

regex_replacements = [
    # Clean up old medical background
    (r'<div class="medical-bg">[\s\S]*?</div>', r''),
    (r'\.medical-bg\s*\{[\s\S]*?\}', r''),
    (r'\.med-icon\s*\{[\s\S]*?\}', r''),
    (r'\.med-icon-\d\s*\{[\s\S]*?\}', r''),
    (r'@keyframes float-med\s*\{[\s\S]*?\}', r''),
]

html_files = glob.glob(os.path.join(STATIC_DIR, "*.html"))

for filepath in html_files:
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        
    original = content
    
    # Apply regex replacements to clean up
    for pattern, new in regex_replacements:
        content = re.sub(pattern, new, content)
        
    # Inject CSS before </head>
    if '<head>' in content and '</head>' in content and '.cyber-container' not in content:
        content = content.replace("</head>", f"{cyberpunk_css}\n</head>")
        
    # Inject HTML right after <body>
    if '<body>' in content and 'cyber-container' not in content:
        content = content.replace("<body>", f"<body>\n{cyberpunk_html}")
        
    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated {os.path.basename(filepath)}")
    else:
        print(f"No changes in {os.path.basename(filepath)}")

print("Light Cyberpunk Redesign complete.")
