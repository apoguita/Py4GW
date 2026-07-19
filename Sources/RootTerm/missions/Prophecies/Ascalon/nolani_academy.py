"""Nolani Academy behavior tree."""

from __future__ import annotations

from Py4GWCoreLib import TitleID
from Py4GWCoreLib.py4gwcorelib_src.BehaviorTree import BehaviorTree
from Sources.ApoSource.ApoBottingLib import wrappers as BT
from Sources.RootTerm import bt_helpers as H
from Sources.RootTerm.config import MissionConfig

AGGRO_RANGE = 1100.0
MOVE_TIMEOUT_MS = 90000


def _combat_route(name: str, steps: list[tuple[float, float]]) -> BehaviorTree:
    return BT.VanquishNode(
        name=name,
        steps=steps,
        clear_area_radius=AGGRO_RANGE,
        pause_on_combat=True,
        timeout_ms=MOVE_TIMEOUT_MS,
    )


def build(cfg: MissionConfig) -> BehaviorTree:
    return BT.Sequence(
        name='Nolani Academy',
        children=[
            BT.LogMessage("Let's do Nolani Academy", module_name='RMA'),
            BT.SetHardMode(False),
            H.enter_mission('Nolani', confirm_extra=True),
            H.mission_consumables(),
            H.set_title(int(TitleID.Ebon_Vanguard)),
            BT.AddModelToLootWhitelist(2582),
            _combat_route(
                'Nolani Hidden Route',
                [
                    (1199.86, 13856.27), (3643.42, 15025.54), (4462.81, 16616.13),
                    (5887.46, 16092.21), (7779.88, 18416.34), (7567.20, 15778.91),
                    (6353.17, 14455.10), (8502.56, 13746.58), (8292.09, 11762.33),
                    (7638.68, 10516.06), (7128.58, 8645.34), (7376.85, 6003.29),
                    (9382.25, 5045.53), (10127.84, 4181.92), (10916.77, 2772.24),
                ],
            ),
            BT.Move((10557.11, 1632.79), pause_on_combat=False, tolerance=150.0),
            BT.MoveAndInteractByModelID(2114, log=True),
            BT.Wait(15000),
            BT.LootItems(distance=2000.0, timeout_ms=30000),
            _combat_route(
                'Nolani Deliver Tome',
                [
                    (10706.39, 2991.47), (8078.37, 5667.91), (5962.10, 6208.28),
                    (5723.94, 3626.09), (6819.18, 1933.93), (5806.97, -8.64),
                    (6610.01, -1803.44), (3815.54, -620.37), (117.05, -1328.53),
                    (-2391.31, -1763.85), (-4114.97, -482.35), (-7124.29, -1816.29),
                    (-8903.19, -2593.50), (-7335.63, -2379.27), (-8274.38, -4329.30),
                    (-10288.22, -5564.24), (-12025.50, -6230.05), (-13274.48, -5830.60),
                ],
            ),
            H.interact_gadget_id(1673, (-13405.83, -6034.15), 'Nolani Tome Pedestal'),
            BT.Wait(5000),
            BT.Move((-13187.85, -5984.63), pause_on_combat=False, tolerance=150.0),
            H.interact_player_number(2504, 'Nolani Talk to Old Ascalon Spirit', aftercast_ms=25000),
            _combat_route(
                'Nolani Reach Rurik',
                [
                    (-12207.46, -6345.21), (-10087.85, -5513.81), (-7970.74, -4092.66),
                    (-6969.54, -1654.25), (-5144.68, -558.49), (-1376.31, -482.30),
                    (-557.50, 1666.80), (-2958.49, 3792.83), (-1774.88, 5278.34),
                    (-491.69, 5852.25), (1236.20, 7051.47), (-797.30, 7514.10),
                    (-647.17, 8507.22), (-63.44, 10642.98),
                ],
            ),
            _combat_route(
                'Nolani Escort Rurik to Gate',
                [
                    (-0.56, 12986.04), (653.68, 9602.64), (-357.08, 6451.81),
                    (-1933.38, 5083.88), (-1219.65, 2411.41), (-728.62, -30.55),
                    (-3414.35, -1138.52), (-2201.12, -1853.91), (836.59, -1324.35),
                ],
            ),
            BT.Wait(3000),
            H.skip_cinematic('Nolani Gate Cinematic', wait_ms=3000),
            _combat_route(
                'Nolani Defeat Bonfaaz Burntfur',
                [
                    (-2746.61, -4484.06), (-1453.42, -7489.17), (780.26, -10433.18),
                    (4881.26, -10741.67), (5807.55, -13332.95), (4199.90, -15298.89),
                    (6007.72, -17914.33),
                ],
            ),
            H.skip_cinematic('Nolani End Cinematic', wait_ms=3000),
            BT.WaitForMapLoad(map_id=cfg.completion_map, timeout_ms=120000),
        ],
    )
