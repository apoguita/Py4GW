import os
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import unquote

BASE_URL = "https://wiki.guildwars.com"
GALLERY_URL = BASE_URL + "/wiki/Gallery_of_high_resolution_skill_icons/large"
IMAGE_ROOT = BASE_URL + "/images"
OUTPUT_DIR = "./skill_icons"

os.makedirs(OUTPUT_DIR, exist_ok=True)

response = requests.get(GALLERY_URL)
soup = BeautifulSoup(response.text, "html.parser")

count = 0

for img_tag in soup.find_all("img"):
    src = img_tag.get("src", "")
    if "/thumb/" not in src:
        continue
    # Extract full path by stripping everything after filename
    match = re.match(r"/images/thumb/([^/]+)/([^/]+)/(.*?)(?:/|$)", src)
    if not match:
        continue

    dir1, dir2, filename = match.groups()
    full_img_url = f"{IMAGE_ROOT}/{dir1}/{dir2}/{filename}"
    full_img_url = unquote(full_img_url)

    # Download the image
    img_data = requests.get(full_img_url).content
    save_path = os.path.join(OUTPUT_DIR, filename)

    with open(save_path, "wb") as f:
        f.write(img_data)
        print(f"✅ Downloaded: {filename}")
        count += 1

print(f"\nDone! {count} images saved to: {OUTPUT_DIR}")
