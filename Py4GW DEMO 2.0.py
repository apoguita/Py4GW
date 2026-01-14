import PyImGui
from Py4GWCoreLib.AgentArray import AgentArray
from py4gw_demo_src.helpers import draw_kv_table
from Py4GWCoreLib.Player import Player
from py4gw_demo_src.helpers import VIEW_LIST, _selected_view
from py4gw_demo_src.map_demo import draw_map_data, draw_mission_map_tab, draw_mini_map_tab, draw_world_map_tab, draw_pregame_tab
from py4gw_demo_src.agent_demo import draw_agents_view
from py4gw_demo_src.pathing_map_demo import renderer
from Py4GWCoreLib.native_src.context.AgentContext import AgentStruct, AgentLivingStruct, AgentItemStruct, AgentGadgetStruct

MODULE_NAME = "Py4GW DEMO 2.0"

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
    
    def _display_array_data(array:list[int], raw_array:list[AgentStruct], title:str):
        # Display AgentArray data
        if len(array) == 0 or len(raw_array) == 0:
            PyImGui.text(f"No {title} data available.")
            return
        PyImGui.text(f"--- {title} ---")
        PyImGui.indent(20.0)
        PyImGui.text(f"Total Agents in {title}: {len(array)}")
        PyImGui.text(f"Total Raw Agents in {title}: {len(raw_array)}")
        PyImGui.separator()
        PyImGui.unindent(20.0)
        
    array = AgentArray.GetAgentArray()
    raw_array = AgentArray.GetAgentArrayRaw()
    _display_array_data(array, raw_array, "All Agents")
    
    ally_array = AgentArray.GetAllyArray()
    raw_ally_array = AgentArray.GetAllyArrayRaw()
    _display_array_data(ally_array, raw_ally_array, "Ally Agents")
    
    neutral_array = AgentArray.GetNeutralArray()
    raw_neutral_array = AgentArray.GetNeutralArrayRaw()
    _display_array_data(neutral_array, raw_neutral_array, "Neutral Agents")
    
    enemy_array = AgentArray.GetEnemyArray()
    raw_enemy_array = AgentArray.GetEnemyArrayRaw()
    _display_array_data(enemy_array, raw_enemy_array, "Enemy Agents")
    
    spirit_pet_array = AgentArray.GetSpiritPetArray()
    raw_spirit_pet_array = AgentArray.GetSpiritPetArrayRaw()
    _display_array_data(spirit_pet_array, raw_spirit_pet_array, "Spirit/Pet Agents")
    
    minion_array = AgentArray.GetMinionArray()
    raw_minion_array = AgentArray.GetMinionArrayRaw()
    _display_array_data(minion_array, raw_minion_array, "Minion Agents")
    
    npc_minipet_array = AgentArray.GetNPCMinipetArray()
    raw_npc_minipet_array = AgentArray.GetNPCMinipetArrayRaw()
    _display_array_data(npc_minipet_array, raw_npc_minipet_array, "NPC Minipet Agents")
    
    item_array = AgentArray.GetItemArray()
    raw_item_array = AgentArray.GetItemArrayRaw()
    _display_array_data(item_array, raw_item_array, "Item Agents")
    
    owned_item_array = AgentArray.GetOwnedItemArray()
    raw_owned_item_array = AgentArray.GetOwnedItemArrayRaw()
    _display_array_data(owned_item_array, raw_owned_item_array, "Owned Item Agents")
    
    gadget_array = AgentArray.GetGadgetArray()
    raw_gadget_array = AgentArray.GetGadgetArrayRaw()
    _display_array_data(gadget_array, raw_gadget_array, "Gadget Agents")
    
    dead_ally_array = AgentArray.GetDeadAllyArray()
    raw_dead_ally_array = AgentArray.GetDeadAllyArrayRaw()
    _display_array_data(dead_ally_array, raw_dead_ally_array, "Dead Ally Agents")
    
    dead_enemy_array = AgentArray.GetDeadEnemyArray()
    raw_dead_enemy_array = AgentArray.GetDeadEnemyArrayRaw()
    _display_array_data(dead_enemy_array, raw_dead_enemy_array, "Dead Enemy Agents")

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



def main():
    draw_window()

if __name__ == "__main__":
    main()
