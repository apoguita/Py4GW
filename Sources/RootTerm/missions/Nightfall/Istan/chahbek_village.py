"""Chahbek Village behavior tree (quest 978)."""

from __future__ import annotations

from Py4GWCoreLib import TitleID
from Py4GWCoreLib.py4gwcorelib_src.BehaviorTree import BehaviorTree
from Sources.ApoSource.ApoBottingLib import wrappers as BT
from Sources.RootTerm import bt_helpers as H
from Sources.RootTerm.config import MissionConfig

NPC_XY = (3542.21, -5201.80)


def build(cfg: MissionConfig) -> BehaviorTree:
    return BT.Sequence(
        name='Chahbek Village',
        children=[
            BT.LogMessage("Let's do Chahbek Village", module_name='RMA'),
            BT.MoveAndDialog(NPC_XY, 0x81, pause_on_combat=False, log=True),
            BT.Wait(1000),
            BT.MoveAndDialog(NPC_XY, 0x84, pause_on_combat=False, log=True),
            BT.WaitUntilOnExplorable(timeout_ms=30000),
            BT.Wait(2000),
            H.mission_consumables(),
            H.set_title(int(TitleID.Lightbringer)),
            BT.VanquishNode(
                name='Chahbek Clear Corsairs',
                steps=[
                    (3246.24, -3531.79),
                    (1814.75, -3718.83),
                    (226.88, -5757.88),
                    (-683.73, -4043.84),
                    (-2000.08, -3392.83),
                    (-4320.19, -2137.18),
                ],
                clear_area_radius=600.0,
                pause_on_combat=True,
            ),
            BT.MoveAndInteractWithGadget((-4715.77, -1836.36), pause_on_combat=False),
            BT.Wait(1000),
            BT.MoveAndInteractWithGadget((-1696.50, -2564.60), pause_on_combat=False),
            BT.Wait(4000),
            BT.InteractWithGadgetAtXY((-1696.50, -2564.60)),
            BT.Wait(1000),
            BT.MoveAndInteractWithGadget((-4715.77, -1836.36), pause_on_combat=False),
            BT.Wait(1000),
            BT.MoveAndInteractWithGadget(
                [(-1818.94, -3599.51), (-1725.04, -4104.62)],
                pause_on_combat=False,
            ),
            BT.Wait(4000),
            BT.InteractWithGadgetAtXY((-1725.04, -4104.62)),
            BT.Wait(1000),
            BT.VanquishNode(
                name='Chahbek Boss Finish',
                steps=[
                    (-2672.59, -3801.81),
                    (-2398.64, -6207.63),
                    (-4223.66, -6597.19),
                    (-3909.37, -4700.47),
                    (-3068.31, -2816.32),
                    (-2160.76, -424.09),
                    (-1698.78, 1248.06),
                    (-29.31, -1009.32),
                ],
                clear_area_radius=600.0,
                pause_on_combat=True,
            ),
            H.skip_cinematic('Chahbek End Cinematic', wait_ms=1000),
            BT.WaitForMapLoad(map_id=cfg.completion_map, timeout_ms=120000),
        ],
    )
