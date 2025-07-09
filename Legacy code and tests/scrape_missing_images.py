import os
import requests
from bs4 import BeautifulSoup

INPUT_FILE = "links_of_missing_images.txt"
OUTPUT_DIR = "Textures/Item Models"
LOG_FILE = "missing_items_log.txt"

os.makedirs(OUTPUT_DIR, exist_ok=True)
missing = []

with open(INPUT_FILE, encoding="utf-8") as f:
    lines = [line.strip() for line in f if line.strip()]

for line in lines:
    try:
        model_id, value = line.split(",", 1)
        model_id = model_id.strip()
        value = value.strip()

        if value.startswith("http"):
            name = value.split("/")[-1]
            url = value
        else:
            name = value.replace(" ", "_")
            url = f"https://wiki.guildwars.com/wiki/{name}"

        filename_base = f"[{model_id}] - {name.replace('_', ' ')}"

        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        img = soup.find("img")

        if not img or "src" not in img.attrs:
            missing.append(f"{model_id},{value}")
            continue

        img_url = img["src"]
        if img_url.startswith("/"):
            img_url = "https://wiki.guildwars.com" + img_url

        ext = os.path.splitext(img_url)[1].split("?")[0]
        img_data = requests.get(img_url, timeout=10).content

        with open(os.path.join(OUTPUT_DIR, f"{filename_base}{ext}"), "wb") as out:
            out.write(img_data)

    except Exception:
        missing.append(f"{model_id},{value}")

with open(LOG_FILE, "w", encoding="utf-8") as log:
    log.write("\n".join(missing))
