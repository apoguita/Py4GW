"""A Gate Too Far behavior tree."""

from Py4GWCoreLib import TitleID
from Py4GWCoreLib.py4gwcorelib_src.BehaviorTree import BehaviorTree
from Sources.ApoSource.ApoBottingLib import wrappers as BT
from Sources.RootTerm import bt_helpers as H
from Sources.RootTerm.config import MissionConfig


def build(cfg: MissionConfig) -> BehaviorTree:
    return BT.Sequence(
        name='A Gate Too Far',
        children=[
            H.mission_consumables(),
            H.set_title(int(TitleID.Deldrimor)),
            BT.MoveAndDialog((140.79, -664.07), 0x81, pause_on_combat=False),
            BT.SendDialog(0x86),
            BT.WaitForMapLoad(map_id=cfg.mission_map, timeout_ms=120000),
            BT.VanquishNode(
                name='Gate Level 1',
                steps=[
                    (-7939.19, -8236.75), (-8503.19, -6458.65), (-8482.08, -3730.64),
                    (-4480.54, -2570.26), (-4241.66, 831.40), (-4051.21, 1575.58),
                    (-6094.60, 1214.07), (-6226.66, 2932.92), (-6244.83, 6197.25),
                    (-5495.48, 7438.15), (-7545.33, 6433.09), (-8059.18, 4887.56),
                    (-6225.13, 5954.66), (-5241.35, 3959.85), (-6310.10, 2459.40),
                    (-8148.47, 975.34), (-10079.35, 557.36), (-11816.74, 361.78),
                    (-13037.22, 2173.07), (-15058.44, 3224.26), (-14783.17, 5700.87),
                    (-15965, 7933.68), (-18536.82, 9319.38),
                ],
                pause_on_combat=True,
                timeout_ms=90000,
            ),
            BT.MoveAndExitMap([(-18769.05, 9713.16), (-20000, 9740)], target_map_id=cfg.map2),
            BT.VanquishNode(
                name='Gate Level 2',
                steps=[
                    (19732.16, 3418.35), (20066.38, 6599.54), (19207.95, 10755.72),
                    (18260.83, 11153.54), (15112.38, 11103.18), (12877.34, 11661.35),
                    (11219.69, 13678.69), (10213.87, 16199.13), (8255.81, 17116.79),
                    (4654.04, 17014.84),
                ],
                pause_on_combat=True,
                timeout_ms=90000,
            ),
            BT.MoveAndExitMap([(4035.24, 17319.94), (3200, 17650)], target_map_id=cfg.map3),
            BT.VanquishNode(
                name='Gate Level 3',
                steps=[
                    (5933.77, 19279.47), (7770.95, 16673.60), (8372.51, 16769.46),
                    (5823.90, 16183.85), (4087.57, 13952.66), (5201.56, 12537.60),
                    (6186.10, 11157.88), (6641.01, 7995.78), (6988.30, 6650.17),
                    (5946.24, 5424.67), (7551.97, 4398.54), (7565.61, 2604.62),
                ],
                pause_on_combat=True,
                timeout_ms=90000,
            ),
            H.skip_cinematic('A Gate Too Far End'),
            BT.WaitForMapLoad(map_id=cfg.completion_map, timeout_ms=120000),
        ],
    )
