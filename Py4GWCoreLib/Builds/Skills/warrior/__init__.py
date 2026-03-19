from __future__ import annotations

from typing import TYPE_CHECKING

from .NoAttribute import NoAttribute as NoAttributeClass
from .Strength import Strength as StrengthClass
from .AxeMastery import AxeMastery as AxeMasteryClass
from .HammerMastery import HammerMastery as HammerMasteryClass
from .Swordsmanship import Swordsmanship as SwordsmanshipClass
from .Tactics import Tactics as TacticsClass

if TYPE_CHECKING:
    from Py4GWCoreLib.BuildMgr import BuildMgr


class WarriorSkills:
    def __init__(self, build: BuildMgr) -> None:
        self.build: BuildMgr = build
        self.NoAttribute: NoAttributeClass = NoAttributeClass(build)
        self.Strength: StrengthClass = StrengthClass(build)
        self.AxeMastery: AxeMasteryClass = AxeMasteryClass(build)
        self.HammerMastery: HammerMasteryClass = HammerMasteryClass(build)
        self.Swordsmanship: SwordsmanshipClass = SwordsmanshipClass(build)
        self.Tactics: TacticsClass = TacticsClass(build)

