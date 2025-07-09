import json
import re
from collections import defaultdict
from pathlib import Path

# Paths
json_path = Path("loot_config.json")
enum_path = Path("modelids.txt")
output_path = Path("grouped_loot_output.py")

# Load modelid enum mapping
enum_lookup = {}
with enum_path.open(encoding="utf-8") as f:
    for line in f:
        if "=" in line:
            name, value = map(str.strip, line.split("=", 1))
            enum_lookup[name] = f"ModelID.{name}"

# Parse loot_config.json
with json_path.open(encoding="utf-8") as f:
    loot_data = json.load(f)

grouped_loot = defaultdict(lambda: defaultdict(list))

for entry in loot_data:
    model_id = entry.get("model_id")
    group = entry.get("group", "Unknown")
    subgroup = entry.get("subgroup", "Unknown")

    match = re.match(r"ModelID\.([A-Za-z0-9_]+)", model_id or "")
    if not match:
        continue
    enum_name = match.group(1)

    if enum_name in enum_lookup:
        grouped_loot[group][subgroup].append(enum_lookup[enum_name])

# Write output to Python file
with output_path.open("w", encoding="utf-8") as f:
    f.write("from ModelID import ModelID\n\n")
    f.write("grouped_loot = {\n")
    for group, subgroups in grouped_loot.items():
        f.write(f'    "{group}": {{\n')
        for subgroup, items in subgroups.items():
            f.write(f'        "{subgroup}": [\n')
            for item in items:
                f.write(f"            {item},\n")
            f.write("        ],\n")
        f.write("    },\n")
    f.write("}\n")
