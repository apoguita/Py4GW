import os
import re
import string
import sys
import urllib.parse
import difflib
from typing import Optional

from Widgets.frenkey.LootEx import models, module_import, utility
import importlib

from Py4GWCoreLib.Py4GWcorelib import ActionQueueManager, ConsoleLog
from Py4GWCoreLib.enums import ItemType, ServerLanguage

libraries_loaded : bool = False

requests = None
BeautifulSoup4 = None

try:
    module_import.ModuleImporter.prepare_module_import()
    from bs4 import BeautifulSoup as BS
    import requests
    
    requests = importlib.reload(requests)
    BeautifulSoup4 = BS
    print("Successfully imported BeautifulSoup and requests!")
    libraries_loaded = True

except ModuleNotFoundError as e:
    print(f"Error importing modules: {e}")
    print("Please ensure you have BeautifulSoup and requests installed in your Python environment.")
    # sys.exit(1)


from Widgets.frenkey.LootEx.data import Data
data = Data()

class WikiScraper:
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
            score = WikiScraper.string_similarity(query, candidate)
            if score > best_score:
                best_score = score
                best = candidate

        return best if best_score >= min_score else None

    @staticmethod
    def get_all_materials() -> dict[str, models.Item]:
        """
        Returns a list of all materials from the items data.
        """
        materials = {}

        for item in data.Items.get(models.ItemType.Materials_Zcoins, {}).values():
            if item.item_type == models.ItemType.Materials_Zcoins:
                materials[item.names.get(ServerLanguage.English, item.name).lower()] = item

        return materials
    
    MATERIALS: dict[str, models.Item] = {}
    
    @staticmethod
    def extract_materials(td) -> models.SalvageInfoCollection:
        materials : models.SalvageInfoCollection = models.SalvageInfoCollection()
        
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
                    
                materials[material_name] = models.SalvageInfo(
                    material_name=material_name,
                    min_amount=entry.get("min", -1) if entry.get("min") != entry.get("max") else -1,
                    max_amount=entry.get("max", -1) if entry.get("min") != entry.get("max") else -1,
                    amount=entry.get("min", -1) if entry.get("min") == entry.get("max") else -1
                )
                
        
        if materials:
            WikiScraper.MATERIALS = WikiScraper.get_all_materials()
            fixed_materials = models.SalvageInfoCollection()
            
            for material_name, salvage_info in materials.items():
                lower_name = material_name.lower()
                best_match = WikiScraper.get_best_match(lower_name, [m.name for m in WikiScraper.MATERIALS.values()], 0.9)
                
                ConsoleLog("LootEx", f"Found material {material_name} with best match {best_match} ({lower_name})")
                
                if best_match:
                    material = next((m for m in WikiScraper.MATERIALS.values() if m.name.lower() == best_match.lower()), None)
                    
                    if material:
                        salvage_info.material_name = material.names.get(ServerLanguage.English, material.name)
                        salvage_info.material_model_id = material.model_id
                    
                    fixed_materials[salvage_info.material_name] = salvage_info
                    
            materials = fixed_materials
        
        return materials
    
    @staticmethod
    def scrape_info_from_wiki(item: models.Item):
        if not BeautifulSoup4 or not requests:
            ConsoleLog("LootEx", "Cannot scrape wiki info: Required libraries not loaded.")
            return
        
        url = item.wiki_url
        response = requests.get(url)
        soup = BeautifulSoup4(response.text, 'html.parser')

        info_table = soup.find('table')

        if info_table is None:
            return None

        if info_table:
            rows = info_table.find_all('tr')
            scraped = False

            for row in rows:
                th = row.find('th')

                if th:
                    material_names = []                
                    
                    if th.find('a', string="Common salvage"):
                        td = row.find('td')

                        #<td>4-5 <a href="/wiki/Granite_Slab" title="Granite Slab">Granite Slabs</a><br>1-49 <a href="/wiki/Pile_of_Glittering_Dust" title="Pile of Glittering Dust">Piles of Glittering Dust</a></td>    
                        if td:
                            mats = WikiScraper.extract_materials(td)
                            
                            if mats:
                                item.common_salvage = mats
                                scraped = True

                    rare_material_names = []
                    if th.find('a', string="Rare salvage"):
                        td = row.find('td')

                        if td:
                            mats = WikiScraper.extract_materials(td)
                            
                            if mats:
                                item.rare_salvage = mats
                                scraped = True

                    if "Type" in th.get_text():
                        td = row.find('td')
                        
                        if td:
                            text = td.get_text(strip=True)
                            
                            if text:
                                scraped = True          
                                                      
                                if item.item_type == models.ItemType.Unknown:                                
                                    try:
                                        item.item_type = ItemType[text]
                                    except KeyError:
                                        if "upgrade" in text.lower():
                                            item.item_type = ItemType.Rune_Mod
                                        
                                        elif "focus" in text.lower():
                                            item.item_type = ItemType.Offhand
                                            
                                        elif "consumable" in text.lower():
                                            item.item_type = ItemType.Usable
                                            
                                        elif "sweet" in text.lower():
                                            item.item_type = ItemType.Usable
                                            
                                        elif "alcohol" in text.lower():
                                            item.item_type = ItemType.Usable
                                            
                                        else:
                                            item.item_type = ItemType.Unknown
                                            ConsoleLog("LootEx", f"Unknown item type '{text}' for {item.name} ({item.model_id}) in {item.wiki_url}.")
                                    
                                
                    if th.find('a', string="Inventory icon"):
                        td = row.find('td')                        

                        if td:
                            # Extract the image URL
                            img = td.find('img')
                            if img and 'src' in img.attrs:
                                item.inventory_icon_url = f"https://wiki.guildwars.com{img['src']}"
                                scraped = True
                
             
            if item.item_type == ItemType.Rune_Mod:
                tr = rows[1]
                td = tr.find('td')   
                name = item.names.get(ServerLanguage.English, item.name).lower()
                image_index = 0 if "minor" in name else 1 if "major" in name else 2 if "superior" in name else -1
                
                if td and image_index >= 0:
                    if "rune" in item.wiki_url.lower():
                        images = td.find_all('img')
                        if not images or image_index >= len(images):
                            print(f"Image at index {image_index} not found.")
                            return ""

                        # Extract and normalize the src
                        img = images[image_index]
                        item.inventory_icon_url = f"https://wiki.guildwars.com{img['src']}"
                        
                    elif "insignia" in item.wiki_url.lower():  
                        # Extract the image URL
                        img = td.find('img')
                        if img and 'src' in img.attrs:
                            item.inventory_icon_url = f"https://wiki.guildwars.com{img['src']}"
                            scraped = True
                            
                        pass            

            if not item.inventory_icon_url or item.inventory_icon_url == "":
                # Try to find the first image in the table as a fallback

                first_image = info_table.find('img')

                if first_image and 'src' in first_image.attrs:
                    item.inventory_icon_url = f"https://wiki.guildwars.com{first_image['src']}"      
            
            if item.inventory_icon_url and "Disambig_icon" in item.inventory_icon_url:
                # If the icon is a disambiguation icon, set it to None
                item.inventory_icon_url = None
            
            if scraped and not item.wiki_scraped:
                item.wiki_scraped = True
    
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
        decoded = urllib.parse.unquote(last_part)

        decoded = decoded.replace("_", " ")  # Replace spaces with underscores

        # Allow characters valid on most filesystems: keep letters, numbers, spaces, underscores,
        # dashes, apostrophes, parentheses, and periods
        # Replace only truly invalid characters with underscore
        sanitized = re.sub(r'[<>:"/\\|?*\x00-\x1F]', '_', decoded)

        # Replace multiple underscores with one (optional cleanup)
        sanitized = re.sub(r'_+', '_', sanitized)

        # Strip leading/trailing spaces/underscores
        return sanitized.strip(" _")

    @staticmethod
    def download_image(item: models.Item) -> bool:       
        """
        Downloads an image from the given URL and saves it to the item's inventory_icon_url path.
        """
        
        if not BeautifulSoup4 or not requests:
            ConsoleLog("LootEx", "Cannot download image: Required libraries not loaded.")
            return False
        
        if not item.inventory_icon_url:
            ConsoleLog("LootEx", f"No URL provided for {item.name}. Cannot download image.")
            return False
                
        filename = WikiScraper.get_image_name(item.inventory_icon_url)
        file_directory = os.path.dirname(os.path.abspath(__file__))
        data_directory = os.path.join(file_directory, "data")
        texture_directory = os.path.join(utility.Util.GetPy4GWPath(), "Textures", "Items")
        path = os.path.join(texture_directory, filename)
        if not os.path.exists(texture_directory):
            os.makedirs(texture_directory)            
        
        if not filename:
            ConsoleLog("LootEx", f"Invalid filename for {item.name}. Cannot download image.")
            return False    
        
        if os.path.exists(path):
            item.inventory_icon = filename
            data.SaveItems(True)
            return True
        
        try:
            response = requests.get(item.inventory_icon_url)
            response.raise_for_status()  # Raise an error for bad responses                               
            
            # Save the image to the item's inventory_icon_url path
            with open(path, 'wb') as file:
                file.write(response.content)
                item.inventory_icon = filename
                
            ConsoleLog("LootEx", f"Downloaded image for {item.name} from {item.inventory_icon_url} to {path}.")
            data.SaveItems(True)
            return True
        
        except requests.RequestException as e:
            ConsoleLog("LootEx", f"Failed to download image for {item.name} from {item.inventory_icon_url}: {e}")            
        return False
    
    @staticmethod
    def scrape_multiple_entries(items: list[models.Item]):
        if not BeautifulSoup4 or not requests:
            ConsoleLog("LootEx", "Cannot scrape wiki info: Required libraries not loaded.")
            return
        
        total = len(items)
        i  = 0
        
        for entry in items:
            # Skip entries with no wiki_url
            i += 1
            
            if not entry:
                continue
            
            def ScrapeEntry(entry: models.Item, i: int):
                ConsoleLog("LootEx", f"Scraping {entry.name} from {entry.wiki_url} | ({i} / {total})...")                
                # Scrape the item information from the wiki
                WikiScraper.scrape_info_from_wiki(entry)
                
                if not entry.inventory_icon_url or not WikiScraper.download_image(entry):
                    data.SaveItems(True)
                    
                
                if i >= total:
                    ConsoleLog("LootEx", "Finished scraping all entries.")
                    return
            
            try:                
                if not entry.wiki_url:
                    ConsoleLog("LootEx", f"Skipping {entry.name} due to missing wiki URL.")
                    continue
                
                ActionQueueManager().AddAction("ACTION", 
                ScrapeEntry, entry, i)         
                            
            except Exception as e:
                print(f"Error scraping {entry.wiki_url}: {e}")
            

    @staticmethod
    def scrape_missing_entries():   
        if not BeautifulSoup4 or not requests:
            ConsoleLog("LootEx", "Cannot scrape wiki info: Required libraries not loaded.")
            return
                     
        # items_with_missing_info = [
        #     item for subdict in data.Items.values() for item in subdict.values() if not item.wiki_scraped
        # ]              
        armor_types = [
            models.ItemType.Headpiece,
            models.ItemType.Chestpiece,
            models.ItemType.Gloves,
            models.ItemType.Leggings,
            models.ItemType.Boots
        ]
        
        items_with_missing_info = [
            item for subdict in data.Items.values() for item in subdict.values() if not item.wiki_scraped and item.item_type not in armor_types 
        ]
                      
        # items_with_missing_info = [
        #     item for subdict in data.Items.values() for item in subdict.values() if item.inventory_icon_url and not item.inventory_icon
        # ]
        
        WikiScraper.scrape_multiple_entries(items_with_missing_info)
