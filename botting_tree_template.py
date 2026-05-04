from __future__ import annotations

from typing import Callable

from Py4GWCoreLib.BottingTree import BottingTree
from Py4GWCoreLib.IniManager import IniManager
from Py4GWCoreLib.py4gwcorelib_src.BehaviorTree import BehaviorTree
from Py4GWCoreLib.native_src.internals.types import Vec2f
from Py4GWCoreLib.enums_src.Model_enums import ModelID
from Py4GWCoreLib.Player import Player
from Sources.ApoSource.ApoBottingLib import wrappers as BT
from Py4GWCoreLib.enums_src.GameData_enums import Range


MODULE_NAME = "Botting Tree Template"
INI_PATH = "Widgets/Automation/Bots/Templates"
INI_FILENAME = "BottingTreeTemplate.ini"

initialized = False
ini_key = ""
botting_tree: BottingTree | None = None


def ensure_botting_tree() -> BottingTree:
    global botting_tree

    if botting_tree is None:
        botting_tree = BottingTree.Create(
            MODULE_NAME,
            main_routine=get_execution_steps(),
            routine_name="Proof of Legend Sequence",
            repeat=True,
            reset=False,
            configure_fn=lambda tree: tree.Config.ConfigureUpkeepTrees(
                disable_looting=True,
                restore_isolation_on_stop=True,
                enable_outpost_imp_service=True,
                enable_explorable_imp_service=True,
                imp_target_bag=1,
                imp_slot=0,
                imp_log=False,
                enable_party_wipe_recovery=True,
            ),
        )

    return botting_tree
def InitializeBot() -> BehaviorTree:
    bot = ensure_botting_tree()
    return BehaviorTree(
        BehaviorTree.SequenceNode(
            name="Initialize Bot",
            children=[
                bot.Config.Aggressive(auto_loot=False),
            ],
        )
    )


def get_execution_steps() -> list[tuple[str, Callable[[], BehaviorTree]]]:
    return [
        ("Initialize Bot", InitializeBot),
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
