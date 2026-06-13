import os
import glob
import re

STATIC_DIR = "c:/Users/stali/mediops01/static"

medical_bg_html = """<body>
    <div class="medical-bg">
        <i class="fa-solid fa-pills med-icon med-icon-1"></i>
        <i class="fa-solid fa-dna med-icon med-icon-2"></i>
        <i class="fa-solid fa-stethoscope med-icon med-icon-3"></i>
        <i class="fa-solid fa-heart-pulse med-icon med-icon-4"></i>
        <i class="fa-solid fa-syringe med-icon med-icon-5"></i>
        <i class="fa-solid fa-briefcase-medical med-icon med-icon-6"></i>
    </div>"""

html_files = glob.glob(os.path.join(STATIC_DIR, "*.html"))

for filepath in html_files:
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        
    original = content
    
    # Check if the HTML is missing
    if '<div class="medical-bg">' not in content:
        # We need to replace the exact <body> tag, or <body class="..."> tag
        # But earlier I just replaced "<body>"
        content = content.replace("<body>", medical_bg_html)
        
    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Fixed {os.path.basename(filepath)}")
    else:
        print(f"Already correct: {os.path.basename(filepath)}")

print("Medical HTML injection complete.")
