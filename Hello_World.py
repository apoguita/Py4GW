from Py4GWCoreLib import *
import re
import sys

MODULE_NAME = "chat logger"

action_queue = ActionQueue()

agent_name_recieved = True
agent_name = ""
target = 0

agent_ids = []
agent_names = {}

item_id = 0
item_name_recieved = True
item_name = ""

item_ids = []
item_names = {}

chat_log_recieved = True
chat_log = []

parse_chat_log_recieved = True
parse_chat_log = []
parsed_string = ""

def DrawWindow():
    global agent_name_recieved, agent_name, target
    global agent_ids, agent_names
    global item_id, item_name, item_name_recieved
    global item_ids, item_names
    global chat_log_recieved, chat_log
    global action_queue
    global parse_chat_log_recieved, parse_chat_log, parsed_string
    try:
        if PyImGui.begin("Async data Tester"):
            if PyImGui.collapsing_header("Agent Names"):
                if PyImGui.button("Get Target Name"):
                    target = Player.GetTargetID()
                    Agent.RequestName(target)
                    agent_name_recieved = False
                    
                if not agent_name_recieved and Agent.IsNameReady(target):
                    agent_name_recieved = True
                    agent_name = Agent.GetName(target)
                    
                PyImGui.text(f"Target Name: {agent_name}")
                
                PyImGui.separator()
                
                if PyImGui.collapsing_header("NPC Array Names"):
                    if PyImGui.button("Get NPC Array Names"):
                        agent_ids = []
                        agent_names = {}
                        agent_ids = AgentArray.GetNPCMinipetArray()
                        for agent_id in agent_ids:
                            Agent.RequestName(agent_id)
                            
                    for agent_id in agent_ids:
                        if Agent.IsNameReady(agent_id):
                            agent_names[agent_id] = Agent.GetName(agent_id)
                        
                        
                    for agent_id, name in agent_names.items():
                        PyImGui.text(f"Agent {agent_id}: {name}")
                        
            PyImGui.separator()
            
            if PyImGui.collapsing_header("Items"):
                hovered_item = Inventory.GetHoveredItemID()
                if hovered_item != 0:
                    item_id = hovered_item
                    
                item_id = PyImGui.input_int("Item ID", item_id)
                if PyImGui.button("Get Item Name"):
                    Item.RequestName(item_id)
                    item_name = ""
                    item_name_recieved = False
                    
                if not item_name_recieved and Item.IsNameReady(item_id):
                    item_name_recieved = True
                    item_name = Item.GetName(item_id)  
                    
                PyImGui.text(f"Item Name: {item_name}")
                
                PyImGui.separator()
                
                if PyImGui.button("Get Item Array Names"):
                    item_ids = []
                    item_names.clear()
                    bags_to_check = ItemArray.CreateBagList(1, 2, 3, 4)
                    item_ids = ItemArray.GetItemArray(bags_to_check)
                    for item in item_ids:
                        Item.RequestName(item)
                        
                for item_id in item_ids:
                    if Item.IsNameReady(item_id):
                        item_names[item_id] = Item.GetName(item_id)
                        
                for item_id, name in item_names.items():
                    PyImGui.text(f"Item {item_id}: {name}")
                    
            PyImGui.separator()
            
            if PyImGui.collapsing_header("Chat Log"):
                if PyImGui.button("Request Chat History"):
                    chat_log = []
                    Player.RequestChatHistory()
                    chat_log_recieved = False  # Reset flag

                # Poll for chat log readiness
                if not chat_log_recieved and Player.IsChatHistoryReady():
                    chat_log = Player.GetChatHistory()
                    chat_log_recieved = True  # Mark as received

                # Display chat log
                for line in chat_log:
                    PyImGui.text(line)

                PyImGui.separator()
                
                PyImGui.text("this routine will send a chat command and then will parse the outcome")
                if PyImGui.button("Parse Chat Entry"):
                    parse_chat_log = []
                    action_queue.add_action(Player.SendChatCommand,"deaths")
                    action_queue.add_action(Player.RequestChatHistory)
                    parse_chat_log_recieved = False
                    
                if not parse_chat_log_recieved and Player.IsChatHistoryReady():
                    parse_chat_log_recieved = True
                    parse_chat_log = Player.GetChatHistory()
                    if len(parse_chat_log) > 0:
                        last_line = parse_chat_log[-1]
                        numbers = re.findall(r"\d{1,3}(?:,\d{3})*", last_line)
                        numeric_values = [int(num.replace(",", "")) for num in numbers] if numbers else []
                        
                        PyImGui.text(last_line)

                        # Display extracted numbers
                        if len(numeric_values) >= 2:
                            parsed_string = f"Died: {numeric_values[0]}, Experience: {numeric_values[1]}"
                    
                PyImGui.text(parsed_string)
                     
        PyImGui.end()

    except Exception as e:
        Py4GW.Console.Log("tester", f"Unexpected Error: {str(e)}", Py4GW.Console.MessageType.Error)


previous_user_vars = {}

def render_user_variable_monitor():
    global previous_user_vars

    if PyImGui.begin("User Variable Monitor"):
        PyImGui.text("Tracking actively used variables:")

        # Capture the global scope (user script variables)
        global_vars = globals().copy()

        # Capture the local scope of the function that called this one
        frame = sys._getframe(1)  # Get caller's frame
        local_vars = frame.f_locals.copy()  # Get current function locals

        # Merge local and global variables (excluding built-ins and functions)
        user_vars = {k: v for k, v in {**global_vars, **local_vars}.items()
                     if not k.startswith("__") and not callable(v)}

        for key, value in user_vars.items():
            if key not in previous_user_vars:
                PyImGui.text_colored(f"[NEW] {key} = {value}", (0, 1, 0, 1))  # Green for new variables
            elif previous_user_vars[key] != value:
                PyImGui.text_colored(f"[UPDATED] {key} = {value}", (1, 1, 0, 1))  # Yellow for updated variables
            else:
                PyImGui.text(f"{key} = {value}")

        # Detect deleted variables
        for key in previous_user_vars.keys():
            if key not in user_vars:
                PyImGui.text_colored(f"[REMOVED] {key}", (1, 0, 0, 1))  # Red for removed variables

        # Store the current state of variables
        previous_user_vars = user_vars.copy()

    PyImGui.end()




def main():
    DrawWindow()
    render_user_variable_monitor()
    if not action_queue.is_empty():
        action_queue.execute_next()

if __name__ == "__main__":
    main()
