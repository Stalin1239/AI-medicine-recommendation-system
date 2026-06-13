import os

base = r'c:\Users\stali\mediops01\static'

# Files that need cyber-inject.js added
needs_cyber = ['doctor-login.html', 'index.html', 'login.html', 'signup.html', 'video-room.html']

# Files that need mediops.css added
needs_css = ['diagnosis-interface.html']

# Font override to inject into <head> (before </head>)
sora_link = '    <link href="https://fonts.googleapis.com/css2?family=Sora:wght@300;400;500;600;700;800&family=Space+Grotesk:wght@300;400;500;600;700&family=Space+Mono:ital,wght@0,400;0,700;1,400&display=swap" rel="stylesheet">\n'

# Font override inline style
sora_style = '''    <style>
    /* Font override — smooth Sora instead of blocky fonts */
    * { -webkit-font-smoothing: antialiased; -moz-osx-font-smoothing: grayscale; }
    .font-display, .cyber-label, .stat-label, .badge, .btn-neon,
    .logo-text, .section-title, .page-title, .topbar-title, .modal-title,
    .sidebar-user-name, .stat-value, h1, h2, h3, h4 {
        font-family: 'Sora', sans-serif !important;
        letter-spacing: normal !important;
    }
    </style>\n'''

for filename in os.listdir(base):
    if not filename.endswith('.html'):
        continue
    
    filepath = os.path.join(base, filename)
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    changed = False
    
    # Add Sora font link if not present
    if 'Sora' not in content and '</head>' in content:
        content = content.replace('</head>', sora_link + sora_style + '</head>', 1)
        changed = True
        print(f"Added Sora font link to {filename}")
    
    # Add mediops.css if missing
    if 'mediops.css' not in content and filename in needs_css:
        content = content.replace('<head>', '<head>\n    <link rel="stylesheet" href="/static/mediops.css">', 1)
        changed = True
        print(f"Added mediops.css to {filename}")
    
    # Add cyber-inject.js if missing
    if 'cyber-inject.js' not in content and filename in needs_cyber:
        content = content.replace('</body>', '    <script src="/static/cyber-inject.js"></script>\n</body>', 1)
        changed = True
        print(f"Added cyber-inject.js to {filename}")
    
    if changed:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

print("\nAll done!")
