import requests
from bs4 import BeautifulSoup, NavigableString, Tag
from urllib.parse import urljoin
import json
import re

HEADERS = {'User-Agent': 'Mozilla/5.0'}
SKILL_LIST_URL = "https://wiki.guildwars.com/wiki/Skill_template_format/Skill_list"
MAX_SKILLS = 10  # First 10 for test

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
            href = urljoin("https://wiki.guildwars.com", link.get("href"))
            skills.append((skill_id, name, href))
            #if len(skills) >= MAX_SKILLS:
            #    break
        except ValueError:
            continue
    return skills

def extract_descriptions(soup):
    def format_text_with_ranges(element):
        """Returns text with [!x...y...z!] formatting for green bold spans, without duplication."""
        result = []
        skip = set()

        for item in element.descendants:
            if item in skip:
                continue

            if isinstance(item, Tag):
                if item.name == "span":
                    style = item.get("style", "")
                    if "color: green" in style and "font-weight: bold" in style:
                        text = item.get_text(strip=True)
                        result.append(f"[!{text}!]")  # Wrap range
                        skip.update(item.descendants)
                elif item.name == "br":
                    result.append("\n")
            elif isinstance(item, NavigableString):
                parent = item.parent
                if parent in skip:
                    continue
                text = str(item).strip()
                if text:
                    result.append(text)

        return " ".join(result).replace(" .", ".").replace("  ", " ")

    full_description = ""
    concise_description = ""

    for div in soup.find_all("div", class_="noexcerpt"):
        p_tag = div.find("p")
        if p_tag:
            full_description = format_text_with_ranges(p_tag)
            break

    for div in soup.find_all("div", class_="noexcerpt"):
        dl = div.find("dl")
        if not dl:
            continue
        dt = dl.find("dt")
        if dt and "Concise description" in dt.get_text():
            text_parts = []
            for sibling in dl.next_siblings:
                if isinstance(sibling, Tag):
                    raw = format_text_with_ranges(sibling)
                elif isinstance(sibling, NavigableString):
                    raw = str(sibling).strip()
                else:
                    continue
                # Apply fallback formatting in case green span didn't catch
                raw = re.sub(r'\b(\d+\.\.\.\d+(?:\.\.\.\d+)?)\b', r'[!\1!]', raw)
                text_parts.append(raw)
            concise_description = " ".join(part for part in text_parts if part).strip()
            break

    return full_description, concise_description

def extract_progression(soup):
    results = []

    for table in soup.find_all("table", class_="skill-progression"):
        rows = table.find_all("tr")
        if len(rows) < 2:
            continue

        # Step 1: Extract attribute and field names
        attr_cell = rows[1].find_all("td")[0]
        attr_div = attr_cell.find("div", class_="attr")
        attribute = attr_div.get_text(strip=True) if attr_div else "Unknown"

        field_divs = attr_cell.find_all("div", class_="var")
        field_names = [field.get_text(strip=True) for field in field_divs]

        # Step 2: Initialize dict for each field
        field_data = [
            {
                "attribute": attribute,
                "field": field_name,
                "values": {}
            }
            for field_name in field_names
        ]

        # Step 3: Extract values by column
        value_cell = rows[1].find_all("td")[1]  # the right-hand cell
        for column in value_cell.find_all("div", class_="column"):
            divs = column.find_all("div")
            if len(divs) < 2:
                continue

            try:
                level = int(divs[0].get_text(strip=True))
            except ValueError:
                continue

            values = [d.get_text(strip=True) for d in divs[1:]]
            for i, val in enumerate(values):
                if i < len(field_data):
                    field_data[i]["values"][level] = val

        results.extend(field_data)

    return results



def main():
    all_skills = {}
    skills = get_skill_list()

    for skill_id, name, url in skills:
        print(f"Processing [{skill_id}] {name}")
        res = requests.get(url, headers=HEADERS)
        soup = BeautifulSoup(res.text, 'html.parser')

        full_desc, concise_desc = extract_descriptions(soup)
        progression = extract_progression(soup)

        all_skills[skill_id] = {
            "name": name,
            "url": url,
            "desc_full": full_desc,
            "desc_concise": concise_desc,
            "progression": progression
        }

    with open("skills_output.json", "w", encoding="utf-8") as f:
        json.dump(all_skills, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    main()
