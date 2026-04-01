from __future__ import annotations

from typing import TYPE_CHECKING

from .NoAttribute import NoAttribute as NoAttributeClass
from .PvE import PvE as PvEClass

if TYPE_CHECKING:
    from Py4GWCoreLib.BuildMgr import BuildMgr


class AnySkills:
    def __init__(self, build: BuildMgr) -> None:
        self.build: BuildMgr = build
        self.NoAttribute: NoAttributeClass = NoAttributeClass(build)
        self.PvE: PvEClass = PvEClass(build)

