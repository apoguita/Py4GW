"""Mission dispatch table for playable scripts."""

from __future__ import annotations

from typing import Callable

from Py4GWCoreLib.py4gwcorelib_src.BehaviorTree import BehaviorTree

from Sources.RootTerm.config import MissionConfig
from Sources.RootTerm.missions.EOTN.CentralStorylines import against_the_charr
from Sources.RootTerm.missions.EOTN.CentralStorylines import curse_of_the_nornbear
from Sources.RootTerm.missions.EOTN.FinalEncounters import a_time_for_heroes
from Sources.RootTerm.missions.EOTN.TheShiverpeaks import a_gate_too_far
from Sources.RootTerm.missions.EOTN.TheShiverpeaks import blood_washes_blood
from Sources.RootTerm.missions.Nightfall.Istan import chahbek_village
from Sources.RootTerm.missions.Prophecies.Ascalon import fort_ranik
from Sources.RootTerm.missions.Prophecies.Ascalon import great_northern_wall
from Sources.RootTerm.missions.Prophecies.Ascalon import ruins_of_surmia

MissionBuilder = Callable[[MissionConfig], BehaviorTree]

DISPATCH: dict[int, MissionBuilder] = {
    936: great_northern_wall.build,
    937: fort_ranik.build,
    938: ruins_of_surmia.build,
    978: chahbek_village.build,
    1003: against_the_charr.build,
    1006: curse_of_the_nornbear.build,
    1007: blood_washes_blood.build,
    1008: a_gate_too_far.build,
    1010: a_time_for_heroes.build,
}
