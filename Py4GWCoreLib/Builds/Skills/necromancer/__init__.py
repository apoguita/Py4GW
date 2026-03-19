from __future__ import annotations

from typing import TYPE_CHECKING

from .NoAttribute import NoAttribute as NoAttributeClass
from .BloodMagic import BloodMagic as BloodMagicClass
from .DeathMagic import DeathMagic as DeathMagicClass
from .SoulReaping import SoulReaping as SoulReapingClass
from .Curses import Curses as CursesClass

if TYPE_CHECKING:
    from Py4GWCoreLib.BuildMgr import BuildMgr


class NecromancerSkills:
    def __init__(self, build: BuildMgr) -> None:
        self.build: BuildMgr = build
        self.NoAttribute: NoAttributeClass = NoAttributeClass(build)
        self.BloodMagic: BloodMagicClass = BloodMagicClass(build)
        self.DeathMagic: DeathMagicClass = DeathMagicClass(build)
        self.SoulReaping: SoulReapingClass = SoulReapingClass(build)
        self.Curses: CursesClass = CursesClass(build)

