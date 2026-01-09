from Py4GWCoreLib import *

module_name = "Simple Follower"

class GameAreas:
    def __init__(self):
        self.Touch = 144
        self.Adjacent = 166
        self.Nearby = 252
        self.Area = 322
        self.Earshot = 1012  #aggro bubble
        self.Spellcast = 1248
        self.Spirit = 2500
        self.Compass = 5000

follow_distance = GameAreas().Area


def main():
    global module_name, follow_distance
    try:
        if  Party.IsPartyLoaded():
            leader_id = Party.GetPartyLeaderID()
            my_id = Player.GetAgentID()

            if my_id != leader_id:
                leader_x, leader_y = Agent.GetXY(leader_id)
                my_x, my_y = Agent.GetXY(my_id)

                distance = Utils.Distance((leader_x, leader_y), (my_x,my_y))
                if distance > follow_distance:
                    Player.Interact(leader_id)

        

    # Handle specific exceptions to provide detailed error messages
    except ImportError as e:
        Py4GW.Console.Log(module_name, f"ImportError encountered: {str(e)}", Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log(module_name, f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
    except ValueError as e:
        Py4GW.Console.Log(module_name, f"ValueError encountered: {str(e)}", Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log(module_name, f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
    except TypeError as e:
        Py4GW.Console.Log(module_name, f"TypeError encountered: {str(e)}", Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log(module_name, f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
    except Exception as e:
        # Catch-all for any other unexpected exceptions
        Py4GW.Console.Log(module_name, f"Unexpected error encountered: {str(e)}", Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log(module_name, f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
    finally:
        # Optional: Code that will run whether an exception occurred or not
        #Py4GW.Console.Log(module_name, "Execution of Main() completed", Py4GW.Console.MessageType.Info)
        # Place any cleanup tasks here
        pass

# This ensures that Main() is called when the script is executed directly.
if __name__ == "__main__":
    main()
