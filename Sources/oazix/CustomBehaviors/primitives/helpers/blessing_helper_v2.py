"""
Blessing Helper V2 - Uses encoded names to find NPCs and UIManager for dialog management.
THAT STUFF IS AN WORK-IN-PROGRESS ATTEMPT AND WILL BE MOVED TO THE CORE LIBRARY.
"""
from enum import Enum
from typing import Any, Callable, Dict, Generator

import PyAgent
from Py4GWCoreLib.UIManager import UIManager
from Sources.aC_Scripts.aC_api import Verify_Blessing
from Py4GWCoreLib import AgentArray, Player
from Py4GWCoreLib.Py4GWcorelib import ThrottledTimer
from Py4GWCoreLib.enums import Allegiance, Range
from Py4GWCoreLib.Agent import Agent
from Sources.oazix.CustomBehaviors.primitives import constants
from Sources.oazix.CustomBehaviors.primitives.helpers import custom_behavior_helpers


class BlessingNpcV2(Enum):
    """
    Blessing NPC definitions using encoded names.
    Each entry contains a list of encoded name byte sequences that identify the NPC.
    Fill in the correct encoded name codes for each NPC type.
    """
    # TODO: Fill in encoded names - use enc name tester.py to find the correct codes
    # Format: ([enc_name_bytes_1, enc_name_bytes_2, ...], "display_name")
    Sunspear_Scout              = ([[1, 129, 216, 71, 88, 179, 225, 255, 119, 64, 0, 0], [1, 129, 192, 71, 144, 187, 17, 211, 164, 104, 0, 0]], "Sunspear Scout")     
    Wandering_Priest            = ([], "Wandering Priest")
    Vabbian_Scout               = ([], "Vabbian Scout")
    Ghostly_Scout               = ([], "Ghostly Scout")
    Ghostly_Priest              = ([], "Ghostly Priest")
    Whispers_Informants         = ([], "Whispers Informants")
    Forgotten_Warden            = ([], "Forgotten Warden")
    Kurzick_Priest              = ([], "Kurzick Priest")
    Luxon_Priest                = ([], "Luxon Priest")
    Beacons_of_Droknar          = ([], "Beacons of Droknar")
    Ascalonian_Refugees         = ([], "Ascalonian Refugees")
    Asuran_Krewe                = ([], "Asuran Krewe")
    Norn_Hunters                = ([], "Norn Hunters")

    def __init__(self, encoded_names: list[list[int]], display_name: str):
        self.encoded_names = encoded_names
        self.display_name = display_name


def _match_encoded_name(agent_id: int, npc: BlessingNpcV2) -> bool:
    """Check if an agent's encoded name matches any of the NPC's known encoded names."""
    if not npc.encoded_names:
        return False
    agent_enc_name = PyAgent.PyAgent.GetAgentEncName(agent_id)
    for enc_name in npc.encoded_names:
        if agent_enc_name == enc_name:
            return True
    return False


def find_first_blessing_npc(within_range: float) -> tuple[BlessingNpcV2, int] | None:
    """
    Find the first blessing NPC within range using encoded names.
    Returns tuple of (BlessingNpcV2, agent_id) or None if not found.
    """
    player_pos = Player.GetXY()

    agent_ids: list[int] = AgentArray.GetNPCMinipetArray()
    agent_ids = AgentArray.Filter.ByCondition(agent_ids, lambda agent_id: Agent.IsValid(agent_id))
    agent_ids = AgentArray.Filter.ByDistance(agent_ids, player_pos, within_range)
    agent_ids = AgentArray.Sort.ByDistance(agent_ids, player_pos)

    for agent_id in agent_ids:
        for npc in BlessingNpcV2:
            if _match_encoded_name(agent_id, npc):
                return (npc, agent_id)

    return None


def wait_npc_dialog_visible(timeout_ms: int) -> Generator[Any, None, bool]:
    """Wait until NPC dialog is visible or timeout."""
    throttle_timer = ThrottledTimer(timeout_ms)
    while not throttle_timer.IsExpired():
        if UIManager.IsNPCDialogVisible():
            return True
        yield from custom_behavior_helpers.Helpers.wait_for(100)
    return False


def _generic_dialog_sequence(npc_result: tuple[BlessingNpcV2, int], timeout_ms: int) -> Generator[Any, None, bool]:
    """Generic dialog sequence: just click button 1."""
    throttle_timer = ThrottledTimer(timeout_ms)
    sequence_choices = [1]
    for sequence_choice in sequence_choices:
        while not throttle_timer.IsExpired():
            click_result = UIManager.ClickDialogButton(choice=sequence_choice, debug=constants.DEBUG)
            if not click_result:
                if constants.DEBUG:
                    print(f"impossible to click_dialog_button {sequence_choice}.")
                return False
            yield from custom_behavior_helpers.Helpers.wait_for(500)
    return True


def _norn_sequence(npc_result: tuple[BlessingNpcV2, int], timeout_ms: int) -> Generator[Any, None, bool]:
    """Norn blessing sequence - may require fighting."""
    if constants.DEBUG:
        print(f"start _norn_sequence")

    # Stage 1: wait for challenge dialog
    click_result = UIManager.ClickDialogButton(choice=1, debug=constants.DEBUG)
    if not click_result:
        if constants.DEBUG:
            print(f"impossible to click_dialog_button 1.")
        return False

    # Stage 2: either already blessed or wait for hostility
    yield from custom_behavior_helpers.Helpers.wait_for(1000)
    if Verify_Blessing.has_any_blessing(Player.GetAgentID()):
        return True

    # Stage 3: wait until friendly again
    wait_result = yield from _wait_until_friendly_again(npc_result, timeout_ms)
    if not wait_result:
        if constants.DEBUG:
            print(f"impossible to wait_until_friendly_again 1.")
        return False

    # Stage 4: final interact & blessing
    click_result = UIManager.ClickDialogButton(choice=1, debug=constants.DEBUG)
    if not click_result:
        if constants.DEBUG:
            print(f"impossible to click_dialog_button 1.")
        return False

    return True


def _wait_until_friendly_again(npc_result: tuple[BlessingNpcV2, int], timeout_ms: int) -> Generator[Any, None, bool]:
    """Wait until the NPC is no longer hostile."""
    throttle_timer = ThrottledTimer(timeout_ms)
    while not throttle_timer.IsExpired():
        if Agent.GetAllegiance(npc_result[1]) != Allegiance.Enemy:
            return True
        yield from custom_behavior_helpers.Helpers.wait_for(500)
    return False


def _kurzick_luxon_sequence(npc_result: tuple[BlessingNpcV2, int], timeout_ms: int) -> Generator[Any, None, bool]:
    """Kurzick/Luxon blessing sequence with donation handling."""
    # Stage 1: initial request → click 1
    click_result = UIManager.ClickDialogButton(choice=1, debug=constants.DEBUG)
    if not click_result:
        if constants.DEBUG:
            print(f"impossible to click_dialog_button 1.")
        return False
    yield from custom_behavior_helpers.Helpers.wait_for(500)

    # Stage 2: donation menu appears → decide bribe vs no-bribe
    count = UIManager.GetDialogButtonCount(constants.DEBUG)
    if constants.DEBUG:
        print(f"get_dialog_button_count = {count}")

    if count == 3:
        # bribe path
        if constants.DEBUG:
            print(f"{npc_result[0].display_name}: click 2 (high donation)")
        click_result = UIManager.ClickDialogButton(choice=2, debug=constants.DEBUG)
        if not click_result:
            if constants.DEBUG:
                print(f"impossible to click_dialog_button 2.")
            return False
        yield from custom_behavior_helpers.Helpers.wait_for(500)
    else:
        # no-bribe path: just close
        if constants.DEBUG:
            print(f"{npc_result[0].display_name}: click 1 (no bribe)")
        click_result = UIManager.ClickDialogButton(choice=1, debug=constants.DEBUG)
        if not click_result:
            if constants.DEBUG:
                print(f"impossible to click_dialog_button 1.")
            return False
        return True

    # Stage 3: confirm large donation → click "1"
    if constants.DEBUG:
        print(f"{npc_result[0].display_name}: click 1 (confirm large donation)")
    click_result = UIManager.ClickDialogButton(choice=1, debug=constants.DEBUG)
    if not click_result:
        if constants.DEBUG:
            print(f"impossible to click_dialog_button 1.")
        return False
    yield from custom_behavior_helpers.Helpers.wait_for(500)

    # Stage 4: final close → click "1" or immediate verify
    if constants.DEBUG:
        print(f"{npc_result[0].display_name}: click 1 (final close)")
    click_result = UIManager.ClickDialogButton(choice=1, debug=constants.DEBUG)
    if not click_result:
        if constants.DEBUG:
            print(f"impossible to click_dialog_button 1.")
        return False
    yield from custom_behavior_helpers.Helpers.wait_for(500)

    if Verify_Blessing.has_any_blessing(Player.GetAgentID()):
        if constants.DEBUG:
            print("has_any_blessing=True")
        return True
    else:
        if constants.DEBUG:
            print("has_any_blessing=False")
        return False


# Dialog sequence mapping
DIALOG_SEQUENCES: Dict[BlessingNpcV2, Callable[[tuple[BlessingNpcV2, int], int], Generator[Any, None, bool]]] = {
    BlessingNpcV2.Sunspear_Scout: _generic_dialog_sequence,
    BlessingNpcV2.Wandering_Priest: _generic_dialog_sequence,
    BlessingNpcV2.Ghostly_Scout: _generic_dialog_sequence,
    BlessingNpcV2.Kurzick_Priest: _kurzick_luxon_sequence,
    BlessingNpcV2.Luxon_Priest: _kurzick_luxon_sequence,
    BlessingNpcV2.Norn_Hunters: _norn_sequence,
}


def run_dialog_sequences(timeout_ms: int) -> Generator[Any, None, bool]:
    """Run the appropriate dialog sequence for the nearby blessing NPC."""
    npc_result: tuple[BlessingNpcV2, int] | None = find_first_blessing_npc(Range.Earshot.value)
    if npc_result is None:
        return False
    if constants.DEBUG:
        print(f"npc_result:{npc_result}")
    npc: BlessingNpcV2 = npc_result[0]

    sequence_execution = DIALOG_SEQUENCES.get(npc, None)
    if sequence_execution is None:
        sequence_execution = _generic_dialog_sequence
    if constants.DEBUG:
        print(f"sequence_execution:{sequence_execution}")

    generator = sequence_execution(npc_result, timeout_ms)
    result = yield from generator
    return result

