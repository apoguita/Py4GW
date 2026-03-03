import PyImGui
from Py4GWCoreLib.AgentArray import AgentArray
from Sources.ApoSource.py4gw_demo_src.helpers import draw_kv_table
from Py4GWCoreLib.Player import Player
from Sources.ApoSource.py4gw_demo_src.helpers import VIEW_LIST, _selected_view
from Sources.ApoSource.py4gw_demo_src.map_demo import draw_map_data, draw_mission_map_tab, draw_mini_map_tab, draw_world_map_tab, draw_pregame_tab
from Sources.ApoSource.py4gw_demo_src.agent_demo import draw_agents_view
from Sources.ApoSource.py4gw_demo_src.pathing_map_demo import renderer
from Py4GWCoreLib import Color, ImGui

MODULE_NAME = "Py4GW DEMO 2.0"
MODULE_ICON = "Textures/Module_Icons/Py4GW.png"

def draw_agent_array_data():
    info = """
The AgentArray module provides methods to access and manipulate collections of agents in the game world.
It allows you to retrieve arrays of agents based on various criteria, such as alliegances or types.
You can use this module to efficiently gather data about multiple agents, filter them based on specific
visibility, or other attributes.
Key functionalities include:
    - Retrieving all agents in the game world.
    - PreFiltering agents
    - Merging agent arrays
    - Sorting agents
"""

    PyImGui.text_wrapped(info)
    PyImGui.separator()
    
    def _display_array_data(array:list[int], title:str):
        # Display AgentArray data
        if len(array) == 0:
            PyImGui.text(f"No {title} data available.")
            return
        PyImGui.text(f"--- {title} ---")
        PyImGui.indent(20.0)
        PyImGui.text(f"Total Agents in {title}: {len(array)}")
        PyImGui.separator()
        PyImGui.unindent(20.0)
        
    array = AgentArray.GetAgentArray()
    _display_array_data(array, "All Agents")
    
    ally_array = AgentArray.GetAllyArray()
    _display_array_data(ally_array, "Ally Agents")
    
    neutral_array = AgentArray.GetNeutralArray()
    _display_array_data(neutral_array, "Neutral Agents")
    
    enemy_array = AgentArray.GetEnemyArray()
    _display_array_data(enemy_array, "Enemy Agents")
    
    spirit_pet_array = AgentArray.GetSpiritPetArray()
    _display_array_data(spirit_pet_array, "Spirit/Pet Agents")
    
    minion_array = AgentArray.GetMinionArray()
    _display_array_data(minion_array, "Minion Agents")
    
    npc_minipet_array = AgentArray.GetNPCMinipetArray()
    _display_array_data(npc_minipet_array, "NPC Minipet Agents")
    
    item_array = AgentArray.GetItemArray()
    _display_array_data(item_array, "Item Agents")
    
    owned_item_array = AgentArray.GetOwnedItemArray()
    _display_array_data(owned_item_array, "Owned Item Agents")
    
    gadget_array = AgentArray.GetGadgetArray()
    _display_array_data(gadget_array, "Gadget Agents")
    
    dead_ally_array = AgentArray.GetDeadAllyArray()
    _display_array_data(dead_ally_array, "Dead Ally Agents")
    
    dead_enemy_array = AgentArray.GetDeadEnemyArray()
    _display_array_data(dead_enemy_array, "Dead Enemy Agents")

#region Main Window
def draw_window():
    global _selected_view
    if PyImGui.begin(MODULE_NAME, True, PyImGui.WindowFlags.AlwaysAutoResize):
        # ================= LEFT PANEL =================
        PyImGui.begin_child(
            "left_panel",
            (250.0, 700.0),   # fixed width, full height
            True,
            0
        )

        PyImGui.text("Modules")
        PyImGui.separator()

        for is_child, name in VIEW_LIST:
            if is_child:
                PyImGui.indent(20.0)
                #name = name.replace(" |- ", "")
            if PyImGui.selectable(
                name,
                _selected_view == name,
                PyImGui.SelectableFlags.NoFlag,
                (0.0, 0.0)
            ):
                _selected_view = name
                
            if is_child:
                PyImGui.unindent(20.0)

        PyImGui.end_child()

        PyImGui.same_line(0,-1)
        
        # ================= RIGHT PANEL =================
        PyImGui.begin_child(
            "right_panel",
            (700.0, 700.0),     # take remaining space
            False,
            0
        )
        
        if _selected_view == "Map":
            draw_map_data()
        elif _selected_view == "Mission Map":
            draw_mission_map_tab()
        elif _selected_view == "Mini Map":
            draw_mini_map_tab()
        elif _selected_view == "World Map":
            draw_world_map_tab()
        elif _selected_view == "Pregame Data":
            draw_pregame_tab()
        elif _selected_view == "Geo Location and Pathing":
            renderer.Draw_PathingMap_Window()
        elif _selected_view == "AgentArray":
            draw_agent_array_data() 
        
        elif _selected_view == "Agents":
            draw_agents_view()

        PyImGui.end_child()

    PyImGui.end()

def tooltip():
    PyImGui.begin_tooltip()

    # Title
    title_color = Color(255, 200, 100, 255)
    ImGui.push_font("Regular", 20)
    PyImGui.text_colored("Py4GW Demo", title_color.to_tuple_normalized())
    ImGui.pop_font()
    PyImGui.spacing()
    PyImGui.separator()

    # Description
    PyImGui.text("A comprehensive live API reference and demonstration utility.")
    PyImGui.text("This script showcases every internal class and data access method")
    PyImGui.text("available within the Py4GW library for developer education.")
    PyImGui.spacing()

    # Features
    PyImGui.text_colored("Demonstrated Modules:", title_color.to_tuple_normalized())
    PyImGui.bullet_text("Merchant Engine: Traders, Crafters, and Collectors interaction")
    PyImGui.bullet_text("Skill & Effect: Detailed skill data, skillbar control, and buff monitoring")
    PyImGui.bullet_text("Inventory: Automated identification, salvaging, and gold tracking")
    PyImGui.bullet_text("World Tools: 3D Overlay rings, Map travel, and Quest management")
    PyImGui.bullet_text("Core Utilities: Latency (Ping) statistics, Timers, and Keystroke emulation")

    PyImGui.spacing()
    PyImGui.separator()
    PyImGui.spacing()

    # Credits
    PyImGui.text_colored("Credits:", title_color.to_tuple_normalized())
    PyImGui.bullet_text("Developed by Apo")

    PyImGui.end_tooltip()

def main():
    draw_window()

if __name__ == "__main__":
    main()
