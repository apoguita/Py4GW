from Py4GWCoreLib import *

MODULE_NAME = "A"

action_queue_manager = ActionQueueManager()

def configure():
    pass

def main():
    global action_queue_manager
    
    all_queues = {
            "ACTION",
            "LOOT",
            "MERCHANT",
            "SALVAGE",
            "IDENTIFY", 
            "FAST", 
            "TRANSITION",
        }
    
    if not Routines.Checks.Map.MapValid():
        return
    
    if PyImGui.begin("ActionQueue Monitor", PyImGui.WindowFlags.AlwaysAutoResize):
        if PyImGui.begin_tab_bar("InfoTabBar"):
            for queue_name in all_queues:
                if PyImGui.begin_tab_item(queue_name):
                    action_queue = action_queue_manager.GetAllActionNames(queue_name)
                    if action_queue:
                        PyImGui.text(f"Number of actions in {queue_name}: {len(action_queue)}")
                    else:
                        PyImGui.text(f"No actions in {queue_name}.")
                     
                    if PyImGui.begin_child("InfoCurrentActions", size=(0, 100),border=True, flags=PyImGui.WindowFlags.HorizontalScrollbar):
                        for action in action_queue:
                            PyImGui.text(f"Action: {action}")
                        PyImGui.end_child()
                        
                    PyImGui.separator()
                    action_history = action_queue_manager.GetHistoryNames(queue_name)
                    if action_history:
                        PyImGui.text(f"Number of actions in {queue_name} history: {len(action_history)}")
                    else:
                        PyImGui.text(f"No actions in {queue_name} history.")
                      
                    if PyImGui.button("Clear Action Queue"):
                        action_queue_manager.ResetQueue(queue_name)
                        
                    if PyImGui.button("Clear History"):
                        action_queue_manager.ClearHistory(queue_name)
                        
                    if PyImGui.button("Copy to Clipboard"):
                        PyImGui.set_clipboard_text("\n".join(action_history))
                        
                    if PyImGui.begin_child("InfoHistoryActions", size=(0, 300),border=True, flags=PyImGui.WindowFlags.HorizontalScrollbar):
                        for action in reversed(action_history):
                            PyImGui.text(f"Action: {action}")
                        PyImGui.end_child()
                    PyImGui.end_tab_item() 
            PyImGui.end_tab_bar() 
    PyImGui.end()
    
    
if __name__ == "__main__":
    main()