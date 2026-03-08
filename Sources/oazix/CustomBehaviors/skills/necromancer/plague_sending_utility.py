from typing import List, Any, Generator, Callable, override

from Py4GWCoreLib import GLOBAL_CACHE, Routines, Range, Agent, Player
from Sources.Nikon_Scripts.BotUtilities import GameAreas
from Sources.oazix.CustomBehaviors.primitives import constants
from Sources.oazix.CustomBehaviors.primitives.behavior_state import BehaviorState
from Sources.oazix.CustomBehaviors.primitives.bus.event_bus import EventBus
from Sources.oazix.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Sources.oazix.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Sources.oazix.CustomBehaviors.primitives.helpers.targeting_order import TargetingOrder
from Sources.oazix.CustomBehaviors.primitives.scores.score_per_agent_quantity_definition import ScorePerAgentQuantityDefinition
from Sources.oazix.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase

class PlagueSendingUtility(CustomSkillUtilityBase):
    def __init__(self,
    event_bus: EventBus,
    current_build: list[CustomSkill],
    skill: CustomSkill = CustomSkill("Plague_Sending"),
    score_definition: ScorePerAgentQuantityDefinition = ScorePerAgentQuantityDefinition(lambda enemy_qte: 48 if enemy_qte >= 3 else 32 if enemy_qte <= 2 else 24),
    mana_required_to_cast: int = 12,
    allowed_states: list[BehaviorState] = [BehaviorState.IN_AGGRO]
    ) -> None:

        super().__init__(
            event_bus=event_bus,
            skill=skill,
            in_game_build=current_build,
            score_definition=score_definition,
            mana_required_to_cast=mana_required_to_cast,
            allowed_states=allowed_states)
        
        self.score_definition: ScorePerAgentQuantityDefinition = score_definition

    def _get_cultists_fervor_best_targets(self) -> list[custom_behavior_helpers.SortableAgentData]:
        return custom_behavior_helpers.Targets.get_all_possible_enemies_ordered_by_priority_raw(
            within_range=Range.Spellcast,
            condition=lambda agent_id: not Agent.IsBleeding(agent_id) and not Agent.IsSpirit(agent_id),
            sort_key=(TargetingOrder.AGENT_QUANTITY_WITHIN_RANGE_DESC, TargetingOrder.HP_ASC),
            range_to_count_enemies=GameAreas.Adjacent)

    def _get_targets(self) -> list[custom_behavior_helpers.SortableAgentData]:
        return custom_behavior_helpers.Targets.get_all_possible_enemies_ordered_by_priority_raw(
            within_range=Range.Spellcast,
            condition=lambda agent_id: not Agent.IsSpirit(agent_id),
            sort_key=(TargetingOrder.AGENT_QUANTITY_WITHIN_RANGE_DESC, TargetingOrder.HP_ASC),
            range_to_count_enemies=GameAreas.Adjacent)

    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:

        if not custom_behavior_helpers.Resources.player_can_sacrifice_health(percentage_to_sacrifice=10):
            print("Cannot Sacrifice Health")
            return None



        # do we have something worth sending?
        scoreMult = 0.25
        if Agent.IsCrippled(Player.GetAgentID()) or Agent.IsPoisoned(Player.GetAgentID()):
            scoreMult = 1.0
        # send deep wound with more priority - should also check for dazed will look at how combat.py does later.
        # todo 1. not sure if should be higher or lower priority than finish him,
        # todo 2. will need to check for urgoz so we dont spam
        if Agent.IsDeepWounded(Player.GetAgentID()):
            scoreMult += 1.25

        if Routines.Checks.Effects.HasBuff(Player.GetAgentID(), GLOBAL_CACHE.Skill.GetID("Cultists_Fervor")):
            # find someone not bleeding to send to, Cultists_Fervor will give us bleeding.
            scoreMult += 0.5
            targets = self._get_cultists_fervor_best_targets()
            if len(targets) != 0:
                if constants.DEBUG: print("Have a fervor best target")
                return self.score_definition.get_score(targets[0].enemy_quantity_within_range) * scoreMult


        # Cultists_Fervor doesnt have anyone to cause bleeding to, are we at least conditioned already and have a reason to send?

        #if nothing just be done
        if not Agent.IsConditioned(Player.GetAgentID()):
            if constants.DEBUG: print("No Conditions to send")
            return None


        targets = self._get_targets()
        if len(targets) == 0: return None
        return self.score_definition.get_score(targets[0].enemy_quantity_within_range) * scoreMult

    @override
    def _execute(self, state: BehaviorState) -> Generator[Any, None, BehaviorResult]:
        if constants.DEBUG: print("Do Plague Sending")

        if Routines.Checks.Effects.HasBuff(Player.GetAgentID(), GLOBAL_CACHE.Skill.GetID("Cultists_Fervor")):
            enemies = self._get_cultists_fervor_best_targets()
            if len(enemies) != 0:
                target = enemies[0]
                result = yield from custom_behavior_helpers.Actions.cast_skill_to_target(self.custom_skill, target_agent_id=target.agent_id)
                return result
        # intentional fallthrough and else case

        enemies = self._get_targets()
        if len(enemies) == 0: return BehaviorResult.ACTION_SKIPPED
        target = enemies[0]
        result = yield from custom_behavior_helpers.Actions.cast_skill_to_target(self.custom_skill, target_agent_id=target.agent_id)
        return result