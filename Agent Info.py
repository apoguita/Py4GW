from Py4GWCoreLib import *

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

#region AgentNames
class AgentArrayNames:
    global RAW_AGENT_ARRAY
    def __init__(self):
        self.agents = AgentArray.GetRawAgentArray()
        self.agent_names = {}
        self.update_queue:ThrottledTimer = ThrottledTimer(500)
        self.thread_manager = MultiThreading(log_actions=False)
        self.requesting_names = False

    def request_agent_names(self):
        if self.requesting_names:
            self.update_queue.Reset()
            return
        self.requesting_names = True
        requested_ids = set()
        
        for agent in self.agents:
            if agent:
                Agent.RequestName(agent.id)
                requested_ids.add(agent.id)

        sleep(0.1)
        
        new_name_map = {}
        
        for agent_id in requested_ids:
            retries = 0
            while not Agent.IsNameReady(agent_id) and retries < 20:
                retries += 1
                sleep(0.1)
            name = Agent.GetName(agent_id)
            new_name_map[agent_id] = name
            
        self.requesting_names = False
        self.agent_names = new_name_map  # Replace the whole cache
        self.requesting_names = False
            
    def get_name(self, agent_id):
        if agent_id in self.agent_names:
            return self.agent_names[agent_id]
        else:
            return "Unknown"
        
    def reset(self):
        self.agents = []
        self.agent_names = {}
        self.update_queue.Reset()
        self.requesting_names = False
        self.thread_manager.stop_thread("self.request_agent_names")
        
    def update(self):
        self.agents = AgentArray.GetRawAgentArray()
            
        if self.update_queue.IsExpired() and self.agents:
            AGENT_NAMES.thread_manager.stop_thread("self.request_agent_names")
            AGENT_NAMES.thread_manager.add_thread("self.request_agent_names", self.request_agent_names)
            AGENT_NAMES.update_queue.Reset()
    
AGENT_NAMES = AgentArrayNames()

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
            AGENT_NAMES.get_name(agent.id),
            f"({agent.x:.2f}, {agent.y:.2f}, {agent.z:.2f})",
            _get_type(agent)
        )
        
    player = Agent.agent_instance(Player.GetAgentID())
    nearest_enemy = Agent.agent_instance(Routines.Agents.GetNearestEnemy() or 0)
    nearest_ally = Agent.agent_instance(Routines.Agents.GetNearestAlly() or 0)
    nearest_item = Agent.agent_instance(Routines.Agents.GetNearestItem() or 0)
    nearest_gadget = Agent.agent_instance(Routines.Agents.GetNearestGadget() or 0)
    nearest_npc = Agent.agent_instance(Routines.Agents.GetNearestNPC() or 0)
    target = Agent.agent_instance(Player.GetTargetID() or 0)

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
                agent = Agent.agent_instance(agent_id)
                if agent and agent.id != 0:
                    combo_items.append(f"{agent.id} - {AGENT_NAMES.get_name(agent.id)}")
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
                    Player.ChangeTarget(SELECTED_AGENT_ID)

            PyImGui.end_child()
            
        if PyImGui.begin_child("InfoGlobalArea", size=(600, 500),border=True, flags=PyImGui.WindowFlags.HorizontalScrollbar):
            if PyImGui.begin_tab_bar("InfoTabBar"):
                agent = player
                tab_name = f"Player: {agent.id} - {AGENT_NAMES.get_name(agent.id)}"
                if agent.id != 0:
                    if PyImGui.begin_tab_item(tab_name):
                        PyImGui.text(f"ID: {agent.id}")
                        PyImGui.text(f"Name: {AGENT_NAMES.get_name(agent.id)}")
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
 
                                PyImGui.text("Terrain Normal")
                                PyImGui.table_next_column()
                                PyImGui.text(f"X: {agent.terrain_normal[0]:.2f}")
                                PyImGui.table_next_column()
                                PyImGui.text(f"Y: {agent.terrain_normal[1]:.2f}")
                                PyImGui.table_next_column()
                                PyImGui.text(f"Z: {agent.terrain_normal[2]:.2f}")
                                PyImGui.table_next_column()
                                PyImGui.text(f"Ground: {agent.ground}")
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
                                
                                PyImGui.end_table()
                                
                        if agent.id == Player.GetAgentID():
                            if PyImGui.collapsing_header(f"Player Instance Exclusive Data:"):
                               PyImGui.text(f"Instance Timer In Frames: {agent.instance_timer_in_frames}")
                               PyImGui.text(f"Instance Timer: {agent.instance_timer}")
                               PyImGui.text(f"Timer2: {agent.timer2}")
                               PyImGui.text(f"Randomizer: {agent.rand1}")
                               PyImGui.text(f"Randomizer2: {agent.rand2}")
                               
                                
                        PyImGui.end_tab_item()
                PyImGui.end_tab_bar()
            PyImGui.end_child()
        
    PyImGui.end()

def main():
    global AGENT_NAMES
    
    if not Routines.Checks.Map.MapValid():
        AGENT_NAMES.reset()
        return
    
    DrawMainWindow()
    
    AGENT_NAMES.update()    
        
if __name__ == "__main__":
    main()
