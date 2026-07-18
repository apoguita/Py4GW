"""Shared movement, combat, gadget, and completion helpers."""

from __future__ import annotations

import time
from typing import Any
from typing import Generator
from typing import Optional
from typing import Sequence
from typing import Tuple

from Py4GWCoreLib import Agent
from Py4GWCoreLib import AgentArray
from Py4GWCoreLib import Botting
from Py4GWCoreLib import Inventory
from Py4GWCoreLib import Map
from Py4GWCoreLib import Player
from Py4GWCoreLib import Routines
from Py4GWCoreLib import TitleID

Point = Tuple[float, float]


def free_inventory_slots() -> int:
    try:
        return int(Inventory.GetFreeSlotCount())
    except Exception:
        return 0


def is_party_wiped() -> bool:
    """True when the player is dead (party wipe / defeat)."""
    try:
        me = Player.GetAgentID()
        if me and Agent.IsDead(me):
            return True
    except Exception:
        pass
    return False


def is_mission_bitmap_complete(map_id: int, hard_mode: bool) -> bool:
    """Best-effort bitmap check; mission indices often align with map IDs."""
    try:
        data = Player.GetMissionsCompletedHM() if hard_mode else Player.GetMissionsCompleted()
    except Exception:
        return False
    if not data:
        return False
    # Bitmap array: each entry is a 32-bit mask. Index by map_id bit.
    word = map_id // 32
    bit = map_id % 32
    if word < 0 or word >= len(data):
        return False
    return bool(data[word] & (1 << bit))


def mission_succeeded(completion_map: int, hard_mode: bool, ran_attempt: bool) -> bool:
    if not ran_attempt:
        return False
    try:
        if Map.GetMapID() == completion_map:
            return True
    except Exception:
        pass
    return is_mission_bitmap_complete(completion_map, hard_mode)


def configure_aggressive(bot: Botting) -> None:
    bot.Templates.Aggressive()


def aggro_path(bot: Botting, points: Sequence[Point], step_name: str = '') -> None:
    bot.Move.FollowAutoPathAggro(list(points), step_name=step_name or 'AggroPath')


def move_path(bot: Botting, points: Sequence[Point], step_name: str = '') -> None:
    bot.Move.FollowPath(list(points), step_name=step_name or 'MovePath')


def interact_gadget_id(bot: Botting, gadget_id: int, step_name: str = '') -> None:
    bot.Interact.WithGadgetID(gadget_id, step_name=step_name or f'Gadget_{gadget_id}')


def interact_gadget_xy(bot: Botting, x: float, y: float, step_name: str = '') -> None:
    bot.Move.XYAndInteractGadget(x, y, step_name=step_name or 'GadgetXY')


def interact_npc_xy(bot: Botting, x: float, y: float, step_name: str = '') -> None:
    bot.Interact.WithNpcAtXY(x, y, step_name=step_name or 'NPC')


def set_title(bot: Botting, title_id: int) -> None:
    bot.Player.SetTitle(title_id)


def skip_cinematic_coro(timeout_ms: int = 30000) -> Generator[Any, Any, None]:
    deadline = time.time() + (timeout_ms / 1000.0)
    while time.time() < deadline:
        if is_party_wiped():
            return
        if Map.IsInCinematic():
            Map.SkipCinematic()
            yield from Routines.Yield.wait(1000)
            # Wait for map to stabilize after cinematic.
            stable = 0
            while stable < 8000:
                if Map.IsMapReady() and not Map.IsMapLoading() and not Map.IsInCinematic():
                    break
                yield from Routines.Yield.wait(250)
                stable += 250
            return
        yield from Routines.Yield.wait(250)


def add_skip_cinematic(bot: Botting, name: str = 'Skip Cinematic', timeout_ms: int = 30000) -> None:
    def _state():
        yield from skip_cinematic_coro(timeout_ms)

    bot.States.AddCustomState(_state, name)


def wait_for_map(bot: Botting, map_id: int, step_name: str = '') -> None:
    bot.Wait.ForMapToChange(target_map_id=map_id)


def pickup_nearby_loot_coro(timeout_ms: int = 30000) -> Generator[Any, Any, None]:
    """Loot items in range for up to timeout_ms."""
    deadline = time.time() + (timeout_ms / 1000.0)
    while time.time() < deadline:
        if is_party_wiped():
            return
        try:
            items = AgentArray.GetItemArray()
        except Exception:
            items = []
        if not items:
            return
        me = Player.GetAgentID()
        px, py = Player.GetXY()
        nearest = None
        nearest_dist = 2500.0 ** 2
        for item_id in items:
            try:
                ix, iy = Agent.GetXY(item_id)
            except Exception:
                continue
            d2 = (ix - px) ** 2 + (iy - py) ** 2
            if d2 < nearest_dist:
                nearest_dist = d2
                nearest = item_id
        if nearest is None:
            return
        try:
            Player.Interact(nearest)
        except Exception:
            pass
        yield from Routines.Yield.wait(350)


def add_pickup_loot(bot: Botting, name: str = 'Pickup Loot', timeout_ms: int = 30000) -> None:
    def _state():
        yield from pickup_nearby_loot_coro(timeout_ms)

    bot.States.AddCustomState(_state, name)


def find_agent_by_player_number(player_number: int, max_range: float = 3500.0) -> Optional[int]:
    me = Player.GetAgentID()
    px, py = Player.GetXY()
    try:
        allies = AgentArray.GetAllyArray()
    except Exception:
        allies = []
    best = None
    best_d2 = max_range ** 2
    for aid in allies:
        try:
            if Agent.GetPlayerNumber(aid) != player_number:
                continue
            if Agent.IsDead(aid):
                continue
            ax, ay = Agent.GetXY(aid)
            d2 = (ax - px) ** 2 + (ay - py) ** 2
            if d2 <= best_d2:
                best_d2 = d2
                best = aid
        except Exception:
            continue
    return best


def interact_model_player_number_coro(player_number: int, max_range: float = 3500.0) -> Generator[Any, Any, bool]:
    agent_id = find_agent_by_player_number(player_number, max_range)
    if agent_id is None:
        return False
    try:
        ax, ay = Agent.GetXY(agent_id)
        yield from Routines.Yield.Movement.FollowPath([(ax, ay)])
        Player.Interact(agent_id)
        yield from Routines.Yield.wait(2000)
        return True
    except Exception:
        return False


TITLE_VANGUARD = int(TitleID.Ebon_Vanguard)
TITLE_LIGHTBRINGER = int(TitleID.Lightbringer)
