"""Fort Ranik behavior tree (quest 937)."""

from __future__ import annotations

from Py4GWCoreLib import TitleID
from Py4GWCoreLib.py4gwcorelib_src.BehaviorTree import BehaviorTree
from Sources.ApoSource.ApoBottingLib import wrappers as BT
from Sources.RootTerm import bt_helpers as H
from Sources.RootTerm.config import MissionConfig


def build(cfg: MissionConfig) -> BehaviorTree:
    return BT.Sequence(
        name='Fort Ranik',
        children=[
            BT.LogMessage("Let's do Fort Ranik", module_name='RMA'),
            H.enter_mission('Ranik', confirm_extra=True),
            H.mission_consumables(),
            H.set_title(int(TitleID.Ebon_Vanguard)),
            BT.VanquishNode(
                name='Ranik Rescue Armin',
                steps=[
                    (-4438, -27521), (-4085.27, -25360.53), (-4018, -24944),
                    (-3604, -23337), (-3338, -22464), (-3305.90, -22416.73),
                    (-3495, -21252), (-4018, -19549), (-4303.10, -18862.53),
                    (-4430, -18608), (-4899, -18034),
                    (-5308, -16938), (-5147, -15541), (-4906, -15068), (-4329, -15365),
                    (-3422, -15149), (-2818, -12873), (-1882, -11732), (-1192, -10964),
                    (-897, -9912), (-921, -9498),
                ],
                clear_area_radius=1100.0,
                pause_on_combat=True,
                timeout_ms=90000,
            ),
            BT.Wait(5000),
            H.interact_player_number(2156, 'Ranik Accept Armin Bonus'),
            BT.VanquishNode(
                name='Ranik Main Push',
                steps=[
                    (-398, -10160), (433, -8660), (1718, -7103), (2243, -6654),
                    (3251, -6839), (4290.54, -6987.38), (5344, -6890), (6289, -6351), (5669, -5581),
                    (4791, -5666), (3199, -4962), (2402, -4639), (1070, -4077),
                    (-488, -3111), (-1427, -1854), (-1019, -314), (62, 152),
                    (2517, -66), (3726, -572), (4402, -673), (4752, -26),
                    (5092, 2151), (5291, 3095), (5898, 3190), (6426, 2347),
                    (6585, 1629), (6678, 784), (6736, -615), (6735, -1514),
                ],
                clear_area_radius=1100.0,
                pause_on_combat=True,
                timeout_ms=90000,
            ),
            BT.Wait(3000),
            H.interact_player_number(2153, 'Ranik Rescue Deeter'),
            BT.Wait(20000),
            BT.VanquishNode(
                name='Ranik To Siegemaster',
                steps=[
                    (6783, -1980), (6772, -1616), (6457, 2183), (5808, 3425),
                    (2848, 4942), (-52, 6788), (-726, 6538), (-149, 6546),
                    (-560, 8043), (-756, 9795), (-1252, 10178), (-2621, 11190),
                    (-2079, 12515), (-1112, 13026), (-489, 13063), (939, 12901),
                    (3047, 12938), (3759, 14248), (4142, 15217), (3486, 16512),
                    (2476, 18033), (2367, 17772), (2070, 16218),
                ],
                clear_area_radius=1100.0,
                pause_on_combat=True,
                timeout_ms=90000,
            ),
            BT.ClearEnemiesInArea((2045.92, 15675.97), radius=2500.0),
            H.interact_nearest_npc((2045.92, 15675.97), 'Ranik Start Lormar Salvage'),
            H.skip_cinematic('Ranik Intro Cinematic', wait_ms=2000),
            BT.VanquishNode(
                name='Ranik Catapult Part 1 Route',
                steps=[(1275, 15580), (2192, 15602), (2519, 16189), (3893, 17958)],
                clear_area_radius=1100.0,
                pause_on_combat=True,
                timeout_ms=90000,
            ),
            BT.MoveAndInteractWithGadget((3893.15, 17958.28), pause_on_combat=True),
            BT.Wait(3000),
            H.pickup_nearby_items('Ranik Pickup Catapult Part 1'),
            BT.Move([(2494, 16252), (2046, 15676)], pause_on_combat=False),
            H.interact_nearest_npc((2045.92, 15675.97), 'Ranik Deliver Catapult Part 1'),
            BT.VanquishNode(
                name='Ranik Catapult Part 2 Route',
                steps=[(3568, 16390), (4401, 15034)],
                clear_area_radius=1100.0,
                pause_on_combat=True,
                timeout_ms=90000,
            ),
            BT.MoveAndInteractWithGadget((4401, 15034), pause_on_combat=True),
            BT.Wait(3000),
            H.pickup_nearby_items('Ranik Pickup Catapult Part 2'),
            BT.Move([(4164, 15421), (3377, 16704), (2046, 15676)], pause_on_combat=False),
            H.interact_nearest_npc((2045.92, 15675.97), 'Ranik Deliver Catapult Part 2'),
            BT.MoveAndInteractWithGadget(
                [(1239, 14236), (1493, 13566), (2615, 12904)],
                pause_on_combat=True,
            ),
            BT.Wait(3000),
            H.pickup_nearby_items('Ranik Pickup Catapult Part 3'),
            BT.Move([(1609, 13527), (1220, 14052), (1215, 15524), (2024, 15681)], pause_on_combat=False),
            H.interact_nearest_npc((2045.92, 15675.97), 'Ranik Deliver Catapult Part 3', aftercast_ms=5000),
            BT.Wait(5000),
            BT.MoveAndInteractWithGadget((2190.47, 15324.97), pause_on_combat=False),
            BT.Wait(10000),
            BT.InteractWithGadgetAtXY((2190.47, 15324.97)),
            BT.Wait(5000),
            BT.InteractWithGadgetAtXY((2190.47, 15324.97)),
            BT.Wait(3000),
            BT.VanquishNode(
                name='Ranik Advance',
                steps=[
                    (852, 16520), (288, 17387), (862, 18667), (1152, 20083),
                    (595, 20697), (-22, 20581), (-1674, 20360), (-2301, 19094),
                ],
                clear_area_radius=1100.0,
                pause_on_combat=True,
                timeout_ms=90000,
            ),
            BT.MoveAndInteractWithGadget((-2301, 19094), pause_on_combat=False),
            BT.VanquishNode(
                name='Ranik Final Assault',
                steps=[
                    (-1209, 18855), (-1940, 18307), (-3370, 17392), (-4420, 16774),
                    (-2682, 17754), (-2159, 18118), (-4095, 16860), (-4575, 16571),
                    (-5309, 16233), (-6285, 16393), (-7065, 16704), (-7540, 17345),
                    (-6737, 18359), (-6170, 19075), (-5982, 19331),
                ],
                clear_area_radius=1100.0,
                pause_on_combat=True,
                timeout_ms=90000,
            ),
            H.skip_cinematic('Ranik End Cinematic', wait_ms=1000),
            BT.WaitForMapLoad(map_id=cfg.completion_map, timeout_ms=120000),
        ],
    )
