from enum import Enum
from typing import Any, Callable, Dict, Generator, List

from Bots.aC_Scripts.aC_api import Blessing_dialog_helper, Verify_Blessing
from Py4GWCoreLib import AgentArray
from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE
from Py4GWCoreLib.Py4GWcorelib import ThrottledTimer
from Py4GWCoreLib.enums import Allegiance, Range
from Widgets.CustomBehaviors.primitives import constants
from Widgets.CustomBehaviors.primitives.helpers import custom_behavior_helpers

class BlessingNpc(Enum):
    Sunspear_Scout              = (4778, 4776)
    Wandering_Priest            = (5384, 5383)
    Vabbian_Scout               = (5632,)
    Ghostly_Scout               = (5547,)
    Ghostly_Priest              = (5615,)
    Whispers_Informants         = (5218, 5683)
    Kurzick_Priest              = (593, 912, 3426)
    Luxon_Priest                = (1947, 3641)
    Beacons_of_Droknar          = (5865,)
    Ascalonian_Refugees         = (1986, 1987, 6044, 6045)
    Asuran_Krewe                = (6755, 6756, 6775) # 6775 can cause issue as shared with many other azura npc...
    Norn_Hunters                = (6374, 6380)

    def __init__(self, *mids: int):
        self.model_ids = mids

def find_first_blessing_npc(within_range:float)  -> tuple[BlessingNpc,int] | None:
    
    player_pos = GLOBAL_CACHE.Player.GetXY()

    agent_ids: list[int] = GLOBAL_CACHE.AgentArray.GetAgentArray()
    agent_ids = AgentArray.Filter.ByCondition(agent_ids, lambda agent_id: GLOBAL_CACHE.Agent.IsValid(agent_id))
    agent_ids = AgentArray.Filter.ByDistance(agent_ids, player_pos, within_range)
    agent_ids = AgentArray.Sort.ByDistance(agent_ids, player_pos)

    for npc in BlessingNpc:
        for agent_id in agent_ids:
            if GLOBAL_CACHE.Agent.GetModelID(agent_id) in npc.model_ids:
                return (npc, agent_id)

    return None

def wait_npc_dialog_visible(timeout_ms:int) -> Generator[Any, None, bool]:
    throttle_timer = ThrottledTimer(timeout_ms)
    while not throttle_timer.IsExpired():
        is_npc_dialog_visible = Blessing_dialog_helper.is_npc_dialog_visible()
        if is_npc_dialog_visible == True: return True
        yield from custom_behavior_helpers.Helpers.wait_for(100)
    return False

def __generic_dialog_sequence(npc_result:tuple[BlessingNpc,int], timeout_ms:int) -> Generator[Any, None, bool]:
    throttle_timer = ThrottledTimer(timeout_ms)
    sequence_choices = [1]
    for sequence_choice in sequence_choices:
        while not throttle_timer.IsExpired():
            click_dialog_button_result = Blessing_dialog_helper.click_dialog_button(choice=sequence_choice, debug=constants.DEBUG)
            if click_dialog_button_result == False: 
                if constants.DEBUG: print(f"impossible to click_dialog_button {sequence_choice}.")
                return False 
            yield from custom_behavior_helpers.Helpers.wait_for(500)
    return True

def __norn_sequence(npc_result:tuple[BlessingNpc,int], timeout_ms:int) -> Generator[Any, None, bool]:
    if constants.DEBUG:print(f"start __norn_sequence")

    # Stage 1: wait for challenge dialog
    click_dialog_button_result = Blessing_dialog_helper.click_dialog_button(choice=1, debug=constants.DEBUG)
    if click_dialog_button_result == False: 
        if constants.DEBUG:print(f"impossible to click_dialog_button 1.")
        return False 

    # Stage 2: either already blessed or wait for hostility
    yield from custom_behavior_helpers.Helpers.wait_for(1000)
    if Verify_Blessing.has_any_blessing(GLOBAL_CACHE.Player.GetAgentID()):
        return True

    # Stage 3: wait until friendly again
    wait_until_friendly_again_result = yield from __wait_until_friendly_again(npc_result, timeout_ms)
    if wait_until_friendly_again_result == False: 
        if constants.DEBUG: print(f"impossible to wait_until_friendly_again_result 1.")
        return False 

    # Stage 4: final interact & blessing
    click_dialog_button_result = Blessing_dialog_helper.click_dialog_button(choice=1, debug=constants.DEBUG)
    if click_dialog_button_result == False: 
        if constants.DEBUG: print(f"impossible to click_dialog_button 1.")
        return False 
    
    return True

def __wait_until_friendly_again(npc_result:tuple[BlessingNpc,int], timeout_ms:int):
    throttle_timer = ThrottledTimer(timeout_ms)
    while not throttle_timer.IsExpired():
        if GLOBAL_CACHE.Agent.GetAllegiance(npc_result[1]) != Allegiance.Enemy: 
            return True
        yield from custom_behavior_helpers.Helpers.wait_for(500)
    return False 

def __kurzick_luxon_sequence(npc_result:tuple[BlessingNpc,int], timeout_ms:int) -> Generator[Any, None, bool]:

    # Stage 0: (possible) pre-interact delay → approach & interact
        # non-leader: hold off for 2 seconds
        # now either leader, or 2 s have passed → actually move + interact

    # Stage 1: initial request → click 1
    click_dialog_button_result = Blessing_dialog_helper.click_dialog_button(choice=1, debug=constants.DEBUG)
    if click_dialog_button_result == False: 
        if constants.DEBUG: print(f"impossible to click_dialog_button 1.")
        return False 
    yield from custom_behavior_helpers.Helpers.wait_for(500)

    # Stage 2: donation menu appears → decide bribe vs no-bribe
    count = Blessing_dialog_helper.get_dialog_button_count(True)
    if constants.DEBUG: print(f"get_dialog_button_count = {count}")

    if count == 3:
        # bribe path
        if constants.DEBUG: print(f"{npc_result[0].name}: click 2 (high donation)")
        click_dialog_button_result = Blessing_dialog_helper.click_dialog_button(choice=2, debug=constants.DEBUG)
        if click_dialog_button_result == False: 
            if constants.DEBUG: print(f"impossible to click_dialog_button 2.")
            return False
        yield from custom_behavior_helpers.Helpers.wait_for(500)
    else:
        # no-bribe path: just close
        if constants.DEBUG: print(f"{npc_result[0].name}: click 1 (no bribe)")
        click_dialog_button_result = Blessing_dialog_helper.click_dialog_button(choice=1, debug=constants.DEBUG)
        if click_dialog_button_result == False: 
            if constants.DEBUG: print(f"impossible to click_dialog_button 1.")
            return False
        return True
    
    # Stage 3: confirm large donation → click “1”
    if constants.DEBUG: print(f"{npc_result[0].name}: click 1 (confirm large donation)")
    click_dialog_button_result = Blessing_dialog_helper.click_dialog_button(choice=1, debug=constants.DEBUG)
    if click_dialog_button_result == False: 
        if constants.DEBUG: print(f"impossible to click_dialog_button 1.")
        return False
    yield from custom_behavior_helpers.Helpers.wait_for(500)

    # Stage 4: final close → click “1” or immediate verify
    if constants.DEBUG: print(f"{npc_result[0].name}: click 1 (final close)")
    click_dialog_button_result = Blessing_dialog_helper.click_dialog_button(choice=1, debug=constants.DEBUG)
    if click_dialog_button_result == False: 
        if constants.DEBUG: print(f"impossible to click_dialog_button 1.")
        return False
    yield from custom_behavior_helpers.Helpers.wait_for(500)

    if Verify_Blessing.has_any_blessing(GLOBAL_CACHE.Player.GetAgentID()):
        if constants.DEBUG: print("has_any_blessing=True")
        return True
    else:
        if constants.DEBUG: print("has_any_blessing=False")
        return False    

DIALOG_SEQUENCES_NEW: Dict[BlessingNpc, Callable[[tuple[BlessingNpc,int], int], Generator[Any, None, bool]]] = {
    BlessingNpc.Sunspear_Scout: __generic_dialog_sequence,
    BlessingNpc.Wandering_Priest: __generic_dialog_sequence,
    BlessingNpc.Ghostly_Scout: __generic_dialog_sequence,
    BlessingNpc.Kurzick_Priest: __kurzick_luxon_sequence,
    BlessingNpc.Luxon_Priest: __kurzick_luxon_sequence,
    BlessingNpc.Norn_Hunters: __norn_sequence,
}

def run_dialog_sequences(timeout_ms:int) -> Generator[Any, None, bool]:
    npc_result:tuple[BlessingNpc,int] | None = find_first_blessing_npc(Range.Earshot.value)
    if npc_result is None: return False
    if constants.DEBUG:print(f"npc_result:{npc_result}")
    npc:BlessingNpc = npc_result[0]

    sequence_execution = DIALOG_SEQUENCES_NEW.get(npc, None)
    if sequence_execution is None: sequence_execution = __generic_dialog_sequence
    if constants.DEBUG:print(f"sequence_execution:{sequence_execution}")

    generator = sequence_execution(npc_result, timeout_ms)
    result = yield from generator
    return result
