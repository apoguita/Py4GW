import PyImGui
import PyMap
from typing import Tuple

Title = "PyMap Debug Info"
map_instance = PyMap.PyMap()
def RGBToNormal(r, g, b, a):
    """return a normalized RGBA tuple from 0-255 values"""
    return r / 255.0, g / 255.0, b / 255.0, a / 255.0
    
def ShowStatus(condition: bool, message: str) -> None:
    if condition:
        green: Tuple[float, float, float, float] = RGBToNormal(0, 255, 0, 255)
        PyImGui.text_colored(f"{message}", green)
    else:
        red: Tuple[float, float, float, float] = RGBToNormal(255, 0, 0, 255)
        PyImGui.text_colored(f"{message}", red)
        
def FormatInstanceTime(ms: int) -> str:
    seconds = ms / 1000.0

    if seconds < 60:
        return f"{seconds:.3f} s"

    minutes = seconds / 60.0
    if minutes < 60:
        whole_min = int(minutes)
        rem_sec = seconds - whole_min * 60
        return f"{whole_min}m {rem_sec:.1f}s"

    hours = minutes / 60.0
    whole_hr = int(hours)
    rem_min = minutes - whole_hr * 60
    return f"{whole_hr}h {int(rem_min)}m"


map_id = 0
server_region = 0
district_number = 0
language = 0

def draw_window():
    global Title, map_instance
    global map_id, server_region, district_number, language
    if PyImGui.begin(Title):

        if map_instance is None:
            PyImGui.text("No map instance loaded. Click 'Refresh Map Instance' to load.")
            PyImGui.end()
            return
        
        not_empty = lambda x: x is not None and (not isinstance(x,   int) or x != 0)
        valid_small_int = lambda x: x is not None and isinstance(x, int) and x >= 0 and x < 9999
        
        if PyImGui.collapsing_header("Map Instance Debug Information:"):
            ShowStatus(not_empty(map_instance.instance_type), f"Instance Type: {map_instance.instance_type.ToInt()} {map_instance.instance_type.GetName()}")
            ShowStatus(map_instance.is_map_ready, "Map is Ready")
            ShowStatus(True, "Instance Time: " + FormatInstanceTime(map_instance.instance_time))
            ShowStatus(not_empty(map_instance.map_id.ToInt()), f"Map ID: {map_instance.map_id.ToInt()} - {map_instance.map_id.GetName()}")
            PyImGui.text(f"Map Internal ID: {map_instance.GetMapID()}")
            ShowStatus(not_empty(map_instance.server_region), f"Server Region: {map_instance.server_region.ToInt()} {map_instance.server_region.GetName()}")
            ShowStatus(True, f"District: {map_instance.district}")
            ShowStatus(True, f"Language: {map_instance.language.ToInt()} - {map_instance.language.GetName()}")
            ShowStatus(True, f"Foes Killed: {map_instance.foes_killed}")
            ShowStatus(True, f"Foes To Kill: {map_instance.foes_to_kill}")
            ShowStatus(not map_instance.is_in_cinematic, f"Is In Cinematic: {map_instance.is_in_cinematic}")
            PyImGui.text(f"Campaign: {map_instance.campaign.GetName()}")
            PyImGui.text(f"Continent: {map_instance.continent.GetName()}")
            PyImGui.text(f"Region Type: {map_instance.region_type.GetName()}")
            PyImGui.text(f"Has Enter Button: {map_instance.has_enter_button}")
            PyImGui.text(f"Is On World Map: {map_instance.is_on_world_map}")
            PyImGui.text(f"Is PvP: {map_instance.is_pvp}")
            PyImGui.text(f"Is Guild Hall: {map_instance.is_guild_hall}")
            PyImGui.text(f"Is Vanquishable Area: {map_instance.is_vanquishable_area}")
            PyImGui.text(f"Amount Of Players In Instance: {map_instance.amount_of_players_in_instance}")
            PyImGui.text(f"Flags: {map_instance.flags}")
            PyImGui.text(f"Thumbnail ID: {map_instance.thumbnail_id}")
            PyImGui.text(f"Min Party Size: {map_instance.min_party_size}")
            PyImGui.text(f"Max Party Size: {map_instance.max_party_size}")
            PyImGui.text(f"Min Player Size: {map_instance.min_player_size}")
            PyImGui.text(f"Max Player Size: {map_instance.max_player_size}")
            PyImGui.text(f"Controlled Outpost ID: {map_instance.controlled_outpost_id}")
            PyImGui.text(f"Fraction Mission: {map_instance.fraction_mission}")
            PyImGui.text(f"Min Level: {map_instance.min_level}")
            PyImGui.text(f"Max Level: {map_instance.max_level}")
            PyImGui.text(f"Needed PQ: {map_instance.needed_pq}")
            PyImGui.text(f"Mission Maps To: {map_instance.mission_maps_to}")
            PyImGui.text(f"Icon Position X: {map_instance.icon_position_x}")
            PyImGui.text(f"Icon Position Y: {map_instance.icon_position_y}")
            PyImGui.text(f"Icon Start X: {map_instance.icon_start_x}")
            PyImGui.text(f"Icon Start Y: {map_instance.icon_start_y}")
            PyImGui.text(f"Icon End X: {map_instance.icon_end_x}")
            PyImGui.text(f"Icon End Y: {map_instance.icon_end_y}")
            PyImGui.text(f"Icon Start X Dupe: {map_instance.icon_start_x_dupe}")
            PyImGui.text(f"Icon Start Y Dupe: {map_instance.icon_start_y_dupe}")
            PyImGui.text(f"Icon End X Dupe: {map_instance.icon_end_x_dupe}")
            PyImGui.text(f"Icon End Y Dupe: {map_instance.icon_end_y_dupe}")
            PyImGui.text(f"File ID: {map_instance.file_id}")
            PyImGui.text(f"Mission Chronology: {map_instance.mission_chronology}")
            PyImGui.text(f"HA Map Chronology: {map_instance.ha_map_chronology}")
            PyImGui.text(f"Name ID: {map_instance.name_id}")
            PyImGui.text(f"Description ID: {map_instance.description_id}")
            PyImGui.text(f"Map Boundaries: {map_instance.map_boundaries}")
            
            
        if PyImGui.collapsing_header("Methods:"):
            map_id = PyImGui.input_int("Map ID", map_id)
            server_region = PyImGui.input_int("Server Region", server_region)
            district_number = PyImGui.input_int("District Number", district_number)
            language = PyImGui.input_int("Language", language)
                
            if PyImGui.button("Travel"):
                map_instance.Travel(map_id)
                
            if PyImGui.button("Travel to district"):
                map_instance.Travel(server_region, district_number, language)
                
            if PyImGui.button("TravelGH"):
                map_instance.TravelGH()
                
            if PyImGui.button("LeaveGH"):
                map_instance.LeaveGH()

            
                
        

            
    PyImGui.end()
    
    if map_instance is not None:
        map_instance.GetContext()

def main():
    draw_window()


if __name__ == "__main__":
    main()
