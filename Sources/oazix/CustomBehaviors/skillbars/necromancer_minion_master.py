from typing import override

from Sources.oazix.CustomBehaviors.primitives.scores.score_per_agent_quantity_definition import ScorePerAgentQuantityDefinition
from Sources.oazix.CustomBehaviors.primitives.scores.score_per_health_gravity_definition import ScorePerHealthGravityDefinition
from Sources.oazix.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Sources.oazix.CustomBehaviors.primitives.skillbars.custom_behavior_base_utility import CustomBehaviorBaseUtility
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase
from Sources.oazix.CustomBehaviors.skills.common.breath_of_the_great_dwarf_utility import BreathOfTheGreatDwarfUtility
from Sources.oazix.CustomBehaviors.skills.common.by_urals_hammer_utility import ByUralsHammerUtility
from Sources.oazix.CustomBehaviors.skills.common.ebon_battle_standard_of_honor_utility import EbonBattleStandardOfHonorUtility
from Sources.oazix.CustomBehaviors.skills.common.ebon_battle_standard_of_wisdom_utility import EbonBattleStandardOfWisdom
from Sources.oazix.CustomBehaviors.skills.common.ebon_vanguard_assassin_support_utility import EbonVanguardAssassinSupportUtility
from Sources.oazix.CustomBehaviors.skills.common.great_dwarf_weapon_utility import GreatDwarfWeaponUtility
from Sources.oazix.CustomBehaviors.skills.common.i_am_unstoppable_utility import IAmUnstoppableUtility
from Sources.oazix.CustomBehaviors.skills.generic.generic_resurrection_utility import GenericResurrectionUtility
from Sources.oazix.CustomBehaviors.skills.generic.minion_invocation_from_corpse_utility import MinionInvocationFromCorpseUtility
from Sources.oazix.CustomBehaviors.skills.necromancer.blood_bond_utility import BloodBondUtility
from Sources.oazix.CustomBehaviors.skills.necromancer.blood_is_power_utility import BloodIsPowerUtility
from Sources.oazix.CustomBehaviors.skills.necromancer.blood_of_the_master import BloodOfTheMasterUtility
from Sources.oazix.CustomBehaviors.skills.necromancer.signet_of_lost_souls_utility import SignetOfLostSoulsUtility
from Sources.oazix.CustomBehaviors.skills.paragon.fall_back_utility import FallBackUtility
from Sources.oazix.CustomBehaviors.skills.ritualist.mend_body_and_soul_utility import MendBodyAndSoulUtility
from Sources.oazix.CustomBehaviors.skills.ritualist.life_utility import LifeUtility
from Sources.oazix.CustomBehaviors.skills.ritualist.protective_was_kaolai_utility import ProtectiveWasKaolaiUtility
from Sources.oazix.CustomBehaviors.skills.ritualist.soothing_memories_utility import SoothingMemoriesUtility
from Sources.oazix.CustomBehaviors.skills.ritualist.spirit_light_utility import SpiritLightUtility
from Sources.oazix.CustomBehaviors.skills.ritualist.spirit_transfer_utility import SpiritTransferUtility


class NecromancerMinionMaster_UtilitySkillBar(CustomBehaviorBaseUtility):

    def __init__(self):
        super().__init__()
        in_game_build = list(self.skillbar_management.get_in_game_build().values())

        # core skills
        self.animate_shambling_horror_utility: CustomSkillUtilityBase = MinionInvocationFromCorpseUtility(event_bus=self.event_bus, skill=CustomSkill("Animate_Shambling_Horror"), current_build=in_game_build, score_definition=ScoreStaticDefinition(62))
        self.animate_bone_fiend_utility: CustomSkillUtilityBase = MinionInvocationFromCorpseUtility(event_bus=self.event_bus, skill=CustomSkill("Animate_Bone_Fiend"), current_build=in_game_build, score_definition=ScoreStaticDefinition(61))
        self.animate_vampiric_horror_utility: CustomSkillUtilityBase = MinionInvocationFromCorpseUtility(event_bus=self.event_bus, skill=CustomSkill("Animate_Vampiric_Horror"), current_build=in_game_build, score_definition=ScoreStaticDefinition(60))
        self.blood_of_the_master_utility: CustomSkillUtilityBase = BloodOfTheMasterUtility(event_bus=self.event_bus, current_build=in_game_build, score_definition=ScoreStaticDefinition(33))

        # optional
        self.great_dwarf_weapon_utility: CustomSkillUtilityBase = GreatDwarfWeaponUtility(event_bus=self.event_bus, current_build=in_game_build, score_definition=ScoreStaticDefinition(30))
        self.breath_of_the_great_dwarf_utility: CustomSkillUtilityBase = BreathOfTheGreatDwarfUtility(event_bus=self.event_bus, current_build=in_game_build, score_definition=ScorePerHealthGravityDefinition(9))

        # common
        self.ebon_battle_standard_of_honor_utility: CustomSkillUtilityBase = EbonBattleStandardOfHonorUtility(event_bus=self.event_bus, score_definition=ScorePerAgentQuantityDefinition(lambda agent_qte: 45 if agent_qte >= 3 else 35 if agent_qte <= 2 else 25), current_build=in_game_build,  mana_required_to_cast=15)
        self.ebon_vanguard_assassin_support: CustomSkillUtilityBase = EbonVanguardAssassinSupportUtility(event_bus=self.event_bus, score_definition=ScoreStaticDefinition(71), current_build=in_game_build, mana_required_to_cast=15)
        self.ebon_battle_standard_of_wisdom: CustomSkillUtilityBase = EbonBattleStandardOfWisdom(event_bus=self.event_bus, score_definition= ScorePerAgentQuantityDefinition(lambda agent_qte: 80 if agent_qte >= 3 else 60 if agent_qte <= 2 else 40), current_build=in_game_build, mana_required_to_cast=18)
        self.i_am_unstopabble: CustomSkillUtilityBase = IAmUnstoppableUtility(event_bus=self.event_bus, current_build=in_game_build, score_definition=ScoreStaticDefinition(99))
        self.fall_back_utility: CustomSkillUtilityBase = FallBackUtility(event_bus=self.event_bus, current_build=in_game_build)
        self.signet_of_lost_souls_utility: CustomSkillUtilityBase = SignetOfLostSoulsUtility(event_bus=self.event_bus, current_build=in_game_build)
        self.by_urals_hammer_utility: CustomSkillUtilityBase = ByUralsHammerUtility(event_bus=self.event_bus, current_build=in_game_build)

    @property
    @override
    def custom_skills_in_behavior(self) -> list[CustomSkillUtilityBase]:
        return [
            self.animate_bone_fiend_utility,
            self.animate_vampiric_horror_utility,
            self.animate_shambling_horror_utility,
            self.blood_of_the_master_utility,
            
            self.great_dwarf_weapon_utility,
            self.breath_of_the_great_dwarf_utility,
            self.ebon_vanguard_assassin_support,
            self.ebon_battle_standard_of_wisdom,
            self.i_am_unstopabble,
            self.fall_back_utility,
            self.signet_of_lost_souls_utility,
            self.by_urals_hammer_utility,
        ]

    @property
    @override
    def skills_required_in_behavior(self) -> list[CustomSkill]:
        return [
            self.blood_of_the_master_utility.custom_skill,
        ]
