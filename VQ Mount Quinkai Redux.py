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
            reset=False,
            multi_account=True,
            configure_fn=lambda tree: tree.Config.ConfigureUpkeep(
                disable_looting=False,
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
                    ModelID.Honeycomb.value,
                    ModelID.War_Supplies.value,
                ],
                enable_party_wipe_recovery=True,
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
            bot.Config.Aggressive(multi_account=True, auto_loot=False),
            BT.CreateParty(multibox_invite=True),
            BT.MoveAndExitMap((-5490, 13672),MOUNT_QINKAI),
        ],
    )


def Killroute() -> BehaviorTree:
    LUXON_PRIEST_COORDS = Vec2f(-8394, -9801)
    
    Vanquish_Path:list[tuple[float, float]] = [
       
      (-17490.23, -10193.84), #tendril
      (-13498.94, -4763.97),
      (-11674.48, -4599.29), #wallow patrol
      (-14406.66, -2555.92), #hole
      (-13735.23, -1511.41), #exit hole
      (-10319.44, 2159.07), #cave entrance
      (-7937.16, 3062.79), #wallow patrol
      (-9173.34, 7675.70),
      (-8041.39, 8370.92),
      (-4787.85, 6801.43), #clear
      (-3314.36, 7860.74),
      (-2001.17, 9037.19),
      (-6694.74, 2240.26), #out of cave
      (-9176.05, -13.35),
      (-6789.09, 189.53), #just in case
      (-6890.70, -3249.73), #lower wallows
      (-8307.69, -5465.48),
      (-5021.97, -3830.00),
      (-2310.74, -8512.54),
      (1983.03, -8555.85), #lower oxix
      (6484.80, 1017.07), #wallow patrol
      (6212.15, -8736.39), #beach onis
      (11368.18, -7458.21), #beach patrol
      (14728.93, -9258.35),
      (14774.19, -4493.75),
      (11622.91, -4078.38),
      (13287.39, 296.37),
      (16030.41, 6932.02),
      (11591.91, 7965.41), #water
      (10822.86, 9232.65),
      (7920.46, 5972.42),
      (6274.33, 7410.21), #hill
      (5824.00, 5289.97),
      (4266.50, 5832.48),
      
      (1506.29, 1406.74), #last aptrols
      (1737.57, 1202.17),
      (4450.66, 1146.03), #just in case
      (700.20, -398.73),
      (-273.59, -2516.34),
      (95.02, -3131.64),
      (-1687.58, -3565.68),

    ]


    return BT.Sequence(
        name='Killroute',
        children=[
            BT.TakeFactionBlessing(
                pos=LUXON_PRIEST_COORDS,
                faction='luxon',
                multi_account=True,
            ),
            BT.MoveAndKill((-13384.42, -9866.60)), #snake yetis 
            BT.MoveAndKill((-14866.09, -7877.18)), #1st boss entry
            BT.MoveAndKill((-16848.73, -9500.47)), #1st boss
            BT.MoveAndKill((-11624.00, -3465.98)), #wallow patrol
            BT.MoveAndKill((-13161.35, -1919.82), Range.Spirit.value), #killspot Boss 2
            BT.MoveAndKill((-9122.62, -581.28)), #wallow patrol 2
            BT.MoveAndKill((-7353.36, 2719.63)), #wallow patrol 3
            BT.MoveAndKill((-10231.84, 2839.61)), #cave entrance
            BT.MoveAndKill((-8779.03, 8012.96)), #wallow patrol cave corner
            BT.MoveAndKill((-3257.39, 8005.20)), #killspot Boss 3
            BT.MoveAndKill((-7352.91, 1323.47)), #to south
            BT.MoveAndKill((-6666.01, -4688.44)), #wallow patrols 4, 5, 6
            BT.MoveAndKill((-23.21, -9324.52)), #wallow patrol 7
            BT.MoveAndKill((5566.71, -3648.33)), #wallow patrol 8 part 1
            BT.MoveAndKill((6897.17, -196.10)), #wallow patrol 8 part 2
            BT.MoveAndKill((6243.11, -8762.36)), #beach onis
            BT.MoveAndKill((11648.28, -6957.10)), #beach patrol
            BT.MoveAndKill((14615.63, -7808.74)), #beach patrol 2
            BT.MoveAndKill((13236.78, -3757.25)), #beach patrol 3
            BT.MoveAndKill((13283.18, 970.89)), #beach exit
            BT.MoveAndKill((10531.36, 8155.91)), #water patrol 1
            BT.MoveAndKill((5295.29, 6138.04)), #hill patrol 1
            BT.MoveAndKill((2336.91, 1077.21)), #fork patrols
            BT.MoveAndKill((-372.49, -2613.79)), #last patrol
        ]
    )

def get_execution_steps() -> list[tuple[str, Callable[[], BehaviorTree]]]:
    return [
        ('Initialize Bot', InitializeBot),
        ('Killroute', Killroute),
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
