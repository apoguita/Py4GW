import os
import shutil
import requests
from bs4 import BeautifulSoup

# Paths
highres_folder = "skill_icons"
lowres_folder = "gw_skills_png_32x32"

# URL with skill list
wiki_url = "https://wiki.guildwars.com/wiki/Skill_template_format/Skill_list"

# Download and parse the skill list page
response = requests.get(wiki_url)
soup = BeautifulSoup(response.text, "html.parser")

# Parse skill table
rows = soup.select("table.sortable tbody tr")
skills = {}

for row in rows:
    cols = row.find_all("td")
    if len(cols) < 2:
        continue
    skill_id = cols[0].text.strip()
    skill_name = cols[1].text.strip()
    if not skill_id.isdigit():
        continue
    skills[int(skill_id)] = skill_name

# Sanitize file names
def sanitize(name):
    name = name.replace("/", "_").replace("\\", "_")
    name = name.replace(":", "_").replace("?", "").replace("\"", "").replace("*", "")
    name = name.replace("<", "").replace(">", "").replace("|", "")
    return name

# Ensure folders exist
os.makedirs(highres_folder, exist_ok=True)

# Process
for skill_id, skill_name in skills.items():
    expected_jpg = f"[{skill_id}] - {sanitize(skill_name)}.jpg"
    expected_png = f"[{skill_id}] - {sanitize(skill_name)}.png"

    dest_path_jpg = os.path.join(highres_folder, expected_jpg)
    dest_path_png = os.path.join(highres_folder, expected_png)

    # Skip if either already exists
    if os.path.exists(dest_path_jpg) or os.path.exists(dest_path_png):
        continue

    lowres_file = os.path.join(lowres_folder, f"{skill_id}.png")
    if os.path.exists(lowres_file):
        print(f"Copying fallback for skill ID {skill_id}: {skill_name}")
        shutil.copyfile(lowres_file, dest_path_png)

print("Finished processing all missing skills.")
