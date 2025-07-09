import os
import re

# Folder with named skill images
skill_icon_folder = "skill_icons"

# Extract Skill IDs from file names like: [1234] - Skill Name.jpg / .png
existing_ids = set()
pattern = re.compile(r"\[(\d+)\]")

for file in os.listdir(skill_icon_folder):
    match = pattern.search(file)
    if match:
        skill_id = int(match.group(1))
        existing_ids.add(skill_id)

# Full skill ID range
all_ids = set(range(0, 3432))  # 0 to 3431 inclusive

# Determine missing IDs
missing_ids = sorted(all_ids - existing_ids)

# Output
print(f"Missing {len(missing_ids)} skill IDs:")
print(missing_ids)
