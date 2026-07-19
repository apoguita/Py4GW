"""Zen Daijun behavior tree."""

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
        name='Zen Daijun',
        children=[
            H.enter_mission('Zen Daijun', confirm_extra=True),
            H.mission_consumables(),
            _route('Zen Meet Togo and Vhang', [(15390.76, 10700.74)]),
            BT.Wait(12000),
            _route('Zen First Shrine Route', [(13947.37, 9992.67), (12134.37, 11163.43)]),
            H.interact_gadget_id(2890, (11760, 11339.48), 'Zen Shrine of Zunraa 1'),
            BT.Wait(7000),
            _route(
                'Zen First Afflicted',
                [(13007.05, 12505.07), (11731.15, 10618.77), (9152.42, 9028.86), (10250.08, 8569.23)],
            ),
            H.interact_gadget_id(2890, (9695.40, 7993.86), 'Zen Shrine of Zunraa 2'),
            BT.Wait(7000),
            _route(
                'Zen Second Afflicted',
                [
                    (8810.87, 5940.41), (7592.46, 4090.03), (6727.82, 2994.74),
                    (5677.11, 2082.88), (4931.12, 1566.18),
                ],
            ),
            H.interact_gadget_id(2890, (4828.47, 1497.95), 'Zen Shrine of Zunraa 3'),
            BT.Wait(7000),
            _route(
                'Zen Western Sweep',
                [
                    (6046.72, 2026.94), (5747.90, 463.60), (6046.72, 2026.94),
                    (4589.67, 3642.48), (3488.16, 5530.04), (1566.16, 6940.97),
                    (-42.77, 6744.66), (-3040.14, 8913.43), (-5702.43, 9254.14),
                    (-8239.15, 9083.23), (-9011.56, 7709.74), (-6119.54, 5296.56),
                    (-5532.48, 3826.03), (-5040.52, 2984.02),
                ],
            ),
            H.interact_gadget_id(2890, (-4971.42, 3008.29), 'Zen Shrine of Zunraa 4'),
            BT.Wait(7000),
            _route(
                'Zen Southwest Approach',
                [
                    (-8643.23, 3508.33), (-9905.16, 4205.73), (-11842.73, 2987.10),
                    (-13734.34, 2806.67), (-14385.04, 1027.67), (-12711.48, 1598.55),
                    (-12460.67, 251.77), (-11346.38, 854.51),
                ],
            ),
            BT.Wait(20000),
            _route('Zen Defeat Yijo', [(-9778.59, -75.65), (-8859.35, -627.41)]),
            BT.Wait(20000),
            _route('Zen Finish', [(-7552.23, -1419.17), (-7231.34, -1680.38)]),
            H.skip_cinematic('Zen End Cinematic', wait_ms=3000),
            BT.WaitForMapLoad(map_id=cfg.completion_map, timeout_ms=120000),
        ],
    )
