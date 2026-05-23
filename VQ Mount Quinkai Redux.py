from __future__ import annotations

from typing import Callable

from Py4GWCoreLib.BottingTree import BottingTree
from Py4GWCoreLib.IniManager import IniManager
from Py4GWCoreLib.enums_src.Model_enums import ModelID
from Py4GWCoreLib.native_src.internals.types import Vec2f
from Sources.ApoSource.ApoBottingLib import wrappers as BT
from Py4GWCoreLib.routines_src.behaviourtrees_src.constants import *
from Py4GWCoreLib.py4gwcorelib_src.BehaviorTree import BehaviorTree
from Py4GWCoreLib.enums import Range

MODULE_NAME = 'VQ Mount Quinkai Redux'
INI_PATH = 'Widgets/Automation/Bots/VQ Mount Quinkai Redux'
INI_FILENAME = 'VQ_Mount_Quinkai_Redux.ini'
DONATION_THRESHOLD = 10_000

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
            reset=False,
            multi_account=True,
            configure_fn=lambda tree: tree.Config.ConfigureUpkeep(
                consumable_upkeeps=[
                    ModelID.Armor_Of_Salvation.value,
                    ModelID.Essence_Of_Celerity.value,
                    ModelID.Grail_Of_Might.value,
                    ModelID.Birthday_Cupcake.value,
                    ModelID.Golden_Egg.value,
                    ModelID.Candy_Corn.value,
                    ModelID.Candy_Apple.value,
                    ModelID.Slice_Of_Pumpkin_Pie.value,
                    ModelID.Drake_Kabob.value,
                    ModelID.Bowl_Of_Skalefin_Soup.value,
                    ModelID.Pahnai_Salad.value,
                    ModelID.Four_Leaf_Clover.value,
                    ModelID.Honeycomb.value,
                    ModelID.War_Supplies.value,
                ],
                enable_party_wipe_recovery=False,
            ),
        )

    return botting_tree

def InitializeBot() -> BehaviorTree:
    bot = ensure_botting_tree()
    return BT.Sequence(
        name='Initialize Bot',
        map_id_or_name=ASPENWOOD_GATE_LUXON,
        random_travel=False,
        hard_mode=True,
        children=[
            bot.Config.Aggressive(multi_account=True),
            BT.CreateParty(multibox_invite=True),
            BT.MoveAndExitMap((-5490, 13672),MOUNT_QINKAI),
        ],
    )

def Killroute() -> BehaviorTree:
    LUXON_PRIEST_COORDS = Vec2f(-8394, -9801)
    vanquish_steps: list[object] = [
        [(-13384.42, -9866.60)],  # snake yetis
        [(-14866.09, -7877.18)],  # 1st boss entry
        [(-16848.73, -9500.47)],  # 1st boss
        [(-11624.00, -3465.98)],  # wallow patrol
        {'pos': [(-13161.35, -1919.82)], 'clear_area_radius': Range.Spirit.value},  # killspot boss 2
        [(-9122.62, -581.28)],  # wallow patrol 2
        [(-7353.36, 2719.63)],  # wallow patrol 3
        [(-10231.84, 2839.61)],  # cave entrance
        [(-8779.03, 8012.96)],  # wallow patrol cave corner
        [(-3257.39, 8005.20)],  # killspot boss 3
        [(-7352.91, 1323.47)],  # to south
        [(-6666.01, -4688.44)],  # wallow patrols 4, 5, 6
        [(-23.21, -9324.52)],  # wallow patrol 7
        [(5566.71, -3648.33)],  # wallow patrol 8 part 1
        [(6897.17, -196.10)],  # wallow patrol 8 part 2
        [(6243.11, -8762.36)],  # beach onis
        [(11648.28, -6957.10)],  # beach patrol
        [(14615.63, -7808.74)],  # beach patrol 2
        [(13236.78, -3757.25)],  # beach patrol 3
        [(13283.18, 970.89)],  # beach exit
        [(10531.36, 8155.91)],  # water patrol 1
        [(5295.29, 6138.04)],  # hill patrol 1
        [(2336.91, 1077.21)],  # fork patrols
        [(-372.49, -2613.79)],  # last patrol
    ]
    
    return BT.Sequence(
        name='Killroute',
        children=[
            BT.TakeFactionBlessing(
                pos=LUXON_PRIEST_COORDS,
                faction='luxon',
                multi_account=True,
            ),
            BT.VanquishNode(vanquish_steps, name='MountQinkaiVanquishPath'),
            BT.Resign(wait_for_map_load=True, target_map_id=ASPENWOOD_GATE_LUXON, multi_account=True),
        ]
    )


def DonateFaction() -> BehaviorTree:
    return BT.DonateFaction(
        faction='luxon',
        threshold=DONATION_THRESHOLD,
        travel_map_id=CAVALON,
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
