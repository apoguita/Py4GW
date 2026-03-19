from __future__ import annotations

from typing import TYPE_CHECKING

from .NoAttribute import NoAttribute as NoAttributeClass
from .Communing import Communing as CommuningClass
from .RestorationMagic import RestorationMagic as RestorationMagicClass
from .ChannelingMagic import ChannelingMagic as ChannelingMagicClass
from .SpawningPower import SpawningPower as SpawningPowerClass

if TYPE_CHECKING:
    from Py4GWCoreLib.BuildMgr import BuildMgr


class RitualistSkills:
    def __init__(self, build: BuildMgr) -> None:
        self.build: BuildMgr = build
        self.NoAttribute: NoAttributeClass = NoAttributeClass(build)
        self.Communing: CommuningClass = CommuningClass(build)
        self.RestorationMagic: RestorationMagicClass = RestorationMagicClass(build)
        self.ChannelingMagic: ChannelingMagicClass = ChannelingMagicClass(build)
        self.SpawningPower: SpawningPowerClass = SpawningPowerClass(build)

