"""Nahpui Quarter behavior tree."""

from Py4GWCoreLib.py4gwcorelib_src.BehaviorTree import BehaviorTree
from Sources.ApoSource.ApoBottingLib import wrappers as BT
from Sources.RootTerm import bt_helpers as H
from Sources.RootTerm.config import MissionConfig


def _route(name: str, steps: list[tuple[float, float]]) -> BehaviorTree:
    return BT.VanquishNode(
        name=name, steps=steps, clear_area_radius=1100.0, pause_on_combat=True, timeout_ms=90000
    )


def build(cfg: MissionConfig) -> BehaviorTree:
    return BT.Sequence(
        name='Nahpui Quarter',
        children=[
            H.enter_mission('Nahpui'),
            H.mission_consumables(),
            _route('Nahpui Left Portal', [(-14672.70, 2912.89)]),
            BT.Wait(27000),
            BT.Move((-14000, 3100), pause_on_combat=False, tolerance=300.0),
            BT.Wait(3000),
            _route(
                'Nahpui Kaijun Don',
                [(-7905.66, 4966.45), (-8491.89, 7522.19), (-7959.55, 9656.93), (-6948.59, 9900.39)],
            ),
            _route(
                'Nahpui Kuonghsan',
                [
                    (-5286.18, 7754.91), (-3184.81, 7099.60), (-938.39, 8826.81),
                    (839.06, 10150.05), (2313.35, 9902.02), (2843.15, 8233.45),
                    (2430.86, 6664.43), (198.30, 5312.93),
                ],
            ),
            _route(
                'Nahpui Tahmu',
                [
                    (818.17, 4012.68), (412.25, 1872.35), (-722.26, 521.08),
                    (671.52, -1371.70), (-490.44, -2588.97), (-1977.30, -4066.83),
                    (-3204.25, -5837.32), (-4705.01, -6992.23), (-6072.64, -7532.83),
                    (-7331.12, -7072.13),
                ],
            ),
            _route(
                'Nahpui Hai Jii',
                [
                    (-10050.26, -8264.56), (-7687.05, -10066.73), (-7245.03, -12481.55),
                    (-9763.44, -12677.44), (-11094.54, -12645.63), (-12147.89, -12456.08),
                    (-13982, -12269.51), (-14575.80, -12797.82), (-17277.51, -12541.40),
                    (-17643.58, -11097.11), (-17647.75, -9528.61),
                ],
            ),
            H.skip_cinematic('Nahpui End Cinematic', wait_ms=3000),
            BT.WaitForMapLoad(map_id=cfg.completion_map, timeout_ms=120000),
        ],
    )
