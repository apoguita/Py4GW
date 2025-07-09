import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import unquote
from pathlib import Path

SKILL_LIST_URL = "https://wiki.guildwars.com/wiki/Skill_template_format/Skill_list"
OUTPUT_DIR = "skill_icons"
EXISTING_IDS = {int(f.name.split("]")[0][1:]) for f in Path(OUTPUT_DIR).glob("[*] - *.jpg")}
HEADERS = {'User-Agent': 'Mozilla/5.0'}

def get_skill_list():
    response = requests.get(SKILL_LIST_URL, headers=HEADERS)
    soup = BeautifulSoup(response.text, 'html.parser')
    table = soup.find("table")
    skills = []
    for row in table.find_all("tr")[1:]:
        cols = row.find_all("td")
        if len(cols) < 2:
            continue
        try:
            skill_id = int(cols[0].text.strip())
            link = cols[1].find("a")
            if not link:
                continue
            name = link.get("title").strip()
            href = "https://wiki.guildwars.com" + link.get("href")
            skills.append((skill_id, name, href))
        except ValueError:
            continue
    return skills

def get_image_url_from_skill_page(skill_url):
    res = requests.get(skill_url, headers=HEADERS)
    soup = BeautifulSoup(res.text, 'html.parser')
    image_div = soup.find("div", class_="skill-image")
    if not image_div:
        return None
    img_tag = image_div.find("img")
    if not img_tag:
        return None
    return "https://wiki.guildwars.com" + img_tag.get("src")

def sanitize_filename(name):
    return name.replace(":", "").replace("?", "").replace("\"", "").replace("/", "_").replace("\\", "_").replace("*", "").replace("<", "").replace(">", "").replace("|", "")

def download_image(url, filename):
    r = requests.get(url, headers=HEADERS)
    if r.status_code == 200:
        with open(filename, "wb") as f:
            f.write(r.content)

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    skills = get_skill_list()
    print(f"Total skills found: {len(skills)}")
    for skill_id, name, url in skills:
        if skill_id in EXISTING_IDS:
            continue
        print(f"Downloading {skill_id} - {name}")
        img_url = get_image_url_from_skill_page(url)
        if img_url:
            safe_name = sanitize_filename(name)
            filename = os.path.join(OUTPUT_DIR, f"[{skill_id}] - {safe_name}.jpg")
            download_image(img_url, filename)
        else:
            print(f"Image not found for {skill_id} - {name}")

if __name__ == "__main__":
    main()
