from __future__ import annotations

from typing import Callable

from Py4GWCoreLib.BottingTree import BottingTree
from Py4GWCoreLib.IniManager import IniManager
from Py4GWCoreLib.py4gwcorelib_src.BehaviorTree import BehaviorTree
from Py4GWCoreLib import Utils

from Sources.ApoSource.ApoBottingLib import wrappers as BT

MODULE_NAME = "Farm Gemstones Redux"
INI_PATH = "Widgets/Automation/Bots/Farm Gemstones Redux"
INI_FILENAME = "Farm_Gemstones_Redux.ini"

GATE_OF_ANGUISH_OUTPOST = 474
MISSION_MAP = 445

ENTRY_DIALOG_ID = 0x84

ENTRY_PRIEST_COORDS = (6010, -13344)
ZHELLIX_ANCHOR_COORDS = (-3079, -4578)

MIN_DEFENSE_TIME_MS = 60_000
NO_ACTIVITY_END_MS = 12_000

initialized = False
ini_key = ""

botting_tree: BottingTree | None = None

_defense_start_time = 0
_last_enemy_seen = 0


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


def mark_run_start():
    global _defense_start_time
    global _last_enemy_seen

    now = Utils.GetBaseTimestamp()

    _defense_start_time = now
    _last_enemy_seen = now

    return BehaviorTree.NodeState.SUCCESS


#
# REPLACE THESE WITH YOUR EXISTING FUNCTIONS
#
def get_alive_enemies_around_zhellix():
    return []


def get_alive_enemies_around_fight_position():
    return []


def use_summons():
    return BehaviorTree.NodeState.SUCCESS


def monitor_defense():

    global _last_enemy_seen

    now = Utils.GetBaseTimestamp()

    zhellix_enemies = get_alive_enemies_around_zhellix()
    fight_enemies = get_alive_enemies_around_fight_position()

    if zhellix_enemies or fight_enemies:
        _last_enemy_seen = now
        return BehaviorTree.NodeState.RUNNING

    elapsed_ms = now - _defense_start_time
    idle_ms = now - _last_enemy_seen

    if elapsed_ms < MIN_DEFENSE_TIME_MS:
        return BehaviorTree.NodeState.RUNNING

    if idle_ms < NO_ACTIVITY_END_MS:
        return BehaviorTree.NodeState.RUNNING

    return BehaviorTree.NodeState.SUCCESS


def InitializeBot() -> BehaviorTree:
    bot = ensure_botting_tree()
    return BT.Sequence(
        name='Initialize Bot',
        map_id_or_name=GATE_OF_ANGUISH_OUTPOST,
        random_travel=False,
        hard_mode=True,
        children=[
            bot.Config.Aggressive(multi_account=True, auto_loot=False),
            BT.CreateParty(multibox_invite=True),
        ],
    )


def RunGemstones() -> BehaviorTree:

    return BT.Sequence(
        name="Run Gemstones",
        children=[

            BehaviorTree.ActionNode(
                mark_run_start,
                name="Mark Run Start",
            ),

            BT.MoveAndDialog(
                ENTRY_PRIEST_COORDS,
                ENTRY_DIALOG_ID,
            ),

            BT.WaitForMapToChange(
                map_id=MISSION_MAP,
            ),

            BT.Move(
                ZHELLIX_ANCHOR_COORDS,
            ),

            BehaviorTree.ActionNode(
                use_summons,
                name="Use Summons",
            ),

            BT.Wait(
                15000,
            ),

            BehaviorTree.WaitUntilNode(
                monitor_defense,
                throttle_interval_ms=500,
                timeout_ms=0,
                name="Defend Zhellix",
            ),

            BT.Resign(
                wait_for_map_load=True,
                target_map_id=GATE_OF_ANGUISH_OUTPOST,
                multi_account=True,
            ),
        ],
    )


def get_execution_steps() -> list[tuple[str, Callable[[], BehaviorTree]]]:
    return [
        ("Initialize Bot", InitializeBot),
        ("Run Gemstones", RunGemstones),
    ]


def main():

    global initialized
    global ini_key

    if not initialized:

        if not ini_key:

            ini_key = IniManager().ensure_key(
                INI_PATH,
                INI_FILENAME,
            )

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