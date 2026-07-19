"""The Great Northern Wall behavior tree (quest 936)."""

from __future__ import annotations

from Py4GWCoreLib import TitleID
from Py4GWCoreLib.py4gwcorelib_src.BehaviorTree import BehaviorTree
from Sources.ApoSource.ApoBottingLib import wrappers as BT
from Sources.RootTerm import bt_helpers as H
from Sources.RootTerm.config import MissionConfig


def build(cfg: MissionConfig) -> BehaviorTree:
    return BT.Sequence(
        name='The Great Northern Wall',
        children=[
            BT.LogMessage("Let's do The Great Northern Wall", module_name='RMA'),
            H.enter_mission('GNW', confirm_extra=True),
            H.mission_consumables(),
            H.set_title(int(TitleID.Ebon_Vanguard)),
            BT.AddModelToLootWhitelist(2115),
            BT.AddModelToLootWhitelist(2113),
            BT.AddModelToLootWhitelist(2114),
            BT.AddModelToLootWhitelist(2116),
            BT.VanquishNode(
                name='GNW Meet NPC',
                steps=[(5927, -12943), (5119, -12169)],
                pause_on_combat=True,
                timeout_ms=90000,
            ),
            BT.MoveAndInteract((5061.98, -12074.61), pause_on_combat=False),
            BT.VanquishNode(
                name='GNW To Lever',
                steps=[
                    (5117, -11825), (5666, -11008), (6180, -10266), (6042, -9902), (6043, -9647),
                    (5859, -8242), (4845, -7637), (3913, -6246), (3073, -5160), (2558, -4901),
                    (598, -4521), (-583, -4428), (-1439, -4194), (-2008, -4036), (-2865, -3665),
                    (-3181, -3183), (-3766, -1297), (-3693, 117), (-3297, 513), (-2749, 660),
                    (-2614, 1277), (-2399, 1632), (-3292, 3928),
                ],
                pause_on_combat=True,
                timeout_ms=90000,
            ),
            BT.MoveAndInteractWithGadget((-3377, 4053), pause_on_combat=False),
            BT.Wait(3000),
            BT.VanquishNode(
                name='GNW Wreckage 1',
                steps=[(-4748, 4837), (-6121, 4657), (-7332, 4485), (-9275, 4606), (-9622, 4951), (-11270, 6707)],
                pause_on_combat=True,
                timeout_ms=90000,
            ),
            H.interact_gadget_id(1784, (-11270, 6707), 'GNW Wreckage 1'),
            BT.Wait(3000),
            BT.LootItems(distance=2500.0, timeout_ms=30000),
            BT.VanquishNode(
                name='GNW Wreckage 2',
                steps=[
                    (-10690, 7517), (-9836, 8318), (-9025, 9176), (-8839, 9700), (-8596, 10412),
                    (-8123, 10902), (-6753, 11067), (-6320, 11133), (-5007, 10912), (-4732, 9952),
                    (-5433, 8420), (-5276, 7788),
                ],
                pause_on_combat=True,
                timeout_ms=90000,
            ),
            H.interact_gadget_id(1784, (-5276, 7788), 'GNW Wreckage 2'),
            BT.Wait(3000),
            BT.LootItems(distance=2500.0, timeout_ms=30000),
            BT.VanquishNode(
                name='GNW Wreckage 3',
                steps=[
                    (-5136, 9003), (-4478, 10520), (-3648, 11487), (-4555, 13087), (-4758, 13317),
                    (-5581, 14200), (-5678, 15040), (-5362, 16591), (-5657, 17077), (-6025, 17262),
                    (-6936, 17446), (-7298, 16981), (-7435, 16060), (-7607, 15373), (-8544, 14453),
                    (-8606, 14199), (-8013, 14160),
                ],
                pause_on_combat=True,
                timeout_ms=90000,
            ),
            H.interact_gadget_id(1784, (-8013, 14160), 'GNW Wreckage 3'),
            BT.Wait(3000),
            BT.LootItems(distance=2500.0, timeout_ms=30000),
            BT.VanquishNode(
                name='GNW Wreckage 4',
                steps=[
                    (-8640, 14358), (-7929, 15055), (-7545, 15897), (-7456, 16708), (-6821, 17413),
                    (-5937, 18039), (-5087, 18599), (-4445, 18215), (-3650, 17856), (-3228, 18216),
                    (-3139, 18889), (-2996, 19468), (-2588, 19503), (-2332, 19051),
                ],
                pause_on_combat=True,
                timeout_ms=90000,
            ),
            H.interact_gadget_id(1784, (-2332, 19051), 'GNW Wreckage 4'),
            BT.Wait(3000),
            BT.LootItems(distance=2500.0, timeout_ms=30000),
            BT.VanquishNode(
                name='GNW Deliver Bonus',
                steps=[
                    (-1232, 19299), (-465, 18898), (311, 18252), (822, 17825), (1108, 17167),
                    (801, 16274), (147, 15611), (-354, 14757), (-236, 14267),
                ],
                pause_on_combat=True,
                timeout_ms=90000,
            ),
            BT.MoveAndInteract((-236.11, 14266.26), pause_on_combat=False),
            BT.Wait(3000),
            BT.MoveAndInteract((-236.11, 14266.26), pause_on_combat=False),
            BT.Wait(3000),
            BT.VanquishNode(
                name='GNW Finish Push',
                steps=[
                    (-299, 15045), (340, 15751), (1168, 17067), (275, 18305), (-1210, 19087),
                    (-2413, 19233), (-2897, 19567), (-3108, 18753), (-3455, 17857), (-4582, 18338),
                    (-5284, 18402), (-6928, 17346), (-7479, 16095), (-8094, 14771), (-9441, 14091),
                    (-10222, 13381), (-10923, 12597), (-12060, 12192), (-13379, 12071),
                    (-14306, 11886), (-15974, 11873), (-16772, 12837), (-16809, 15328),
                ],
                pause_on_combat=True,
                timeout_ms=90000,
            ),
            H.skip_cinematic('GNW Cinematic 1', wait_ms=8000),
            BT.MoveDirect(
                [
                    (-14498, 12744), (-14519, 12036), (-14559, 10728), (-14683, 7850), (-13282, 3291),
                    (-9115, 345), (-8389, -412), (-7986, -1579), (-6362, -3446), (-5253, -4236),
                    (-3538, -5138), (1929, -7414), (3179, -7894), (4844, -9014), (6002, -10033),
                    (5958, -10849), (5172, -11916),
                ],
                pause_on_combat=False,
                timeout_ms=90000,
                tolerance=250.0,
            ),
            BT.MoveAndInteract((5172, -11916), pause_on_combat=False),
            H.skip_cinematic('GNW Cinematic 2', wait_ms=1000),
            BT.WaitForMapLoad(map_id=cfg.completion_map, timeout_ms=120000),
        ],
    )
