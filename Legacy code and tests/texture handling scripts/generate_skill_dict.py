import os
import re

ICON_FOLDER = "skill_icons"
OUTPUT_FILE = "skill_icon_map.py"
pattern = re.compile(r"\[(\d+)\]\s*-\s*(.+)\.jpg")

skill_dict = {}

for filename in os.listdir(ICON_FOLDER):
    match = pattern.match(filename)
    if match:
        skill_id = int(match.group(1))
        skill_dict[skill_id] = filename

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    f.write("skill_icon_map = {\n")
    for skill_id in sorted(skill_dict):
        f.write(f"    {skill_id}: {repr(skill_dict[skill_id])},\n")
    f.write("}\n")
