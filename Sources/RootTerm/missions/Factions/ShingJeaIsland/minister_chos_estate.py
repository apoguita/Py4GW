"""Minister Cho's Estate behavior tree."""

from Py4GWCoreLib.py4gwcorelib_src.BehaviorTree import BehaviorTree
from Sources.ApoSource.ApoBottingLib import wrappers as BT
from Sources.RootTerm import bt_helpers as H
from Sources.RootTerm.config import MissionConfig


def _route(name: str, steps: list[tuple[float, float]]) -> BehaviorTree:
    return BT.VanquishNode(
        name=name, steps=steps, clear_area_radius=1100.0, pause_on_combat=True, timeout_ms=90000
    )


def _gate(name: str, steps: list[tuple[float, float]]) -> BehaviorTree:
    return BT.MoveDirect(steps, pause_on_combat=False, tolerance=300.0, timeout_ms=90000, log=False)


def build(cfg: MissionConfig) -> BehaviorTree:
    return BT.Sequence(
        name="Minister Cho's Estate",
        children=[
            H.enter_mission('Minister Cho', confirm_extra=True),
            H.mission_consumables(),
            _gate(
                'Minister Cho Meet Togo',
                [(6264.99, -7381.35), (5438.78, -7719.41), (4789.56, -8223.23)],
            ),
            _gate(
                'Minister Cho First Gate',
                [(2930.84, -9747.31), (1554.88, -9657.38), (490.25, -8868.56), (-38.68, -8424.63)],
            ),
            _route(
                'Minister Cho First Combat',
                [(-38.68, -8424.63), (338.49, -7394.05), (2211.32, -5609.10)],
            ),
            _gate('Minister Cho Tutorial Gate', [(2211.32, -5609.10), (3016.76, -5054.50), (4561.17, -5721.56)]),
            BT.Wait(8000),
            _gate('Minister Cho Boy Gate', [(4858.58, -5060.47), (4172.04, -3561.60), (4422.56, -2770.28)]),
            _route(
                'Minister Cho Middle Combat',
                [
                    (4422.56, -2770.28), (6115.01, -1410.66), (4800.35, -188.05),
                    (2831.63, 543.56), (2062.59, 1483.59),
                ],
            ),
            _gate('Minister Cho AFK Gate', [(1723.76, 1737.98), (995.31, 1851.93)]),
            _route(
                'Minister Cho Boss Gate Route',
                [
                    (995.31, 1851.93), (-96.41, 812.39), (-545.83, -153.44),
                    (-1930.21, -2003.77), (-1361.03, -2993.86), (-2837.73, -4558.68),
                ],
            ),
            _gate('Minister Cho Boss Gate', [(-3374.95, -4789.19), (-3958.61, -5357.37)]),
            _route(
                'Minister Cho Animal Enclosure',
                [
                    (-3958.61, -5357.37), (-4939.85, -6653.10), (-6584.78, -7480.33),
                    (-7721.43, -7247.29), (-8521.07, -5151.97), (-9257.88, -5017.96),
                    (-9288.70, -3578.31), (-8760.59, -2072.78), (-7560.81, -1137.60),
                ],
            ),
            _route(
                'Minister Cho Sickened Guards',
                [
                    (-6965, 1351.61), (-8152.03, 2270.59), (-9627.77, 1692.16),
                    (-11306.53, 2237.83), (-13146.20, 1205.35), (-14501.01, 1221.93),
                    (-15374.92, 2416.90), (-16920.52, 2448.64),
                ],
            ),
            H.interact_player_number(3292, 'Minister Cho Finale Interaction', aftercast_ms=3000),
            H.skip_cinematic('Minister Cho First Cinematic', wait_ms=3000),
            _route('Minister Cho Final Combat', [(-16920.52, 2448.64)]),
            H.skip_cinematic('Minister Cho End Cinematic', wait_ms=3000),
            BT.WaitForMapLoad(map_id=cfg.completion_map, timeout_ms=120000),
        ],
    )
