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

MODULE_NAME = 'Tihark Orchard (Zaishen quest)'
INI_PATH = 'Widgets/Automation/Bots/Tihark Orchard'
INI_FILENAME = 'Tihark_Orchard.ini'

initialized = False
ini_key = ''
botting_tree: BottingTree | None = None

def ensure_botting_tree() -> BottingTree:
    global botting_tree

    if botting_tree is None:
        botting_tree = BottingTree.Create(
            MODULE_NAME,
            main_routine=get_execution_steps(),
            routine_name='MainSequence',
            repeat=False,
        )

    return botting_tree

def AcquireZMission() -> BehaviorTree:
    return BT.Sequence(
        name='Take Zaishen Mission',
        map_id_or_name=EMBARK_BEACH,
        random_travel=False,
        hard_mode=True,
        children=[
            BT.MoveAndDialog((-206.20, -3480.20), 0x83DA01)
        ],
    )

def TurnInMission() -> BehaviorTree:
    return BT.Sequence(
        name='Turn in Mission',
        map_id_or_name=EMBARK_BEACH,
        random_travel=False,
        hard_mode=True,
        children=[
            BT.HandleAutoQuest((-708.29, -3207.30))
        ],
    )


def DoMission() -> BehaviorTree:
    PATH_TO_TALKORA = [(-5243.16, -5885.16), (-36.27, -3086.04), (-10958.97, 1535.55), (-11145.00, 2400.00)]
    PATH_TO_GUARD = (-10799.00, 2478.00)
    PATH_TO_METHU_THE_WISE = (-11148.00, 2704.00)
    PATH_TO_BOKKA = (-11403.00, 1257.00)
    PATH_TO_AMTHUR = (-10880.00, 145.00)
    KILL_PATH = [[(-7808.27, 2277.65)], 
                 [(-5930.22, 3588.73)], 
                 [(-7981.76, 380.05)], 
                 [(-6094.06, -3301.68)]]
    return BT.Sequence(
        name='Killroute',
        map_id_or_name=TIHARK_ORCHARD,
        random_travel=False,
        hard_mode=True,
        children=[
            BT.MoveAndDialog((-1458.05, 13841.14), 0x84), #Enter Mission
            BT.WaitUntilOnExplorable(),
            BT.MoveAndDialog(PATH_TO_TALKORA, 0x84), #Talkhora
            BT.MoveAndDialog(PATH_TO_GUARD, 0x84), #Guard
            BT.MoveAndDialog(PATH_TO_METHU_THE_WISE, 0x84), #Methu the Wise
            BT.MoveAndDialog(PATH_TO_BOKKA, 0x84), #Bokka
            BT.MoveAndDialog(PATH_TO_AMTHUR, 0x84), #Amthur
            BT.MoveAndInteract(PATH_TO_AMTHUR),
            BT.Wait(5000, announce_delay=True),
            BT.VanquishNode(steps=KILL_PATH),
            BT.WaitUntilOnOutpost(),
        ]
    )




def get_execution_steps() -> list[tuple[str, Callable[[], BehaviorTree]]]:
    return [
        ('Take Zaishen Mission', AcquireZMission),
        ('Do Mission', DoMission),
        ('Turn in Mission', TurnInMission)
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
