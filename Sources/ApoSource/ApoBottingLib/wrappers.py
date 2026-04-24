import PyImGui

from Py4GWCoreLib.py4gwcorelib_src.BehaviorTree import BehaviorTree
from Py4GWCoreLib.routines_src.BehaviourTrees import BT as RoutinesBT, Routines
from Py4GWCoreLib.native_src.internals.types import Vec2f
from Py4GWCoreLib.enums import Range
from Py4GWCoreLib.enums_src.IO_enums import CHAR_MAP, Key
from Py4GWCoreLib.enums_src.UI_enums import ControlAction
from Py4GWCoreLib.enums_src.Region_enums import District
from Py4GWCoreLib.Agent import Agent
from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE
from Py4GWCoreLib.Map import Map
from Py4GWCoreLib.Player import Player
from Py4GWCoreLib.UIManager import UIManager, WindowFrames
from Py4GWCoreLib.py4gwcorelib_src.ActionQueue import ActionQueueManager
from Py4GWCoreLib.py4gwcorelib_src.Keystroke import Keystroke
from Py4GWCoreLib.py4gwcorelib_src.Lootconfig_src import LootConfig
import random
import time
from types import SimpleNamespace

PointOrPath = Vec2f | list[Vec2f]
DEFAULT_MOVE_TOLERANCE = 150.0
DEFAULT_INTERACT_SETTLE_MS = 250


def _as_path(pos: PointOrPath) -> list[Vec2f]:
    return pos if isinstance(pos, list) else [pos]


def _sequence_from_points(
    name: str,
    points: list[Vec2f],
    leaf_builder,
) -> BehaviorTree:
    if not points:
        return BehaviorTree(
            BehaviorTree.SucceederNode(
                name=f"{name}EmptyPath",
            )
        )

    if len(points) == 1:
        return leaf_builder(points[0])

    return BehaviorTree(
        BehaviorTree.SequenceNode(
            name=name,
            children=[leaf_builder(point) for point in points],
        )
    )

#region LOGGING

def LogMessage(message: str, 
               module_name: str = "ApobottingLib", 
               print_to_console: bool = True, 
               print_to_blackboard: bool = True) -> BehaviorTree:
    return RoutinesBT.Player.LogMessage(
        source=module_name,
        to_console=print_to_console,
        to_blackboard=print_to_blackboard,
        message=message,
    )
    

  
#region Player  
def AutoDialog(button_number: int = 0) -> BehaviorTree:
    return RoutinesBT.Player.SendAutomaticDialog(button_number=button_number)

def Wait(duration_ms: int, log: bool = False) -> BehaviorTree:
    return RoutinesBT.Player.Wait(duration_ms=duration_ms, log=log)

def WaitUntilOnExplorable(timeout_ms: int = 15000) -> BehaviorTree:
    def _wait_until_on_explorable() -> BehaviorTree.NodeState:
        if Routines.Checks.Map.MapValid() and Routines.Checks.Map.IsExplorable():
            return BehaviorTree.NodeState.SUCCESS
        return BehaviorTree.NodeState.RUNNING

    return BehaviorTree(
        BehaviorTree.WaitUntilNode(
            name="WaitUntilOnExplorable",
            condition_fn=_wait_until_on_explorable,
            throttle_interval_ms=500,
            timeout_ms=timeout_ms,
        )
    )

def WaitUntilOutOfCombat(range: float = Range.Earshot.value, timeout_ms: int = 60000) -> BehaviorTree:
    aggro_area = range if hasattr(range, "value") else SimpleNamespace(value=float(range))

    def _wait_until_out_of_combat() -> BehaviorTree.NodeState:
        if not Routines.Checks.Agents.InDanger(aggro_area=aggro_area):
            return BehaviorTree.NodeState.SUCCESS
        return BehaviorTree.NodeState.RUNNING

    return BehaviorTree(
        BehaviorTree.WaitUntilNode(
            name="WaitUntilOutOfCombat",
            condition_fn=_wait_until_out_of_combat,
            throttle_interval_ms=1000,
            timeout_ms=timeout_ms,
        )
    )

def WaitUntilOnCombat(range: float = Range.Earshot.value, timeout_ms: int = 60000) -> BehaviorTree:
    aggro_area = range if hasattr(range, "value") else SimpleNamespace(value=float(range))

    def _wait_until_on_combat() -> BehaviorTree.NodeState:
        if Routines.Checks.Agents.InDanger(aggro_area=aggro_area):
            return BehaviorTree.NodeState.SUCCESS
        return BehaviorTree.NodeState.RUNNING

    return BehaviorTree(
        BehaviorTree.WaitUntilNode(
            name="WaitUntilOnCombat",
            condition_fn=_wait_until_on_combat,
            throttle_interval_ms=1000,
            timeout_ms=timeout_ms,
        )
    )

def PressKeybind(keybind_index: int, duration_ms: int = 75, log: bool = False) -> BehaviorTree:
    return RoutinesBT.Keybinds.PressKeybind(
        keybind_index=keybind_index,
        duration_ms=duration_ms,
        log=log,
    )

def OpenHero() -> BehaviorTree:
    return PressKeybind(Key.H.value)

def OpenSkillsAndAttributes() -> BehaviorTree:
    return PressKeybind(ControlAction.ControlAction_OpenSkillsAndAttributes.value)

def StoreProfessionNames() -> BehaviorTree:
    return RoutinesBT.Player.StoreProfessionNames()

def SaveBlackboardValue(key: str, value, log: bool = False) -> BehaviorTree:
    return RoutinesBT.Player.SaveBlackboardValue(
        key=key,
        value=value,
        log=log,
    )

def LoadBlackboardValue(
    source_key: str,
    target_key: str = "result",
    fail_if_missing: bool = True,
    log: bool = False,
) -> BehaviorTree:
    return RoutinesBT.Player.LoadBlackboardValue(
        source_key=source_key,
        target_key=target_key,
        fail_if_missing=fail_if_missing,
        log=log,
    )

def HasBlackboardValue(key: str, log: bool = False) -> BehaviorTree:
    return RoutinesBT.Player.HasBlackboardValue(
        key=key,
        log=log,
    )

def ClearBlackboardValue(key: str, log: bool = False) -> BehaviorTree:
    return RoutinesBT.Player.ClearBlackboardValue(
        key=key,
        log=log,
    )

def StoreRerollContext(
        character_name_key: str = "reroll_character_name",
        profession_key: str = "reroll_primary_profession",
        campaign_key: str = "reroll_campaign",
        campaign_name: str = "Nightfall",
        fallback_profession: str = "Warrior",
    ) -> BehaviorTree:
    def _store_reroll_context(node: BehaviorTree.Node) -> BehaviorTree.NodeState:
        primary_profession, _ = Agent.GetProfessionNames(Player.GetAgentID())
        node.blackboard[character_name_key] = Player.GetName()
        node.blackboard[profession_key] = primary_profession or fallback_profession
        node.blackboard[campaign_key] = campaign_name
        return BehaviorTree.NodeState.SUCCESS

    return BehaviorTree(
        BehaviorTree.ActionNode(
            name="StoreRerollContext",
            action_fn=_store_reroll_context,
            aftercast_ms=0,
        )
    )

def LogoutToCharacterSelect() -> BehaviorTree:
    def _logout_to_character_select() -> BehaviorTree.NodeState:
        if Map.Pregame.InCharacterSelectScreen():
            return BehaviorTree.NodeState.SUCCESS
        Map.Pregame.LogoutToCharacterSelect()
        return BehaviorTree.NodeState.SUCCESS

    return BehaviorTree(
        BehaviorTree.ActionNode(
            name="LogoutToCharacterSelect",
            action_fn=_logout_to_character_select,
            aftercast_ms=0,
        )
    )

def WaitUntilCharacterSelect(timeout_ms: int = 45000) -> BehaviorTree:
    def _wait_until_character_select() -> BehaviorTree.NodeState:
        if Map.Pregame.InCharacterSelectScreen():
            return BehaviorTree.NodeState.SUCCESS
        return BehaviorTree.NodeState.RUNNING

    return BehaviorTree(
        BehaviorTree.WaitUntilNode(
            name="WaitUntilCharacterSelect",
            condition_fn=_wait_until_character_select,
            throttle_interval_ms=250,
            timeout_ms=timeout_ms,
        )
    )

def ClickWindowFrame(frame_name: str, aftercast_ms: int = 250) -> BehaviorTree:
    def _click_window_frame() -> BehaviorTree.NodeState:
        frame = WindowFrames.get(frame_name)
        if frame is None:
            return BehaviorTree.NodeState.FAILURE
        frame.FrameClick()
        return BehaviorTree.NodeState.SUCCESS

    return BehaviorTree(
        BehaviorTree.ActionNode(
            name=f"ClickWindowFrame({frame_name})",
            action_fn=_click_window_frame,
            aftercast_ms=aftercast_ms,
        )
    )

def TypeTextFromBlackboard(
        key: str,
        delay_ms: int = 50,
        name: str = "TypeTextFromBlackboard",
    ) -> BehaviorTree:
    state = {
        "text": None,
        "index": 0,
        "last_ms": 0.0,
    }

    def _type_text(node: BehaviorTree.Node) -> BehaviorTree.NodeState:
        if state["text"] is None:
            state["text"] = str(node.blackboard.get(key, "") or "")
            state["index"] = 0
            state["last_ms"] = 0.0
            if not state["text"]:
                return BehaviorTree.NodeState.FAILURE

        now = time.monotonic() * 1000
        if state["last_ms"] and now - state["last_ms"] < delay_ms:
            return BehaviorTree.NodeState.RUNNING

        text = state["text"]
        if state["index"] >= len(text):
            state["text"] = None
            state["index"] = 0
            state["last_ms"] = 0.0
            return BehaviorTree.NodeState.SUCCESS

        char = text[state["index"]]
        key_info = CHAR_MAP.get(char)
        if key_info is not None:
            mapped_key, needs_shift = key_info
            if needs_shift:
                Keystroke.Press(Key.LShift.value)
            Keystroke.PressAndRelease(mapped_key.value)
            if needs_shift:
                Keystroke.Release(Key.LShift.value)

        state["index"] += 1
        state["last_ms"] = now
        return BehaviorTree.NodeState.RUNNING

    return BehaviorTree(
        BehaviorTree.ActionNode(
            name=name,
            action_fn=_type_text,
            aftercast_ms=0,
        )
    )

def PasteTextFromBlackboard(
        key: str,
        name: str = "PasteTextFromBlackboard",
    ) -> BehaviorTree:
    def _paste_text(node: BehaviorTree.Node) -> BehaviorTree.NodeState:
        text = str(node.blackboard.get(key, "") or "")
        if not text:
            return BehaviorTree.NodeState.FAILURE
        PyImGui.set_clipboard_text(text)
        Keystroke.PressAndReleaseCombo([Key.Ctrl.value, Key.V.value])
        return BehaviorTree.NodeState.SUCCESS

    return BehaviorTree(
        BehaviorTree.ActionNode(
            name=name,
            action_fn=_paste_text,
            aftercast_ms=0,
        )
    )

def PressRightArrowTimes(
        count_key: str,
        delay_ms: int = 100,
        name: str = "PressRightArrowTimes",
    ) -> BehaviorTree:
    state = {
        "remaining": None,
        "last_ms": 0.0,
    }

    def _press_right_arrow_times(node: BehaviorTree.Node) -> BehaviorTree.NodeState:
        if state["remaining"] is None:
            state["remaining"] = max(0, int(node.blackboard.get(count_key, 0) or 0))
            state["last_ms"] = 0.0

        if state["remaining"] <= 0:
            state["remaining"] = None
            state["last_ms"] = 0.0
            return BehaviorTree.NodeState.SUCCESS

        now = time.monotonic() * 1000
        if state["last_ms"] and now - state["last_ms"] < delay_ms:
            return BehaviorTree.NodeState.RUNNING

        Keystroke.PressAndRelease(Key.RightArrow.value)
        state["remaining"] -= 1
        state["last_ms"] = now
        return BehaviorTree.NodeState.RUNNING

    return BehaviorTree(
        BehaviorTree.ActionNode(
            name=name,
            action_fn=_press_right_arrow_times,
            aftercast_ms=0,
        )
    )

def StoreCampaignArrowCount(
        campaign_key: str = "reroll_campaign",
        count_key: str = "reroll_campaign_arrow_count",
    ) -> BehaviorTree:
    campaign_counts = {
        "Nightfall": 0,
        "Prophecies": 1,
        "Factions": 2,
    }

    def _store_campaign_arrow_count(node: BehaviorTree.Node) -> BehaviorTree.NodeState:
        campaign_name = str(node.blackboard.get(campaign_key, "Nightfall") or "Nightfall")
        node.blackboard[count_key] = campaign_counts.get(campaign_name, 0)
        return BehaviorTree.NodeState.SUCCESS

    return BehaviorTree(
        BehaviorTree.ActionNode(
            name="StoreCampaignArrowCount",
            action_fn=_store_campaign_arrow_count,
            aftercast_ms=0,
        )
    )

def StoreProfessionArrowCount(
        profession_key: str = "reroll_primary_profession",
        count_key: str = "reroll_profession_arrow_count",
    ) -> BehaviorTree:
    profession_counts = {
        "Warrior": 0,
        "Ranger": 1,
        "Monk": 2,
        "Necromancer": 3,
        "Mesmer": 4,
        "Elementalist": 5,
        "Assassin": 6,
        "Ritualist": 7,
        "Paragon": 6,
        "Dervish": 7,
    }

    def _store_profession_arrow_count(node: BehaviorTree.Node) -> BehaviorTree.NodeState:
        profession_name = str(node.blackboard.get(profession_key, "Warrior") or "Warrior")
        node.blackboard[count_key] = profession_counts.get(profession_name, 0)
        return BehaviorTree.NodeState.SUCCESS

    return BehaviorTree(
        BehaviorTree.ActionNode(
            name="StoreProfessionArrowCount",
            action_fn=_store_profession_arrow_count,
            aftercast_ms=0,
        )
    )

def ResolveRerollNewCharacterName(
        character_name_key: str = "reroll_character_name",
        new_character_name_key: str = "reroll_character_name",
    ) -> BehaviorTree:
    def _fallback_name(current_name: str) -> str:
        suffixes = ["A", "B", "C", "D", "E", "F", "K", "H", "I", "J"]
        cleaned = "".join(ch for ch in (current_name or "") if ch.isalpha() or ch == " ")
        cleaned = " ".join(cleaned.split())
        if not cleaned:
            return "Fallback A"
        parts = cleaned.split()
        current_suffix = parts[-1] if parts and parts[-1] in suffixes else None
        while parts and parts[-1] in suffixes:
            parts.pop()
        base_name = " ".join(parts).strip() or "Fallback"
        suffix = suffixes[(suffixes.index(current_suffix) + 1) % len(suffixes)] if current_suffix in suffixes else suffixes[0]
        return f"{base_name} {suffix}"

    def _resolve_new_name(node: BehaviorTree.Node) -> BehaviorTree.NodeState:
        character_name = str(node.blackboard.get(character_name_key, "") or "")
        if not character_name:
            return BehaviorTree.NodeState.FAILURE
        try:
            names = [c.player_name for c in Map.Pregame.GetAvailableCharacterList()]
        except Exception:
            names = []
        node.blackboard[new_character_name_key] = _fallback_name(character_name) if character_name in names else character_name
        return BehaviorTree.NodeState.SUCCESS

    return BehaviorTree(
        BehaviorTree.ActionNode(
            name="ResolveRerollNewCharacterName",
            action_fn=_resolve_new_name,
            aftercast_ms=0,
        )
    )

def DeleteCharacterFromBlackboard(
        character_name_key: str = "reroll_character_name",
        timeout_ms: int = 45000,
    ) -> BehaviorTree:
    return BehaviorTree(
        BehaviorTree.SequenceNode(
            name="DeleteCharacterFromBlackboard",
            children=[
                LogoutToCharacterSelect(),
                WaitUntilCharacterSelect(timeout_ms=timeout_ms),
                Wait(1000),
                ClickWindowFrame("DeleteCharacterButton", aftercast_ms=750),
                PasteTextFromBlackboard(character_name_key, name="PasteDeleteCharacterName"),
                Wait(750),
                ClickWindowFrame("FinalDeleteCharacterButton", aftercast_ms=750),
                Wait(7000),
            ],
        )
    )

def CreateCharacterFromBlackboard(
        character_name_key: str = "reroll_new_character_name",
        campaign_key: str = "reroll_campaign",
        profession_key: str = "reroll_primary_profession",
        timeout_ms: int = 60000,
    ) -> BehaviorTree:
    return BehaviorTree(
        BehaviorTree.SequenceNode(
            name="CreateCharacterFromBlackboard",
            children=[
                WaitUntilCharacterSelect(timeout_ms=timeout_ms),
                Wait(1000),
                ClickWindowFrame("CreateCharacterButton1", aftercast_ms=500),
                ClickWindowFrame("CreateCharacterButton2", aftercast_ms=1000),
                ClickWindowFrame("CreateCharacterTypeNextButton", aftercast_ms=1000),
                StoreCampaignArrowCount(campaign_key=campaign_key),
                PressRightArrowTimes("reroll_campaign_arrow_count", name="SelectCampaign"),
                Wait(500),
                ClickWindowFrame("CreateCharacterNextButtonGeneric", aftercast_ms=1000),
                StoreProfessionArrowCount(profession_key=profession_key),
                PressRightArrowTimes("reroll_profession_arrow_count", name="SelectProfession"),
                Wait(500),
                ClickWindowFrame("CreateCharacterNextButtonGeneric", aftercast_ms=1000),
                ClickWindowFrame("CreateCharacterNextButtonGeneric", aftercast_ms=1000),
                ClickWindowFrame("CreateCharacterNextButtonGeneric", aftercast_ms=1000),
                ClickWindowFrame("CreateCharacterNextButtonGeneric", aftercast_ms=1000),
                PasteTextFromBlackboard(character_name_key, name="PasteCreateCharacterName"),
                Wait(1000),
                ClickWindowFrame("FinalCreateCharacterButton", aftercast_ms=3000),
                Wait(7000),
            ],
        )
    )

def ResetActionQueues() -> BehaviorTree:
    def _reset_action_queues() -> BehaviorTree.NodeState:
        ActionQueueManager().ResetAllQueues()
        return BehaviorTree.NodeState.SUCCESS

    return BehaviorTree(
        BehaviorTree.ActionNode(
            name="ResetActionQueues",
            action_fn=_reset_action_queues,
            aftercast_ms=0,
        )
    )

def CancelSkillRewardWindow() -> BehaviorTree:
    def _cancel_skill_reward_window() -> BehaviorTree.NodeState:
        cancel_button_frame_id = UIManager.GetFrameIDByHash(784833442)
        if not cancel_button_frame_id or not UIManager.FrameExists(cancel_button_frame_id):
            return BehaviorTree.NodeState.SUCCESS
        UIManager.FrameClick(cancel_button_frame_id)
        return BehaviorTree.NodeState.SUCCESS

    return BehaviorTree(
        BehaviorTree.ActionNode(
            name="CancelSkillRewardWindow",
            action_fn=_cancel_skill_reward_window,
            aftercast_ms=1000,
        )
    )

#region Map
def WaitForMapLoad(map_id: int, timeout_ms: int = 30000) -> BehaviorTree:
    return RoutinesBT.Map.WaitforMapLoad(map_id=map_id, timeout=timeout_ms)

def WaitForMapToChange(map_id: int, timeout_ms: int = 30000) -> BehaviorTree:
    return WaitForMapLoad(map_id=map_id, timeout_ms=timeout_ms)


def TravelToOutpost(outpost_id: int) -> BehaviorTree:
    return RoutinesBT.Map.TravelToOutpost(outpost_id=outpost_id)

def TravelToRandomDistrict(target_map_id: int = 0, target_map_name: str = "", region_pool: str = "eu") -> BehaviorTree:
    def _normalize_region_pool() -> str:
        mode = (region_pool or "eu").strip().lower()
        mode = mode.replace("+", "_").replace("-", "_").replace(" ", "_")
        aliases = {
            "euasia": "eu_asia",
            "eu_asia": "eu_asia",
            "asia_only": "asia",
            "eu_only": "eu",
        }
        mode = aliases.get(mode, mode)
        return mode if mode in ("eu", "eu_asia", "asia") else "eu"

    def _get_random_district_candidates() -> list[int]:
        eu = [
            District.EuropeItalian.value,
            District.EuropeSpanish.value,
            District.EuropePolish.value,
            District.EuropeRussian.value,
        ]
        asia = [
            District.AsiaKorean.value,
            District.AsiaChinese.value,
            District.AsiaJapanese.value,
        ]

        mode = _normalize_region_pool()
        if mode == "asia":
            return asia
        if mode == "eu_asia":
            return eu + asia
        return eu

    def _travel_to_random_district(node: BehaviorTree.Node) -> BehaviorTree.NodeState:
        resolved_map_id = Map.GetMapIDByName(target_map_name) if target_map_name else target_map_id
        if resolved_map_id <= 0:
            return BehaviorTree.NodeState.FAILURE
        if Map.IsMapReady() and Map.IsMapIDMatch(Map.GetMapID(), resolved_map_id):
            node.blackboard["travel_to_random_district_target_map_id"] = resolved_map_id
            return BehaviorTree.NodeState.SUCCESS

        district = random.choice(_get_random_district_candidates())
        node.blackboard["travel_to_random_district_target_map_id"] = resolved_map_id
        node.blackboard["travel_to_random_district_district"] = district
        Map.TravelToDistrict(resolved_map_id, district)
        return BehaviorTree.NodeState.SUCCESS

    return BehaviorTree(
        BehaviorTree.SequenceNode(
            name="TravelToRandomDistrict",
            children=[
                BehaviorTree.ActionNode(
                    name="TravelToRandomDistrictAction",
                    action_fn=_travel_to_random_district,
                    aftercast_ms=500,
                ),
                BehaviorTree.SubtreeNode(
                    name="WaitForRandomDistrictMapLoad",
                    subtree_fn=lambda node: WaitForMapLoad(
                        map_id=int(node.blackboard.get("travel_to_random_district_target_map_id", target_map_id)),
                    ),
                ),
            ],
        )
    )

def TravelGH() -> BehaviorTree:
    return RoutinesBT.Map.TravelGH()

def LeaveGH() -> BehaviorTree:
    return RoutinesBT.Map.LeaveGH()

#region Party
def LeaveParty() -> BehaviorTree:
    def _leave_party() -> BehaviorTree.NodeState:
        GLOBAL_CACHE.Party.LeaveParty()
        return BehaviorTree.NodeState.SUCCESS

    return BehaviorTree(
        BehaviorTree.ActionNode(
            name="LeaveParty",
            action_fn=_leave_party,
            aftercast_ms=250,
        )
    )

def AddHero(hero_id: int) -> BehaviorTree:
    def _add_hero() -> BehaviorTree.NodeState:
        GLOBAL_CACHE.Party.Heroes.AddHero(hero_id)
        return BehaviorTree.NodeState.SUCCESS

    return BehaviorTree(
        BehaviorTree.ActionNode(
            name=f"AddHero({hero_id})",
            action_fn=_add_hero,
            aftercast_ms=250,
        )
    )

def AddHeroList(hero_ids: list[int]) -> BehaviorTree:
    return BehaviorTree(
        BehaviorTree.SequenceNode(
            name="AddHeroList",
            children=[AddHero(hero_id).root for hero_id in hero_ids],
        )
    )

def AddHenchman(henchman_id: int) -> BehaviorTree:
    def _add_henchman() -> BehaviorTree.NodeState:
        GLOBAL_CACHE.Party.Henchmen.AddHenchman(henchman_id)
        return BehaviorTree.NodeState.SUCCESS

    return BehaviorTree(
        BehaviorTree.ActionNode(
            name=f"AddHenchman({henchman_id})",
            action_fn=_add_henchman,
            aftercast_ms=250,
        )
    )

def AddHenchmanList(henchman_ids: list[int]) -> BehaviorTree:
    return BehaviorTree(
        BehaviorTree.SequenceNode(
            name="AddHenchmanList",
            children=[AddHenchman(henchman_id).root for henchman_id in henchman_ids],
        )
    )

#region Movement
def Move(
    pos: PointOrPath,
    pause_on_combat: bool = True,
    tolerance: float = DEFAULT_MOVE_TOLERANCE,
) -> BehaviorTree:
    return _sequence_from_points(
        "MovePath",
        _as_path(pos),
        lambda point: RoutinesBT.Player.Move(
            x=point.x,
            y=point.y,
            tolerance=tolerance,
            pause_on_combat=pause_on_combat,
            log=False,
        ),
    )

def MoveAndExitMap(pos: Vec2f, target_map_id: int = 0, target_map_name: str = "") -> BehaviorTree:
    return BehaviorTree(
        BehaviorTree.SequenceNode(
            name="MoveAndExitMap",
            children=[
                Move(pos).root,
                WaitForMapLoad(map_id=target_map_id if target_map_id else Map.GetMapIDByName(target_map_name)).root,
            ],
        )
    )

def MoveDirect(list_of_positions: list[Vec2f], pause_on_combat: bool = True) -> BehaviorTree:
    return RoutinesBT.Player.MoveDirect(list_of_positions, pause_on_combat=pause_on_combat, log=False)

def MoveAndKill(pos: PointOrPath, clear_area_radius: float = Range.Spirit.value) -> BehaviorTree:
    return _sequence_from_points(
        "MoveAndKillPath",
        _as_path(pos),
        lambda point: RoutinesBT.Player.MoveAndKill(
            coords=point,
            clear_area_radius=clear_area_radius,
        ),
    )

def MoveAndTarget(
    pos: PointOrPath,
    target_distance: float = Range.Adjacent.value,
    move_tolerance: float = DEFAULT_MOVE_TOLERANCE,
    log: bool = False,
) -> BehaviorTree:
    points = _as_path(pos)
    return BehaviorTree(
        BehaviorTree.SequenceNode(
            name="MoveAndTargetPath",
            children=[
                *[
                    RoutinesBT.Player.Move(
                        x=point.x,
                        y=point.y,
                        tolerance=move_tolerance,
                        log=False,
                    ).root
                    for point in points[:-1]
                ],
                RoutinesBT.Player.Move(
                    x=points[-1].x,
                    y=points[-1].y,
                    tolerance=move_tolerance,
                    log=False,
                ).root,
                RoutinesBT.Agents.TargetNearestNPCXY(
                    x=points[-1].x,
                    y=points[-1].y,
                    distance=target_distance,
                    log=log,
                ).root,
            ],
        )
    )

def MoveAndInteract(
    pos: PointOrPath,
    target_distance: float = Range.Area.value,
    move_tolerance: float = DEFAULT_MOVE_TOLERANCE,
) -> BehaviorTree:
    points = _as_path(pos)
    return BehaviorTree(
        BehaviorTree.SequenceNode(
            name="MoveAndInteractPath",
            children=[
                *[RoutinesBT.Player.Move(x=point.x, y=point.y, tolerance=move_tolerance, log=False).root for point in points[:-1]],
                RoutinesBT.Player.Move(
                    x=points[-1].x,
                    y=points[-1].y,
                    tolerance=move_tolerance,
                    log=False,
                ).root,
                RoutinesBT.Agents.TargetNearestNPCXY(
                    x=points[-1].x,
                    y=points[-1].y,
                    distance=target_distance,
                    log=False,
                ).root,
                RoutinesBT.Player.InteractTarget(log=False).root,
                Wait(DEFAULT_INTERACT_SETTLE_MS).root,
            ],
        )
    )

def MoveAndAutoDialog(
    pos: PointOrPath,
    button_number: int = 0,
    target_distance: float = Range.Nearby.value,
    move_tolerance: float = DEFAULT_MOVE_TOLERANCE,
) -> BehaviorTree:
    points = _as_path(pos)
    if len(points) <= 1:
        point = points[0]
        return BehaviorTree(
            BehaviorTree.SequenceNode(
                name="MoveAndAutoDialog",
                children=[
                    RoutinesBT.Player.Move(
                        x=point.x,
                        y=point.y,
                        tolerance=move_tolerance,
                        log=False,
                    ).root,
                    RoutinesBT.Agents.TargetNearestNPCXY(
                        x=point.x,
                        y=point.y,
                        distance=target_distance,
                        log=False,
                    ).root,
                    RoutinesBT.Player.InteractTarget(log=False).root,
                    Wait(DEFAULT_INTERACT_SETTLE_MS).root,
                    RoutinesBT.Player.SendAutomaticDialog(button_number=button_number, log=False).root,
                ],
            )
        )

    return BehaviorTree(
        BehaviorTree.SequenceNode(
            name="MoveAndAutoDialogPath",
            children=[
                *[RoutinesBT.Player.Move(x=point.x, y=point.y, tolerance=move_tolerance, log=False).root for point in points[:-1]],
                RoutinesBT.Player.Move(x=points[-1].x, y=points[-1].y, tolerance=move_tolerance, log=False).root,
                RoutinesBT.Agents.TargetNearestNPCXY(
                    x=points[-1].x,
                    y=points[-1].y,
                    distance=target_distance,
                    log=False,
                ).root,
                RoutinesBT.Player.InteractTarget(log=False).root,
                Wait(DEFAULT_INTERACT_SETTLE_MS).root,
                RoutinesBT.Player.SendAutomaticDialog(button_number=button_number, log=False).root,
            ],
        )
    )

def MoveAndDialog(
    pos: PointOrPath,
    dialog_id: int | str,
    target_distance: float = Range.Nearby.value,
    move_tolerance: float = DEFAULT_MOVE_TOLERANCE,
) -> BehaviorTree:
    points = _as_path(pos)
    return BehaviorTree(
        BehaviorTree.SequenceNode(
            name="MoveAndDialogPath",
            children=[
                *[RoutinesBT.Player.Move(x=point.x, y=point.y, tolerance=move_tolerance, log=False).root for point in points[:-1]],
                RoutinesBT.Player.Move(x=points[-1].x, y=points[-1].y, tolerance=move_tolerance, log=False).root,
                RoutinesBT.Agents.TargetNearestNPCXY(
                    x=points[-1].x,
                    y=points[-1].y,
                    distance=target_distance,
                    log=False,
                ).root,
                RoutinesBT.Player.InteractTarget(log=False).root,
                Wait(DEFAULT_INTERACT_SETTLE_MS).root,
                RoutinesBT.Player.SendDialog(dialog_id=dialog_id, log=False).root,
            ],
        )
    )

def DialogAtXY(pos: Vec2f, dialog_id: int | str, target_distance: float = 200.0) -> BehaviorTree:
    return BehaviorTree(
        BehaviorTree.SequenceNode(
            name="DialogAtXY",
            children=[
                RoutinesBT.Agents.TargetNearestNPCXY(
                    x=pos.x,
                    y=pos.y,
                    distance=target_distance,
                    log=False,
                ).root,
                RoutinesBT.Player.InteractTarget(log=False).root,
                Wait(DEFAULT_INTERACT_SETTLE_MS).root,
                RoutinesBT.Player.SendDialog(dialog_id=dialog_id, log=False).root,
            ],
        )
    )

def InteractWithGadgetAtXY(pos: Vec2f, target_distance: float = 200.0) -> BehaviorTree:
    return BehaviorTree(
        BehaviorTree.SequenceNode(
            name="InteractWithGadgetAtXY",
            children=[
                RoutinesBT.Agents.TargetNearestGadgetXY(
                    x=pos.x,
                    y=pos.y,
                    distance=target_distance,
                    log=False,
                ).root,
                RoutinesBT.Player.InteractTarget(log=False).root,
                Wait(DEFAULT_INTERACT_SETTLE_MS).root,
            ],
        )
    )
    
def MoveAndAutoDialogByModelID(modelID_or_encStr: int | str, button_number: int = 0) -> BehaviorTree:
    return RoutinesBT.Agents.MoveTargetInteractAndAutomaticDialogByModelID(
        modelID_or_encStr=modelID_or_encStr,
        button_number=button_number,
        log=False,
    )

def MoveAndDialogByModelID(modelID_or_encStr: int | str, dialog_id: int | str) -> BehaviorTree:
    return RoutinesBT.Agents.MoveTargetInteractAndDialogByModelID(
        modelID_or_encStr=modelID_or_encStr,
        dialog_id=dialog_id,
        log=False,
    )

def TargetAndDialogByModelID(modelID_or_encStr: int | str, dialog_id: int | str) -> BehaviorTree:
    return RoutinesBT.Agents.TargetInteractAndDialogByModelID(
        modelID_or_encStr=modelID_or_encStr,
        dialog_id=dialog_id,
        log=False,
    )

def MoveAndTargetByModelID(modelID_or_encStr: int | str, log: bool = False) -> BehaviorTree:
    return RoutinesBT.Agents.MoveAndTargetByModelID(
        modelID_or_encStr=modelID_or_encStr,
        log=log
    )
    
def MoveAndInteractByModelID(modelID_or_encStr: int | str, target_distance: float = Range.Nearby.value) -> BehaviorTree:
    return RoutinesBT.Agents.MoveTargetAndInteractByModelID(
        modelID_or_encStr=modelID_or_encStr,
    )

#region Agents
def ClearEnemiesInArea(pos: Vec2f, radius: float = Range.Spirit.value, allowed_alive_enemies: int = 0) -> BehaviorTree:
    return RoutinesBT.Agents.ClearEnemiesInArea(
        x=pos.x,
        y=pos.y,
        radius=radius,
        allowed_alive_enemies=allowed_alive_enemies,
    )

def WaitForClearEnemiesInArea(pos: Vec2f, radius: float = Range.Spirit.value, allowed_alive_enemies: int = 0) -> BehaviorTree:
    return RoutinesBT.Agents.WaitForClearEnemiesInArea(
        x=pos.x,
        y=pos.y,
        radius=radius,
        allowed_alive_enemies=allowed_alive_enemies,
    )
     
#region Items

def IsItemInInventoryBags(modelID_or_encStr: int | str) -> BehaviorTree:
    return RoutinesBT.Items.IsItemInInventoryBags(modelID_or_encStr=modelID_or_encStr)

def IsItemEquipped(modelID_or_encStr: int | str) -> BehaviorTree:
    return RoutinesBT.Items.IsItemEquipped(modelID_or_encStr=modelID_or_encStr)

def EquipItemByModelID(modelID_or_encStr: int | str, aftercast_ms: int = 250) -> BehaviorTree:
    return RoutinesBT.Items.EquipItemByModelID(
        modelID_or_encStr=modelID_or_encStr,
        aftercast_ms=aftercast_ms,
    )

def EquipInventoryBag(
        modelID_or_encStr: int | str,
        target_bag: int,
        timeout_ms: int = 2500,
        poll_interval_ms: int = 125,
        log: bool = False,
    ) -> BehaviorTree:
    return RoutinesBT.Items.EquipInventoryBag(
        modelID_or_encStr=modelID_or_encStr,
        target_bag=target_bag,
        timeout_ms=timeout_ms,
        poll_interval_ms=poll_interval_ms,
        log=log,
    )

def DestroyItems(model_ids: list[int], log: bool = False, aftercast_ms: int = 75) -> BehaviorTree:
    return RoutinesBT.Items.DestroyItems(
        model_ids=model_ids,
        log=log,
        aftercast_ms=aftercast_ms,
    )
    
def DestroyBonusItems(exclude_list: list[int] = [], log: bool = False, aftercast_ms: int = 75) -> BehaviorTree:
    return RoutinesBT.Items.DestroyBonusItems(
        exclude_list=exclude_list,
        log=log,
        aftercast_ms=aftercast_ms,
    )
    
def SpawnBonusItems(log: bool = False, spawn_settle_ms: int = 50) -> BehaviorTree:
    return RoutinesBT.Items.SpawnBonusItems(log=log, aftercast_ms=spawn_settle_ms)

def SpawnAndDestroyBonusItems(exclude_list: list[int] = [], log: bool = False) -> BehaviorTree:
    return BehaviorTree(
        BehaviorTree.SequenceNode(
            name="SpawnAndDestroyBonusItems",
            children=[
                SpawnBonusItems(log=log).root,
                Wait(100).root,
                DestroyBonusItems(exclude_list=exclude_list, log=log).root,
            ],
        )
    )

def AddModelToLootWhitelist(model_id: int) -> BehaviorTree:
    def _add_model_to_loot_whitelist() -> BehaviorTree.NodeState:
        LootConfig().AddToWhitelist(model_id)
        return BehaviorTree.NodeState.SUCCESS

    return BehaviorTree(
        BehaviorTree.ActionNode(
            name=f"AddModelToLootWhitelist({model_id})",
            action_fn=_add_model_to_loot_whitelist,
            aftercast_ms=50,
        )
    )

def LootItems(distance: float = Range.Earshot.value, timeout_ms: int = 10000) -> BehaviorTree:
    state = {
        "started_at": 0.0,
        "last_item_agent_id": 0,
    }

    def _loot_items() -> BehaviorTree.NodeState:
        if state["started_at"] == 0.0:
            state["started_at"] = time.monotonic()

        if GLOBAL_CACHE.Inventory.GetFreeSlotCount() <= 0:
            return BehaviorTree.NodeState.SUCCESS

        loot_array = LootConfig().GetfilteredLootArray(
            distance=distance,
            multibox_loot=True,
            allow_unasigned_loot=False,
        )
        if not loot_array:
            return BehaviorTree.NodeState.SUCCESS

        if (time.monotonic() - state["started_at"]) * 1000 >= timeout_ms:
            return BehaviorTree.NodeState.SUCCESS

        item_agent_id = loot_array[0]
        state["last_item_agent_id"] = item_agent_id
        Player.ChangeTarget(item_agent_id)
        Player.Interact(item_agent_id, False)
        return BehaviorTree.NodeState.RUNNING

    return BehaviorTree(
        BehaviorTree.ActionNode(
            name="LootItems",
            action_fn=_loot_items,
            aftercast_ms=500,
        )
    )

def HasItemQuantity(model_id: int, quantity: int) -> BehaviorTree:
    return RoutinesBT.Items.HasItemQuantity(model_id=model_id, quantity=quantity)

def DepositModelToStorage(model_id: int, aftercast_ms: int = 350) -> BehaviorTree:
    state = {
        "deposited_any": False,
    }

    def _deposit_model_to_storage() -> BehaviorTree.NodeState:
        item_id = GLOBAL_CACHE.Inventory.GetFirstModelID(model_id)
        if item_id == 0:
            return BehaviorTree.NodeState.SUCCESS

        GLOBAL_CACHE.Inventory.DepositItemToStorage(item_id)
        state["deposited_any"] = True
        return BehaviorTree.NodeState.RUNNING

    return BehaviorTree(
        BehaviorTree.ActionNode(
            name=f"DepositModelToStorage({model_id})",
            action_fn=_deposit_model_to_storage,
            aftercast_ms=aftercast_ms,
        )
    )

def DepositGoldKeep(gold_amount_to_leave_on_character: int = 0, aftercast_ms: int = 350) -> BehaviorTree:
    def _deposit_gold_keep() -> BehaviorTree.NodeState:
        gold_on_character = GLOBAL_CACHE.Inventory.GetGoldOnCharacter()
        gold_in_storage = GLOBAL_CACHE.Inventory.GetGoldInStorage()
        if gold_on_character <= gold_amount_to_leave_on_character:
            return BehaviorTree.NodeState.SUCCESS

        available_storage = max(0, 1_000_000 - gold_in_storage)
        gold_to_deposit = min(
            gold_on_character - gold_amount_to_leave_on_character,
            available_storage,
        )
        if gold_to_deposit <= 0:
            return BehaviorTree.NodeState.SUCCESS

        GLOBAL_CACHE.Inventory.DepositGold(gold_to_deposit)
        return BehaviorTree.NodeState.SUCCESS

    return BehaviorTree(
        BehaviorTree.ActionNode(
            name=f"DepositGoldKeep({gold_amount_to_leave_on_character})",
            action_fn=_deposit_gold_keep,
            aftercast_ms=aftercast_ms,
        )
    )

def ExchangeCollectorItem(
        output_model_id: int,
        trade_model_ids: list[int],
        quantity_list: list[int],
        cost: int = 0,
        aftercast_ms: int = 500,
    ) -> BehaviorTree:
    return RoutinesBT.Items.ExchangeCollectorItem(
        output_model_id=output_model_id,
        trade_model_ids=trade_model_ids,
        quantity_list=quantity_list,
        cost=cost,
        aftercast_ms=aftercast_ms,
    )

def CraftItem(
        output_model_id: int,
        cost: int,
        trade_model_ids: list[int],
        quantity_list: list[int],
        aftercast_ms: int = 500,
    ) -> BehaviorTree:
    def _craft_item() -> BehaviorTree.NodeState:
        k = min(len(trade_model_ids), len(quantity_list))
        if k == 0:
            return BehaviorTree.NodeState.FAILURE

        target_item_id = 0
        for offered_item_id in GLOBAL_CACHE.Trading.Merchant.GetOfferedItems():
            if GLOBAL_CACHE.Item.GetModelID(offered_item_id) == output_model_id:
                target_item_id = offered_item_id
                break
        if target_item_id == 0:
            return BehaviorTree.NodeState.FAILURE

        trade_item_ids = []
        for model_id in trade_model_ids[:k]:
            item_id = GLOBAL_CACHE.Inventory.GetFirstModelID(model_id)
            if item_id == 0:
                return BehaviorTree.NodeState.FAILURE
            trade_item_ids.append(item_id)

        GLOBAL_CACHE.Trading.Crafter.CraftItem(
            target_item_id,
            cost,
            trade_item_ids,
            quantity_list[:k],
        )
        return BehaviorTree.NodeState.SUCCESS

    return BehaviorTree(
        BehaviorTree.ActionNode(
            name=f"CraftItem({output_model_id})",
            action_fn=_craft_item,
            aftercast_ms=aftercast_ms,
        )
    )
     
def NeedsInventoryCleanup(exclude_models: list[int] | None = None) -> BehaviorTree:
    return RoutinesBT.Items.NeedsInventoryCleanup(exclude_models=exclude_models)

def SellInventoryItems(
        exclude_models: list[int] | None = None,
        log: bool = False,
    ) -> BehaviorTree:
    return RoutinesBT.Items.SellInventoryItems(
        exclude_models=exclude_models,
        log=log,
    ) 
    
def DestroyZeroValueItems(
        exclude_models: list[int] | None = None,
        log: bool = False,
        aftercast_ms: int = 100,
    ) -> BehaviorTree:
    return RoutinesBT.Items.DestroyZeroValueItems(
        exclude_models=exclude_models,
        log=log,
        aftercast_ms=aftercast_ms,
    )

def CustomizeWeapon(
        frame_label: str = "Merchant.CustomizeWeaponButton",
        aftercast_ms: int = 500,
    ) -> BehaviorTree:
    return RoutinesBT.Items.CustomizeWeapon(
        frame_label=frame_label,
        aftercast_ms=aftercast_ms,
    )

#region skills
def LoadSkillbar(template: str, log: bool = False) -> BehaviorTree:
    return RoutinesBT.Skills.LoadSkillbar(
        template=template,
        log=log,
    )

def LoadHeroSkillbar(hero_index: int, template: str, log: bool = False) -> BehaviorTree:
    return RoutinesBT.Skills.LoadHeroSkillbar(
        hero_index=hero_index,
        template=template,
        log=log,
    )

def CastSkillID(skill_id: int,
                target_agent_id: int = 0,
                extra_condition: bool = True,
                aftercast_delay_ms: int = 50,
                log: bool = False
) -> BehaviorTree:
    return RoutinesBT.Skills.CastSkillID(
        skill_id=skill_id,
        target_agent_id=target_agent_id,
        extra_condition=extra_condition,
        aftercast_delay=aftercast_delay_ms,
        log=log,
    )
RoutinesBT.Skills.CastSkillID
