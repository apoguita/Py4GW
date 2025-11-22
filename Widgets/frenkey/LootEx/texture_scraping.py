import difflib
import os
import re
import shutil
from typing import Optional
from urllib import parse
from bs4 import BeautifulSoup, Tag
from bs4.element import NavigableString

## Current folder path \\ data \\ scraped_items.json
ITEM_FILE = "C:\\Users\\lasse\\OneDrive\\Programmieren\\Frenkey\\Guild Wars\\Py4GW\\Widgets\\frenkey\\LootEx\\data\\scraped_items.json"
WIKI_FOLDER_PATH = "C:\\Users\\lasse\\OneDrive\\Programmieren\\Frenkey\\Guild Wars\\gw_wiki_mirror\\wiki.guildwars.com\\wiki"
IMAGES_PATH = "C:\\Users\\lasse\\OneDrive\\Programmieren\\Frenkey\\Guild Wars\\gw_wiki_mirror\\wiki.guildwars.com\\images"
BASE_PATH = "C:\\Users\\lasse\\OneDrive\\Programmieren\\Frenkey\\Guild Wars\\gw_wiki_mirror\\wiki.guildwars.com"
LOOKUP_FOLDER = "C:\\Users\\lasse\\OneDrive\\Programmieren\\Frenkey\\Guild Wars\\wiki_lookup"
    
item_types = [
    "Salvage",
    "Axe",
    "Bag",
    "Boots",
    "Bow",
    "Bundle",
    "Chestpiece",
    "Rune Mod",
    "Usable",
    "Dye",
    "Material",
    "Offhand",
    "Gloves",
    "Hammer",
    "Headpiece",
    "CC Shards", #??
    "Key",
    "Leggings",
    "Gold Coin",
    "Quest Item",
    "Wand",
    "Shield",
    "Staff",
    "Sword",
    "Kit",
    "Trophy",
    "Scroll",
    "Daggers",
    "Present",
    "Minipet",
    "Scythe",
    "Spear",
    "Weapon",
    "Martial Weapon",
    "Offhand Or Shield",
    "Equippable Item",
    "Spellcasting Weapon",
    "Storybook",
    "Costume",
    "Costume Headpiece",
    # "Unknown"
    
    "Focus item",
    "Consumable",
    "Tonic",
    "Alcohol",
    "Polymock piece",
    "Summoning stone",
    "Dagger",
    "Rune",
    "Container",
    "Sweet",
    "Miniature",
    "Caster",
    "Martial",
    "Firework",
    "upgrade",
    "component",
    "Festive item",
    "item",
    "insignia"
]

item_types = [it.lower() for it in item_types]
    
class SalvageResult:
    def __init__(self, name: str, min_amount: int = -1, max_amount: int = -1, amount: int = -1):
        self.name = name
        self.min_amount = min_amount
        self.max_amount = max_amount
        self.amount = amount        
    
    def to_json(self) -> dict:
        return {
            "name": self.name,
            "min_amount": self.min_amount,
            "max_amount": self.max_amount,
            "amount": self.amount
        }
        
    @staticmethod
    def from_json(data: dict) -> 'SalvageResult':
        return SalvageResult(
            name=data["name"],
            min_amount=data.get("min_amount", -1),
            max_amount=data.get("max_amount", -1),
            amount=data.get("amount", -1)
        )

class Item:
    def __init__(self, name: str):
        self.name = name
        self.inventory_icon_url: Optional[str] = None
        self.common_salvage: list[SalvageResult] = []
        self.rare_salvage: list[SalvageResult] = []
        self.item_type: Optional[str] = None
        self.acquisition_tree : Optional[list[dict]] = None
        self.description : Optional[str] = None
        self._inventory_icon_exists : Optional[bool] = None
    
    @property
    def IconPath(self) -> str:
        if self.inventory_icon_url is None:
            return ""
        
        relative_file_path_from_url = self.inventory_icon_url.lstrip("/\\").replace("/", "\\")
        path = os.path.join("C:\\Users\\lasse\\OneDrive\\Programmieren\\Frenkey\\Guild Wars\\gw_wiki_mirror\\wiki.guildwars.com", relative_file_path_from_url)
        
        return path
    
    @property
    def IconExists(self) -> bool:
        if self._inventory_icon_exists is None:
            relative_file_path_from_url = self.inventory_icon_url.lstrip("/\\").replace("/", "\\") if self.inventory_icon_url else None 
            path = os.path.join("C:\\Users\\lasse\\OneDrive\\Programmieren\\Frenkey\\Guild Wars\\gw_wiki_mirror\\wiki.guildwars.com", relative_file_path_from_url) if relative_file_path_from_url else None
            
            self._inventory_icon_exists = os.path.exists(path) if path else False
        
        return bool(self._inventory_icon_exists)
        
    def to_json(self) -> dict:
        return {
            "name": self.name,
            "inventory_icon_url": self.inventory_icon_url,
            "common_salvage": [s.to_json() for s in self.common_salvage],
            "rare_salvage": [s.to_json() for s in self.rare_salvage],
            "item_type": self.item_type,
            "acquisition_tree": self.acquisition_tree,
            "description": self.description
        }        
    
    @staticmethod
    def from_json(data: dict) -> 'Item':
        item = Item(data["name"])
        item.inventory_icon_url = data.get("inventory_icon_url")
        item.common_salvage = [SalvageResult.from_json(s) for s in data.get("common_salvage", [])]
        item.rare_salvage = [SalvageResult.from_json(s) for s in data.get("rare_salvage", [])]
        item.item_type = data.get("item_type")
        item.acquisition_tree = data.get("acquisition_tree")
        item.description = data.get("description")
        
        return item

@staticmethod
def string_similarity(a: str, b: str) -> float:
    """
    Returns similarity ratio between two strings (0.0 to 1.0).
    """
    return difflib.SequenceMatcher(None, a.lower(), b.lower()).ratio()

@staticmethod
def get_best_match(query: str, candidates: list[str], min_score: float = 0.85) -> Optional[str]:
    """
    Returns the best matching string from candidates with a similarity above min_score.
    
    Args:
        query (str): the input string to match.
        candidates (list[str]): list of strings to search for a match.
        min_score (float): minimum similarity required (0.0 to 1.0).

    Returns:
        Optional[str]: best match string, or None if none above threshold.
    """
    best = None
    best_score = 0.0
    
    for candidate in candidates:
        score = string_similarity(query, candidate)
        if score > best_score:
            best_score = score
            best = candidate

    return best if best_score >= min_score else None

@staticmethod
def get_materials(td) -> list[SalvageResult]:
    materials : list[SalvageResult] = []
    if not td:
        return materials

    tokens = list(td.children)
    current_amount = None
                
    for token in tokens:
        if isinstance(token, str):
            # Handle amount strings: "1-5", "4", etc.
            stripped = token.strip()
            if stripped:
                range_match = re.match(r"^(\d+)\s*-\s*(\d+)$", stripped)
                single_match = re.match(r"^(\d+)$", stripped)
                if range_match:
                    current_amount = {
                        "min": int(range_match.group(1)),
                        "max": int(range_match.group(2))
                    }
                elif single_match:
                    current_amount = {
                        "min": int(single_match.group(1)),
                        "max": int(single_match.group(1))
                    }
        elif token.name == "a":
            material_name = token.get("title", token.get_text(strip=True))
            entry = {
                "name": material_name,
                "min": -1,
                "max": -1
            }
            
            if current_amount:
                entry["min"] = current_amount["min"]
                entry["max"] = current_amount["max"]
                current_amount = None
                
            salvage_result = SalvageResult(
                name=material_name,
                min_amount=entry.get("min", -1) if entry.get("min") != entry.get("max") else -1,
                max_amount=entry.get("max", -1) if entry.get("min") != entry.get("max") else -1,
                amount=entry.get("min", -1) if entry.get("min") == entry.get("max") else -1
            )
            materials.append(salvage_result)
            
                
    return materials

@staticmethod
def get_aquisition(soup: BeautifulSoup) -> str:
     # Locate <h2>Acquisition</h2>
    acquisition_header = soup.find(
        lambda tag: tag.name == "h2" and tag.find("span", {"id": "Acquisition"})
    )
    if acquisition_header is None:
        return ""

    acquisition_nodes = []
    for sibling in acquisition_header.find_next_siblings():
        # Acquisition section ends at the next H2
        if sibling.name == "h2":
            break
        acquisition_nodes.append(sibling)

    # Recursive walker to flatten lists
    def walk(node, result):
        # Handle link-only content
        if node.name == "a":
            text = node.get_text(strip=True)
            if text:
                result.append(text)
            return

        # <dt> sections (campaign names like "Core", "Eye of the North")
        if node.name == "dt":
            text = node.get_text(" ", strip=True)
            if text:
                result.append(text)
            return

        # <li> entries (the main list entries)
        if node.name == "li":
            text = node.get_text(" ", strip=True)
            if text:
                result.append(text)
            # Also inspect children for nested lists
            for child in node.children:
                if hasattr(child, "name"):
                    walk(child, result)
            return

        # <ul> or <dl>
        if node.name in ["ul", "dl"]:
            for child in node.children:
                if hasattr(child, "name"):
                    walk(child, result)
            return

        # Other tags: walk deeper
        for child in getattr(node, "children", []):
            if hasattr(child, "name") or child.strip():
                walk(child, result)

    flat_entries = []
    for n in acquisition_nodes:
        walk(n, flat_entries)

    # Remove duplicates while preserving order
    seen = set()
    clean = []
    for entry in flat_entries:
        if entry not in seen:
            clean.append(entry)
            seen.add(entry)

    return "\n".join(clean)


def text_with_linebreaks(node):
    """
    Convert a tag or node to text while preserving <br> as '\n'.
    """
    # Create a copy so we don't modify the original
    for br in node.find_all("br"):
        br.replace_with("\n")
    text = node.get_text(" ", strip=True)
    # Now collapse spaces but keep \n
    parts = [p.strip() for p in text.split("\n")]
    return "\n".join([p for p in parts if p != ""])

def extract_acquisition_section_nodes(soup):
    """
    Return list of nodes (Tags) that belong to the Acquisition section.
    """
    # Find <h2> whose span id is Acquisition (exact)
    acquisition_h2 = None
    for h2 in soup.find_all(["h2", "h3"]):
        span = h2.find("span", {"id": "Acquisition"})
        if span:
            acquisition_h2 = h2
            break
    if not acquisition_h2:
        return []

    nodes = []
    for sib in acquisition_h2.find_next_siblings():
        if isinstance(sib, Tag) and sib.name in ("h2", "h1"):
            break
        # Only keep tags that contain data (ul, dl, p, etc.)
        if isinstance(sib, Tag):
            # Skip empty or purely edit tags
            if sib.name == "div" and not sib.get_text(strip=True):
                continue
            nodes.append(sib)
    return nodes

def get_label_from_li(li_tag):
    """
    Produce a label for an <li> by taking the first child(s) that are not the nested <ul>.
    Keeps inline links and text. Strips trailing ":" and whitespace.
    """
    parts = []
    for child in li_tag.contents:
        if isinstance(child, Tag) and child.name == "ul":
            break
        if isinstance(child, NavigableString):
            text = child.strip()
            if text:
                parts.append(text)
        elif isinstance(child, Tag):
            # if it's <a>, <b>, etc. include its text
            if child.name == "br":
                parts.append("\n")
            else:
                t = child.get_text(" ", strip=True)
                if t:
                    parts.append(t)
    label = " ".join([p for p in (s.replace("\n", " ").strip() for s in parts) if p])
    return label.rstrip(":").strip()

def parse_ul(ul_tag):
    """
    Parse a <ul> into a list of nodes [{'name':..., 'children':[...]}]
    """
    result = []
    for li in [li for li in ul_tag.find_all("li", recursive=False)]:
        name = get_label_from_li(li)
        # find direct child <ul> (only immediate nested uls)
        child_ul = None
        for child in li.find_all(recursive=False):
            if child.name == "ul":
                child_ul = child
                break
        children = parse_ul(child_ul) if child_ul else []
        # If label empty but children exist, we may want to lift children up.
        node = {"name": name if name else None, "children": children}
        result.append(node)
    return result

def parse_dl(dl_tag):
    """
    Parse a <dl> into a list of nodes where <dt> are 'name' and following <dd> or nested lists are children.
    Many wiki pages use <dl><dt>Campaign</dt></dl> followed by <ul>.
    This function will convert <dt> into nodes; callers should look at surrounding nodes (ul) for their children.
    """
    nodes = []
    for dt in dl_tag.find_all("dt", recursive=False):
        name = dt.get_text(" ", strip=True)
        nodes.append({"name": name, "children": []})
    return nodes

def build_acquisition_tree(nodes):
    """
    nodes: list of Tag objects that belong to the Acquisition section in order.
    Return a list of ordered tree nodes preserving structure.
    Strategy:
    - Walk through nodes sequentially.
    - When we see a <dl> with <dt>, often the following <ul> contains the children for those dt entries.
    - When we see a <ul> alone, parse directly.
    - Handles nested/mixed patterns.
    """
    try:
        out = []
        i = 0
        n = len(nodes)
        while i < n:
            node = nodes[i]
            if node.name == "dl":
                # parse dt entries, then check next node for a <ul> that contains children
                dt_nodes = parse_dl(node)
                # look ahead for a following <ul> or series of <ul> that belong to these dt entries
                j = i + 1
                # collect subsequent uls until a non-ul/dl/p appears or next h2
                following_uls = []
                while j < n and nodes[j].name in ("ul", "dl"):
                    if nodes[j].name == "ul":
                        following_uls.append(nodes[j])
                    elif nodes[j].name == "dl":
                        # nested dl -> treat it as separate; break to let outer loop handle
                        break
                    j += 1
                # If the number of dt == number of uls, pair them; else if there's one ul, attach it to all dt entries
                if following_uls:
                    if len(dt_nodes) == len(following_uls):
                        paired = []
                        for dt_node, ul in zip(dt_nodes, following_uls):
                            dt_node["children"] = parse_ul(ul)
                            paired.append(dt_node)
                        out.extend(paired)
                    else:
                        if len(following_uls) > 0 and len(dt_nodes) > 1:                        
                            # Attach the first ul to the first dt, or attach the single ul to each dt if reasonable.
                            ul = following_uls[0]
                            # Heuristic: if only one ul, and dt_nodes > 1 -> attach whole ul parsed as children under first dt
                            dt_nodes[0]["children"] = parse_ul(ul)
                            out.extend(dt_nodes)
                            
                    # advance i to j
                    i = j
                    continue
                else:
                    # no following ul: keep dt nodes without children
                    out.extend(dt_nodes)
                    i += 1
                    continue

            elif node.name == "ul":
                parsed = parse_ul(node)
                out.extend(parsed)
                i += 1
                continue

            elif node.name == "p":
                # sometimes a paragraph indicates a single acquisition note (e.g., "Dropped by X" or "Sold by Y")
                text = text_with_linebreaks(BeautifulSoup(str(node), "html.parser"))
                if text:
                    out.append({"name": text, "children": []})
                i += 1
                continue

            else:
                # any other tag: try to extract plain text; if it contains a <ul> inside, parse that
                inner_ul = node.find("ul", recursive=False)
                if inner_ul:
                    parsed = parse_ul(inner_ul)
                    out.extend(parsed)
                else:
                    text = node.get_text(" ", strip=True)
                    if text:
                        out.append({"name": text, "children": []})
                i += 1
                continue

        # Clean up nodes that have name None but children -> lift children up or keep as-is
        cleaned = []
        for item in out:
            if item.get("name") in (None, "") and item.get("children"):
                # lift children up to preserve order but avoid anonymous nodes
                cleaned.extend(item["children"])
            else:
                cleaned.append(item)
        return cleaned
    except Exception as e:
        print("Error building acquisition tree:", e)
        return []

unknown_item_types : list[str] = []
@staticmethod
def scrape_info_from_wiki(path: str) -> Optional[Item]:
    with open(path, 'r', encoding='utf-8') as file:
        html_text = file.read()
    
    soup = BeautifulSoup(html_text, 'html.parser')

    info_table = soup.find('table')
    item : Optional[Item] = None
    has_rarity = False
    has_stackable = False
    has_attributes = False

    if info_table is None:
        return None

    if info_table:
        rows = info_table.find_all('tr')

        for row in rows:
            th = row.find('th')
            
            if th:
                if 'colspan' in th.attrs:
                    item_name = th.get_text(strip=True)
                    item = Item(item_name)
                    
                if item is None:
                    continue
                
                has_rarity |= th.find('a', string="Rarity") is not None
                has_stackable |= th.find('a', string="Stackable") is not None
                
                has_attributes |= th.find('a', string="Attribute requirement(s)") is not None
                has_attributes |= th.find('a', string="Attribute requirement") is not None
                has_attributes |= th.find('a', string="Attributes") is not None
                has_attributes |= th.find('a', string="Attribute") is not None
                    
                
                if th.find('a', string="Common salvage"):
                    td = row.find('td')

                    #<td>4-5 <a href="/wiki/Granite_Slab" title="Granite Slab">Granite Slabs</a><br>1-49 <a href="/wiki/Pile_of_Glittering_Dust" title="Pile of Glittering Dust">Piles of Glittering Dust</a></td>    
                    if td:
                        item.common_salvage = get_materials(td)

                if th.find('a', string="Rare salvage"):
                    td = row.find('td')

                    if td:
                        item.rare_salvage = get_materials(td)


                if "Type" in th.get_text():
                    td = row.find('td')
                    
                    if td:
                        text = td.get_text(strip=True)
                        lower_text = text.lower()
                        
                        if any(it in lower_text for it in item_types):
                            item.item_type = text
                        else:
                            if lower_text not in unknown_item_types:
                                unknown_item_types.append(lower_text)
                                
                            
                if th.find('a', string="Inventory icon"):
                    td = row.find('td')     

                    if td:
                        # Extract the image URL
                        img = td.find('img')
                        if img and 'src' in img.attrs:
                            item.inventory_icon_url = img['src'].lstrip("/\\").replace("/", "\\")
            
                    
            td = row.find("td", attrs={"colspan": "2", "align": "center"})
            if td is not None:                
                a = td.find("a", class_="image")
                
                if a is not None:
                    img = a.find("img")
                    
                    if img is not None:
                        if item.inventory_icon_url is None or img['src'].lower().endswith('.png') and (not item.inventory_icon_url.lower().endswith('.png') or (img['width'] == '64' and img['height'] == '64')):
                            item.inventory_icon_url = img['src'].lstrip("/\\").replace("/", "\\")
                        
        if item is None:
            return None
        
        ## Get the description from the first paragraph after the infobox table
        description = ""
        def extract_description_with_linebreaks(html_text: str) -> str:
            soup = BeautifulSoup(html_text, "html.parser")
            info_table = soup.find("table")
            if not info_table:
                return ""

            # Find the first paragraph after the table
            next_node = info_table.find_next_sibling()
            while next_node and next_node.name != "p":
                next_node = next_node.find_next_sibling()

            if not next_node:
                return ""

            # Extract text with line breaks for <br> tags
            description_parts = []
            for elem in next_node.descendants:
                if isinstance(elem, NavigableString):
                    description_parts.append(str(elem))
                elif elem.name == "br":
                    description_parts.append("\n")

            return "".join(description_parts).strip()
                            
        if item and (item.item_type or (item.common_salvage or item.rare_salvage) or (has_stackable and has_rarity)):           
            # item.inventory_icon_exists = os.path.exists(os.path.join(BASE_PATH, item.inventory_icon_url)) if isinstance(item.inventory_icon_url, str) else False 
                
            acq_nodes = extract_acquisition_section_nodes(soup)
            item.acquisition_tree = build_acquisition_tree(acq_nodes)
            item.description = extract_description_with_linebreaks(html_text)
            
            return item
    
    return None
                   
@staticmethod            
def get_image_name(url: str) -> str:
    # Extract the last part of the URL (the filename)
    last_part = url.rsplit('/', 1)[-1]

    # Remove "File:" prefix if present
    last_part = last_part.replace("File:", "")

    # Remove px size prefix like "134px-"
    last_part = re.sub(r'^\d+px-', '', last_part)
    last_part = last_part.replace("%22", "")  # Remove URL-encoded quotes

    # Decode URL-encoded characters
    decoded = parse.unquote(last_part)

    decoded = decoded.replace("_", " ")  # Replace spaces with underscores

    # Allow characters valid on most filesystems: keep letters, numbers, spaces, underscores,
    # dashes, apostrophes, parentheses, and periods
    # Replace only truly invalid characters with underscore
    sanitized = re.sub(r'[<>:"/\\|?*\x00-\x1F]', '_', decoded)

    # Replace multiple underscores with one (optional cleanup)
    sanitized = re.sub(r'_+', '_', sanitized)

    # Strip leading/trailing spaces/underscores
    return sanitized.strip(" _")


illegal_name_starters = [
    "Category%3",
    "File%3",
    "Gallery",
    "Guild%3",
    "GWW%3",
    "List_",
    "Talk%3",
    "User%3",
]

##Load existing items
import json


items : dict[str, Item] = {}

def load_items() -> dict[str, Item]:
    global ITEM_FILE
    
    if os.path.exists(ITEM_FILE):
        with open(ITEM_FILE, 'r', encoding='utf-8') as f:
            item_data = json.load(f)
        
        items = {name: Item.from_json(data) for name, data in item_data.items()}
        return items
    
    return {}

def save_items():
    global items
    
    ## Save updated items
    with open(ITEM_FILE, 'w', encoding='utf-8') as f:
        item_data = {name: item.to_json() for name, item in items.items()}
        json.dump(item_data, f, indent=4, ensure_ascii=False)

def get_items():
    count = 0

    for filename in os.listdir(WIKI_FOLDER_PATH):
        if filename.endswith(".html"):
            ## Skip illegal names
            if any(filename.startswith(starter) for starter in illegal_name_starters):
                continue
            
            item_name = filename[:-5]  # Remove .html extension
            file_path = os.path.join(WIKI_FOLDER_PATH, filename)
            
            # print(f"Scraping item: {item_name} from {file_path}")
            
            scraped_item = scrape_info_from_wiki(file_path)
            
            if scraped_item:
                items[item_name] = scraped_item
                print(f"Scraped data for item: {scraped_item.name}")
                    
                count += 1
                if count % 10 == 0:
                    print(f"Processed {count} items so far...")
                    save_items()
                    
            # else:
            #     print(f"No data scraped for item: {item_name}")  
            
def update_items():
    count = 0
    
    for item_name in list(items.keys()):
        filename = item_name + ".html"
        file_path = os.path.join(WIKI_FOLDER_PATH, filename)
        
        if os.path.exists(file_path):
            scraped_item = scrape_info_from_wiki(file_path)
            
            if scraped_item:
                items[item_name] = scraped_item
                print(f"Updated data for item: {scraped_item.name}")
                count += 1
                
                if count % 10 == 0:
                    print(f"Updated {count} items so far...")
                    save_items()

def get_image_files(items: dict[str, Item]) -> list[str]:
    image_files = []
    item_names = list(item.name for item in items.values())
    potential_files = 0
    files_with_wrong_ending = {}
    
    ## List all image files in the images directory and all subdirectories recursively
    for root, dirs, files in os.walk(IMAGES_PATH):
        for file in files:
            
            ## Check if the file is a png
            if file.lower().endswith('.png'):
                
                ## get item name without extension
                item_name = file[:-4].replace("_", " ").replace("%22", "").replace("%27", "'")
                
                if item_name in item_names:
                    potential_files += 1
                    
                    ## Check image dimension, we only want 64x64 icons
                    file_path = os.path.join(root, file)
                    from PIL import Image
                    with Image.open(file_path) as img:
                        width, height = img.size
                        if width == 64 and height == 64:
                            image_files.append(file)
    
    print("Potential image files matching item names:", potential_files)
    
    for ending, count in files_with_wrong_ending.items():
        print(f"Files with ending .{ending}: {count}")
        
    return image_files

items = load_items()
print("Loaded", len(items), "items from file.")

def check_duplicated_filenames(items):
    file_paths = {}
    for item_name, item in items.items():
        if item.inventory_icon_url:
        #get file name without path
            image_file_name = os.path.basename(item.inventory_icon_url)
            if not image_file_name in file_paths:
                file_paths[image_file_name] = []
        
            if not item.inventory_icon_url in file_paths[image_file_name]:
                file_paths[image_file_name].append(item.inventory_icon_url)

    for image_file, urls in file_paths.items():
        if len(urls) > 1:
            print(f"Image file '{image_file}' is used by multiple URLs:")
            for url in urls:
                print(f" - {url}")

# get_items()
# update_items()

# images = get_image_files(items)
# print("Found", len(images), "image files.")

items_with_icon = list(item for item in items.values() if item.inventory_icon_url)
items_with_existing_icon = list(item for item in items.values() if item.IconExists)

print("Out of ", len(items), "items,", len(items_with_icon), "have an inventory icon set,", len(items_with_existing_icon), "have an existing inventory icon.")

files_with_wrong_ending = {}
for item_name, item in items.items():
    if item.inventory_icon_url:
        file_ending = item.inventory_icon_url.split('.')[-1]
        if file_ending.lower() != 'png':
            if file_ending not in files_with_wrong_ending:
                files_with_wrong_ending[file_ending] = 0
                
            files_with_wrong_ending[file_ending] += 1

for ending, count in files_with_wrong_ending.items():
    print(f"Files with ending .{ending}: {count}")
    

# Talk User User TalkGuild Wars Wiki Talk File File talk MediaWiki MediaWiki talk Template Template talk Help Help talk Category talk Guild Guild talk Game link Game link talk ArenaNet ArenaNet talk Feedback Feedback talk Widget Widget talk
illegal_file_starts = [
    "Talk%3",
    "User%3",
    "User_Talk%3",
    "Guild_Wars_Wiki_Talk%3",
    "File%3",
    "File_talk%3",
    "MediaWiki%3",
    "MediaWiki_talk%3",
    "Template%3",
    "Template_talk%3",
    "Help%3",
    "Help_talk%3",
    "Category%3",
    "Category_talk%3",
    "Guild%3",
    "Guild_talk%3",
    "Game_link%3",
    "Game_link_talk%3",
    "ArenaNet%3",
    "ArenaNet_talk%3",
    "Feedback%3",
    "Feedback_talk%3",
    "Widget%3",
    "Widget_talk%3",
    "Skill_history",
    "GWW%3",
    "Guild_Wars_Wiki_talk%3",
    "Image%3",
    "Special%3",
    "User_talk%3",
]

## Count all files with illegal names in WIKI_FOLDER_PATH
illegal_count = 0
legal_count = 0

## create  os.path.join(LOOKUP_FOLDER, "images") and os.path.join(LOOKUP_FOLDER, "pages") if not exists
os.makedirs(os.path.join(LOOKUP_FOLDER, "images"), exist_ok=True)   
os.makedirs(os.path.join(LOOKUP_FOLDER, "pages"), exist_ok=True)

# for filename in os.listdir(WIKI_FOLDER_PATH):
#     is_folder = os.path.isdir(os.path.join(WIKI_FOLDER_PATH, filename))
#     if is_folder or any(filename.startswith(starter) for starter in illegal_file_starts):
#         illegal_count += 1
#     else:
#         legal_count += 1
#         ##Copy to LOOKUP_FOLDER
#         src_path = os.path.join(WIKI_FOLDER_PATH, filename)
#         dest_path = os.path.join(LOOKUP_FOLDER, "pages", filename)
#         shutil.copy2(src_path, dest_path)

for item in items_with_existing_icon:
    if item is None or item.inventory_icon_url is None:
        continue
    
    is_folder = os.path.isdir(os.path.join(IMAGES_PATH, item.inventory_icon_url))
    
    if is_folder:
        continue
    
    src_path = item.IconPath
    file_name = os.path.basename(item.inventory_icon_url)
    dest_path = os.path.join(LOOKUP_FOLDER, "images", file_name)
    
    if os.path.exists(src_path):
        shutil.copy2(src_path, dest_path)

print(f"Number of files with illegal names: {illegal_count}")
print(f"Number of files with legal names: {legal_count}")