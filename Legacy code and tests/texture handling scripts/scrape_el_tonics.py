import os
import requests
from bs4 import BeautifulSoup

OUTPUT_FOLDER = os.path.join("Textures", "Item Models")
MISSING_LOG = "missing_el_tonics.txt"

os.makedirs(OUTPUT_FOLDER, exist_ok=True)

el_tonics = [
    ("30647", "El_Abominable_Tonic"),
    ("30625", "El_Abyssal_Tonic"),
    ("36428", "El_Acolyte_Jin_Tonic"),
    ("36429", "El_Acolyte_Sousuke_Tonic"),
    ("36447", "El_Anton_Tonic"),
    ("30635", "El_Automatonic_Tonic"),
    ("36658", "El_Avatar_Of_Balthazar_Tonic"),
    ("36661", "El_Balthazars_Champion_Tonic"),
    ("30639", "El_Boreal_Tonic"),
    ("30627", "El_Cerebral_Tonic"),
    ("31143", "El_Cottontail_Tonic"),
    ("31147", "El_Crate_Of_Fireworks"),
    ("36457", "El_Destroyer_Tonic"),
    ("36426", "El_Dunkoro_Tonic"),
    ("36664", "El_Flame_Sentinel_Tonic"),
    ("30641", "El_Gelatinous_Tonic"),
    ("36660", "El_Ghostly_Hero_Tonic"),
    ("36663", "El_Ghostly_Priest_Tonic"),
    ("36434", "El_Goren_Tonic"),
    ("36652", "El_Guild_Lord_Tonic"),
    ("36442", "El_Gwen_Tonic"),
    ("36448", "El_Hayda_Tonic"),
    ("32850", "El_Henchman_Tonic"),
    ("36455", "El_Jora_Tonic"),
    ("36444", "El_Kahmu_Tonic"),
    ("36450", "El_Keiran_Thackeray_Tonic"),
    ("36425", "El_Koss_Tonic"),
    ("36461", "El_Kuunavang_Tonic"),
    ("36449", "El_Livia_Tonic"),
    ("30629", "El_Macabre_Tonic"),
    ("36432", "El_Magrid_The_Sly_Tonic"),
    ("36456", "El_Margonite_Tonic"),
    ("36433", "El_Master_Of_Whispers_Tonic"),
    ("36427", "El_Melonni_Tonic"),
    ("36451", "El_Miku_Tonic"),
    ("31021", "El_Mischievious_Tonic"),
    ("36436", "El_Morgahn_Tonic"),
    ("36452", "El_Mox_Tonic"),
    ("36435", "El_Norgu_Tonic"),
    ("36440", "El_Ogden_Stonehealer_Tonic"),
    ("36438", "El_Olias_Tonic"),
    ("30643", "El_Phantasmal_Tonic"),
    ("36659", "El_Priest_Of_Balthazar_Tonic"),
    ("36455", "El_Prince_Rurik_Tonic"),
    ("36446", "El_Pyre_Fiercehot_Tonic"),
    ("36458", "El_Queen_Salma_Tonic"),
    ("36437", "El_Razah_Tonic"),
    ("34156", "El_Reindeer_Tonic"),
    ("30633", "El_Searing_Tonic"),
    ("36453", "El_Shiro_Tonic"),
    ("30827", "El_Sinister_Automatonic_Tonic"),
    ("30637", "El_Skeletonic_Tonic"),
    ("36460", "El_Slightly_Mad_King_Tonic"),
    ("36430", "El_Tahlkora_Tonic"),
    ("23242", "El_Transmogrifier_Tonic"),
    ("30631", "El_Trapdoor_Tonic"),
    ("31173", "El_Unseen_Tonic"),
    ("36441", "El_Vekk_Tonic"),
    ("36443", "El_Xandra_Tonic"),
    ("29241", "El_Yuletide_Tonic"),
    ("36439", "El_Zenmai_Tonic"),
    ("36431", "El_Zhed_Shadowhoof_Tonic"),
]

def get_image_url(page_url):
    try:
        r = requests.get(page_url, timeout=10)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, 'html.parser')
        img = soup.find("img")
        return "https://wiki.guildwars.com" + img['src'] if img and img.get('src') else None
    except Exception:
        return None

def download(model_id, enum_name):
    page_suffix = enum_name.replace("El_", "")
    wiki_url = f"https://wiki.guildwars.com/wiki/Everlasting_{page_suffix}"
    image_url = get_image_url(wiki_url)

    if not image_url:
        print(f"[{model_id}] ❌ No image found: {wiki_url}")
        return False

    try:
        r = requests.get(wiki_url, timeout=10)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, 'html.parser')
        title_tag = soup.find("h1", id="firstHeading")
        wiki_title = title_tag.text.strip() if title_tag else enum_name.replace('_', ' ')
    except Exception:
        wiki_title = enum_name.replace('_', ' ')

    ext = os.path.splitext(image_url)[-1].split("?")[0]
    filename = f"[{model_id}] - {wiki_title}{ext}"
    path = os.path.join(OUTPUT_FOLDER, filename)

    try:
        img_data = requests.get(image_url, timeout=10).content
        with open(path, 'wb') as f:
            f.write(img_data)
        print(f"[{model_id}] ✅ {filename}")
        return True
    except Exception as e:
        print(f"[{model_id}] ❌ Download failed: {e}")
        return False


# Main loop
with open(MISSING_LOG, "w", encoding="utf-8") as log:
    for model_id, enum_name in el_tonics:
        success = download(model_id, enum_name)
        if not success:
            log.write(f"{model_id},{enum_name}\n")
