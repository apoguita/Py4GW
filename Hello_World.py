from Py4GWCoreLib import *


def DrawWindow():

    try:
        if PyImGui.begin("Has Buff?"):
            has_buff = Effects.BuffExists(Player.GetAgentID(), 2546) or Effects.EffectExists(Player.GetAgentID(), 2546)
            PyImGui.text(f"status of the buff {has_buff}")
        PyImGui.end()

    except Exception as e:
        Py4GW.Console.Log("tester", f"Unexpected Error{str(e)}", Py4GW.Console.MessageType.Error)



def main():
    DrawWindow()

if __name__ == "__main__":
    main()