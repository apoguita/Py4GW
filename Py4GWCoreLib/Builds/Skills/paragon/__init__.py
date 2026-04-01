from __future__ import annotations

from typing import TYPE_CHECKING

from .NoAttribute import NoAttribute as NoAttributeClass
from .SpearMastery import SpearMastery as SpearMasteryClass
from .Command import Command as CommandClass
from .Motivation import Motivation as MotivationClass
from .Leadership import Leadership as LeadershipClass

if TYPE_CHECKING:
    from Py4GWCoreLib.BuildMgr import BuildMgr


class ParagonSkills:
    def __init__(self, build: BuildMgr) -> None:
        self.build: BuildMgr = build
        self.NoAttribute: NoAttributeClass = NoAttributeClass(build)
        self.SpearMastery: SpearMasteryClass = SpearMasteryClass(build)
        self.Command: CommandClass = CommandClass(build)
        self.Motivation: MotivationClass = MotivationClass(build)
        self.Leadership: LeadershipClass = LeadershipClass(build)

