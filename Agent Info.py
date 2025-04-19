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
            while not Agent.IsNameReady(agent_id) and retries < 10:
                retries += 1
                sleep(0.1)
            name = Agent.GetName(agent_id)
            new_name_map[agent_id] = 
            
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
def DrawMainWindow():
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

    if PyImGui.begin(window_module.window_name, window_module.window_flags):
        
        player = Agent.agent_instance(Player.GetAgentID())
        nearest_enemy = Agent.agent_instance(Routines.Agents.GetNearestEnemy() or 0)
        nearest_ally = Agent.agent_instance(Routines.Agents.GetNearestAlly() or 0)
        nearest_item = Agent.agent_instance(Routines.Agents.GetNearestItem() or 0)
        nearest_gadget = Agent.agent_instance(Routines.Agents.GetNearestGadget() or 0)
        nearest_npc = Agent.agent_instance(Routines.Agents.GetNearestNPC() or 0)
        target = Agent.agent_instance(Player.GetTargetID() or 0)

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
        
        gadget_array = AgentArray.GetGadgetArray()
        for gadget_id in gadget_array:
           PyImGui.text(f"Gadget ID: {gadget_id}")

        
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
