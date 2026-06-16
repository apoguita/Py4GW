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

MODULE_NAME = 'VQ Drazach Thicket Redux'
INI_PATH = 'Widgets/Automation/Bots/VQ Drazach Thicket Redux'
INI_FILENAME = 'VQ_Drazach_Thicket_Redux.ini'
DONATION_THRESHOLD = 20_000

ETERNAL_GROVE_OUTPOST = 222
DRAZACH_THICKET    = 195
HOUSE_ZU_HELZER    = 77

KURZICK_PRIEST_COORDS = Vec2f(-5592.00, -16263.00)
EXIT_OUTPOST_COORDS   = Vec2f(-7544.00, 14343.00)

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
            repeat=True,
            multi_account=True,
            configure_fn=lambda tree: tree.Config.ConfigureUpkeep(
                consumable_upkeeps=CONSUMABLE_UPKEEPS,
            ),
        )

    return botting_tree


def InitializeBot() -> BehaviorTree:
    bot = ensure_botting_tree()
    return BT.Sequence(
        name='Initialize Bot',
        map_id_or_name=ETERNAL_GROVE_OUTPOST,
        random_travel=False,
        hard_mode=True,
        children=[
            bot.Config.Aggressive(multi_account=True, auto_loot=False),
            BT.CreateParty(multibox_invite=True),
            BT.MoveAndExitMap(EXIT_OUTPOST_COORDS, DRAZACH_THICKET),
        ],
    )


def Killroute() -> BehaviorTree:
    vanquish_steps: list[object] = [
        (-9878.31, -14870.55),
        (-6024.71, -10824.51),
        (-4546.84, -9157.54),
        (-6683.80, -8867.51),
        (-7756.96, -9672.30),
        (-5651.87, -6857.37),
        (-6603.41, -5635.55),
        (-11036.84, -8096.66),
        (-12024.07, -8840.55),
        (-10875.07, -5594.80),
        (-10516.25, -2471.60),
        (-9792.65, -536.86),
        (-11308.45, 3273.95),
        (-12730.60, 5712.96),
        (-7237.03, -2142.75),
        (-7105.36, -2426.90),
        (-4554.99, 776.04),
        (-1223.03, 2129.13),
        (-1896.83, 5606.69),
        (-1813.93, -2020.71),
        (-5234.42, -5652.45),
        (211.23, -5091.44),
        (1371.50, -4038.61),
        (3255.87, -4785.59),
        (1558.04, -6938.50),
        (668.36, -9314.83),
        (2366.87, -9547.91),
        (5625.59, -1360.20),
        (4755.49, 821.61),
        (7347.70, 311.06),
        (9152.04, 4514.65),
        (13031.58, 7149.48),
        (9152.04, 4514.65),
        (7016.99, 6483.00),
        (3104.65, 10852.02),
        (8982.88, 10737.52),
        (7201.44, 13909.25),
        (7109.79, 12134.53),
        (3154.82, 11441.71),
        (1574.23, 15445.42),
        (-1110.71, 15221.18),
        (-5693.68, 15871.91),
        (-6212.60, 13582.10),
        (-4150.74, 12059.19),
        (-5363.25, 10258.17),
        (-2856.84, 10372.21),
        (1247.34, 9651.55),
        (2498.04, 11076.82),
        (-2488.08, 8399.15),
        (-2095.59, 7311.56),
        (-3500.78, 6488.78),
        (-6663.06, 4662.32),
        (-5713.13, 8684.84),
        (-7201.17, 9957.66),
        (-7640.64, 12424.33),
        (-10422.90, 10846.65),
        (-12227.19, 7684.96),
        (-12730.60, 5712.96),
        (-10030.67, 4909.71),
    ]

    return BT.Sequence(
        name='Killroute',
        children=[
            BT.TakeBlessing(
                pos=KURZICK_PRIEST_COORDS,
                faction='kurzick',
                multi_account=True,
            ),
            BT.VanquishNode(vanquish_steps, name='DrazachThicketVanquishPath', flag_heroes_to_waypoint=False),
            BT.Resign(wait_for_map_load=True, target_map_id=ETERNAL_GROVE_OUTPOST, multi_account=True),
        ]
    )


def DonateFaction() -> BehaviorTree:
    return BT.DonateFaction(
        faction='kurzick',
        threshold=DONATION_THRESHOLD,
        travel_map_id=HOUSE_ZU_HELZER,
        multi_account=True,
        log=True,
    )


def get_execution_steps() -> list[tuple[str, Callable[[], BehaviorTree]]]:
    return [
        ('Initialize Bot', InitializeBot),
        ('Killroute', Killroute),
        ('DonateFaction', DonateFaction),
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
