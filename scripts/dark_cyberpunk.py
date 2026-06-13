import os
import glob
import re

STATIC_DIR = "c:/Users/stali/mediops01/static"

dark_cyberpunk_css = """
        /* DARK MEDICAL CYBERPUNK CSS GUIDE */
        :root {
          /* Deep Dark Backgrounds */
          --bg-base: #020617;       
          --bg-card: rgba(2, 6, 23, 0.7); 
          
          /* Neon Accents */
          --neon-primary: #00E5FF;  
          --neon-secondary: #0077FF; 
          
          /* Text Colors */
          --text-main: #FFFFFF;
          --text-muted: rgba(255, 255, 255, 0.5);
          
          /* Reusable Glowing Shadows (Using RGB of #00E5FF) */
          --glow-sm: 0 0 10px rgba(0, 229, 255, 0.3);
          --glow-md: 0 0 20px rgba(0, 229, 255, 0.5), 0 0 40px rgba(0, 229, 255, 0.2);
          --border-neon: rgba(0, 229, 255, 0.3);
        }

        body {
            background-color: var(--bg-base);
            color: var(--text-main);
            min-height: 100vh;
            margin: 0;
            position: relative;
        }

        /* Dark Moody Background Image */
        body::before {
          content: '';
          position: fixed;
          inset: 0;
          /* Using a high-quality dark medical/tech abstract image from Unsplash */
          background-image: url('https://images.unsplash.com/photo-1550751827-4bd374c3f58b?q=80&w=2070&auto=format&fit=crop');
          background-size: cover;
          background-position: center;
          
          /* CRITICAL: Darken heavily and boost colors */
          filter: brightness(0.15) saturate(1.8);
          
          z-index: -2; 
        }

        /* Subtle CRT Scanlines Overlay */
        body::after {
          content: '';
          position: fixed;
          inset: 0;
          background: repeating-linear-gradient(
            0deg,
            transparent,
            transparent 3px,
            rgba(0, 0, 0, 0.1) 3px,
            rgba(0, 0, 0, 0.1) 4px
          );
          pointer-events: none; 
          z-index: 9999;
        }

        /* Glassmorphism (Frosted Glass) for Cards */
        .glass-card, .card, .form-card, .auth-box, .sidebar, .modal-content {
          background: var(--bg-card) !important;
          backdrop-filter: blur(16px) saturate(180%) !important;
          -webkit-backdrop-filter: blur(16px) saturate(180%) !important;
          
          border: 1px solid var(--border-neon) !important;
          border-radius: 16px !important;
          box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5) !important;
          
          /* Remove clip-path from previous design */
          clip-path: none !important; 
        }

        /* Neon Glowing Text */
        .neon-heading, h1, h2, h3 {
          color: #FFF !important;
          font-weight: 800;
          text-shadow: 
            0 0 5px rgba(0, 229, 255, 0.8),
            0 0 20px rgba(0, 229, 255, 0.5),
            0 0 40px rgba(0, 229, 255, 0.3) !important;
        }

        /* Glowing Buttons */
        .cyber-button, button, .btn {
          background: transparent !important;
          color: var(--neon-primary) !important;
          border: 1px solid var(--neon-primary) !important;
          padding: 12px 24px;
          border-radius: 8px;
          text-transform: uppercase;
          letter-spacing: 2px;
          font-weight: bold;
          cursor: pointer;
          transition: all 0.3s ease;
          clip-path: none !important; /* Remove old cyberpunk clip */
        }
        
        .cyber-button:hover, button:hover, .btn:hover {
          background: var(--neon-primary) !important;
          color: var(--bg-base) !important;
          box-shadow: var(--glow-md) !important;
          transform: translateY(-2px);
          animation: none !important; /* Remove glitch */
        }

        /* Floating Medical Equipment (Particles Effect) */
        .medical-particles {
          position: fixed;
          inset: 0;
          z-index: -1;
          pointer-events: none;
          overflow: hidden;
        }
        
        .particle {
          position: absolute;
          animation: floatMed var(--duration, 12s) var(--delay, 0s) ease-in-out infinite both;
          opacity: var(--opacity, 0.3);
          font-size: var(--size, 2rem);
          filter: drop-shadow(0 0 10px rgba(0, 229, 255, 0.6));
          will-change: transform;
        }
        
        .particle:nth-child(1) { top: 10%; left: 5%;  --duration: 14s; --delay: 0s;  --size: 2.2rem; --opacity: 0.2; }
        .particle:nth-child(2) { top: 25%; right: 8%; --duration: 10s; --delay: -3s; --size: 1.5rem; --opacity: 0.4; }
        .particle:nth-child(3) { top: 55%; left: 15%; --duration: 16s; --delay: -7s; --size: 3rem;   --opacity: 0.15; }
        .particle:nth-child(4) { top: 75%; right: 12%;--duration: 12s; --delay: -2s; --size: 1.8rem; --opacity: 0.3; }
        .particle:nth-child(5) { top: 85%; left: 30%; --duration: 15s; --delay: -9s; --size: 2.5rem; --opacity: 0.25; }
        .particle:nth-child(6) { top: 40%; right: 35%;--duration: 11s; --delay: -5s; --size: 1.2rem; --opacity: 0.5; }
        
        @keyframes floatMed {
          0%   { transform: translateY(0) translateX(0) rotate(0deg) scale(1); }
          25%  { transform: translateY(-25px) translateX(15px) rotate(10deg) scale(1.1); }
          50%  { transform: translateY(-10px) translateX(-20px) rotate(-5deg) scale(0.95); }
          75%  { transform: translateY(-30px) translateX(10px) rotate(8deg) scale(1.05); }
          100% { transform: translateY(0) translateX(0) rotate(0deg) scale(1); }
        }

        /* The Pulsing Medical Cross */
        .health-card {
          position: relative;
        }
        .health-card::before,
        .health-card::after {
          content: '';
          position: absolute;
          top: 20px;
          right: 20px;
          background: var(--neon-primary);
          box-shadow: 0 0 15px var(--neon-primary);
          border-radius: 2px;
          animation: heartbeat 1.5s ease-in-out infinite;
          z-index: 10;
        }
        .health-card::before { width: 6px; height: 24px; right: 29px; }
        .health-card::after { width: 24px; height: 6px; top: 29px; }
        
        @keyframes heartbeat {
          0%, 100% { transform: scale(1); opacity: 0.8; }
          15% { transform: scale(1.3); opacity: 1; box-shadow: 0 0 25px var(--neon-primary); }
          30% { transform: scale(1); opacity: 0.8; }
          45% { transform: scale(1.3); opacity: 1; box-shadow: 0 0 25px var(--neon-primary); }
          60% { transform: scale(1); opacity: 0.8; }
        }

        /* EKG Sweep on Dashboards */
        .medical-dashboard {
          position: relative;
          overflow: hidden;
        }
        .medical-dashboard::after {
          content: '';
          position: absolute;
          bottom: 0;
          left: -100%;
          width: 50%;
          height: 3px;
          background: linear-gradient(to right, transparent, var(--neon-primary), transparent);
          box-shadow: 0 -2px 10px var(--neon-primary);
          animation: ekgSweep 3s linear infinite;
          z-index: 10;
        }
        
        @keyframes ekgSweep {
          0% { left: -100%; }
          100% { left: 200%; }
        }
        
        /* Inputs Fixes for Dark Theme */
        input, select, textarea {
            background: rgba(0,0,0,0.5) !important;
            border: 1px solid var(--border-neon) !important;
            color: var(--text-main) !important;
        }
"""

dark_cyberpunk_html = """
    <div class="medical-particles" aria-hidden="true">
      <div class="particle">🩺</div>
      <div class="particle">💊</div>
      <div class="particle">⚕️</div>
      <div class="particle">🧬</div>
      <div class="particle">💉</div>
      <div class="particle">💊</div>
    </div>
"""

html_files = glob.glob(os.path.join(STATIC_DIR, "*.html"))

for filepath in html_files:
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        
    original = content
    
    # 1. Clean up OLD Light Cyberpunk HTML
    content = re.sub(r'<div class="cyber-container">[\s\S]*?</div>\s*</div>\s*</div>', '', content)
    # The regex above might miss things if nested. Let's do a more robust string replacement:
    if '<div class="cyber-container">' in content:
        start_idx = content.find('<div class="cyber-container">')
        # We know it ends after the DNA equip div. Let's just find the end of that block.
        end_str = "</div>\n    </div>"
        end_idx = content.find(end_str, start_idx) + len(end_str)
        if end_idx > len(end_str):
            content = content[:start_idx] + content[end_idx:]

    # 2. Clean up old CSS
    # Remove everything from CYBERPUNK BACKGROUND SYSTEM to the end of style
    if '/* CYBERPUNK BACKGROUND SYSTEM */' in content:
        start_idx = content.find('/* CYBERPUNK BACKGROUND SYSTEM */')
        end_idx = content.find('</style>')
        if start_idx != -1 and end_idx != -1:
            content = content[:start_idx] + content[end_idx:]

    # 3. Clean up :root
    if ':root {' in content:
        start_idx = content.find(':root {')
        end_idx = content.find('}', start_idx) + 1
        if start_idx != -1 and end_idx != -1:
            content = content[:start_idx] + content[end_idx:]

    # 4. Inject new CSS
    if '</style>' in content and '/* DARK MEDICAL CYBERPUNK CSS GUIDE */' not in content:
        content = content.replace("</style>", f"{dark_cyberpunk_css}\n</style>")

    # 5. Inject new HTML right after <body>
    if '<body>' in content and 'medical-particles' not in content:
        content = content.replace("<body>", f"<body>\n{dark_cyberpunk_html}")
        
    # 6. Add .health-card and .medical-dashboard to the main layout
    if 'class="container"' in content:
        content = content.replace('class="container"', 'class="container medical-dashboard"')
        
    # Any major cards can get health-card class for the cross
    content = content.replace('class="dashboard-card"', 'class="dashboard-card health-card"')
    content = content.replace('class="card"', 'class="card health-card"')
    content = content.replace('class="form-card"', 'class="form-card health-card"')

    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated {os.path.basename(filepath)}")
    else:
        print(f"No changes in {os.path.basename(filepath)}")

print("Dark Medical Cyberpunk Redesign complete.")
