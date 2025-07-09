import os
import re

ENUM_FILE = "modelids.txt"
TEXTURE_FOLDER = os.path.join("Textures", "Item Models")
OUTPUT_FILE = "missing_modelids_from_enum.txt"

# 1. Read all model IDs already scraped
existing_files = os.listdir(TEXTURE_FOLDER)
existing_modelids = {
    re.search(r"\[(\d+)\]", f).group(1) for f in existing_files if re.search(r"\[(\d+)\]", f)
}

# 2. Parse the enum
pattern = re.compile(r'^\s*(\w+)\s*=\s*(\d+)\s*$')
missing = []

with open(ENUM_FILE, "r", encoding="utf-8") as f:
    for line in f:
        match = pattern.match(line)
        if not match:
            continue
        name, modelid = match.groups()
        if modelid not in existing_modelids:
            missing.append((name, modelid))

# 3. Save missing list
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    for name, modelid in missing:
        f.write(f"{modelid},{name}\n")

print(f"✅ Done: {len(missing)} missing entries written to {OUTPUT_FILE}")
