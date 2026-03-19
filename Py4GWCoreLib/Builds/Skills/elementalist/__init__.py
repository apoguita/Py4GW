from __future__ import annotations

from typing import TYPE_CHECKING

from .NoAttribute import NoAttribute as NoAttributeClass
from .AirMagic import AirMagic as AirMagicClass
from .EarthMagic import EarthMagic as EarthMagicClass
from .FireMagic import FireMagic as FireMagicClass
from .WaterMagic import WaterMagic as WaterMagicClass
from .EnergyStorage import EnergyStorage as EnergyStorageClass

if TYPE_CHECKING:
    from Py4GWCoreLib.BuildMgr import BuildMgr


class ElementalistSkills:
    def __init__(self, build: BuildMgr) -> None:
        self.build: BuildMgr = build
        self.NoAttribute: NoAttributeClass = NoAttributeClass(build)
        self.AirMagic: AirMagicClass = AirMagicClass(build)
        self.EarthMagic: EarthMagicClass = EarthMagicClass(build)
        self.FireMagic: FireMagicClass = FireMagicClass(build)
        self.WaterMagic: WaterMagicClass = WaterMagicClass(build)
        self.EnergyStorage: EnergyStorageClass = EnergyStorageClass(build)

