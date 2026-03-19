from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from Py4GWCoreLib.BuildMgr import BuildMgr

class AirMagic:
    def __init__(self, build: BuildMgr) -> None:
        self.build: BuildMgr = build

