import os

files_to_update = [
    "dashboard.html",
    "doctor-dashboard.html",
    "admin-panel.html",
    "consultation-request.html",
    "diagnosis-interface.html"
]

base_dir = r"c:\Users\stali\mediops01\static"

for filename in files_to_update:
    filepath = os.path.join(base_dir, filename)
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if already injected
        if 'cyber-inject.js' not in content:
            # Add script before closing body
            content = content.replace('</body>', '    <script src="/static/cyber-inject.js"></script>\n</body>')
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Updated {filename}")
    else:
        print(f"File not found: {filename}")
