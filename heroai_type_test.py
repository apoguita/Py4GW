from Py4GWCoreLib import *

from HeroAI.types import PlayerBuff, PlayerStruct, CandidateStruct, MemSkill, GameOptionStruct, GameStruct

MODULE_NAME = "type_tester"

def test_structure(struct_cls, struct_name):
    """Helper function to test if a structure can be instantiated."""
    try:
        instance = struct_cls()
        Py4GW.Console.Log(MODULE_NAME, f"[SUCCEED] {struct_name} instantiated successfully.", Py4GW.Console.MessageType.Info)
    except AttributeError as e:
        Py4GW.Console.Log(MODULE_NAME, f"[FAIL] {struct_name} FAILED: {str(e)}", Py4GW.Console.MessageType.Error)
    except Exception as e:
        Py4GW.Console.Log(MODULE_NAME, f"[FAIL] {struct_name} ERROR: {str(e)}", Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log(MODULE_NAME, traceback.format_exc(), Py4GW.Console.MessageType.Debug)

        
def DrawWindow():
    try:
        if PyImGui.begin("type_tester"):
            if PyImGui.button("Run Tests"):
                Py4GW.Console.Log(MODULE_NAME, "=== Testing ctypes Structures in types.py ===", Py4GW.Console.MessageType.Info)

                test_structure(PlayerBuff, "PlayerBuff")
                test_structure(PlayerStruct, "PlayerStruct")
                test_structure(CandidateStruct, "CandidateStruct")
                test_structure(MemSkill, "MemSkill")
                test_structure(GameOptionStruct, "GameOptionStruct")
                test_structure(GameStruct, "GameStruct")
                
                Py4GW.Console.Log(MODULE_NAME, "=== Test Complete ===", Py4GW.Console.MessageType.Info)

        PyImGui.end()

    except Exception as e:
        Py4GW.Console.Log("tester", f"Unexpected Error: {str(e)}", Py4GW.Console.MessageType.Error)


def main():
    DrawWindow()

if __name__ == "__main__":
    main()
