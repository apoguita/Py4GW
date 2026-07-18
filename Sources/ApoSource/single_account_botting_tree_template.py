from __future__ import annotations

from typing import Callable

from Py4GWCoreLib.BottingTree import BottingTree
from Py4GWCoreLib.IniManager import IniManager
from Py4GWCoreLib.py4gwcorelib_src.BehaviorTree import BehaviorTree


MODULE_NAME = 'Single Account Botting Tree Template'
INI_PATH = 'Widgets/Automation/Bots/Templates'
INI_FILENAME = 'SingleAccountBottingTreeTemplate.ini'

initialized = False
ini_key = ''
botting_tree: BottingTree | None = None


def ensure_botting_tree() -> BottingTree:
    global botting_tree

    if botting_tree is None:
        botting_tree = BottingTree.Create(
            MODULE_NAME,
            main_routine=get_execution_steps(),
            routine_name='SingleAccountSequence',
            repeat=True,
            reset=False,
            multi_account=False,
            configure_fn=lambda tree: tree.Config.ConfigureUpkeep(),
        )

    return botting_tree


def InitializeBot() -> BehaviorTree:
    bot = ensure_botting_tree()
    return BehaviorTree(
        BehaviorTree.SequenceNode(
            name='Initialize Bot',
            children=[
                bot.Config.Aggressive(multi_account=False, auto_loot=False),
            ],
        )
    )


def get_execution_steps() -> list[tuple[str, Callable[[], BehaviorTree]]]:
    return [
        ('Initialize Bot', InitializeBot),
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


if __name__ == '__main__':
    main()
