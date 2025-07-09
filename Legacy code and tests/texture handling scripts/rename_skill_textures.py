import os
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import unquote

# === Configuration ===
IMAGE_FOLDER = "skill_icons"
IMAGE_EXTENSION = ".jpg"
SKILL_LIST_URL = "https://wiki.guildwars.com/wiki/Skill_template_format/Skill_list"

# === Step 1: Normalize names ===
def normalize_name(name: str) -> str:
    return re.sub(r'[^a-z0-9]', '', name.lower())

# === Step 2: Get skill ID -> name mapping ===
def get_skill_id_map():
    print("[+] Fetching skill list from wiki...")
    response = requests.get(SKILL_LIST_URL)
    soup = BeautifulSoup(response.text, "html.parser")

    skill_map = {}
    rows = soup.find_all("tr")[1:]  # Skip header row
    for row in rows:
        cols = row.find_all("td")
        if len(cols) < 2:
            continue
        try:
            skill_id = int(cols[0].text.strip())
            name_tag = cols[1].find("a")
            skill_name = name_tag.text.strip() if name_tag else cols[1].text.strip()
            skill_map[skill_name] = skill_id
        except Exception as e:
            print(f"[-] Failed to parse row: {e}")
    print(f"[+] Parsed {len(skill_map)} skills.")
    return skill_map

# === Step 3: Rename images ===
def rename_images(skill_map):
    print("[+] Processing images...")
    for file in os.listdir(IMAGE_FOLDER):
        if not file.lower().endswith(IMAGE_EXTENSION):
            continue
        original_path = os.path.join(IMAGE_FOLDER, file)
        raw_name = os.path.splitext(file)[0].replace("_(large)", "")
        raw_name = unquote(raw_name)

        normalized_file = normalize_name(raw_name)

        matched = [(k, v) for k, v in skill_map.items() if normalize_name(k) == normalized_file]
        if not matched:
            print(f"❌ Could not match: {file}")
            continue

        skill_name, skill_id = matched[0]
        new_filename = f"[{skill_id}] - {skill_name}{IMAGE_EXTENSION}"
        new_path = os.path.join(IMAGE_FOLDER, new_filename)

        try:
            os.rename(original_path, new_path)
            print(f"✅ Renamed: {file} -> {new_filename}")
        except Exception as e:
            print(f"❌ Rename failed for {file}: {e}")

# === Main ===
if __name__ == "__main__":
    if not os.path.exists(IMAGE_FOLDER):
        print(f"[-] Folder not found: {IMAGE_FOLDER}")
        exit(1)

    skill_map = get_skill_id_map()
    rename_images(skill_map)
