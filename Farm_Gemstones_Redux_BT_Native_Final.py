from __future__ import annotations

import time
from typing import Callable

import Py4GW
from Py4GWCoreLib import (
    Agent,
    AgentArray,
    ConsoleLog,
    GLOBAL_CACHE,
    Map,
    Party,
    Player,
)
from Py4GWCoreLib.BottingTree import BottingTree
from Py4GWCoreLib.IniManager import IniManager
from Py4GWCoreLib.native_src.internals.types import Vec2f
from Py4GWCoreLib.py4gwcorelib_src.BehaviorTree import BehaviorTree
from Sources.ApoSource.ApoBottingLib import wrappers as BT

try:
    from Py4GWCoreLib.enums_src.Multiboxing_enums import SharedCommandType
except Exception:
    SharedCommandType = None


MODULE_NAME = "Farm Gemstones Redux"
INI_PATH = "Widgets/Automation/Bots/Farm Gemstones Redux"
INI_FILENAME = "Farm_Gemstones_Redux.ini"

GATE_OF_ANGUISH_OUTPOST = 474
MISSION_MAP = 445

ENTRY_PRIEST_COORDS = Vec2f(6010, -13344)
ENTRY_DIALOG_ID = 0x84

ZHELLIX_ANCHOR_COORDS = Vec2f(-3079, -4578)
FIGHT_POSITION = (-3606.0, -5347.0)

SUMMONING_STONE_MODEL_IDS = (30209, 37810, 31155)
SUMMON_SETTLE_MS = 3_000

INITIAL_SETTLE_MS = 15_000
MIN_DEFENSE_TIME_MS = 120_000
NO_ACTIVITY_END_MS = 60_000

FIGHT_SEARCH_RADIUS = 2200.0
ZHELLIX_NAME_FRAGMENT = "zhellix"
ZHELLIX_SEARCH_RADIUS = 6000.0
ZHELLIX_ATTACK_RADIUS = 1400.0

initialized = False
ini_key = ""
botting_tree: BottingTree | None = None


def ensure_botting_tree() -> BottingTree:
    global botting_tree

    if botting_tree is None:
        botting_tree = BottingTree.Create(
            MODULE_NAME,
            main_routine=get_execution_steps(),
            routine_name="MultiAccountSequence",
            repeat=True,
            multi_account=True,
        )

    return botting_tree


def _make_action_node(
    name: str,
    action_fn: Callable[[BehaviorTree.Node], BehaviorTree.NodeState],
    aftercast_ms: int = 0,
) -> BehaviorTree:
    return BehaviorTree(
        BehaviorTree.ActionNode(
            name=name,
            action_fn=action_fn,
            aftercast_ms=aftercast_ms,
        )
    )


def _log_error(name: str, exc: Exception) -> None:
    ConsoleLog(MODULE_NAME, f"[{name}] failed: {exc}", Py4GW.Console.MessageType.Error)


# ============================================================
# Native BT custom leaves
# ============================================================

def MarkRunStart() -> BehaviorTree:
    def _tick(node: BehaviorTree.Node) -> BehaviorTree.NodeState:
        node.blackboard["gemstones_last_result"] = "starting"
        ConsoleLog(MODULE_NAME, "[Gemstone] Run started")
        return BehaviorTree.NodeState.SUCCESS

    return _make_action_node("Mark Run Start", _tick)


def _find_inventory_item_by_model_ids(model_ids: tuple[int, ...]) -> int:
    try:
        bag_list = GLOBAL_CACHE.ItemArray.CreateBagList(1, 2, 3, 4)
        item_array = GLOBAL_CACHE.ItemArray.GetItemArray(bag_list)
    except Exception:
        return 0

    for item_id in item_array:
        try:
            if int(GLOBAL_CACHE.Item.GetModelID(item_id)) in model_ids:
                return int(item_id)
        except Exception:
            continue

    return 0


def _use_local_item(item_id: int) -> bool:
    if not item_id:
        return False

    candidates = (
        (getattr(GLOBAL_CACHE, "Inventory", None), "UseItem"),
        (getattr(GLOBAL_CACHE, "Inventory", None), "UseInventoryItem"),
        (getattr(GLOBAL_CACHE, "Item", None), "UseItem"),
        (getattr(GLOBAL_CACHE, "Item", None), "Use"),
    )

    for obj, method_name in candidates:
        method = getattr(obj, method_name, None) if obj is not None else None
        if callable(method):
            try:
                method(item_id)
                return True
            except Exception:
                continue

    return False


def _dispatch_summoning_stone_to_alts(model_id: int) -> None:
    if SharedCommandType is None or not model_id:
        return

    command = None
    for command_name in (
        "UseSummoningStone",
        "SummoningStone",
        "UseInventoryItem",
        "UseItem",
    ):
        command = getattr(SharedCommandType, command_name, None)
        if command is not None:
            break

    if command is None:
        ConsoleLog(
            MODULE_NAME,
            "[Summon] No SharedCommandType for summoning stone found; leader only.",
            Py4GW.Console.MessageType.Warning,
        )
        return

    try:
        my_email = Player.GetAccountEmail()
        for acc in GLOBAL_CACHE.ShMem.GetAllAccountData():
            if acc.AccountEmail == my_email:
                continue

            GLOBAL_CACHE.ShMem.SendMessage(
                my_email,
                acc.AccountEmail,
                command,
                (int(model_id), 0, 0, 0),
                ("use_summoning_stone", str(model_id), "", ""),
            )
    except Exception as exc:
        ConsoleLog(MODULE_NAME, f"[Summon] Alt dispatch failed: {exc}", Py4GW.Console.MessageType.Warning)


def UseSummoningStoneAllAccounts() -> BehaviorTree:
    state = {
        "sent": False,
        "start_time": 0.0,
    }

    def _tick(_node: BehaviorTree.Node) -> BehaviorTree.NodeState:
        try:
            now = time.time()

            if not state["sent"]:
                item_id = _find_inventory_item_by_model_ids(SUMMONING_STONE_MODEL_IDS)
                model_id = 0

                if item_id:
                    try:
                        model_id = int(GLOBAL_CACHE.Item.GetModelID(item_id))
                    except Exception:
                        model_id = 0

                ConsoleLog(MODULE_NAME, "[Summon] Requesting summoning stone use")

                if item_id:
                    if not _use_local_item(item_id):
                        ConsoleLog(
                            MODULE_NAME,
                            "[Summon] Could not use leader summoning stone with available Inventory API",
                            Py4GW.Console.MessageType.Warning,
                        )
                else:
                    ConsoleLog(MODULE_NAME, "[Summon] No summoning stone found on leader", Py4GW.Console.MessageType.Warning)

                if model_id:
                    _dispatch_summoning_stone_to_alts(model_id)

                state["sent"] = True
                state["start_time"] = now
                return BehaviorTree.NodeState.RUNNING

            if int((now - float(state["start_time"])) * 1000) < SUMMON_SETTLE_MS:
                return BehaviorTree.NodeState.RUNNING

            state["sent"] = False
            state["start_time"] = 0.0
            return BehaviorTree.NodeState.SUCCESS

        except Exception as exc:
            state["sent"] = False
            state["start_time"] = 0.0
            _log_error("UseSummoningStoneAllAccounts", exc)
            return BehaviorTree.NodeState.FAILURE

    return _make_action_node("Use Summoning Stone All Accounts", _tick)


# ============================================================
# Defense monitor: observation only. HeroAI does the combat.
# ============================================================

def _is_group_alive() -> bool:
    try:
        if not Agent.IsDead(Player.GetAgentID()):
            return True
    except Exception:
        pass

    try:
        for hero in Party.GetHeroes():
            if not Agent.IsDead(hero.agent_id):
                return True
    except Exception:
        pass

    try:
        for hench in Party.GetHenchmen():
            if not Agent.IsDead(hench.agent_id):
                return True
    except Exception:
        pass

    return False


def _find_zhellix(max_dist: float = ZHELLIX_SEARCH_RADIUS) -> int:
    try:
        npcs = AgentArray.GetNPCMinipetArray()
        npcs = AgentArray.Filter.ByDistance(npcs, Player.GetXY(), max_dist)
        npcs = AgentArray.Sort.ByDistance(npcs, Player.GetXY())
    except Exception:
        return 0

    for npc_id in npcs:
        npc_id = int(npc_id)
        try:
            npc_name = Agent.GetNameByID(npc_id)
        except Exception:
            continue

        if npc_name and ZHELLIX_NAME_FRAGMENT in npc_name.lower():
            return npc_id

    return 0


def _get_alive_enemies_around_position(position: tuple[float, float], radius: float) -> list[int]:
    try:
        enemies = AgentArray.GetEnemyArray()
        enemies = AgentArray.Filter.ByDistance(enemies, position, radius)
        enemies = AgentArray.Filter.ByCondition(
            enemies,
            lambda agent_id: not Agent.IsDead(agent_id) and not Agent.IsSpirit(agent_id),
        )
        return [int(enemy_id) for enemy_id in enemies]
    except Exception:
        return []


def _get_alive_enemies_around_fight_position(radius: float = FIGHT_SEARCH_RADIUS) -> list[int]:
    return _get_alive_enemies_around_position(FIGHT_POSITION, radius)


def _get_alive_enemies_around_zhellix(zhellix_id: int, radius: float = ZHELLIX_ATTACK_RADIUS) -> list[int]:
    if not zhellix_id:
        return []

    try:
        zhellix_pos = Agent.GetXY(zhellix_id)
    except Exception:
        return []

    return _get_alive_enemies_around_position(zhellix_pos, radius)


def DefendZhellixMonitor() -> BehaviorTree:
    state = {
        "started": False,
        "start_time": 0.0,
        "last_activity_time": 0.0,
        "settle_done": False,
        "last_dead_log_second": -1,
    }

    def _reset() -> None:
        state["started"] = False
        state["start_time"] = 0.0
        state["last_activity_time"] = 0.0
        state["settle_done"] = False
        state["last_dead_log_second"] = -1

    def _tick(node: BehaviorTree.Node) -> BehaviorTree.NodeState:
        try:
            now = time.time()

            if not state["started"]:
                state["started"] = True
                state["start_time"] = now
                state["last_activity_time"] = now
                state["settle_done"] = False
                state["last_dead_log_second"] = -1
                node.blackboard["gemstones_last_result"] = "running"
                ConsoleLog(MODULE_NAME, "[Gemstone] Monitoring Zhellix defense")
                return BehaviorTree.NodeState.RUNNING

            if int(Map.GetMapID()) == GATE_OF_ANGUISH_OUTPOST:
                node.blackboard["gemstones_last_result"] = "returned_to_outpost"
                ConsoleLog(MODULE_NAME, "[Gemstone] Returned to outpost during defense")
                _reset()
                return BehaviorTree.NodeState.SUCCESS

            elapsed_ms = int((now - float(state["start_time"])) * 1000)

            if not state["settle_done"]:
                if elapsed_ms < INITIAL_SETTLE_MS:
                    return BehaviorTree.NodeState.RUNNING
                state["settle_done"] = True
                ConsoleLog(MODULE_NAME, "[Gemstone] Initial settle finished")

            if not _is_group_alive():
                current_second = elapsed_ms // 1000
                if current_second != state["last_dead_log_second"] and current_second % 5 == 0:
                    state["last_dead_log_second"] = current_second
                    ConsoleLog(MODULE_NAME, "[Gemstone] Group dead, waiting for return to outpost")
                return BehaviorTree.NodeState.RUNNING

            zhellix_id = _find_zhellix()
            zhellix_enemies = _get_alive_enemies_around_zhellix(zhellix_id)
            fight_enemies = _get_alive_enemies_around_fight_position()

            if zhellix_enemies or fight_enemies:
                state["last_activity_time"] = now

            idle_ms = int((now - float(state["last_activity_time"])) * 1000)

            if (
                elapsed_ms >= MIN_DEFENSE_TIME_MS
                and not zhellix_enemies
                and not fight_enemies
                and idle_ms >= NO_ACTIVITY_END_MS
            ):
                node.blackboard["gemstones_last_result"] = "success"
                ConsoleLog(
                    MODULE_NAME,
                    f"[Gemstone] Defense finished after {elapsed_ms // 1000}s; idle={idle_ms // 1000}s",
                )
                _reset()
                return BehaviorTree.NodeState.SUCCESS

            return BehaviorTree.NodeState.RUNNING

        except Exception as exc:
            _reset()
            _log_error("DefendZhellixMonitor", exc)
            return BehaviorTree.NodeState.FAILURE

    return _make_action_node("Defend Zhellix Monitor", _tick)


def ResignIfStillInMission() -> BehaviorTree:
    def _choose(_node: BehaviorTree.Node) -> BehaviorTree:
        try:
            if int(Map.GetMapID()) == MISSION_MAP:
                return BT.Resign(
                    wait_for_map_load=True,
                    target_map_id=GATE_OF_ANGUISH_OUTPOST,
                    multi_account=True,
                    timeout_ms=30_000,
                    log=True,
                )
        except Exception:
            pass

        return BT.Succeeder(name="Skip Resign - Already Outpost")

    return BT.Subtree("Resign If Still In Mission", subtree_fn=_choose)


# ============================================================
# Planner
# ============================================================

def InitializeBot() -> BehaviorTree:
    bot = ensure_botting_tree()

    return BT.Sequence(
        name="Initialize Bot",
        map_id_or_name=GATE_OF_ANGUISH_OUTPOST,
        random_travel=False,
        hard_mode=True,
        children=[
            bot.Config.Aggressive(multi_account=True),
            BT.CreateParty(multibox_invite=True),
        ],
    )


def RunGemstones() -> BehaviorTree:
    return BT.Sequence(
        name="Run Gemstones",
        children=[
            MarkRunStart(),
            BT.MoveAndDialog(
                ENTRY_PRIEST_COORDS,
                ENTRY_DIALOG_ID,
                multi_account=False,
            ),
            BT.WaitForMapToChange(
                map_id=MISSION_MAP,
                timeout_ms=30_000,
            ),
            BT.Move(
                ZHELLIX_ANCHOR_COORDS,
                flag_heroes_to_waypoint=False,
            ),
            UseSummoningStoneAllAccounts(),
            BT.Wait(15_000),
            DefendZhellixMonitor(),
            ResignIfStillInMission(),
        ],
    )


def get_execution_steps() -> list[tuple[str, Callable[[], BehaviorTree]]]:
    return [
        ("Initialize Bot", InitializeBot),
        ("Run Gemstones", RunGemstones),
    ]


def main() -> None:
    global initialized, ini_key

    if not initialized:
        if not ini_key:
            ini_key = IniManager().ensure_key(INI_PATH, INI_FILENAME)
            if not ini_key:
                return
            IniManager().load_once(ini_key)

        ensure_botting_tree()
        initialized = True

    tree = ensure_botting_tree()
    tree.tick()
    tree.UI.draw_window()


if __name__ == "__main__":
    main()
