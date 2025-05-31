from Py4GWCoreLib import *

MODULE_NAME = "tester for everything"

width, height = 0,0
def main():
    global width, height
    
    if PyImGui.begin("timer test"):
        PyImGui.text(f"is dead: {Agent.IsDead(Player.GetAgentID())}")   
    PyImGui.end()
    
if __name__ == "__main__":
    main()
