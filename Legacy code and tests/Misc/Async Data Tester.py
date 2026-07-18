from Py4GWCoreLib import *
import re

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
                    agent_name = Agent.GetNameByID(target)
                    
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
                            agent_names[agent_id] = Agent.GetNameByID(agent_id)
                        
                        
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
                    #the action queue is for sending commands to the game in an orderly fashion
                    #this is to prevent the game from being overwhelmed with commands and time to process them
                    #it is not necessary to send the commands in this way, but its easier for this example
                    action_queue.add_action(Player.SendChatCommand,"deaths")
                    action_queue.add_action(Player.RequestChatHistory)
                    parse_chat_log_recieved = False
                    
                if not parse_chat_log_recieved and Player.IsChatHistoryReady():
                    parse_chat_log_recieved = True
                    parse_chat_log = Player.GetChatHistory()
                    if len(parse_chat_log) > 0:
                        last_line = parse_chat_log[-1]
                        numbers = re.findall(r"\d{1,3}(?:,\d{3})*", last_line) #this is a regex formula to search for the desired numbers
                        numeric_values = [int(num.replace(",", "")) for num in numbers] if numbers else []
                        
                        PyImGui.text(last_line)

                        # Display extracted numbers
                        if len(numeric_values) >= 2:
                            parsed_string = f"Died: {numeric_values[0]}, Experience: {numeric_values[1]}"
                    
                PyImGui.text(parsed_string)





            
                
                          
        PyImGui.end()

    except Exception as e:
        Py4GW.Console.Log("tester", f"Unexpected Error: {str(e)}", Py4GW.Console.MessageType.Error)

chat_throttle_ms = 100 #we need to wait for chat messages to process
chat_throttle_timer = Timer()
chat_throttle_timer.Start()

def main():
    global chat_throttle_timer, chat_throttle_ms
    DrawWindow()
    
    if chat_throttle_timer.HasElapsed(chat_throttle_ms) and not action_queue.is_empty():
        action_queue.execute_next()
        chat_throttle_timer.Reset()

if __name__ == "__main__":
    main()
