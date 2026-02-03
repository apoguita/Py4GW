
from Py4GWCoreLib import PyImGui, Agent
from Py4GWCoreLib import ImGui 
from Py4GWCoreLib import Routines
from Py4GWCoreLib import Allegiance
from Py4GWCoreLib import Color
from typing import Tuple
from Py4GWCoreLib import AgentArray, Agent, Player
from Py4GWCoreLib.native_src.context.AgentContext import AgentStruct, AgentLivingStruct, AgentItemStruct, AgentGadgetStruct

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
    def _get_type(agent:AgentStruct) -> str:
        if agent.is_living_type:
            return "Living"
        elif agent.is_item_type:
            return "Item"
        elif agent.is_gadget_type:
            return "Gadget"
        else:
            return "Unknown"
        
    def _format_agent_row(label: str, agent:AgentStruct | None) -> tuple: 
        from Py4GWCoreLib import GLOBAL_CACHE
        if agent is None:
            return (label, "N/A", "N/A", "N/A", "N/A")
        return (
            label,
            agent.agent_id,
            Agent.GetNameByID(agent.agent_id),
            f"({agent.pos.x:.2f}, {agent.pos.y:.2f}, {agent.z:.2f})",
            _get_type(agent)
        )
        
    def _colored_bool(value: bool) -> Tuple[int, int, int, int]:
        return Color(0,255,0,255).to_tuple() if value else Color(255,0,0,255).to_tuple()
    
    def _draw_agent_tab_item(agent_id:  int):
        from Py4GWCoreLib import GLOBAL_CACHE
        _AGENT_ID = agent_id
        PyImGui.text(f"ID: {_AGENT_ID}")
        PyImGui.text(f"Name: {Agent.GetNameByID(_AGENT_ID)}")
        if PyImGui.button("Target Agent"):
            Player.ChangeTarget(_AGENT_ID)
        PyImGui.separator()
        if PyImGui.collapsing_header(f"Positional Data:"):
            flags = PyImGui.TableFlags.Borders | PyImGui.TableFlags.SizingStretchSame | PyImGui.TableFlags.Resizable
            if PyImGui.begin_table(f"PositionalData##PositionalData{_AGENT_ID}", 5,flags):                                
                PyImGui.table_next_row()
                PyImGui.table_next_column()
                PyImGui.text("Position")
                PyImGui.same_line(0,-1)
                if PyImGui.button("Copy to Clipboard"):
                    PyImGui.set_clipboard_text(f"({Agent.GetXY(_AGENT_ID)[0]:.2f}, {Agent.GetXY(_AGENT_ID)[1]:.2f})")
                PyImGui.table_next_column()
                PyImGui.text(f"X: {Agent.GetXYZ(_AGENT_ID)[0]:.2f}")
                PyImGui.table_next_column()
                PyImGui.text(f"Y: {Agent.GetXYZ(_AGENT_ID)[1]:.2f}")
                PyImGui.table_next_column()
                PyImGui.text(f"Z: {Agent.GetXYZ(_AGENT_ID)[2]:.2f}")
                PyImGui.table_next_column()
                PyImGui.text(f"ZPlane {Agent.GetZPlane(_AGENT_ID):.2f}")
                PyImGui.table_next_row()
                PyImGui.table_next_column()
                
                PyImGui.text("Rotation")
                PyImGui.table_next_column()
                PyImGui.text(f"Angle: {Agent.GetRotationAngle(_AGENT_ID):.2f}")
                PyImGui.table_next_column()
                PyImGui.text(f"Cos: {Agent.GetRotationCos(_AGENT_ID):.2f}")
                PyImGui.table_next_column()
                PyImGui.text(f"Sin: {Agent.GetRotationSin(_AGENT_ID):.2f}")
                PyImGui.table_next_row()
                PyImGui.table_next_column()
                
                PyImGui.text("Velocity")
                PyImGui.table_next_column()
                PyImGui.text(f"X: {Agent.GetVelocityXY(_AGENT_ID)[0]:.2f}")
                PyImGui.table_next_column()
                PyImGui.text(f"Y: {Agent.GetVelocityXY(_AGENT_ID)[1]:.2f}")
                PyImGui.table_next_row()
                PyImGui.table_next_column()

                PyImGui.text("Name Tag")
                PyImGui.table_next_column()
                PyImGui.text(f"X: {Agent.GetNameTagXYZ(_AGENT_ID)[0]:.2f}")
                PyImGui.table_next_column()
                PyImGui.text(f"Y: {Agent.GetNameTagXYZ(_AGENT_ID)[1]:.2f}")
                PyImGui.table_next_column()
                PyImGui.text(f"Z: {Agent.GetNameTagXYZ(_AGENT_ID)[2]:.2f}")
                PyImGui.table_next_row()
                PyImGui.table_next_column()
                
                PyImGui.end_table()
                
        if PyImGui.collapsing_header(f"Agent Properties"):
            flags = PyImGui.TableFlags.Borders | PyImGui.TableFlags.SizingStretchSame | PyImGui.TableFlags.Resizable
            if PyImGui.begin_table(f"AgentProperties##AgentProperties{_AGENT_ID}", 5,flags):                                
                PyImGui.table_next_row()
                PyImGui.table_next_column()
                PyImGui.text("Model 1")
                PyImGui.table_next_column()
                PyImGui.text(f"Width: {Agent.GetModelScale1(_AGENT_ID)[0]:.2f}")
                PyImGui.table_next_column()
                PyImGui.text(f"Height: {Agent.GetModelScale1(_AGENT_ID)[1]:.2f}")
                PyImGui.table_next_row()
                PyImGui.table_next_column()
                PyImGui.text("Model 2")
                PyImGui.table_next_column()
                PyImGui.text(f"Width: {Agent.GetModelScale2(_AGENT_ID)[0]:.2f}")
                PyImGui.table_next_column() 
                PyImGui.text(f"Height: {Agent.GetModelScale2(_AGENT_ID)[1]:.2f}")
                PyImGui.table_next_row()
                PyImGui.table_next_column()
                PyImGui.text("Model 3")
                PyImGui.table_next_column()
                PyImGui.text(f"Width: {Agent.GetModelScale3(_AGENT_ID)[0]:.2f}")
                PyImGui.table_next_column()
                PyImGui.text(f"Height: {Agent.GetModelScale3(_AGENT_ID)[1]:.2f}")
                PyImGui.table_next_row()
                PyImGui.table_next_column()
                PyImGui.text(f"Name Properties")
                PyImGui.table_next_column()
                PyImGui.text(f"{Agent.GetNameProperties(_AGENT_ID)}")
                PyImGui.table_next_column()
                PyImGui.text(f"HEX: {hex(Agent.GetNameProperties(_AGENT_ID))}")
                PyImGui.table_next_column()
                PyImGui.text(f"BIN: {bin(Agent.GetNameProperties(_AGENT_ID))}")
                PyImGui.table_next_row()
                PyImGui.table_next_column()
                PyImGui.text(f"Visual Effectes")
                PyImGui.table_next_column()
                PyImGui.text(f"{Agent.GetVisualEffects(_AGENT_ID)}")
                PyImGui.table_next_column()
                PyImGui.text(f"Hex: {hex(Agent.GetVisualEffects(_AGENT_ID))}")
                PyImGui.table_next_column()
                PyImGui.text(f"Bin: {bin(Agent.GetVisualEffects(_AGENT_ID))}")
                PyImGui.table_next_row()
                PyImGui.table_next_column()
                PyImGui.end_table()

                
        if _AGENT_ID == Player.GetAgentID():
            if PyImGui.collapsing_header(f"Player Instance Exclusive Data:"):
            
                PyImGui.text("Terrain Normal")
                PyImGui.table_next_column()
                PyImGui.text(f"X: {Agent.GetTerrainNormalXYZ(_AGENT_ID)[0]:.2f}")
                PyImGui.table_next_column()
                PyImGui.text(f"Y: {Agent.GetTerrainNormalXYZ(_AGENT_ID)[1]:.2f}")
                PyImGui.table_next_column()
                PyImGui.text(f"Z: {Agent.GetTerrainNormalXYZ(_AGENT_ID)[2]:.2f}")
                PyImGui.table_next_column()
                PyImGui.text(f"Ground: {Agent.GetGround(_AGENT_ID):.2f}")
                
                
        if PyImGui.collapsing_header("Attributes"):

            attributes = Agent.GetAttributes(_AGENT_ID)

            headers = ["Attribute", "Base Level", "Level"]
            data = []
            for attribute in attributes:
                data.append((attribute.GetName(), str(attribute.level_base), str(attribute.level)))

            ImGui.table(f"Attributes Info##attinfo{_AGENT_ID}", headers, data)
            
        PyImGui.text_colored("Is Living", _colored_bool(Agent.IsLiving(_AGENT_ID)))
        PyImGui.same_line(0, -1)
        PyImGui.text_colored("Is Item", _colored_bool(Agent.IsItem(_AGENT_ID)))
        PyImGui.same_line(0, -1)
        PyImGui.text_colored("Is Gadget", _colored_bool(Agent.IsGadget(_AGENT_ID)))
        
        if Agent.IsLiving(_AGENT_ID):
            if PyImGui.collapsing_header("Living Agent Data"):
                flags = PyImGui.TableFlags.Borders | PyImGui.TableFlags.SizingStretchSame | PyImGui.TableFlags.Resizable
                if PyImGui.begin_table(f"livingfields##livingfields{_AGENT_ID}", 3,flags):                                
                    PyImGui.table_next_row()
                    PyImGui.table_next_column()
                    PyImGui.text(f"Owner ID: {Agent.GetOwnerID(_AGENT_ID)}")
                    PyImGui.table_next_column()
                    PyImGui.text(f"Player Number/ModelID: {Agent.GetPlayerNumber(_AGENT_ID)}")
                    PyImGui.table_next_column()
                    PyImGui.text(f"Animation Code: {Agent.GetAnimationCode(_AGENT_ID)}")
                    PyImGui.table_next_row()
                    PyImGui.table_next_column()
                    primary, secondary = Agent.GetProfessions(_AGENT_ID)
                    primary_name, secondary_name = Agent.GetProfessionNames(_AGENT_ID)
                    PyImGui.text(f"Primary: [{primary}] {primary_name}")
                    PyImGui.table_next_column()
                    PyImGui.text(f"Secondary: [{secondary}] {secondary_name}")
                    PyImGui.table_next_column()
                    PyImGui.text(f"Level: {Agent.GetLevel(_AGENT_ID)}")
                    PyImGui.table_next_row()
                    PyImGui.table_next_column()
                    PyImGui.text(f"Energy: {Agent.GetEnergy(_AGENT_ID)}")
                    PyImGui.table_next_column()
                    PyImGui.text(f"Max Energy: {Agent.GetMaxEnergy(_AGENT_ID)}")
                    PyImGui.table_next_column()
                    PyImGui.text(f"Energy Regeneration: {Agent.GetEnergyRegen(_AGENT_ID)}")
                    PyImGui.table_next_row()
                    PyImGui.table_next_column()
                    PyImGui.text(f"Health: {Agent.GetHealth(_AGENT_ID)}")
                    PyImGui.table_next_column()
                    PyImGui.text(f"Max Health: {Agent.GetMaxHealth(_AGENT_ID)}")
                    PyImGui.table_next_column()
                    PyImGui.text(f"Health Regeneration: {Agent.GetHealthRegen(_AGENT_ID)}")
                    PyImGui.table_next_row()
                    PyImGui.table_next_column()
                    PyImGui.text(f"Login Number: {Agent.GetLoginNumber(_AGENT_ID)}")
                    PyImGui.table_next_column()
                    PyImGui.text(f"Dagger Status: {Agent.GetDaggerStatus(_AGENT_ID)}")
                    PyImGui.table_next_column()
                    PyImGui.text(f"Allegiance: {Agent.GetAllegiance(_AGENT_ID)[0]} ({Agent.GetAllegiance(_AGENT_ID)[1]})")
                    PyImGui.table_next_row()
                    PyImGui.table_next_column()
                    PyImGui.text(f"Weapon Type: {Agent.GetWeaponType(_AGENT_ID)[0]} ({Agent.GetWeaponType(_AGENT_ID)[1]})")
                    PyImGui.table_next_column()
                    PyImGui.text(f"Weapon Item Type: {Agent.GetWeaponItemType(_AGENT_ID)}")
                    PyImGui.table_next_column()
                    PyImGui.text(f"Offhand Item Type: {Agent.GetOffhandItemType(_AGENT_ID)}")
                    PyImGui.table_next_row()
                    PyImGui.table_next_column()
                    extra_data = Agent.GetWeaponExtraData(_AGENT_ID)
                    weapon_item_id = extra_data[0]
                    offhand_item_id = extra_data[2]
                    PyImGui.text(f"Weapon Item ID: {weapon_item_id}")
                    PyImGui.table_next_column()
                    PyImGui.text(f"Offhand Item ID: {offhand_item_id}")
                    PyImGui.table_next_row()
                    PyImGui.table_next_column()
                    PyImGui.text_colored("Is Bleeding", _colored_bool(Agent.IsBleeding(_AGENT_ID)))
                    PyImGui.table_next_column()
                    PyImGui.text_colored("Is Conditioned", _colored_bool(Agent.IsConditioned(_AGENT_ID)))
                    PyImGui.table_next_column()
                    PyImGui.text_colored("Is Crippled", _colored_bool(Agent.IsCrippled(_AGENT_ID)))
                    PyImGui.table_next_row()
                    PyImGui.table_next_column()
                    PyImGui.text_colored("Is Dead", _colored_bool(Agent.IsDead(_AGENT_ID)))
                    PyImGui.table_next_column()
                    PyImGui.text_colored("Is Deep Wounded", _colored_bool(Agent.IsDeepWounded(_AGENT_ID)))
                    PyImGui.table_next_column()
                    PyImGui.text_colored("Is Poisoned", _colored_bool(Agent.IsPoisoned(_AGENT_ID)))
                    PyImGui.table_next_row()
                    PyImGui.table_next_column()
                    PyImGui.text_colored("Is Enchanted", _colored_bool(Agent.IsEnchanted(_AGENT_ID)))
                    PyImGui.table_next_column()
                    PyImGui.text_colored("Is Degen Hexed", _colored_bool(Agent.IsDegenHexed(_AGENT_ID)))
                    PyImGui.table_next_column()
                    PyImGui.text_colored("Is Hexed", _colored_bool(Agent.IsHexed(_AGENT_ID)))
                    PyImGui.table_next_row()
                    PyImGui.table_next_column()
                    PyImGui.text_colored("Is Weapon Spelled", _colored_bool(Agent.IsWeaponSpelled(_AGENT_ID)))
                    PyImGui.table_next_column()
                    PyImGui.text_colored("In Combat Stance", _colored_bool(Agent.IsInCombatStance(_AGENT_ID)))
                    PyImGui.table_next_column()
                    PyImGui.text_colored("Has Quest", _colored_bool(Agent.HasQuest(_AGENT_ID)))
                    PyImGui.table_next_row()
                    PyImGui.table_next_column()
                    PyImGui.text_colored("Is Dead By Type Map", _colored_bool(Agent.IsDeadByTypeMap(_AGENT_ID)))
                    PyImGui.table_next_column()
                    PyImGui.text_colored("Is Female", _colored_bool(Agent.IsFemale(_AGENT_ID)))
                    PyImGui.table_next_column()
                    PyImGui.text_colored("Has Boss Glow", _colored_bool(Agent.HasBossGlow(_AGENT_ID)))
                    PyImGui.table_next_row()
                    PyImGui.table_next_column()
                    PyImGui.text_colored("Is Hiding Cape", _colored_bool(Agent.IsHidingCape(_AGENT_ID)))
                    PyImGui.table_next_column()
                    PyImGui.text_colored("Can Be Viewed In Party Window", _colored_bool(Agent.CanBeViewedInPartyWindow(_AGENT_ID)))
                    PyImGui.table_next_column()
                    PyImGui.text_colored("Is Spawned", _colored_bool(Agent.IsSpawned(_AGENT_ID)))
                    PyImGui.table_next_row()
                    PyImGui.table_next_column()
                    PyImGui.text_colored("Is Being Observed", _colored_bool(Agent.IsBeingObserved(_AGENT_ID)))
                    PyImGui.table_next_column()
                    PyImGui.text_colored("Is Knocked Down", _colored_bool(Agent.IsKnockedDown(_AGENT_ID)))
                    PyImGui.table_next_column()
                    PyImGui.text_colored("Is Moving", _colored_bool(Agent.IsMoving(_AGENT_ID)))
                    PyImGui.table_next_row()
                    PyImGui.table_next_column()
                    PyImGui.text_colored("Is Attacking", _colored_bool(Agent.IsAttacking(_AGENT_ID)))
                    PyImGui.table_next_column()
                    PyImGui.text_colored("Is Casting", _colored_bool(Agent.IsCasting(_AGENT_ID)))
                    PyImGui.table_next_column()
                    PyImGui.text_colored("Is Idle", _colored_bool(Agent.IsIdle(_AGENT_ID)))
                    PyImGui.table_next_row()
                    PyImGui.table_next_column()
                    PyImGui.text_colored("Is Alive", _colored_bool(Agent.IsAlive(_AGENT_ID)))
                    PyImGui.table_next_column()
                    PyImGui.text_colored("Is Player", _colored_bool(Agent.IsPlayer(_AGENT_ID)))
                    PyImGui.table_next_column()
                    PyImGui.text_colored("Is NPC", _colored_bool(Agent.IsNPC(_AGENT_ID)))
                    PyImGui.table_next_row()
                    PyImGui.table_next_column()
                    PyImGui.text(f"Casting Skill ID: {Agent.GetCastingSkillID(_AGENT_ID)}")
                    PyImGui.table_next_column()
                    PyImGui.text(f"Overcast: {Agent.GetOvercast(_AGENT_ID)}")
                    PyImGui.table_next_column()
                    PyImGui.text(f"Animation Type: {Agent.GetAnimationType(_AGENT_ID)}")
                    PyImGui.table_next_row()
                    PyImGui.table_next_column()
                    PyImGui.text(f"Weapon Attack Speed: {Agent.GetWeaponAttackSpeed(_AGENT_ID)}")
                    PyImGui.table_next_column()
                    PyImGui.text(f"Attack Speed Modifier: {Agent.GetAttackSpeedModifier(_AGENT_ID)}")
                    PyImGui.table_next_column()
                    PyImGui.text(f"Agent Model Type: {Agent.GetAgentModelType(_AGENT_ID)}")
                    PyImGui.table_next_row()
                    PyImGui.table_next_column()
                    PyImGui.text(f"Transmog NPC ID: {Agent.GetTransmogNPCID(_AGENT_ID)}")
                    PyImGui.table_next_column()
                    PyImGui.text(f"Guild ID: {Agent.GetGuildID(_AGENT_ID)}")
                    PyImGui.table_next_column()
                    PyImGui.text(f"Team ID: {Agent.GetTeamID(_AGENT_ID)}")
                    PyImGui.table_next_row()
                    PyImGui.table_next_column()
                    PyImGui.text(f"Effects: {Agent.GetAgentEffects(_AGENT_ID)}")
                    PyImGui.table_next_column()
                    PyImGui.text(f"Hex: {hex(Agent.GetAgentEffects(_AGENT_ID))}")
                    PyImGui.table_next_column()
                    PyImGui.text(f"Bin: {bin(Agent.GetAgentEffects(_AGENT_ID))}")
                    PyImGui.table_next_row()
                    PyImGui.table_next_column()
                    PyImGui.text(f"Model State: {Agent.GetModelState(_AGENT_ID)}")
                    PyImGui.table_next_column()
                    PyImGui.text(f"Hex: {hex(Agent.GetModelState(_AGENT_ID))}")
                    PyImGui.table_next_column()
                    PyImGui.text(f"Bin: {bin(Agent.GetModelState(_AGENT_ID))}")
                    PyImGui.table_next_row()
                    PyImGui.table_next_column()
                    PyImGui.text(f"Type Map: {Agent.GetTypeMap(_AGENT_ID)}")
                    PyImGui.table_next_column()
                    PyImGui.text(f"Hex: {hex(Agent.GetTypeMap(_AGENT_ID))}")
                    PyImGui.table_next_column()
                    PyImGui.text(f"Bin: {bin(Agent.GetTypeMap(_AGENT_ID))}")
                    PyImGui.table_next_row()
                    PyImGui.table_next_column()
                    PyImGui.text(f"Animation Speed: {Agent.GetAnimationSpeed(_AGENT_ID)}")
                    PyImGui.table_next_column()
                    PyImGui.text(f"Animation Code: {Agent.GetAnimationCode(_AGENT_ID)}")
                    PyImGui.table_next_column()
                    PyImGui.text(f"Animation ID: {Agent.GetAnimationID(_AGENT_ID)}")
 
                    PyImGui.end_table()
    
        if Agent.IsItem(_AGENT_ID):
            if PyImGui.collapsing_header("Item Agent Data"):
                flags = PyImGui.TableFlags.Borders | PyImGui.TableFlags.SizingStretchSame | PyImGui.TableFlags.Resizable
                if PyImGui.begin_table(f"itemfields##itemfields{_AGENT_ID}", 3,flags):                                
                    PyImGui.table_next_row()
                    PyImGui.table_next_column()
                    PyImGui.text(f"Owner ID: {Agent.GetItemAgentOwnerID(_AGENT_ID)}")
                    PyImGui.table_next_column()
                    PyImGui.text(f"Item Id: {Agent.GetItemAgentItemID(_AGENT_ID)}")
                    PyImGui.table_next_row()
                    PyImGui.table_next_column()
                    PyImGui.text(f"Extra Type: {Agent.GetItemAgentExtraType(_AGENT_ID)}")
                    PyImGui.table_next_column()
                    PyImGui.text(f"Hex: {hex(Agent.GetItemAgentExtraType(_AGENT_ID))}")
                    PyImGui.table_next_column()
                    PyImGui.text(f"Bin: {bin(Agent.GetItemAgentExtraType(_AGENT_ID))}")
                    PyImGui.table_next_row()
                    PyImGui.table_next_column()
                    PyImGui.text(f"h00CC: {Agent.GetItemAgenth00CC(_AGENT_ID)}")
                    PyImGui.table_next_column()
                    PyImGui.text(f"Hex: {hex(Agent.GetItemAgenth00CC(_AGENT_ID))}")
                    PyImGui.table_next_column()
                    PyImGui.text(f"Bin: {bin(Agent.GetItemAgenth00CC(_AGENT_ID))}")
                    PyImGui.table_next_row()
                    PyImGui.table_next_column()
                    
                    PyImGui.end_table()
                    
        if Agent.IsGadget(_AGENT_ID):
            if PyImGui.collapsing_header("Gadget Agent Data"):
                flags = PyImGui.TableFlags.Borders | PyImGui.TableFlags.SizingStretchSame | PyImGui.TableFlags.Resizable
                if PyImGui.begin_table(f"gadgetfields##gadgetfields{_AGENT_ID}", 3,flags):                                
                    PyImGui.table_next_row()
                    PyImGui.table_next_column()
                    PyImGui.text(f"Gadget ID: {Agent.GetGadgetAgentID(_AGENT_ID)}")
                    PyImGui.table_next_column()
                    PyImGui.text(f"Extra Type: {Agent.GetGadgetAgentExtraType(_AGENT_ID)}")
                    PyImGui.table_next_row()
                    PyImGui.table_next_column()
                    PyImGui.text(f"h00C4: {Agent.GetGadgetAgenth00C4(_AGENT_ID)}")
                    PyImGui.table_next_column()
                    PyImGui.text(f"Hex: {hex(Agent.GetGadgetAgenth00C4(_AGENT_ID))}")
                    PyImGui.table_next_column()
                    PyImGui.text(f"Bin: {bin(Agent.GetGadgetAgenth00C4(_AGENT_ID))}")
                    PyImGui.table_next_row()
                    PyImGui.table_next_column()
                    PyImGui.text(f"h00C8: {Agent.GetGadgetAgenth00C8(_AGENT_ID)}")
                    PyImGui.table_next_column()
                    PyImGui.text(f"Hex: {hex(Agent.GetGadgetAgenth00C8(_AGENT_ID))}")
                    PyImGui.table_next_column()
                    PyImGui.text(f"Bin: {bin(Agent.GetGadgetAgenth00C8(_AGENT_ID))}")
                    PyImGui.table_next_row()
                    PyImGui.table_next_column()
                    
                    for idx, h00D4 in enumerate(Agent.GetGadgetAgenth00D4(_AGENT_ID)):
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

        
    player:AgentStruct | None = Agent.GetAgentByID(Player.GetAgentID() or 0)
    nearest_enemy:AgentStruct | None = Agent.GetAgentByID(Routines.Agents.GetNearestEnemy() or 0)
    nearest_ally:AgentStruct | None = Agent.GetAgentByID(Routines.Agents.GetNearestAlly() or 0)
    nearest_item:AgentStruct | None = Agent.GetAgentByID(Routines.Agents.GetNearestItem() or 0)
    nearest_gadget:AgentStruct | None = Agent.GetAgentByID(Routines.Agents.GetNearestGadget() or 0)
    nearest_npc:AgentStruct | None = Agent.GetAgentByID(Routines.Agents.GetNearestNPC() or 0)
    target:AgentStruct | None = Agent.GetAgentByID(Player.GetTargetID() or 0)

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
                agent_ids = AgentArray.GetAgentArray()
            else:
                allegiance_enum = list(Allegiance)[SELECTED_ALLIEGANCE]
                
                if allegiance_enum == Allegiance.Ally:
                    agent_ids = AgentArray.GetAllyArray()
                elif allegiance_enum == Allegiance.Neutral:
                    agent_ids = AgentArray.GetNeutralArray()
                elif allegiance_enum == Allegiance.Enemy:
                    agent_ids = AgentArray.GetEnemyArray()
                elif allegiance_enum == Allegiance.SpiritPet:
                    agent_ids = AgentArray.GetSpiritPetArray()
                elif allegiance_enum == Allegiance.Minion:
                    agent_ids = AgentArray.GetMinionArray()
                elif allegiance_enum == Allegiance.NpcMinipet:
                    agent_ids = AgentArray.GetNPCMinipetArray()
                else:
                    agent_ids = AgentArray.GetAgentArray()
            # Build combo items: "id - name"
            combo_items = []
            id_map = []
            for agent_id in agent_ids:
                agent = Agent.GetAgentByID(agent_id)
                if agent and agent.agent_id != 0:
                    from Py4GWCoreLib import GLOBAL_CACHE
                    combo_items.append(f"{agent.agent_id} - {Agent.GetNameByID(agent.agent_id)}")
                    id_map.append(agent.agent_id)  # maintain index mapping

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
                    Player.ChangeTarget(SELECTED_AGENT_ID)

            PyImGui.end_child()
            
        if PyImGui.begin_child("InfoGlobalArea", size=(600, 500),border=True, flags=PyImGui.WindowFlags.HorizontalScrollbar):
            if PyImGui.begin_tab_bar("InfoTabBar"):
                if player and player.agent_id != 0:
                    if PyImGui.begin_tab_item(f"{"Player"}##tab{player.agent_id}"):
                        _draw_agent_tab_item(player.agent_id)
                        PyImGui.end_tab_item()
                
                if target and target.agent_id is not None:
                    if PyImGui.begin_tab_item(f"{"Target"}##tab{target.agent_id}"):
                        _draw_agent_tab_item(target.agent_id)
                        PyImGui.end_tab_item()
                if nearest_enemy and nearest_enemy.agent_id != 0:
                    if PyImGui.begin_tab_item(f"{"Enemy"}##tab{nearest_enemy.agent_id}"):
                        _draw_agent_tab_item(nearest_enemy.agent_id)
                        PyImGui.end_tab_item()
                if nearest_ally and nearest_ally.agent_id != 0:
                    if PyImGui.begin_tab_item(f"{"Ally"}##tab{nearest_ally.agent_id}"):
                        _draw_agent_tab_item(nearest_ally.agent_id)
                        PyImGui.end_tab_item()
                if nearest_item and nearest_item.agent_id != 0:
                    if PyImGui.begin_tab_item(f"{"Item"}##tab{nearest_item.agent_id}"):
                        _draw_agent_tab_item(nearest_item.agent_id)
                        PyImGui.end_tab_item()
                if nearest_gadget and nearest_gadget.agent_id != 0:
                    if PyImGui.begin_tab_item(f"{"Gadget"}##tab{nearest_gadget.agent_id}"):
                        _draw_agent_tab_item(nearest_gadget.agent_id)
                        PyImGui.end_tab_item()
                if nearest_npc and nearest_npc.agent_id != 0:
                    if PyImGui.begin_tab_item(f"{"NPC"}##tab{nearest_npc.agent_id}"):
                        _draw_agent_tab_item(nearest_npc.agent_id)
                        PyImGui.end_tab_item()
                        
                PyImGui.end_tab_bar()
            PyImGui.end_child()
        
    PyImGui.end()
    
def tooltip():
    PyImGui.begin_tooltip()

    # Title
    title_color = Color(255, 200, 100, 255)
    ImGui.push_font("Regular", 20)
    PyImGui.text_colored("Agent Info Viewer", title_color.to_tuple_normalized())
    ImGui.pop_font()
    PyImGui.spacing()
    PyImGui.separator()

    # Description
    PyImGui.text("A diagnostic utility providing real-time technical data on all")
    PyImGui.text("active agents within the current instance, including living")
    PyImGui.text("entities, dropped items, and world gadgets.")
    PyImGui.spacing()

    # Features
    PyImGui.text_colored("Features:", title_color.to_tuple_normalized())
    PyImGui.bullet_text("Technical Data: Real-time positional, rotation, and velocity metrics")
    PyImGui.bullet_text("Agent Analysis: Inspection of model scales, attributes, and visual effects")
    PyImGui.bullet_text("Specialized Tabs: Dedicated views for Player, Target, and Nearest agents")
    PyImGui.bullet_text("State Monitoring: Health/Energy regen and status condition tracking")
    PyImGui.bullet_text("Data Tools: Position copying and allegience-filtered agent selection")

    PyImGui.spacing()
    PyImGui.separator()
    PyImGui.spacing()

    # Credits
    PyImGui.text_colored("Credits:", title_color.to_tuple_normalized())
    PyImGui.bullet_text("Developed by Apo")

    PyImGui.end_tooltip()
    
def main():
    if not Routines.Checks.Map.MapValid():
        return
    
    DrawMainWindow()

if __name__ == "__main__":
    main()
