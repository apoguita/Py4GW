from functools import wraps
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from Py4GWCoreLib.botting_src.helpers import BottingHelpers
    
from .decorators import _yield_step, _fsm_step
from typing import Any, Generator, TYPE_CHECKING, Tuple

#region SKILLS
class _Skills:
    def __init__(self, parent: "BottingHelpers"):
        self.parent = parent.parent
        self._config = parent._config
    
    @_yield_step(label="LoadSkillbar", counter_key="LOAD_SKILLBAR")
    def load_skillbar(self, skill_template: str) -> Generator[Any, Any, None]:
        from ...Routines import Routines
        return (yield from Routines.Yield.Skills.LoadSkillbar(skill_template, log=False))
    
    @_yield_step(label="LoadHeroSkillbar", counter_key="LOAD_HERO_SKILLBAR")
    def load_hero_skillbar(self, hero_index: int, skill_template: str) -> Generator[Any, Any, None]:
        from ...Routines import Routines
        return (yield from Routines.Yield.Skills.LoadHeroSkillbar(hero_index, skill_template, log=False))

    @_yield_step(label="CastSkillID", counter_key="CAST_SKILL_ID")
    def cast_skill_id(self, skill_id: int) -> Generator[Any, Any, bool]:
        from ...Routines import Routines
        return (yield from Routines.Yield.Skills.CastSkillID(skill_id))

    @_yield_step(label="CastSkillSlot", counter_key="CAST_SKILL_SLOT")
    def cast_skill_slot(self, slot: int) -> Generator[Any, Any, bool]:
        from ...Routines import Routines
        return (yield from Routines.Yield.Skills.CastSkillSlot(slot))
        