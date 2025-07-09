import json

# Load the icons.json file (download it from the official Font Awesome repo first)
with open('icons.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Collect only 'free' solid icons (adjust if you need other styles like 'brands' or 'regular')
defs = []
for name, info in data.items():
    if 'solid' in info.get('free', []):
        key = name.upper().replace('-', '_')
        defs.append((key, info['unicode']))

# Sort alphabetically by icon name
defs.sort(key=lambda x: x[0])

# Output to file
with open('fontawesome_icon_defs.py', 'w', encoding='utf-8') as f:
    for key, uni in defs:
        f.write(f"ICON_{key} = '\\u{uni.zfill(4)}'\n")
