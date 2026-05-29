from __future__ import annotations

from typing import Callable

from Py4GWCoreLib.BottingTree import BottingTree
from Py4GWCoreLib.IniManager import IniManager

from Py4GWCoreLib.native_src.internals.types import Vec2f
from Py4GWCoreLib.routines_src.behaviourtrees_src.constants.lists import *
from Sources.ApoSource.ApoBottingLib import wrappers as BT
from Py4GWCoreLib.routines_src.behaviourtrees_src.constants import *
from Py4GWCoreLib.py4gwcorelib_src.BehaviorTree import BehaviorTree
from Py4GWCoreLib.enums import Range

MODULE_NAME = 'VQ Mount Quinkai Redux'
INI_PATH = 'Widgets/Automation/Bots/VQ Mount Quinkai Redux'
INI_FILENAME = 'VQ_Mount_Quinkai_Redux.ini'
DONATION_THRESHOLD = 20_000

initialized = False
ini_key = ''
botting_tree: BottingTree | None = None

def ensure_botting_tree() -> BottingTree:
    global botting_tree

    if botting_tree is None:
        botting_tree = BottingTree.Create(
            MODULE_NAME,
            main_routine=get_execution_steps(),
            routine_name='MultiAccountSequence',
            repeat=False,
            multi_account=True,
        )

    return botting_tree

def InitializeBot() -> BehaviorTree:
    bot = ensure_botting_tree()
    return BT.Sequence(
        name='Initialize Bot',
        map_id_or_name=MIHANU_TOWNSHIP,
        random_travel=False,
        hard_mode=False,
        children=[
            bot.Config.Aggressive(multi_account=True),
            BT.CreateParty(multibox_invite=True),
            BT.MoveAndExitMap((-1508, 5950),HOLDINGS_OF_CHOKHIN),
            BT.LogMessage('Preparing Resign...'),
            BT.MoveAndExitMap((17921, -16987),MIHANU_TOWNSHIP), #prepare resign
            
        ],
    )

def Killroute() -> BehaviorTree:
    vanquish_steps: list[object] = [
        [(16423.77, -14354.97),(6105.68, -14212.85)],
        [(2542.09, -10471.78)],
        [(458.21, -9290.96)],
        [(-821.73, -3236.04)],
        [(1604.01, -5167.11)],
        [(9999.85, -4042.10)],
        [(11859.41, -4922.63)],
        [(11859.41, -4922.63)],
        [(16731.10, -5870.96)],
        [(15378.25, -7226.29)],
        [(10913.97, -7533.19)],
        
    ]
    
    return BT.Sequence(
        name='Killroute',
        children=[
            BT.MoveAndExitMap((-1508, 5950),HOLDINGS_OF_CHOKHIN),
            BT.VanquishNode(vanquish_steps, name='PlantFarmerPath', flag_heroes_to_waypoint=False),
            BT.Resign(wait_for_map_load=True, target_map_id=MIHANU_TOWNSHIP, multi_account=True),
        ]
    )

def RepeatKillroute() -> BehaviorTree:
    return BT.Repeater(
        name='Repeat Killroute',
        repeat_count=5,
        children=[Killroute()],
    )


def get_execution_steps() -> list[tuple[str, Callable[[], BehaviorTree]]]:
    return [
        ('Initialize Bot', InitializeBot),
        ('Repeat Killroute', RepeatKillroute),
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
