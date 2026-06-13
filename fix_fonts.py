import os
import re

base_dir = r"c:\Users\stali\mediops01\static"

old_font = "https://fonts.googleapis.com/css2?family=Orbitron:wght@400;500;600;700;800;900&family=Exo+2:ital,wght@0,300;0,400;0,500;0,600;0,700;1,300;1,400&family=Share+Tech+Mono&display=swap"
new_font = "https://fonts.googleapis.com/css2?family=Sora:wght@300;400;500;600;700;800&family=Space+Grotesk:wght@300;400;500;600;700&family=Space+Mono:ital,wght@0,400;0,700;1,400&display=swap"

html_files = [f for f in os.listdir(base_dir) if f.endswith('.html')]

for filename in html_files:
    filepath = os.path.join(base_dir, filename)
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    updated = content.replace(old_font, new_font)
    # Also replace Orbitron font references in inline styles
    updated = updated.replace("font-family: 'Orbitron'", "font-family: 'Sora'")
    updated = updated.replace('font-family: "Orbitron"', 'font-family: "Sora"')
    updated = updated.replace("font-family:'Orbitron'", "font-family:'Sora'")
    
    if updated != content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(updated)
        print(f"Updated fonts in {filename}")
    else:
        print(f"No Orbitron found in {filename}")
