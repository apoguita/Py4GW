from typing import Any, Generator, override

from Py4GWCoreLib import GLOBAL_CACHE, Routines, Player, Effects
from Py4GWCoreLib.enums import ModelID
from Sources.oazix.CustomBehaviors.primitives.behavior_state import BehaviorState
from Sources.oazix.CustomBehaviors.primitives.bus.event_bus import EventBus
from Sources.oazix.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Sources.oazix.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Sources.oazix.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase

_ALCOHOL_TARGET_LEVEL = 3

# Level 3 alcohol: each drink gives +3 or more — one drink reaches target level
_ALCOHOL_L3_MODEL_IDS = [
    ModelID.Aged_Dwarven_Ale.value,
    ModelID.Aged_Hunters_Ale.value,
    ModelID.Keg_Of_Aged_Hunters_Ale.value,
    ModelID.Bottle_Of_Grog.value,
    ModelID.Spiked_Eggnog.value,
    ModelID.Vial_Of_Absinthe.value,
    ModelID.Witchs_Brew.value,
]
# Level 1 alcohol: each drink gives +1 — needs multiple uses to reach target level
_ALCOHOL_L1_MODEL_IDS = [
    ModelID.Dwarven_Ale.value,
    ModelID.Hunters_Ale.value,
    ModelID.Bottle_Of_Rice_Wine.value,
    ModelID.Bottle_Of_Vabbian_Wine.value,
    ModelID.Bottle_Of_Juniberry_Gin.value,
    ModelID.Shamrock_Ale.value,
    ModelID.Hard_Apple_Cider.value,
    ModelID.Eggnog.value,
]
# Combined list: L3 items preferred first for efficiency
_ALCOHOL_MODEL_IDS = _ALCOHOL_L3_MODEL_IDS + _ALCOHOL_L1_MODEL_IDS


class _AlcoholSelfBuffBase(CustomSkillUtilityBase):
    """Base for self-buff skills that require alcohol level 3 to be effective."""

    def _get_alcohol_level(self) -> int:
        try:
            return max(0, min(5, int(Effects.GetAlcoholLevel())))
        except Exception:
            return 0

    def _drink_alcohol(self) -> bool:
        for model_id in _ALCOHOL_MODEL_IDS:
            if GLOBAL_CACHE.Inventory.GetModelCount(model_id) > 0:
                item_id = GLOBAL_CACHE.Item.GetItemIdFromModelID(model_id)
                if item_id:
                    GLOBAL_CACHE.Inventory.UseItem(item_id)
                    return True
        return False

    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:
        has_buff = Routines.Checks.Effects.HasBuff(Player.GetAgentID(), self.custom_skill.skill_id)
        if not has_buff:
            return self.score_definition.get_score()
        return None

    @override
    def _execute(self, state: BehaviorState) -> Generator[Any, None, BehaviorResult]:
        if self._get_alcohol_level() < _ALCOHOL_TARGET_LEVEL:
            self._drink_alcohol()
            yield
            return BehaviorResult.ACTION_SKIPPED
        result = yield from custom_behavior_helpers.Actions.cast_skill(self.custom_skill)
        return result


class DrunkenMasterUtility(_AlcoholSelfBuffBase):
    def __init__(
        self,
        event_bus: EventBus,
        current_build: list[CustomSkill],
        score_definition: ScoreStaticDefinition = ScoreStaticDefinition(30),
        mana_required_to_cast: int = 5,
        allowed_states: list[BehaviorState] = [BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO],
    ) -> None:
        super().__init__(
            event_bus=event_bus,
            skill=CustomSkill("Drunken_Master"),
            in_game_build=current_build,
            score_definition=score_definition,
            mana_required_to_cast=mana_required_to_cast,
            allowed_states=allowed_states,
        )


class DwarvenStabilityUtility(_AlcoholSelfBuffBase):
    def __init__(
        self,
        event_bus: EventBus,
        current_build: list[CustomSkill],
        score_definition: ScoreStaticDefinition = ScoreStaticDefinition(30),
        mana_required_to_cast: int = 5,
        allowed_states: list[BehaviorState] = [BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO],
    ) -> None:
        super().__init__(
            event_bus=event_bus,
            skill=CustomSkill("Dwarven_Stability"),
            in_game_build=current_build,
            score_definition=score_definition,
            mana_required_to_cast=mana_required_to_cast,
            allowed_states=allowed_states,
        )


class FeelNoPainUtility(_AlcoholSelfBuffBase):
    def __init__(
        self,
        event_bus: EventBus,
        current_build: list[CustomSkill],
        score_definition: ScoreStaticDefinition = ScoreStaticDefinition(30),
        mana_required_to_cast: int = 5,
        allowed_states: list[BehaviorState] = [BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO],
    ) -> None:
        super().__init__(
            event_bus=event_bus,
            skill=CustomSkill("Feel_No_Pain"),
            in_game_build=current_build,
            score_definition=score_definition,
            mana_required_to_cast=mana_required_to_cast,
            allowed_states=allowed_states,
        )
