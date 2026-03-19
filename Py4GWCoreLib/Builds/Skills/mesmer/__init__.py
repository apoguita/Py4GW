from __future__ import annotations

from typing import TYPE_CHECKING

from .NoAttribute import NoAttribute as NoAttributeClass
from .FastCasting import FastCasting as FastCastingClass
from .IllusionMagic import IllusionMagic as IllusionMagicClass
from .DominationMagic import DominationMagic as DominationMagicClass
from .InspirationMagic import InspirationMagic as InspirationMagicClass

if TYPE_CHECKING:
    from Py4GWCoreLib.BuildMgr import BuildMgr


class MesmerSkills:
    def __init__(self, build: BuildMgr) -> None:
        self.build: BuildMgr = build
        self.NoAttribute: NoAttributeClass = NoAttributeClass(build)
        self.FastCasting: FastCastingClass = FastCastingClass(build)
        self.IllusionMagic: IllusionMagicClass = IllusionMagicClass(build)
        self.DominationMagic: DominationMagicClass = DominationMagicClass(build)
        self.InspirationMagic: InspirationMagicClass = InspirationMagicClass(build)

