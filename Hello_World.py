from Py4GWCoreLib import *
import re
import sys

MODULE_NAME = "Frame Tester"



def filter_item_array():
    agent_array = AgentArray.GetAgentArray()
    result_array = []   
    for agent in agent_array:
        if Agent.IsItem(agent):
            result_array.append(agent)
    return result_array

def first_from_array(array):
    if len(array) > 0:
        return array[0]
    return 0

def DrawWindow():
    global item_array
    try:
        item_array = AgentArray.GetItemArray()
        if PyImGui.begin("Frame Tester"):
            PyImGui.text("from item array")
            PyImGui.text("Items: " + ", ".join(str(item) for item in item_array))
            PyImGui.separator()
            fitem_array = filter_item_array()
            PyImGui.text("Filtered Items: " + ", ".join(str(item_id) for item_id in fitem_array))
            
           
            target = 0
            if PyImGui.button("Target Nearest Item"):
                Player.ChangeTarget(first_from_array(fitem_array))
                target = Player.GetTargetID()
                if target != 0:
                    Player.Interact(target,False)
            

        PyImGui.end()

    except Exception as e:
        Py4GW.Console.Log("tester", f"Unexpected Error: {str(e)}", Py4GW.Console.MessageType.Error)






def main():
    DrawWindow()


if __name__ == "__main__":
    main()
