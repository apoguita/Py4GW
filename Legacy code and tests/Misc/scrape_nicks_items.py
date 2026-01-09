import requests
from bs4 import BeautifulSoup
from datetime import datetime, date
from Model_enums import ModelID  # Adjust the import based on your project structure


def normalize_item_name(item_name: str) -> str:
    """
    Normalize item names from wiki to match ModelID enum style.
    Example: "Gold Crimson Skull Coin" -> "Gold_Crimson_Skull_Coin"
    """
    name = item_name.strip()
    name = name.replace("’", "'")  # handle odd apostrophes
    name = name.replace(" ", "_")  # spaces -> underscores
    name = name.replace("(", "").replace(")", "")  # drop brackets
    name = name.replace(",", "")  # drop commas
    # Singularize simple plurals (e.g., Scalps -> Scalp)
    if name.endswith("s") and not name.endswith("ss"):
        if name + "s" not in ModelID.__members__:
            name = name[:-1]
    return name


def scrape_nicholas_cycle():
    url = "https://wiki.guildwars.com/wiki/Nicholas_the_Traveler/Cycle"
    resp = requests.get(url)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")
    table = soup.find("table", {"class": "sortable"})
    if not table:
        raise ValueError("Could not find the sortable table on the page.")
    rows = table.find("tbody").find_all("tr")

    data = []
    for row in rows:
        cols = row.find_all("td")
        if not cols or len(cols) < 6:
            continue

        week_str = cols[0].get_text(strip=True)
        try:
            week_date = datetime.strptime(week_str, "%d %B %Y").date()
        except ValueError:
            continue

        item_link = cols[1].find("a")
        item_name = item_link.get_text(strip=True) if item_link else cols[1].get_text(strip=True)
        normalized_name = normalize_item_name(item_name)

        # Try to match with enum
        if hasattr(ModelID, normalized_name):
            model_id = getattr(ModelID, normalized_name)
        else:
            model_id = None

        location = cols[2].get_text(strip=True)
        region = cols[3].get_text(strip=True)
        campaign = cols[4].get_text(strip=True)

        map_link = cols[5].find("a")
        map_url = f"https://wiki.guildwars.com{map_link['href']}" if map_link else None

        entry = {
            "week": week_date,
            "item": item_name,
            "model_id": model_id,
            "location": location,
            "region": region,
            "campaign": campaign,
            "map_url": map_url,
        }
        data.append(entry)

    return data


def write_dict_file(data, filename="nicholas_cycle.py"):
    with open(filename, "w", encoding="utf-8") as f:
        f.write("#region NICHOLAS_CYCLE\n")
        f.write("from datetime import date\n")
        f.write("from modelid_file import ModelID\n\n")  # adjust filename
        f.write("NICHOLAS_CYCLE: list[dict] = [\n")
        for entry in data:
            f.write("    {\n")
            f.write(f"        \"week\": date({entry['week'].year}, {entry['week'].month}, {entry['week'].day}),\n")
            f.write(f"        \"item\": \"{entry['item']}\",\n")
            if entry["model_id"] is not None:
                f.write(f"        \"model_id\": ModelID.{normalize_item_name(entry['item'])},\n")
            else:
                f.write(f"        \"model_id\": None,\n")
            f.write(f"        \"location\": \"{entry['location']}\",\n")
            f.write(f"        \"region\": \"{entry['region']}\",\n")
            f.write(f"        \"campaign\": \"{entry['campaign']}\",\n")
            f.write(f"        \"map_url\": \"{entry['map_url']}\",\n")
            f.write("    },\n")
        f.write("]\n")
        f.write("#endregion\n")


if __name__ == "__main__":
    data = scrape_nicholas_cycle()
    write_dict_file(data)
    print(f"Scraped {len(data)} entries and wrote nicholas_cycle.py")
