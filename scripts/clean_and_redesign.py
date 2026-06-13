import os
import re

STATIC_DIR = r"c:\Users\stali\mediops01\static"

# Standard light-cyberpunk CSS variables block to prepend/inject
CSS_VARS_BLOCK = """
:root {
    --bg-base: #f8fafc;
    --bg-dark: #f1f5f9;
    --bg-darker: #e2e8f0;
    --bg: #f8fafc;
    --bg2: #f1f5f9;
    --bg3: #e2e8f0;
    --bg-card: rgba(255, 255, 255, 0.75);
    --bg-card-hover: rgba(255, 255, 255, 0.9);
    --card: rgba(255, 255, 255, 0.75);
    --card-solid: #ffffff;
    --neon-primary: #00E5FF;
    --neon-secondary: #FF00FF;
    --neon-tertiary: #7c3aed;
    --primary: #00c8f0;
    --secondary: #e400ff;
    --violet: #7c3aed;
    --green: #00e5a0;
    --success: #10b981;
    --warning: #f59e0b;
    --danger: #ef4444;
    --text-main: #0d1e3d;
    --text: #0d1e3d;
    --text2: #2a4778;
    --text-dim: #475569;
    --text3: #64748b;
    --text-muted: #94a3b8;
    --border: rgba(0, 229, 255, 0.2);
    --border-bright: rgba(0, 229, 255, 0.45);
    --border-neon: rgba(0, 229, 255, 0.35);
    --border-magenta: rgba(255, 0, 255, 0.35);
    --glow-sm: 0 0 10px rgba(0, 229, 255, 0.2);
    --glow-md: 0 0 15px rgba(0, 229, 255, 0.3), 0 0 30px rgba(255, 0, 255, 0.1);
    --glow-lg: 0 0 25px rgba(0, 229, 255, 0.45), 0 0 50px rgba(255, 0, 255, 0.2);
    --primary-glow: rgba(0, 200, 240, 0.25);
    --secondary-glow: rgba(228, 0, 255, 0.2);
    --sidebar-width: 280px;
    --transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}
"""

AUTH_STYLE_BLOCK = """
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: 'Space Grotesk', sans-serif;
            background: transparent;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            overflow-x: hidden;
            color: var(--text-main);
        }
        .container-auth, .auth-container {
            width: 100%;
            max-width: 500px;
            padding: 20px;
            position: relative;
            z-index: 2;
        }
        .auth-box {
            background: var(--bg-card) !important;
            backdrop-filter: blur(25px) saturate(200%) !important;
            -webkit-backdrop-filter: blur(25px) saturate(200%) !important;
            border: 1px solid var(--border-neon) !important;
            border-radius: 30px !important;
            padding: 40px !important;
            box-shadow: var(--glow-md) !important;
            animation: slideIn 0.6s cubic-bezier(0.16, 1, 0.3, 1);
            position: relative;
            overflow: hidden;
        }
        @keyframes slideIn {
            from { opacity: 0; transform: translateY(30px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .auth-box::before {
            content: '';
            position: absolute;
            top: 0; left: 0; right: 0; height: 5px;
            background: linear-gradient(90deg, var(--neon-primary), var(--neon-secondary), var(--neon-tertiary));
            z-index: 5;
        }
        .logo-section, .text-center {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            text-align: center;
            margin-bottom: 25px;
        }
        .logo-icon, .logo-glow {
            width: 65px;
            height: 65px;
            background: linear-gradient(135deg, var(--neon-primary), var(--neon-tertiary)) !important;
            border-radius: 18px !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            font-size: 30px !important;
            margin: 0 auto 15px !important;
            box-shadow: var(--glow-sm) !important;
            color: #ffffff !important;
            animation: pulse-ring 3s infinite;
        }
        @keyframes pulse-ring {
            0% { box-shadow: 0 0 0 0 rgba(0, 229, 255, 0.4); }
            70% { box-shadow: 0 0 0 12px rgba(0, 229, 255, 0); }
            100% { box-shadow: 0 0 0 0 rgba(0, 229, 255, 0); }
        }
        .blob {
            position: absolute;
            width: 500px;
            height: 500px;
            border-radius: 50%;
            background: linear-gradient(135deg, rgba(0, 229, 255, 0.12), rgba(255, 0, 255, 0.08));
            filter: blur(80px);
            z-index: -1;
            pointer-events: none;
            animation: floatBlob 10s ease-in-out infinite alternate;
        }
        .blob2 { top: -10%; left: -20%; }
        .blob3 { bottom: -10%; right: -20%; animation-delay: -5s; }
        @keyframes floatBlob {
            0% { transform: translate(0, 0) scale(1); }
            100% { transform: translate(40px, -40px) scale(1.1); }
        }
        .pulse-line {
            width: 100%;
            height: 40px;
            background: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 20' width='100%25' height='40'%3E%3Cpath d='M0 10 h40 l2 -5 l2 15 l3 -20 l2 15 l1 -5 h48' fill='none' stroke='%2300E5FF' stroke-width='0.5' stroke-dasharray='100' stroke-dashoffset='100'/%3E%3C/svg%3E") repeat-x;
            opacity: 0.25;
            margin-bottom: 20px;
        }
        .demo-card {
            border: 1px dashed var(--border-neon) !important;
            background: rgba(0, 229, 255, 0.04) !important;
            border-radius: 12px !important;
            padding: 12px !important;
            transition: var(--transition) !important;
        }
        .demo-card:hover {
            border-color: var(--neon-secondary) !important;
            background: rgba(255, 0, 255, 0.04) !important;
            transform: translateY(-2px) !important;
        }
"""

def clean_file(filename):
    filepath = os.path.join(STATIC_DIR, filename)
    if not os.path.exists(filepath):
        print(f"File {filename} not found.")
        return

    print(f"Processing {filename}...")
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Check if the file is one of the Auth pages (login, signup, doctor-login)
    is_auth_page = filename in ["login.html", "signup.html", "doctor-login.html"]

    if is_auth_page:
        # Replace the entire style tag content with our clean, correct auth style
        style_pattern = re.compile(r'<style>.*?</style>', re.DOTALL)
        content = style_pattern.sub(f"<style>\n{CSS_VARS_BLOCK}\n{AUTH_STYLE_BLOCK}\n    </style>", content)
        print(f"-> Overwrote style tag for auth page: {filename}")
    else:
        # For non-auth pages, prepend our standard CSS_VARS_BLOCK inside <style>
        style_pattern = re.compile(r'<style>', re.IGNORECASE)
        content = style_pattern.sub(f"<style>\n{CSS_VARS_BLOCK}", content)
        print(f"-> Prepended CSS variables in style tag: {filename}")

    # 2. Cleanup inline styles with dark backgrounds/colors
    replacements = [
        # Dark backgrounds to glassmorphism or transparent
        ('background: rgba(15, 23, 42, 0.8)', 'background: var(--bg-card); backdrop-filter: blur(10px);'),
        ('background: rgba(15, 23, 42, 0.8);', 'background: var(--bg-card); backdrop-filter: blur(10px);'),
        ('background: rgba(0, 0, 0, 0.35)', 'background: var(--bg-card); backdrop-filter: blur(10px);'),
        ('background: rgba(0, 0, 0, 0.3)', 'background: var(--bg-card); backdrop-filter: blur(10px);'),
        ('background: rgba(0,0,0,0.3)', 'background: var(--bg-card); backdrop-filter: blur(10px);'),
        ('background: rgba(0, 0, 0, 0.8)', 'background: rgba(255, 255, 255, 0.85); backdrop-filter: blur(15px); color: var(--text-main);'),
        ('background: rgba(5, 8, 16, 0.95)', 'background: rgba(240, 244, 255, 0.95);'),
        ('background: rgba(5, 8, 19, 0.8)', 'background: rgba(240, 244, 255, 0.8);'),
        ('background: rgba(16, 24, 48, 0.9)', 'background: var(--bg-card);'),
        ('background-color: var(--bg-dark);', 'background-color: var(--bg-card);'),
        ('background-color: #0b0f19;', 'background-color: var(--bg-base);'),
        
        # Text/contrast corrections
        ('color:#ccc;', 'color: var(--text-dim);'),
        ('color:#888;', 'color: var(--text-muted);'),
        ('border-left: 4px solid rgba(255,255,255,0.2)', 'border-left: 4px solid var(--border);'),
        ('background: rgba(0,0,0,0.3)', 'background: var(--bg-card); backdrop-filter: blur(10px);'),
        ('background: rgba(0,240,255,0.05)', 'background: rgba(0, 229, 255, 0.08)'),
        
        # User profile specific
        ('background: rgba(0, 0, 0, 0.35); padding: 8px 20px; border-radius: 50px; border: 1px solid var(--border);',
         'background: var(--bg-card); padding: 8px 20px; border-radius: 50px; border: 1px solid var(--border-neon);'),
    ]

    for old, new in replacements:
        content = content.replace(old, new)

    # 3. Ensure the CSS file and JS file are linked
    if "/static/cyberpunk-light.css" not in content:
        # Prepend the css before </head>
        content = content.replace("</head>", '<link href="/static/cyberpunk-light.css" rel="stylesheet">\n</head>')
        print(f"-> Injected link to cyberpunk-light.css: {filename}")

    if "/static/floating-med.js" not in content:
        # Prepend the script before </body>
        content = content.replace("</body>", '<script src="/static/floating-med.js"></script>\n</body>')
        print(f"-> Injected script tag for floating-med.js: {filename}")

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Completed {filename}.\n")

def run():
    files = [
        "index.html",
        "login.html",
        "signup.html",
        "doctor-login.html",
        "dashboard.html",
        "doctor-dashboard.html",
        "admin-panel.html",
        "consultation-request.html",
        "diagnosis-interface.html",
        "video-room.html"
    ]
    for filename in files:
        clean_file(filename)

if __name__ == "__main__":
    run()
