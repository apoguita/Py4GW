"""Borlis Pass behavior tree."""

from Py4GWCoreLib.py4gwcorelib_src.BehaviorTree import BehaviorTree
from Sources.ApoSource.ApoBottingLib import wrappers as BT
from Sources.RootTerm import bt_helpers as H
from Sources.RootTerm.config import MissionConfig


def _route(name: str, steps: list[tuple[float, float]]) -> BehaviorTree:
    return BT.VanquishNode(
        name=name, steps=steps, clear_area_radius=1100.0, pause_on_combat=True, timeout_ms=90000
    )


def _gadget(gadget_id: int, pos: tuple[float, float], name: str) -> BehaviorTree:
    return H.interact_gadget_id(gadget_id, pos, name)


def build(cfg: MissionConfig) -> BehaviorTree:
    return BT.Sequence(
        name='Borlis Pass',
        children=[
            H.enter_mission('Borlis', confirm_extra=True),
            H.mission_consumables(),
            H.interact_nearest_npc((19939.46, 1628.08), 'Borlis Talk to Guard Hayden'),
            _gadget(2136, (19610.26, 1484.91), 'Borlis Beacon 1'),
            BT.Wait(3000),
            _route('Borlis Beacon 2 Route', [(20046.25, 1702.74), (19617.49, 4046.40), (19598.05, 5958.05)]),
            _gadget(2139, (19191.83, 5395.36), 'Borlis Beacon 2'),
            BT.Wait(3000),
            _route('Borlis Beacon 3 Route', [(19241.48, 6254.15), (18249.62, 7243.14)]),
            _gadget(2140, (17883.43, 7529.60), 'Borlis Beacon 3'),
            BT.Wait(3000),
            _route('Borlis Beacon 4 Route', [(17580.26, 6396.36), (16462.19, 4416.17)]),
            _gadget(2141, (16245.72, 4261.71), 'Borlis Beacon 4'),
            BT.Wait(3000),
            _route('Borlis Beacon 5 Route', [(16695.51, 3608.82), (15541.57, 1906.91), (13588.97, 908.31)]),
            _gadget(2142, (13732.73, 1842.58), 'Borlis Beacon 5'),
            BT.Wait(3000),
            _route('Borlis Beacon 6 Route', [(13249.96, 280.84), (12641.64, -1664.70)]),
            _gadget(2143, (12375.49, -1939.63), 'Borlis Beacon 6'),
            BT.Wait(3000),
            _route('Borlis Beacon 7 Route', [(13331.27, -2049.56), (13775.93, -3462.30)]),
            _gadget(2144, (14037.68, -3773.58), 'Borlis Beacon 7'),
            BT.Wait(3000),
            _route('Borlis Reach Tolis', [(13156.34, -4066.51)]),
            BT.Move((11766.14, -4680.37), pause_on_combat=False, tolerance=150.0),
            BT.MoveAndInteractByModelID(2101, log=True),
            BT.Wait(3000),
            _route(
                'Borlis Fortress',
                [(10381.53, -5291.45), (9620.55, -4293.94), (8302.67, -1996.30), (8292.22, 1014.83)],
            ),
            _gadget(2134, (8247.73, 1305.86), 'Borlis Keg Station 1'),
            BT.Wait(3000),
            _route('Borlis First Wall', [(6987.25, 1166.93), (5183.20, 2884.62), (3140.48, 2759.01)]),
            BT.Move((3023, 2734), pause_on_combat=False, tolerance=150.0),
            BT.DropBundle(),
            BT.Wait(6000),
            _route(
                'Borlis Reach Rornak Wall',
                [
                    (-951.55, 3661), (-1024.39, 3598.06), (2178.51, 2588.50),
                    (1340.09, 115.92), (-296.51, -2702.51), (154.66, -3990.35),
                    (1677.77, -4197.99), (1897.43, -5675.11),
                ],
            ),
            _gadget(2135, (2206.22, -3339.10), 'Borlis Keg Station 2'),
            BT.Wait(3000),
            BT.Move([(1867.04, -5408.18), (933.68, -7084.39), (1009, -7116)], pause_on_combat=False),
            BT.DropBundle(),
            BT.Wait(6000),
            H.interact_nearest_npc((956.62, -7580.55), 'Borlis Talk to Rornak', aftercast_ms=20000),
            BT.Move([(887.75, -6574.53), (1978.07, -5470.16)], pause_on_combat=False),
            _gadget(2135, (2206.22, -3339.10), 'Borlis Bonus Keg'),
            BT.Wait(3000),
            BT.Move([(1867.04, -5408.18), (933.68, -7084.39), (1230.55, -8131.89)], pause_on_combat=False),
            BT.DropBundle(),
            BT.Wait(8000),
            _route(
                'Borlis Dragon Bonus',
                [
                    (1947.32, -8674.79), (2902.39, -9586.70), (4446.90, -9148.91),
                    (6857.48, -8859.98), (9054.28, -9223.73), (12097.91, -9240.54),
                    (14079.38, -8281.81), (15138.78, -9032.01), (17465.24, -9100.51),
                ],
            ),
            _route(
                'Borlis Return from Dragon',
                [
                    (15138.78, -9032.01), (14079.38, -8281.81), (12097.91, -9240.54),
                    (9054.28, -9223.73), (6857.48, -8859.98), (4446.90, -9148.91),
                    (2902.39, -9586.70), (1947.32, -8674.79), (899.49, -7010.20),
                    (2173.20, -4843.40),
                ],
            ),
            _gadget(2135, (2206.22, -3339.10), 'Borlis Rurik Keg'),
            BT.Wait(3000),
            BT.Move((-333.31, -4314.05), pause_on_combat=False),
            BT.DropBundle(),
            BT.Wait(8000),
            _route(
                'Borlis Reach Rurik',
                [
                    (-922.79, -5443.20), (-2732.82, -5442.10), (-4828.19, -4371.28),
                    (-7047.49, -4702.21), (-9594.11, -4944.11), (-9945.19, -2773.91),
                    (-11065.21, -2372.78), (-8807, -1836.31), (-9848.03, -1406.26),
                    (-9410.76, 756.89), (-9301.13, 966.17), (-8310.12, 2996.89),
                ],
            ),
            H.interact_nearest_npc((-8261.93, 4455.88), 'Borlis Talk to Prince Rurik', aftercast_ms=3000),
            H.skip_cinematic('Borlis Rurik Cinematic', wait_ms=3000),
            H.interact_nearest_npc((-10566, 6489), 'Borlis Talk to King Jalis', aftercast_ms=3000),
            _route(
                'Borlis Final Assault',
                [
                    (-11808.51, 6994.88), (-14133.79, 6021.43), (-17164.52, 5247.07),
                    (-18339.62, 3648.51), (-17850.90, 1543.13), (-16765.72, -1025.32),
                    (-15062.54, -2810.68), (-13622.72, -4338.61), (-12817.60, -6250.08),
                    (-14461.67, -8518.06), (-11329.84, -8301.09), (-11499.57, -9334.41),
                ],
            ),
            _gadget(2126, (-11860.97, -9742.15), 'Borlis Beacon 8'),
            BT.Wait(3000),
            _route('Borlis Beacon 9 Route', [(-11329.70, -10109), (-11876.03, -11210.70)]),
            _gadget(2127, (-12074.80, -10735.42), 'Borlis Beacon 9'),
            BT.Wait(3000),
            _route('Borlis Beacon 10 Route', [(-13253.46, -10263.29)]),
            _gadget(2128, (-12821.35, -10068.35), 'Borlis Beacon 10'),
            BT.Wait(3000),
            H.skip_cinematic('Borlis End Cinematic', wait_ms=3000),
            BT.WaitForMapLoad(map_id=cfg.completion_map, timeout_ms=120000),
        ],
    )
