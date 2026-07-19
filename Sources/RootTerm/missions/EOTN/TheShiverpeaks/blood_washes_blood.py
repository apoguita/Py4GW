"""Blood Washes Blood behavior tree."""

from Py4GWCoreLib import TitleID
from Py4GWCoreLib.py4gwcorelib_src.BehaviorTree import BehaviorTree
from Sources.ApoSource.ApoBottingLib import wrappers as BT
from Sources.RootTerm import bt_helpers as H
from Sources.RootTerm.config import MissionConfig


def build(cfg: MissionConfig) -> BehaviorTree:
    return BT.Sequence(
        name='Blood Washes Blood',
        children=[
            H.mission_consumables(),
            H.set_title(int(TitleID.Norn)),
            BT.MoveAndExitMap([(-25754.96, 16041.74), (-26550, 16300)], target_map_id=482),
            BT.VanquishNode(
                name='Cross Bjora Marches',
                steps=[
                    (16890.56, -16295.07), (13281.07, -14684.19), (11426.04, -11273.87),
                    (8681.58, -8351.80), (4562.88, -5023.34), (2643.43, -1491.73),
                    (-811.78, -787.35), (-4905.16, -1951.56), (-7767.45, -54.78),
                    (-10319, -182.54), (-13915.56, -184.13), (-17031.55, 4318.26),
                ],
                pause_on_combat=True,
                timeout_ms=90000,
            ),
            BT.MoveAndExitMap([(-19609.88, 5545.16), (-20500, 5575)], target_map_id=546),
            BT.Move(
                [(12984.56, -20605.87), (12105.67, -20677.68), (11874.58, -22307.19),
                 (10166.49, -23029.54), (9727.47, -21333.75), (9782.81, -21125.48)],
                pause_on_combat=False,
            ),
            H.interact_player_number(6461, 'Speak with Bear Spirit', aftercast_ms=1000),
            BT.SendDialog(0x84),
            BT.MoveAndExitMap(
                [(12988.34, -20397.69), (15266.63, -20437.96), (16000, -20475)],
                target_map_id=cfg.mission_map,
            ),
            BT.VanquishNode(
                name='Blood Washes Blood',
                steps=[
                    (1030.86, -4043.86), (-482.66, -2648.55), (-1791.38, -2234.62),
                    (-2159.38, -498.06), (-3058.86, 2376.23), (-1735.81, 2727.71),
                    (-18.15, 4574.90), (2008.16, 5593.78), (1088.41, 7747.85),
                    (208.15, 7752.79), (417.09, 9682.33), (-532.69, 10002.68),
                    (785.45, 10486.46), (1854.64, 11953.47), (-358.82, 12959.63),
                    (-1802.53, 12199.75), (1059.32, 13726.36), (3202.68, 13668.24),
                    (988.01, 14226.69), (3735.99, 13467.75), (7262.06, 12387.28),
                    (8409.62, 12098.68), (10746.95, 11868.91), (11775.67, 10846.75),
                    (12623.10, 9800.03), (13611.45, 8682.89), (15433.16, 8725.60),
                    (16084.40, 7006.34), (14293.30, 5024.11), (13674.05, 3739.03),
                    (14122.98, 1920.65), (14130.92, 986.74), (15011.57, -40.17),
                    (16355.53, -549.90), (16266.16, 814.62), (17969.41, 1863.44),
                    (18339.86, 3698.66), (16726.57, 3932.91), (16266.16, 814.62),
                ],
                pause_on_combat=True,
                timeout_ms=90000,
            ),
            H.skip_cinematic('Blood Washes Blood End'),
            BT.WaitForMapLoad(map_id=cfg.completion_map, timeout_ms=120000),
        ],
    )
