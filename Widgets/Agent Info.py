from Py4GWCoreLib import GLOBAL_CACHE
from Py4GWCoreLib import PyImGui
from Py4GWCoreLib import ImGui 
from Py4GWCoreLib import Routines
from Py4GWCoreLib import Allegiance
from Py4GWCoreLib import Color
from typing import Tuple

MODULE_NAME = "Agent Info Viewer"
LOG_ACTIONS = True


#region WinwowStup
window_module = ImGui.WindowModule(
    MODULE_NAME, 
    window_name="Agent Info Viewer", 
    window_size=(0, 0),
    window_flags=PyImGui.WindowFlags.AlwaysAutoResize
)

#endregion

#region ImGui
SELECTED_ALLIEGANCE = 0
SELECTED_AGENT_INDEX = 0 
SELECTED_AGENT_ID = 0    
def DrawMainWindow():
    global SELECTED_ALLIEGANCE, SELECTED_AGENT_INDEX, SELECTED_AGENT_ID
    def _get_type(agent) -> str:
        if agent.is_living:
            return "Living"
        elif agent.is_item:
            return "Item"
        elif agent.is_gadget:
            return "Gadget"
        else:
            return "Unknown"
        
    def _format_agent_row(label: str, agent) -> tuple:
        if agent is None or agent.id == 0:
            return (label, "0", "", "", "")
        return (
            label,
            agent.id,
            GLOBAL_CACHE.Agent.GetName(agent.id),
            f"({agent.x:.2f}, {agent.y:.2f}, {agent.z:.2f})",
            _get_type(agent)
        )
        
    def _colored_bool(value: bool) -> Tuple[int, int, int, int]:
        return Color(0,255,0,255).to_tuple() if value else Color(255,0,0,255).to_tuple()
    
    def _draw_agent_tab_item(agent):
        if not GLOBAL_CACHE.Agent.IsValid(agent.id):   
            return   
        PyImGui.text(f"ID: {agent.id}")
        PyImGui.text(f"Name: {GLOBAL_CACHE.Agent.GetName(agent.id)}")
        if PyImGui.button("Target Agent"):
            GLOBAL_CACHE.Player.ChangeTarget(agent.id)
        PyImGui.separator()
        if PyImGui.collapsing_header(f"Positional Data:"):
            flags = PyImGui.TableFlags.Borders | PyImGui.TableFlags.SizingStretchSame | PyImGui.TableFlags.Resizable
            if PyImGui.begin_table(f"PositionalData##PositionalData{agent.id}", 5,flags):                                
                PyImGui.table_next_row()
                PyImGui.table_next_column()
                PyImGui.text("Position")
                PyImGui.table_next_column()
                PyImGui.text(f"X: {agent.x:.2f}")
                PyImGui.table_next_column()
                PyImGui.text(f"Y: {agent.y:.2f}")
                PyImGui.table_next_column()
                PyImGui.text(f"Z: {agent.z:.2f}")
                PyImGui.table_next_column()
                PyImGui.text(f"ZPlane {agent.zplane:.2f}")
                PyImGui.table_next_row()
                PyImGui.table_next_column()
                
                PyImGui.text("Rotation")
                PyImGui.table_next_column()
                PyImGui.text(f"Angle: {agent.rotation_angle:.2f}")
                PyImGui.table_next_column()
                PyImGui.text(f"Cos: {agent.rotation_cos:.2f}")
                PyImGui.table_next_column()
                PyImGui.text(f"Sin: {agent.rotation_sin:.2f}")
                PyImGui.table_next_row()
                PyImGui.table_next_column()
                
                PyImGui.text("Velocity")
                PyImGui.table_next_column()
                PyImGui.text(f"X: {agent.velocity_x:.2f}")
                PyImGui.table_next_column()
                PyImGui.text(f"Y: {agent.velocity_y:.2f}")
                PyImGui.table_next_row()
                PyImGui.table_next_column()

                PyImGui.text("Name Tag")
                PyImGui.table_next_column()
                PyImGui.text(f"X: {agent.name_tag_x:.2f}")
                PyImGui.table_next_column()
                PyImGui.text(f"Y: {agent.name_tag_y:.2f}")
                PyImGui.table_next_column()
                PyImGui.text(f"Z: {agent.name_tag_z:.2f}")
                PyImGui.table_next_row()
                PyImGui.table_next_column()
                
                PyImGui.end_table()
                
        if PyImGui.collapsing_header(f"Agent Properties"):
            flags = PyImGui.TableFlags.Borders | PyImGui.TableFlags.SizingStretchSame | PyImGui.TableFlags.Resizable
            if PyImGui.begin_table(f"AgentProperties##AgentProperties{agent.id}", 5,flags):                                
                PyImGui.table_next_row()
                PyImGui.table_next_column()
                PyImGui.text("Model 1")
                PyImGui.table_next_column()
                PyImGui.text(f"Width: {agent.model_width1:.2f}")
                PyImGui.table_next_column()
                PyImGui.text(f"Height: {agent.model_height1:.2f}")
                PyImGui.table_next_row()
                PyImGui.table_next_column()
                PyImGui.text("Model 2")
                PyImGui.table_next_column()
                PyImGui.text(f"Width: {agent.model_width3:.2f}")
                PyImGui.table_next_column() 
                PyImGui.text(f"Height: {agent.model_height2:.2f}")
                PyImGui.table_next_row()
                PyImGui.table_next_column()
                PyImGui.text("Model 3")
                PyImGui.table_next_column()
                PyImGui.text(f"Width: {agent.model_width3:.2f}")
                PyImGui.table_next_column()
                PyImGui.text(f"Height: {agent.model_height3:.2f}")
                PyImGui.table_next_row()
                PyImGui.table_next_column()
                PyImGui.text(f"Name Properties")
                PyImGui.table_next_column()
                PyImGui.text(f"{agent.name_properties}")
                PyImGui.table_next_column()
                PyImGui.text(f"HEX: {hex(agent.name_properties)}")
                PyImGui.table_next_column()
                PyImGui.text(f"BIN: {bin(agent.name_properties)}")
                PyImGui.table_next_row()
                PyImGui.table_next_column()
                PyImGui.text(f"Visual Effectes")
                PyImGui.table_next_column()
                PyImGui.text(f"{agent.visual_effects}")
                PyImGui.table_next_column()
                PyImGui.text(f"Hex: {hex(agent.visual_effects)}")
                PyImGui.table_next_column()
                PyImGui.text(f"Bin: {bin(agent.visual_effects)}")
                PyImGui.table_next_row()
                PyImGui.table_next_column()
                PyImGui.end_table()

                
        if agent.id == GLOBAL_CACHE.Player.GetAgentID():
            if PyImGui.collapsing_header(f"Player Instance Exclusive Data:"):
            
                PyImGui.text("Terrain Normal")
                PyImGui.table_next_column()
                PyImGui.text(f"X: {agent.terrain_normal[0]:.2f}")
                PyImGui.table_next_column()
                PyImGui.text(f"Y: {agent.terrain_normal[1]:.2f}")
                PyImGui.table_next_column()
                PyImGui.text(f"Z: {agent.terrain_normal[2]:.2f}")
                PyImGui.table_next_column()
                PyImGui.text(f"Ground: {agent.ground}")
                
                
        if PyImGui.collapsing_header("Attributes"):

            attributes = agent.attributes

            headers = ["Attribute", "Base Level", "Level"]
            data = []
            for attribute in attributes:
                data.append((attribute.GetName(), str(attribute.level_base), str(attribute.level)))

            ImGui.table(f"Attributes Info##attinfo{agent.id}", headers, data)
            
        PyImGui.text_colored("Is Living", _colored_bool(agent.is_living))
        PyImGui.same_line(0, -1)
        PyImGui.text_colored("Is Item", _colored_bool(agent.is_item))
        PyImGui.same_line(0, -1)
        PyImGui.text_colored("Is Gadget", _colored_bool(agent.is_gadget))
        
        if agent.is_living:
            if PyImGui.collapsing_header("Living Agent Data"):
                living_agent = agent.living_agent
                flags = PyImGui.TableFlags.Borders | PyImGui.TableFlags.SizingStretchSame | PyImGui.TableFlags.Resizable
                if PyImGui.begin_table(f"livingfields##livingfields{agent.id}", 3,flags):                                
                    PyImGui.table_next_row()
                    PyImGui.table_next_column()
                    PyImGui.text(f"Owner ID: {living_agent.owner_id}")
                    PyImGui.table_next_column()
                    PyImGui.text(f"Player Number/ModelID: {living_agent.player_number}")
                    PyImGui.table_next_column()
                    PyImGui.text(f"Animation Code: {living_agent.animation_code}")
                    PyImGui.table_next_row()
                    PyImGui.table_next_column()
                    PyImGui.text(f"Primary: {living_agent.profession.GetName()}")
                    PyImGui.table_next_column()
                    PyImGui.text(f"Secondary: {living_agent.secondary_profession.GetName()}")
                    PyImGui.table_next_column()
                    PyImGui.text(f"Level: {living_agent.level}")
                    PyImGui.table_next_row()
                    PyImGui.table_next_column()
                    PyImGui.text(f"Energy: {living_agent.energy}")
                    PyImGui.table_next_column()
                    PyImGui.text(f"Max Energy: {living_agent.max_energy}")
                    PyImGui.table_next_column()
                    PyImGui.text(f"Energy Regeneration: {living_agent.energy_regen}")
                    PyImGui.table_next_row()
                    PyImGui.table_next_column()
                    PyImGui.text(f"Health: {living_agent.hp}")
                    PyImGui.table_next_column()
                    PyImGui.text(f"Max Health: {living_agent.max_hp}")
                    PyImGui.table_next_column()
                    PyImGui.text(f"Health Regeneration: {living_agent.hp_regen}")
                    PyImGui.table_next_row()
                    PyImGui.table_next_column()
                    PyImGui.text(f"Login Number: {living_agent.login_number}")
                    PyImGui.table_next_column()
                    PyImGui.text(f"Dagger Status: {living_agent.dagger_status}")
                    PyImGui.table_next_column()
                    PyImGui.text(f"Allegiance: {living_agent.allegiance.GetName()}")
                    PyImGui.table_next_row()
                    PyImGui.table_next_column()
                    PyImGui.text(f"Weapon Type: {living_agent.weapon_type.GetName()}")
                    PyImGui.table_next_column()
                    PyImGui.text(f"Weapon Item Type: {living_agent.weapon_item_type}")
                    PyImGui.table_next_column()
                    PyImGui.text(f"Offhand Item Type: {living_agent.offhand_item_type}")
                    PyImGui.table_next_row()
                    PyImGui.table_next_column()
                    PyImGui.text(f"Weapon Item ID: {living_agent.weapon_item_id}")
                    PyImGui.table_next_column()
                    PyImGui.text(f"Offhand Item ID: {living_agent.offhand_item_id}")
                    PyImGui.table_next_row()
                    PyImGui.table_next_column()
                    PyImGui.text_colored("Is Bleeding", _colored_bool(living_agent.is_bleeding))
                    PyImGui.table_next_column()
                    PyImGui.text_colored("Is Conditioned", _colored_bool(living_agent.is_conditioned))
                    PyImGui.table_next_column()
                    PyImGui.text_colored("Is Crippled", _colored_bool(living_agent.is_crippled))
                    PyImGui.table_next_row()
                    PyImGui.table_next_column()
                    PyImGui.text_colored("Is Dead", _colored_bool(living_agent.is_dead))
                    PyImGui.table_next_column()
                    PyImGui.text_colored("Is Deep Wounded", _colored_bool(living_agent.is_deep_wounded))
                    PyImGui.table_next_column()
                    PyImGui.text_colored("Is Poisoned", _colored_bool(living_agent.is_poisoned))
                    PyImGui.table_next_row()
                    PyImGui.table_next_column()
                    PyImGui.text_colored("Is Enchanted", _colored_bool(living_agent.is_enchanted))
                    PyImGui.table_next_column()
                    PyImGui.text_colored("Is Degen Hexed", _colored_bool(living_agent.is_degen_hexed))
                    PyImGui.table_next_column()
                    PyImGui.text_colored("Is Hexed", _colored_bool(living_agent.is_hexed))
                    PyImGui.table_next_row()
                    PyImGui.table_next_column()
                    PyImGui.text_colored("Is Weapon Spelled", _colored_bool(living_agent.is_weapon_spelled))
                    PyImGui.table_next_column()
                    PyImGui.text_colored("In Combat Stance", _colored_bool(living_agent.in_combat_stance))
                    PyImGui.table_next_column()
                    PyImGui.text_colored("Has Quest", _colored_bool(living_agent.has_quest))
                    PyImGui.table_next_row()
                    PyImGui.table_next_column()
                    PyImGui.text_colored("Is Dead By Type Map", _colored_bool(living_agent.is_dead_by_typemap))
                    PyImGui.table_next_column()
                    PyImGui.text_colored("Is Female", _colored_bool(living_agent.is_female))
                    PyImGui.table_next_column()
                    PyImGui.text_colored("Has Boss Glow", _colored_bool(living_agent.has_boss_glow))
                    PyImGui.table_next_row()
                    PyImGui.table_next_column()
                    PyImGui.text_colored("Is Hiding Cape", _colored_bool(living_agent.is_hiding_cape))
                    PyImGui.table_next_column()
                    PyImGui.text_colored("Can Be Viewed In Party Window", _colored_bool(living_agent.can_be_viewed_in_party_window))
                    PyImGui.table_next_column()
                    PyImGui.text_colored("Is Spawned", _colored_bool(living_agent.is_spawned))
                    PyImGui.table_next_row()
                    PyImGui.table_next_column()
                    PyImGui.text_colored("Is Being Observed", _colored_bool(living_agent.is_being_observed))
                    PyImGui.table_next_column()
                    PyImGui.text_colored("Is Knocked Down", _colored_bool(living_agent.is_knocked_down))
                    PyImGui.table_next_column()
                    PyImGui.text_colored("Is Moving", _colored_bool(living_agent.is_moving))
                    PyImGui.table_next_row()
                    PyImGui.table_next_column()
                    PyImGui.text_colored("Is Attacking", _colored_bool(living_agent.is_attacking))
                    PyImGui.table_next_column()
                    PyImGui.text_colored("Is Casting", _colored_bool(living_agent.is_casting))
                    PyImGui.table_next_column()
                    PyImGui.text_colored("Is Idle", _colored_bool(living_agent.is_idle))
                    PyImGui.table_next_row()
                    PyImGui.table_next_column()
                    PyImGui.text_colored("Is Alive", _colored_bool(living_agent.is_alive))
                    PyImGui.table_next_column()
                    PyImGui.text_colored("Is Player", _colored_bool(living_agent.is_player))
                    PyImGui.table_next_column()
                    PyImGui.text_colored("Is NPC", _colored_bool(living_agent.is_npc))
                    PyImGui.table_next_row()
                    PyImGui.table_next_column()
                    PyImGui.text(f"Casting Skill ID: {living_agent.casting_skill_id}")
                    PyImGui.table_next_column()
                    PyImGui.text(f"Overcast: {living_agent.overcast}")
                    PyImGui.table_next_column()
                    PyImGui.text(f"Animation Type: {living_agent.animation_type}")
                    PyImGui.table_next_row()
                    PyImGui.table_next_column()
                    PyImGui.text(f"Weapon Attack Speed: {living_agent.weapon_attack_speed}")
                    PyImGui.table_next_column()
                    PyImGui.text(f"Attack Speed Modifier: {living_agent.attack_speed_modifier}")
                    PyImGui.table_next_column()
                    PyImGui.text(f"Agent Model Type: {living_agent.agent_model_type}")
                    PyImGui.table_next_row()
                    PyImGui.table_next_column()
                    PyImGui.text(f"Transmog NPC ID: {living_agent.transmog_npc_id}")
                    PyImGui.table_next_column()
                    PyImGui.text(f"Guild ID: {living_agent.guild_id}")
                    PyImGui.table_next_column()
                    PyImGui.text(f"Team ID: {living_agent.team_id}")
                    PyImGui.table_next_row()
                    PyImGui.table_next_column()
                    PyImGui.text(f"Effects: {living_agent.effects}")
                    PyImGui.table_next_column()
                    PyImGui.text(f"Hex: {hex(living_agent.effects)}")
                    PyImGui.table_next_column()
                    PyImGui.text(f"Bin: {bin(living_agent.effects)}")
                    PyImGui.table_next_row()
                    PyImGui.table_next_column()
                    PyImGui.text(f"Model State: {living_agent.model_state}")
                    PyImGui.table_next_column()
                    PyImGui.text(f"Hex: {hex(living_agent.model_state)}")
                    PyImGui.table_next_column()
                    PyImGui.text(f"Bin: {bin(living_agent.model_state)}")
                    PyImGui.table_next_row()
                    PyImGui.table_next_column()
                    PyImGui.text(f"Type Map: {agent.living_agent.type_map}")
                    PyImGui.table_next_column()
                    PyImGui.text(f"Hex: {hex(agent.living_agent.type_map)}")
                    PyImGui.table_next_column()
                    PyImGui.text(f"Bin: {bin(agent.living_agent.type_map)}")
                    PyImGui.table_next_row()
                    PyImGui.table_next_column()
                    PyImGui.text(f"Animation Speed: {living_agent.animation_speed}")
                    PyImGui.table_next_column()
                    PyImGui.text(f"Animation Code: {living_agent.animation_code}")
                    PyImGui.table_next_column()
                    PyImGui.text(f"Animation ID: {living_agent.animation_id}")
 
                    PyImGui.end_table()
    
        if agent.is_item:
            if PyImGui.collapsing_header("Item Agent Data"):
                item_agent = agent.item_agent
                flags = PyImGui.TableFlags.Borders | PyImGui.TableFlags.SizingStretchSame | PyImGui.TableFlags.Resizable
                if PyImGui.begin_table(f"itemfields##itemfields{agent.id}", 3,flags):                                
                    PyImGui.table_next_row()
                    PyImGui.table_next_column()
                    PyImGui.text(f"Owner ID: {item_agent.owner_id}")
                    PyImGui.table_next_column()
                    PyImGui.text(f"Item Id: {item_agent.item_id}")
                    PyImGui.table_next_row()
                    PyImGui.table_next_column()
                    PyImGui.text(f"Extra Type: {item_agent.extra_type}")
                    PyImGui.table_next_column()
                    PyImGui.text(f"Hex: {hex(item_agent.extra_type)}")
                    PyImGui.table_next_column()
                    PyImGui.text(f"Bin: {bin(item_agent.extra_type)}")
                    PyImGui.table_next_row()
                    PyImGui.table_next_column()
                    PyImGui.text(f"h00CC: {item_agent.h00CC}")
                    PyImGui.table_next_column()
                    PyImGui.text(f"Hex: {hex(item_agent.h00CC)}")
                    PyImGui.table_next_column()
                    PyImGui.text(f"Bin: {bin(item_agent.h00CC)}")
                    PyImGui.table_next_row()
                    PyImGui.table_next_column()
                    
                    PyImGui.end_table()
                    
        if agent.is_gadget:
            if PyImGui.collapsing_header("Gadget Agent Data"):
                gadget_agent = agent.gadget_agent
                flags = PyImGui.TableFlags.Borders | PyImGui.TableFlags.SizingStretchSame | PyImGui.TableFlags.Resizable
                if PyImGui.begin_table(f"gadgetfields##gadgetfields{agent.id}", 3,flags):                                
                    PyImGui.table_next_row()
                    PyImGui.table_next_column()
                    PyImGui.text(f"Gadget ID: {gadget_agent.gadget_id}")
                    PyImGui.table_next_column()
                    PyImGui.text(f"Extra Type: {gadget_agent.extra_type}")
                    PyImGui.table_next_row()
                    PyImGui.table_next_column()
                    PyImGui.text(f"h00C4: {gadget_agent.h00C4}")
                    PyImGui.table_next_column()
                    PyImGui.text(f"Hex: {hex(gadget_agent.h00C4)}")
                    PyImGui.table_next_column()
                    PyImGui.text(f"Bin: {bin(gadget_agent.h00C4)}")
                    PyImGui.table_next_row()
                    PyImGui.table_next_column()
                    PyImGui.text(f"h00C8: {gadget_agent.h00C8}")
                    PyImGui.table_next_column()
                    PyImGui.text(f"Hex: {hex(gadget_agent.h00C8)}")
                    PyImGui.table_next_column()
                    PyImGui.text(f"Bin: {bin(gadget_agent.h00C8)}")
                    PyImGui.table_next_row()
                    PyImGui.table_next_column()
                    
                    for idx, h00D4 in enumerate(gadget_agent.h00D4):
                        PyImGui.text(f"h00D4[{idx}]")
                        PyImGui.table_next_column()
                        PyImGui.text(f"{h00D4}")
                        PyImGui.table_next_column()
                        PyImGui.text(f"Hex: {hex(h00D4)}")
                        PyImGui.table_next_column()
                        PyImGui.text(f"Bin: {bin(h00D4)}")
                        PyImGui.table_next_row()
                        PyImGui.table_next_column()

                    
                    PyImGui.end_table()

        
    player = GLOBAL_CACHE.Agent.GetAgentByID(GLOBAL_CACHE.Player.GetAgentID())
    nearest_enemy = GLOBAL_CACHE.Agent.GetAgentByID(Routines.Agents.GetNearestEnemy() or 0)
    nearest_ally = GLOBAL_CACHE.Agent.GetAgentByID(Routines.Agents.GetNearestAlly() or 0)
    nearest_item = GLOBAL_CACHE.Agent.GetAgentByID(Routines.Agents.GetNearestItem() or 0)
    nearest_gadget = GLOBAL_CACHE.Agent.GetAgentByID(Routines.Agents.GetNearestGadget() or 0)
    nearest_npc = GLOBAL_CACHE.Agent.GetAgentByID(Routines.Agents.GetNearestNPC() or 0)
    target = GLOBAL_CACHE.Agent.GetAgentByID(GLOBAL_CACHE.Player.GetTargetID() or 0)

    if PyImGui.begin(window_module.window_name, window_module.window_flags):
        if PyImGui.begin_child("NearestAgents Info", size=(600, 230),border=True, flags=PyImGui.WindowFlags.HorizontalScrollbar):
            headers = ["Closest", "ID", "Name", "{x,y,z}", "Type"]
            data = [
                _format_agent_row("Player:", player),
                _format_agent_row("Enemy:", nearest_enemy),
                _format_agent_row("Ally:", nearest_ally),
                _format_agent_row("Item:", nearest_item),
                _format_agent_row("Gadget:", nearest_gadget),
                _format_agent_row("NPC/Minipet:", nearest_npc),
                _format_agent_row("Target:", target),
            ]

            ImGui.table("Nearest Agents Data",headers,data)
            
            PyImGui.text("Targetting:")
            PyImGui.push_item_width(175)
            # Build combo items where index 0 = "All" (Unknown), rest map to Allegiance values 1..6
            combo_items = ["All"] + [a.name for a in Allegiance if a != Allegiance.Unknown]
            SELECTED_ALLIEGANCE = PyImGui.combo("Allegiance", SELECTED_ALLIEGANCE, combo_items)
            PyImGui.pop_item_width()
            PyImGui.same_line(0, -1)

            # Efficiently use the correct pre-filtered array
            if SELECTED_ALLIEGANCE == 0:
                agent_ids = GLOBAL_CACHE.AgentArray.GetAgentArray()
            else:
                allegiance_enum = list(Allegiance)[SELECTED_ALLIEGANCE]
                
                if allegiance_enum == Allegiance.Ally:
                    agent_ids = GLOBAL_CACHE.AgentArray.GetAllyArray()
                elif allegiance_enum == Allegiance.Neutral:
                    agent_ids = GLOBAL_CACHE.AgentArray.GetNeutralArray()
                elif allegiance_enum == Allegiance.Enemy:
                    agent_ids = GLOBAL_CACHE.AgentArray.GetEnemyArray()
                elif allegiance_enum == Allegiance.SpiritPet:
                    agent_ids = GLOBAL_CACHE.AgentArray.GetSpiritPetArray()
                elif allegiance_enum == Allegiance.Minion:
                    agent_ids = GLOBAL_CACHE.AgentArray.GetMinionArray()
                elif allegiance_enum == Allegiance.NpcMinipet:
                    agent_ids = GLOBAL_CACHE.AgentArray.GetNPCMinipetArray()
                else:
                    agent_ids = GLOBAL_CACHE.AgentArray.GetAgentArray()

            # Build combo items: "id - name"
            combo_items = []
            id_map = []
            for agent_id in agent_ids:
                agent = GLOBAL_CACHE.Agent.GetAgentByID(agent_id)
                if agent and agent.id != 0:
                    combo_items.append(f"{agent.id} - {GLOBAL_CACHE.Agent.GetName(agent.id)}")
                    id_map.append(agent.id)  # maintain index mapping

            # Show combo
            PyImGui.push_item_width(175)
            SELECTED_AGENT_INDEX = PyImGui.combo("Agent", SELECTED_AGENT_INDEX, combo_items)

            # Validate selection and update selected agent ID
            if 0 <= SELECTED_AGENT_INDEX < len(id_map):
                SELECTED_AGENT_ID = id_map[SELECTED_AGENT_INDEX]
            else:
                SELECTED_AGENT_ID = 0  # Reset if invalid

            PyImGui.pop_item_width()
            PyImGui.same_line(0, -1)

            # Only show the button if there's a valid agent selected
            if SELECTED_AGENT_ID != 0:
                if PyImGui.button("Set Target"):
                    GLOBAL_CACHE.Player.ChangeTarget(SELECTED_AGENT_ID)

            PyImGui.end_child()
            
        if PyImGui.begin_child("InfoGlobalArea", size=(600, 500),border=True, flags=PyImGui.WindowFlags.HorizontalScrollbar):
            if PyImGui.begin_tab_bar("InfoTabBar"):
                if player.id != 0:
                    if PyImGui.begin_tab_item(f"{"Player"}##tab{player.id}"):
                        _draw_agent_tab_item(player)
                        PyImGui.end_tab_item()
                
                if target.id != 0:
                    if PyImGui.begin_tab_item(f"{"Target"}##tab{target.id}"):
                        _draw_agent_tab_item(target)
                        PyImGui.end_tab_item()
                if nearest_enemy.id != 0:
                    if PyImGui.begin_tab_item(f"{"Enemy"}##tab{nearest_enemy.id}"):
                        _draw_agent_tab_item(nearest_enemy)
                        PyImGui.end_tab_item()
                if nearest_ally.id != 0:
                    if PyImGui.begin_tab_item(f"{"Ally"}##tab{nearest_ally.id}"):
                        _draw_agent_tab_item(nearest_ally)
                        PyImGui.end_tab_item()
                if nearest_item.id != 0:
                    if PyImGui.begin_tab_item(f"{"Item"}##tab{nearest_item.id}"):
                        _draw_agent_tab_item(nearest_item)
                        PyImGui.end_tab_item()
                if nearest_gadget.id != 0:
                    if PyImGui.begin_tab_item(f"{"Gadget"}##tab{nearest_gadget.id}"):
                        _draw_agent_tab_item(nearest_gadget)
                        PyImGui.end_tab_item()
                if nearest_npc.id != 0:
                    if PyImGui.begin_tab_item(f"{"NPC"}##tab{nearest_npc.id}"):
                        _draw_agent_tab_item(nearest_npc)
                        PyImGui.end_tab_item()
                        
                PyImGui.end_tab_bar()
            PyImGui.end_child()
        
    PyImGui.end()
    
def configure():
    pass

def main():
    if not Routines.Checks.Map.MapValid():
        return
    
    DrawMainWindow()

if __name__ == "__main__":
    main()
