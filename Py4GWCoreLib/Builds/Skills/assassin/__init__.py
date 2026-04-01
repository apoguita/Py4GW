from __future__ import annotations

from typing import TYPE_CHECKING

from .NoAttribute import NoAttribute as NoAttributeClass
from .DaggerMastery import DaggerMastery as DaggerMasteryClass
from .DeadlyArts import DeadlyArts as DeadlyArtsClass
from .ShadowArts import ShadowArts as ShadowArtsClass
from .CriticalStrikes import CriticalStrikes as CriticalStrikesClass

if TYPE_CHECKING:
    from Py4GWCoreLib.BuildMgr import BuildMgr


class AssassinSkills:
    def __init__(self, build: BuildMgr) -> None:
        self.build: BuildMgr = build
        self.NoAttribute: NoAttributeClass = NoAttributeClass(build)
        self.DaggerMastery: DaggerMasteryClass = DaggerMasteryClass(build)
        self.DeadlyArts: DeadlyArtsClass = DeadlyArtsClass(build)
        self.ShadowArts: ShadowArtsClass = ShadowArtsClass(build)
        self.CriticalStrikes: CriticalStrikesClass = CriticalStrikesClass(build)

