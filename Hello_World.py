from Py4GWCoreLib.BottingTree import BottingTree
from Py4GWCoreLib.IniManager import IniManager
from Py4GWCoreLib.py4gwcorelib_src.BehaviorTree import BehaviorTree
from Py4GWCoreLib import *

import PyImGui

model= 3093

def main():
    if PyImGui.begin("Hello World"):
        if PyImGui.button("search model"):
            array = AgentArray.GetAgentArray()
            for aid in array:
                if Agent.GetModelID(aid) == model:
                    print(f"Found agent with model {model}: {aid}")
                    break
    
    PyImGui.end()
    


if __name__ == "__main__":
    main()
