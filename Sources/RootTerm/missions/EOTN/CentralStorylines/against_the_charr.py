"""Against the Charr behavior tree."""

from Py4GWCoreLib import TitleID
from Py4GWCoreLib.py4gwcorelib_src.BehaviorTree import BehaviorTree
from Sources.ApoSource.ApoBottingLib import wrappers as BT
from Sources.RootTerm import bt_helpers as H
from Sources.RootTerm.config import MissionConfig


def build(cfg: MissionConfig) -> BehaviorTree:
    return BT.Sequence(
        name='Against the Charr',
        children=[
            H.mission_consumables(),
            H.set_title(int(TitleID.Ebon_Vanguard)),
            BT.MoveAndExitMap([(-22371.35, 13317.14), (-22000, 12600)], target_map_id=649),
            BT.VanquishNode(
                name='Cross Grothmar Wardowns',
                steps=[(-18354.12, 9359), (-13224.75, 9036.51), (-11277.86, 5200.53),
                       (-11900.47, 1612.69), (-9664.72, -2992.89)],
                pause_on_combat=True,
                timeout_ms=90000,
            ),
            BT.MoveAndDialog((-9668.97, -2813.23), 0x84, pause_on_combat=False),
            BT.WaitForMapLoad(map_id=cfg.mission_map, timeout_ms=120000),
            H.skip_cinematic('Against the Charr Intro'),
            BT.VanquishNode(
                name='Against the Charr',
                steps=[
                    (-10407.28, -1277.22), (-7846.21, 148.42), (-4012.59, -851.61),
                    (-1494.90, -2156.27), (234.24, -6019.92), (237.59, -10497.45),
                    (3109.09, -12247.86), (6944.20, -12098.49), (9777.08, -11206.25),
                    (13420.83, -8798.42), (14874.23, -6129), (18434.24, -5462.01),
                    (18637.43, -1566.01), (18755.28, -67.48), (20057.48, 742.32),
                    (19305.62, 1595.67), (18234.86, 2721.54), (19794.18, 3592.76),
                ],
                pause_on_combat=True,
                timeout_ms=90000,
            ),
            H.skip_cinematic('Against the Charr End'),
            BT.WaitForMapLoad(map_id=cfg.completion_map, timeout_ms=120000),
        ],
    )
