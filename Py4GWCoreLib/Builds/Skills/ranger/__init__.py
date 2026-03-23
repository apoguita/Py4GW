from __future__ import annotations

from typing import TYPE_CHECKING

from .NoAttribute import NoAttribute as NoAttributeClass
from .BeastMastery import BeastMastery as BeastMasteryClass
from .Expertise import Expertise as ExpertiseClass
from .WildernessSurvival import WildernessSurvival as WildernessSurvivalClass
from .Marksmanship import Marksmanship as MarksmanshipClass

if TYPE_CHECKING:
    from Py4GWCoreLib.BuildMgr import BuildMgr


class RangerSkills:
    def __init__(self, build: BuildMgr) -> None:
        self.build: BuildMgr = build
        self.NoAttribute: NoAttributeClass = NoAttributeClass(build)
        self.BeastMastery: BeastMasteryClass = BeastMasteryClass(build)
        self.Expertise: ExpertiseClass = ExpertiseClass(build)
        self.WildernessSurvival: WildernessSurvivalClass = WildernessSurvivalClass(build)
        self.Marksmanship: MarksmanshipClass = MarksmanshipClass(build)

