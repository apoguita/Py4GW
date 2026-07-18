"""Mission dispatch table for playable Phase-1 scripts."""

from __future__ import annotations

from typing import Callable

from Py4GWCoreLib import Botting

from Sources.incognito.config import MissionConfig
from Sources.incognito.missions import chahbek_village
from Sources.incognito.missions import fort_ranik
from Sources.incognito.missions import great_northern_wall

MissionBuilder = Callable[[Botting, MissionConfig], None]

DISPATCH: dict[int, MissionBuilder] = {
    936: great_northern_wall.build,
    937: fort_ranik.build,
    978: chahbek_village.build,
}
