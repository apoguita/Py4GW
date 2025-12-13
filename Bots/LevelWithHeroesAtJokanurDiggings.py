import random

import Py4GWCoreLib as GW
from Py4GWCoreLib import *
import time

MODULE_NAME = "Jokanur Leveler"


MAIN_THREAD_NAME = "RunBotSequentialLogic"
SKILL_HANDLING_THREAD_NAME = "SkillHandler"
thread_manager = GW.MultiThreading(2.0, log_actions=True)
is_script_running = False
combat_handler:SkillManager.Autocombat = SkillManager.Autocombat()

def StartSequentialEnviroment():
    global thread_manager, is_script_running
    is_script_running = True
    thread_manager.stop_all_threads()
    # Add sequential threads
    thread_manager.add_thread(MAIN_THREAD_NAME, RunBotSequentialLogic)
    # Watchdog thread is necessary to async close other running threads
    thread_manager.start_watchdog(MAIN_THREAD_NAME)
    
    
def StopSequentialEnviroment():
    global thread_manager, is_script_running
    thread_manager.stop_all_threads()
    is_script_running = False


def DrawWindow():
    global is_script_running
    if GW.PyImGui.begin("Jokan it."):
        GW.PyImGui.text("This Script will set up the sequential envitoment and start the bot")
        button_text = "Start script" if not is_script_running else "Stop script"
        if GW.PyImGui.button(button_text):
            if not is_script_running:
                # set up necessary threads
                print ("Starting sequential environment")
                StartSequentialEnviroment()
            else:
                # Stop all threads and clean environment
                StopSequentialEnviroment()

    GW.PyImGui.end()
    


def RunBotSequentialLogic():
    """Thread function that manages counting based on ImGui button presses."""
    global is_script_running
    print(f"Start in Jokanur and add some henchmen or heroes. Strong enough to kill the skale group outside by the first city.")
    Jok = 491
    Fah = 481
    points_in_outpost = [[-1460, -970]]
    points_outside_out = [[18600, 11400], [18500, 11500]]
    points_outside_in = [[18000, 11800], [19250, 11500], [20365, 9474]]
    while is_script_running:
        x, y = GW.Player.GetXY()
        while GW.Map.GetMapID() != Jok and not GW.Map.IsMapReady():
            if GW.Map.IsMapReady():
                GW.Map.Travel(Jok)
            time.sleep(1)
        for p in points_in_outpost:
            MoveTo(p[0], p[1])
        MoveTo(-3000, -1150, attempts=1)
        time.sleep(1)
        while GW.Map.GetMapID() != Fah or not GW.Map.IsMapReady():
            time.sleep(1)
        # get sunspear scout and bounty     
        scout = GW.Routines.Agents.GetNearestNPCXY(19708, 12294, 100)
        MoveTo(19708, 12294)
        GW.Routines.Sequential.Player.InteractAgent(scout)
        time.sleep(1)
        GW.Routines.Sequential.Player.SendDialog("0x85")
        #useitem(30847)    
        for p in points_outside_out:
            MoveTo(p[0], p[1])
        MoveTo(18000, 11800, attempts=1)
        while GW.Routines.Agents.GetNearestEnemy():
            combat_handler.HandleCombat()    
            time.sleep(2)
        for p in points_outside_in:
            MoveTo(p[0], p[1])
        MoveTo(21000, 9000, attempts=1)
        time.sleep(4)


def get_nearest_foe():
    foes = GW.AgentArray.GetEnemyArray()
    dis = 5000 * 5000
    nearest = False
    f: GW.Agent
    for f in foes:
        print(f"foe XY {f.GetXY()}")
        x, y = f.GetXY()
        dist = square_distance(x, y, GW.Player.GetXY()[0], GW.Player.GetXY()[1])
        if dist < dis:
            dis = dist
            nearest = f
    return nearest

def square_distance(x,y, tx, ty):
    return (x-tx)**2 + (y-ty)**2

def MoveTo(tx, ty, variance = 150, rnd = 100, attempts = 120):
    x, y = GW.Player.GetXY()
    while square_distance(x, y, tx, ty) > variance * variance and attempts > 0:
        GW.Player.Move(tx + random.random() * rnd, ty + random.random() * rnd)
        time.sleep(0.5)
        x, y = GW.Player.GetXY()
        attempts -= 1
    
def useitem(model_id):
    item = Item.GetItemIdFromModelID(model_id)
    GW.Inventory.UseItem(item)
    
#endregion   
def main():
    global is_script_running, thread_manager
    
    if is_script_running:
        thread_manager.update_all_keepalives()

    DrawWindow()


if __name__ == "__main__":
    main()
