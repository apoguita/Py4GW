from Py4GWCoreLib import*
import time

#VARIABLES
module_name = "travel test"

class AppState :
    def __init__(self) :
        self.radio_button_selected = 0

state = AppState()


class BotVars:
    def __init__(self, map_id=0):
        self.costumebrawl_map = 721 #COSTUME BRAWL
        self.dragonarena_map = 368 #DRAGON ARENA
        self.dwaynavsgrenth_map = 253 #DWAYNA VS GRENTH
        self.ebonycitadel_map = 445 #EBONY CITADEL OF MALLYX     
        self.chinesela_map = 810 #CHINESE LA 
        self.scarredpsyche_map = 868 #SCARRED PSYCHE
        self.rollerbeetle_map = 467 #ROLLERBEETLE RACING
        self.snowballfight_map = 855 #SNOWBALL FIGHT
        self.bot_started = False
        self.window_module = None
        self.variables = {}

follow_delay_timer = Timer()      

PyPlayer.PyPlayer()
player_instance = PyPlayer.PyPlayer()
timer_instance = Py4GW.Timer()
elapsed_time = timer_instance.get_elapsed_time()
has_elapsed_300000ms = timer_instance.has_elapsed(300000)
text_input = "resign"

bot_vars = BotVars() 
bot_vars.window_module = ImGui.WindowModule(module_name, window_name="Wick Divinus - OUTPOST HACK", window_size=(250, 350))

#FUNCTIONS
def StartBot():
    global bot_vars
    bot_vars.bot_started = True

def StopBot():
    global bot_vars
    bot_vars.bot_started = False

def IsBotStarted():
    global bot_vars
    return bot_vars.bot_started

def ResetEnvironment():
    global FSM_vars
    FSM_vars.state_machine_costumebrawl.reset()
    FSM_vars.state_machine_dragonarena.reset()
    FSM_vars.state_machine_dwaynavsgrenth.reset()
    FSM_vars.state_machine_ebonycitadel.reset()
    FSM_vars.state_machine_chinesela.reset()
    FSM_vars.state_machine_scarredpsyche.reset()
    FSM_vars.state_machine_rollerbeetle.reset()
    FSM_vars.state_machine_snowballfight.reset()
    FSM_vars.state_machine_enterbattle.reset()
    FSM_vars.movement_handler.reset()
    

def check_and_resign():
    if Map.GetInstanceUptime() >= 300000:  # 300000 ms = 5 minutes
        player_instance.SendChatCommand("resign")
    else:
        # Ricontrolla dopo 5 secondi
        threading.Timer(5, check_and_resign).start()

def freeze_until_outpost_or_explorable():
    import time
    for _ in range(90):  # 90 iterations = ~90 seconds total
        if Map.IsOutpost() or Map.IsExplorable():
            break  # Stop waiting if exit condition is met
        time.sleep(1)  # Check every second instead of blocking for 90 sec


#FSM
class StateMachineVars:
    def __init__(self):

        self.movement_handler = Routines.Movement.FollowXY()
        self.last_skill_time = 0
        self.current_skill_index = 1
        
        #FSM COSTUME BRAWL
        self.state_machine_costumebrawl = FSM("COSTUME BRAWL")
                
        #FSM DRAGON ARENA
        self.state_machine_dragonarena = FSM("DRAGON ARENA")

        #FSM DWAYNA VS GRENTH
        self.state_machine_dwaynavsgrenth = FSM("DWAYNA VS GRENTH")

        #FSM EBONY CITADEL OF MALLYX
        self.state_machine_ebonycitadel = FSM("EBONY CITADEL OF MALLYX")

        #FSM CHINESE LA
        self.state_machine_chinesela = FSM("CHINESE LA")

        #FSM SCARRED PSYCHE
        self.state_machine_scarredpsyche = FSM("SCARRED PSYCHE")

        #FSM ROLLERBEETLE RACING
        self.state_machine_rollerbeetle = FSM("ROLLERBEETLE RACING")

        #FSM SNOWBALL FIGHT
        self.state_machine_snowballfight = FSM("SNOWBALL FIGHT")

        #FSM ENTER BATTLE
        self.state_machine_enterbattle = FSM("ENTER BATTLE")
        self.state_machine_enterbattle.instance_start_time = Map.GetInstanceUptime()

FSM_vars = StateMachineVars()
            
#FSM COSTUME BRAWL
FSM_vars.state_machine_costumebrawl.AddState(name="TRAVEL TO COSTUME BRAWL",
                       execute_fn=lambda:Map.Travel(bot_vars.costumebrawl_map),
                       exit_condition=lambda: Map.IsOutpost(),
                       transition_delay_ms=70,
                       run_once=True)

FSM_vars.state_machine_costumebrawl.AddState(name="HACK TRAVEL",
                       execute_fn=lambda:Map.TravelToDistrict(map_id=795, district_number=2),
                       exit_condition=lambda: Map.IsOutpost() or FSM_vars.state_machine_costumebrawl.jump_to_state(0),
                       transition_delay_ms=5000,
                       run_once=True)

#FSM DRAGON ARENA
FSM_vars.state_machine_dragonarena.AddState(name="TRAVEL TO DRAGON ARENA",
                       execute_fn=lambda:Map.Travel(bot_vars.dragonarena_map),
                       exit_condition=lambda: Map.IsOutpost(),
                       transition_delay_ms=50,
                       run_once=True)

FSM_vars.state_machine_dragonarena.AddState(name="HACK TRAVEL",
                       execute_fn=lambda:Map.TravelToDistrict(map_id=795, district_number=2),
                       exit_condition=lambda: Map.IsOutpost() or FSM_vars.state_machine_dragonarena.jump_to_state(0),
                       transition_delay_ms=5000,
                       run_once=True)

#FSM DWAYNA VS GRENTH
FSM_vars.state_machine_dwaynavsgrenth.AddState(name="TRAVEL TO DWAYNA VS GRENTH",
                       execute_fn=lambda:Map.Travel(bot_vars.dwaynavsgrenth_map),
                       exit_condition=lambda: Map.IsOutpost(),
                       transition_delay_ms=300,
                       run_once=True)

FSM_vars.state_machine_dwaynavsgrenth.AddState(name="HACK TRAVEL",
                       execute_fn=lambda:Map.TravelToDistrict(map_id=795, district_number=2),
                       exit_condition=lambda: Map.IsOutpost() or FSM_vars.state_machine_dwaynavsgrenth.jump_to_state(0),
                       transition_delay_ms=5000,
                       run_once=True)

#FSM EBONY CITADEL OF MALLYX
FSM_vars.state_machine_ebonycitadel.AddState(name="TRAVEL TO EBONY CITADEL OF MALLYX",
                       execute_fn=lambda:Map.Travel(bot_vars.ebonycitadel_map),
                       exit_condition=lambda: Map.IsOutpost(),
                       transition_delay_ms=300,
                       run_once=True)

FSM_vars.state_machine_ebonycitadel.AddState(name="HACK TRAVEL",
                       execute_fn=lambda:Map.TravelToDistrict(map_id=795, district_number=2),
                       exit_condition=lambda: Map.IsOutpost() or FSM_vars.state_machine_ebonycitadel.jump_to_state(0),
                       transition_delay_ms=5000,
                       run_once=True)

#FSM CHINESE LA
FSM_vars.state_machine_chinesela.AddState(name="TRAVEL TO CHINESE LA",
                       execute_fn=lambda:Map.Travel(bot_vars.chinesela_map),
                       exit_condition=lambda: Map.IsOutpost(),
                       transition_delay_ms=50,
                       run_once=True)

FSM_vars.state_machine_chinesela.AddState(name="HACK TRAVEL",
                       execute_fn=lambda:Map.TravelToDistrict(map_id=795, district_number=1),
                       exit_condition=lambda: Map.IsOutpost() or FSM_vars.state_machine_chinesela.jump_to_state(0),
                       transition_delay_ms=5000,
                       run_once=True)

#FSM SCARRED PSYCHE
FSM_vars.state_machine_scarredpsyche.AddState(name="TRAVEL TO SCARRED PSYCHE",
                       execute_fn=lambda:Map.Travel(bot_vars.scarredpsyche_map),
                       exit_condition=lambda: Map.IsOutpost(),
                       transition_delay_ms=50,
                       run_once=True)

FSM_vars.state_machine_scarredpsyche.AddState(name="HACK TRAVEL",
                       execute_fn=lambda:Map.TravelToDistrict(map_id=795, district_number=2),
                       exit_condition=lambda: Map.IsOutpost() or FSM_vars.state_machine_scarredpsyche.jump_to_state(0),
                       transition_delay_ms=5000,
                       run_once=True)

#FSM ROLLERBEETLE RACING
FSM_vars.state_machine_rollerbeetle.AddState(name="TRAVEL TO ROLLERBEETLE RACING",
                       execute_fn=lambda:Map.Travel(bot_vars.rollerbeetle_map),
                       exit_condition=lambda: Map.IsOutpost(),
                       transition_delay_ms=50,
                       run_once=True)

FSM_vars.state_machine_rollerbeetle.AddState(name="HACK TRAVEL",
                       execute_fn=lambda:Map.TravelToDistrict(map_id=795, district_number=2),
                       exit_condition=lambda: Map.IsOutpost() or FSM_vars.state_machine_rollerbeetle.jump_to_state(0),
                       transition_delay_ms=5000,
                       run_once=True)

#FSM SNOWBALL FIGHT
FSM_vars.state_machine_snowballfight.AddState(name="TRAVEL TO SNOWBALL FIGHT",
                       execute_fn=lambda:Map.Travel(bot_vars.snowballfight_map),
                       exit_condition=lambda: Map.IsOutpost(),
                       transition_delay_ms=50,
                       run_once=True)

FSM_vars.state_machine_snowballfight.AddState(name="HACK TRAVEL",
                       execute_fn=lambda:Map.TravelToDistrict(map_id=795, district_number=2),
                       exit_condition=lambda: Map.IsOutpost() or FSM_vars.state_machine_snowballfight.jump_to_state(0),
                       transition_delay_ms=5000,
                       run_once=True)

#FSM ENTER BATTLE
FSM_vars.state_machine_enterbattle.AddState(name="Check Dishonorable",
                       exit_condition=lambda: not Effects.BuffExists(Player.GetAgentID(), 2546) and not Effects.EffectExists(Player.GetAgentID(), 2546),
                       run_once=False)

FSM_vars.state_machine_enterbattle.AddState(name="ENTER BATTLE",
                       execute_fn=lambda: Map.EnterChallenge(),
                       exit_condition=lambda: Map.IsMapLoading(),
                       run_once=True)

FSM_vars.state_machine_enterbattle.AddState(name="FREEZE",
                       execute_fn=lambda: freeze_until_outpost_or_explorable(),
                       exit_condition=lambda: Map.IsOutpost() or Map.IsExplorable(),
                       transition_delay_ms=5000,
                       run_once=True)

FSM_vars.state_machine_enterbattle.AddState(name="TRAVEL TO DWAYNA VS GRENTH",
                       execute_fn=lambda:Map.Travel(bot_vars.dwaynavsgrenth_map),
                       exit_condition=lambda: Map.IsOutpost(),
                       transition_delay_ms=300,
                       run_once=True)

FSM_vars.state_machine_enterbattle.AddState(name="HACK TRAVEL",
                       execute_fn=lambda:Map.TravelToDistrict(map_id=795, district_number=2),
                       exit_condition=lambda: Map.IsOutpost() or FSM_vars.state_machine_enterbattle.jump_to_state(3), 
                       transition_delay_ms=4000,
                       run_once=True)


#GUI
def DrawWindow():
    global module_name
    global state

    if PyImGui.begin("Wick Divinus OUTPOST HACK"):

        # Radio buttons
        state.radio_button_selected = PyImGui.radio_button("\uf6e2 COSTUME BRAWL", state.radio_button_selected, 0)
        state.radio_button_selected = PyImGui.radio_button("\uf6d5 DRAGON ARENA", state.radio_button_selected, 1)
        state.radio_button_selected = PyImGui.radio_button("\uf2dc DWAYNA VS GRENTH", state.radio_button_selected, 2)
        state.radio_button_selected = PyImGui.radio_button("\uf447 EBONY CITADEL OF MALLYX", state.radio_button_selected, 3)
        state.radio_button_selected = PyImGui.radio_button("\uf6a1 CHINESE LA", state.radio_button_selected, 4)
        state.radio_button_selected = PyImGui.radio_button("\uf54c SCARRED PSYCHE", state.radio_button_selected, 5)
        state.radio_button_selected = PyImGui.radio_button("\uf188 ROLLERBEETLE RACING", state.radio_button_selected, 6)
        state.radio_button_selected = PyImGui.radio_button("\uf7d0 SNOWBALL FIGHT", state.radio_button_selected, 7)
        state.radio_button_selected = PyImGui.radio_button("\uf101 ENTER BATTLE", state.radio_button_selected, 8)
        #state.radio_button_selected = PyImGui.radio_button("\ue20b Resign", state.radio_button_selected, 9)

        # Buttons for starting/stopping the bot
        if IsBotStarted():
            if PyImGui.button(" \uf04d   STOP"):
                ResetEnvironment()
                StopBot()
        else:
            if PyImGui.button(" \uf04b   START"):
                ResetEnvironment()
                StartBot()

    PyImGui.end()


def main():
    global bot_vars, FSM_vars
    global Py4GW_window_state, Py4GW_descriptions, description_index, ping_handler, timer_instance
    global overlay, show_mouse_world_pos, show_area_rings, mark_target

    try:
        DrawWindow()

        if IsBotStarted():
            # Costume Brawl
            if state.radio_button_selected == 0:
                if FSM_vars.state_machine_costumebrawl.is_finished():
                    ResetEnvironment()
                    StopBot()
                else:
                    FSM_vars.state_machine_costumebrawl.update()

            # Dragon Arena
            elif state.radio_button_selected == 1:
                if FSM_vars.state_machine_dragonarena.is_finished():
                    ResetEnvironment()
                    StopBot()
                else:
                    FSM_vars.state_machine_dragonarena.update()

            # Dwayna vs Grenth
            elif state.radio_button_selected == 2:
                if FSM_vars.state_machine_dwaynavsgrenth.is_finished():
                    ResetEnvironment()
                    StopBot()
                else:
                    FSM_vars.state_machine_dwaynavsgrenth.update()

            # Ebony Citadel of Mallyx
            elif state.radio_button_selected == 3:
                if FSM_vars.state_machine_ebonycitadel.is_finished():
                    ResetEnvironment()
                    StopBot()
                else:
                    FSM_vars.state_machine_ebonycitadel.update()

            # Chinese LA
            elif state.radio_button_selected == 4:
                if FSM_vars.state_machine_chinesela.is_finished():
                    ResetEnvironment()
                    StopBot()
                else:
                    FSM_vars.state_machine_chinesela.update()

            # Scarred Psyche
            elif state.radio_button_selected == 5:
                if FSM_vars.state_machine_scarredpsyche.is_finished():
                    ResetEnvironment()
                    StopBot()
                else:
                    FSM_vars.state_machine_scarredpsyche.update()

            # Roller Beetle
            elif state.radio_button_selected == 6:
                if FSM_vars.state_machine_rollerbeetle.is_finished():
                    ResetEnvironment()
                    StopBot()
                else:
                    FSM_vars.state_machine_rollerbeetle.update()

            # Snowball Fight
            elif state.radio_button_selected == 7:
                if FSM_vars.state_machine_snowballfight.is_finished():
                    ResetEnvironment()
                    StopBot()
                else:
                    FSM_vars.state_machine_snowballfight.update()
            
            # Enter Batle
            elif state.radio_button_selected == 8:
                if FSM_vars.state_machine_enterbattle.is_finished():
                    ResetEnvironment() 
                else:
                    FSM_vars.state_machine_enterbattle.update()

    except ImportError as e:
        Py4GW.Console.Log(
            bot_vars.window_module.module_name,
            f"ImportError encountered: {str(e)}",
            Py4GW.Console.MessageType.Error
        )
        Py4GW.Console.Log(
            bot_vars.window_module.module_name,
            f"Stack trace: {traceback.format_exc()}",
            Py4GW.Console.MessageType.Error
        )
    except ValueError as e:
        Py4GW.Console.Log(
            bot_vars.window_module.module_name,
            f"ValueError encountered: {str(e)}",
            Py4GW.Console.MessageType.Error
        )
        Py4GW.Console.Log(
            bot_vars.window_module.module_name,
            f"Stack trace: {traceback.format_exc()}",
            Py4GW.Console.MessageType.Error
        )
    except TypeError as e:
        Py4GW.Console.Log(
            bot_vars.window_module.module_name,
            f"TypeError encountered: {str(e)}",
            Py4GW.Console.MessageType.Error
        )
        Py4GW.Console.Log(
            bot_vars.window_module.module_name,
            f"Stack trace: {traceback.format_exc()}",
            Py4GW.Console.MessageType.Error
        )
    except Exception as e:
        Py4GW.Console.Log(
            bot_vars.window_module.module_name,
            f"Unexpected error encountered: {str(e)}",
            Py4GW.Console.MessageType.Error
        )
        Py4GW.Console.Log(
            bot_vars.window_module.module_name,
            f"Stack trace: {traceback.format_exc()}",
            Py4GW.Console.MessageType.Error
        )
    finally:
        pass


if __name__ == "__main__":
    main()
