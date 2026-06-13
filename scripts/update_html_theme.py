import os
import re

static_dir = r"c:\Users\stali\mediops01\static"

html_files = [f for f in os.listdir(static_dir) if f.endswith(".html")]

css_link = '    <link href="/static/cyberpunk-light.css" rel="stylesheet">\n'
js_link = '    <script src="/static/floating-med.js"></script>\n'

for filename in html_files:
    filepath = os.path.join(static_dir, filename)
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    
    # 1. Remove the old DARK MEDICAL CYBERPUNK CSS GUIDE block
    # It starts with /* DARK MEDICAL CYBERPUNK CSS GUIDE */ and ends with </style>
    # Wait, the block is inside <style> tags along with other styles possibly.
    # We should just remove the specific block or everything from /* DARK MEDICAL CYBERPUNK CSS GUIDE */ to </style>
    # In login.html, it's inside <style> but other non-dark styles are there too (like body animations).
    # Actually, the dark cyberpunk block replaces existing body styles.
    # Let's remove from /* DARK MEDICAL CYBERPUNK CSS GUIDE */ to the end of the style block.
    
    new_content = re.sub(r'/\* DARK MEDICAL CYBERPUNK CSS GUIDE \*/.*?(?=</style>)', '', content, flags=re.DOTALL)
    
    # Also some files might have <style> tags entirely devoted to it.
    # We can inject the CSS link right before </head>
    if '<link href="/static/cyberpunk-light.css"' not in new_content:
        new_content = new_content.replace('</head>', css_link + '</head>')
        
    # Inject the JS link right before </body>
    if '<script src="/static/floating-med.js"' not in new_content:
        new_content = new_content.replace('</body>', js_link + '</body>')

    # Remove dark tailwind classes if any
    new_content = new_content.replace('bg-slate-900', 'bg-slate-50')
    new_content = new_content.replace('text-white', 'text-slate-900')

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(new_content)
    
    print(f"Updated {filename}")
