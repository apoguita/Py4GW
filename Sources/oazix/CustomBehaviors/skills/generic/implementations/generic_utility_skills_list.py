from Py4GWCoreLib import Agent, Player
from Py4GWCoreLib.enums_src.GameData_enums import Range
from Py4GWCoreLib.enums_src.Model_enums import SpiritModelID
from Py4GWCoreLib.py4gwcorelib_src.Utils import Utils
from Sources.oazix.CustomBehaviors.primitives.behavior_state import BehaviorState
from Sources.oazix.CustomBehaviors.primitives.bus.event_bus import EventBus
from Sources.oazix.CustomBehaviors.primitives.scores.score_per_agent_quantity_definition import ScorePerAgentQuantityDefinition
from Sources.oazix.CustomBehaviors.primitives.scores.score_per_health_gravity_definition import ScorePerHealthGravityDefinition
from Sources.oazix.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase
from Sources.oazix.CustomBehaviors.skills.generic.generic_resurrection_utility import GenericResurrectionUtility
from Sources.oazix.CustomBehaviors.skills.generic.keep_self_effect_up_utility import KeepSelfEffectUpUtility
from Sources.oazix.CustomBehaviors.skills.generic.minion_invocation_from_corpse_utility import MinionInvocationFromCorpseUtility
from Sources.oazix.CustomBehaviors.skills.generic.raw_aoe_attack_utility import RawAoeAttackUtility
from Sources.oazix.CustomBehaviors.skills.generic.raw_simple_attack_utility import RawSimpleAttackUtility
from Sources.oazix.CustomBehaviors.skills.generic.raw_simple_heal_utility import RawSimpleHealUtility
from Sources.oazix.CustomBehaviors.skills.generic.raw_simple_party_heal_utility import RawSimplePartyHealUtility
from Sources.oazix.CustomBehaviors.skills.generic.raw_spirit_utility import RawSpiritUtility
from Sources.oazix.CustomBehaviors.skills.generic.stub_utility import StubUtility
from Sources.oazix.CustomBehaviors.skills.pve.junundu_bite_utility import JunundoBiteUtility
from Sources.oazix.CustomBehaviors.specifics.underworld.dhuums_rest_utility import DhuumsRestUtility
from Sources.oazix.CustomBehaviors.specifics.underworld.ghostly_fury_utility import GhostlyFuryUtility
from Sources.oazix.CustomBehaviors.specifics.underworld.reversal_of_death_utility import ReversalOfDeathUtility
from Sources.oazix.CustomBehaviors.specifics.underworld.encase_skeletal_utility import EncaseSkeletalUtility
from Sources.oazix.CustomBehaviors.specifics.underworld.spiritual_healing_utility import SpiritualHealingUtility

class GenericUtilitySkillsList:
    '''
    This class is a factory for generic utility skills.
    It is not meant to be used directly.
    Thoses skills are automatically added to the utility skillbar if the build is set to complete the build with generic skills.
    '''
    def __init__(self):
        pass
    
    @staticmethod
    def get_generic_utility_skills_list(event_bus: EventBus, in_game_build: list[CustomSkill]) -> list[CustomSkillUtilityBase]:
        skills: list[CustomSkillUtilityBase] = []
        
        skills.append(GenericResurrectionUtility(event_bus=event_bus, skill=CustomSkill("Flesh_of_My_Flesh"), current_build=in_game_build))
        skills.append(GenericResurrectionUtility(event_bus=event_bus, skill=CustomSkill("Signet_of_Return"), current_build=in_game_build))
        skills.append(GenericResurrectionUtility(event_bus=event_bus, skill=CustomSkill("Resurrection"), current_build=in_game_build))
        skills.append(GenericResurrectionUtility(event_bus=event_bus, skill=CustomSkill("Resurrection_Chant"), current_build=in_game_build))
        skills.append(GenericResurrectionUtility(event_bus=event_bus, skill=CustomSkill("Resurrection_Signet"), current_build=in_game_build))
        skills.append(GenericResurrectionUtility(event_bus=event_bus, skill=CustomSkill("Rebirth"), current_build=in_game_build))

        skills.append(RawSpiritUtility(event_bus=event_bus, skill=CustomSkill("Vampirism"), current_build=in_game_build, score_definition=ScoreStaticDefinition(50), owned_spirit_model_id=SpiritModelID.VAMPIRISM))
        skills.append(RawSpiritUtility(event_bus=event_bus, skill=CustomSkill("Bloodsong"), current_build=in_game_build, score_definition=ScoreStaticDefinition(50), owned_spirit_model_id=SpiritModelID.BLOODSONG))
        skills.append(RawSpiritUtility(event_bus=event_bus, skill=CustomSkill("Shadowsong"), current_build=in_game_build, score_definition=ScoreStaticDefinition(50), owned_spirit_model_id=SpiritModelID.SHADOWSONG))
        skills.append(RawSpiritUtility(event_bus=event_bus, skill=CustomSkill("Pain"), current_build=in_game_build, score_definition=ScoreStaticDefinition(50), owned_spirit_model_id=SpiritModelID.PAIN))
        skills.append(RawSpiritUtility(event_bus=event_bus, skill=CustomSkill("Disenchantment"), current_build=in_game_build, score_definition=ScoreStaticDefinition(50), owned_spirit_model_id=SpiritModelID.DISENCHANTMENT))
        skills.append(RawSpiritUtility(event_bus=event_bus, skill=CustomSkill("Anguish"), current_build=in_game_build, score_definition=ScoreStaticDefinition(50), owned_spirit_model_id=SpiritModelID.ANGUISH))

        skills.append(RawSimplePartyHealUtility(event_bus=event_bus, skill=CustomSkill("Divine_Healing"), current_build=in_game_build, score_definition=ScorePerHealthGravityDefinition(1)))
        skills.append(RawSimplePartyHealUtility(event_bus=event_bus, skill=CustomSkill("Heavens_Delight"), current_build=in_game_build, score_definition=ScorePerHealthGravityDefinition(1)))
        skills.append(RawSimpleHealUtility(event_bus=event_bus, skill=CustomSkill("Patient_Spirit"), current_build=in_game_build, score_definition=ScorePerHealthGravityDefinition(1)))
        skills.append(RawSimpleHealUtility(event_bus=event_bus, skill=CustomSkill("Healing_Burst"), current_build=in_game_build, score_definition=ScorePerHealthGravityDefinition(1)))

        skills.append(KeepSelfEffectUpUtility(event_bus=event_bus, skill=CustomSkill("Air_of_Superiority"), current_build=in_game_build, score_definition=ScoreStaticDefinition(30), allowed_states=[BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO]))

        skills.append(KeepSelfEffectUpUtility(event_bus=event_bus, skill=CustomSkill("I_Am_the_Strongest"), current_build=in_game_build, score_definition=ScoreStaticDefinition(90), allowed_states=[BehaviorState.IN_AGGRO]))

        # naive JUNUNDU version
        skills.append(RawSimpleAttackUtility(event_bus=event_bus, skill=CustomSkill("Junundu_Strike"), current_build=in_game_build, score_definition=ScoreStaticDefinition(65)))
        skills.append(KeepSelfEffectUpUtility(event_bus=event_bus, skill=CustomSkill("Junundu_Tunnel"), current_build=in_game_build, score_definition=ScoreStaticDefinition(67), allowed_states=[BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO, BehaviorState.FAR_FROM_AGGRO]))

        skills.append(RawAoeAttackUtility(event_bus=event_bus, skill=CustomSkill("Blinding_Breath"), current_build=in_game_build, score_definition=ScorePerAgentQuantityDefinition(lambda enemy_qte: 70 if enemy_qte >= 2 else 69)))
        skills.append(RawSimpleAttackUtility(event_bus=event_bus, skill=CustomSkill("Burning_Breath"), current_build=in_game_build, score_definition=ScoreStaticDefinition(70), custom_agent_targeting_predicate=lambda agent_id: Utils.Distance(Player.GetXY(), Agent.GetXY(agent_id)) > Range.Nearby.value))
        skills.append(RawAoeAttackUtility(event_bus=event_bus, skill=CustomSkill("Choking_Breath"), current_build=in_game_build, score_definition=ScorePerAgentQuantityDefinition(lambda enemy_qte: 70 if enemy_qte >= 2 else 69), custom_agent_targeting_predicate=lambda agent_id: Agent.IsCasting(agent_id)))

        skills.append(StubUtility(event_bus=event_bus, skill=CustomSkill("Leave_Junundu"), current_build=in_game_build))
        skills.append(StubUtility(event_bus=event_bus, skill=CustomSkill("Unknown_Junundu_Ability"), current_build=in_game_build))
        skills.append(RawAoeAttackUtility(event_bus=event_bus, skill=CustomSkill("Junundu_Siege"), current_build=in_game_build, score_definition=ScorePerAgentQuantityDefinition(lambda enemy_qte: 80 if enemy_qte >= 2 else 79), custom_agent_targeting_predicate=lambda agent_id: Utils.Distance(Player.GetXY(), Agent.GetXY(agent_id)) > Range.Nearby.value))

        # Dhuum phase
        skills.append(SpiritualHealingUtility(event_bus=event_bus, current_build=in_game_build))
        skills.append(ReversalOfDeathUtility(event_bus=event_bus, current_build=in_game_build))
        skills.append(DhuumsRestUtility(event_bus=event_bus, current_build=in_game_build))
        skills.append(GhostlyFuryUtility(event_bus=event_bus, current_build=in_game_build))
        skills.append(EncaseSkeletalUtility(event_bus=event_bus, current_build=in_game_build))

        return skills
