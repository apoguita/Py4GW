from typing import override

from Sources.oazix.CustomBehaviors.primitives.scores.score_per_agent_quantity_definition import ScorePerAgentQuantityDefinition
from Sources.oazix.CustomBehaviors.primitives.scores.score_per_health_gravity_definition import ScorePerHealthGravityDefinition
from Sources.oazix.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Sources.oazix.CustomBehaviors.primitives.skillbars.custom_behavior_base_utility import CustomBehaviorBaseUtility
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase
from Sources.oazix.CustomBehaviors.skills.common.breath_of_the_great_dwarf_utility import BreathOfTheGreatDwarfUtility
from Sources.oazix.CustomBehaviors.skills.common.ebon_battle_standard_of_wisdom_utility import EbonBattleStandardOfWisdom
from Sources.oazix.CustomBehaviors.skills.common.ebon_vanguard_assassin_support_utility import EbonVanguardAssassinSupportUtility
from Sources.oazix.CustomBehaviors.skills.common.great_dwarf_weapon_utility import GreatDwarfWeaponUtility
from Sources.oazix.CustomBehaviors.skills.necromancer.weaken_armor_utility import WeakenArmorUtility
from Sources.oazix.CustomBehaviors.skills.ritualist.recuperation_utility import RecuperationUtility
from Sources.oazix.CustomBehaviors.skills.ritualist.life_utility import LifeUtility
from Sources.oazix.CustomBehaviors.skills.ritualist.mend_body_and_soul_utility import MendBodyAndSoulUtility
from Sources.oazix.CustomBehaviors.skills.ritualist.mending_grip_utility import MendingGripUtility
from Sources.oazix.CustomBehaviors.skills.ritualist.protective_was_kaolai_utility import ProtectiveWasKaolaiUtility
from Sources.oazix.CustomBehaviors.skills.ritualist.spirit_light_utility import SpiritLightUtility
from Sources.oazix.CustomBehaviors.skills.ritualist.spirit_transfer_utility import SpiritTransferUtility
from Sources.oazix.CustomBehaviors.skills.ritualist.xinraes_weapon_utility import XinraesWeaponUtility
from Sources.oazix.CustomBehaviors.skills.common.you_are_all_weaklings_utility import YouAreAllWeaklingsUtility


class NecromancerXinraeRestoration_UtilitySkillBar(CustomBehaviorBaseUtility):

    def __init__(self):
        super().__init__()
        in_game_build = list(self.skillbar_management.get_in_game_build().values())

        # core skills
        self.xinraes_weapon_utility: CustomSkillUtilityBase = XinraesWeaponUtility(event_bus=self.event_bus, current_build=in_game_build)
        self.mend_body_and_soul_utility: CustomSkillUtilityBase = MendBodyAndSoulUtility(event_bus=self.event_bus, current_build=in_game_build, score_definition=ScorePerHealthGravityDefinition(7))
        self.spirit_light_utility: CustomSkillUtilityBase = SpiritLightUtility(event_bus=self.event_bus, current_build=in_game_build, score_definition=ScorePerHealthGravityDefinition(8))
        self.protective_was_kaolai_utility: CustomSkillUtilityBase = ProtectiveWasKaolaiUtility(event_bus=self.event_bus, current_build=in_game_build, score_definition=ScorePerHealthGravityDefinition(7))
        self.recuperation_utility: CustomSkillUtilityBase = RecuperationUtility(event_bus=self.event_bus, current_build=in_game_build, score_definition=ScoreStaticDefinition(40))

        # optional
        self.life_utility: CustomSkillUtilityBase = LifeUtility(event_bus=self.event_bus, current_build=in_game_build, score_definition=ScorePerHealthGravityDefinition(5))
        self.spirit_transfer_utility: CustomSkillUtilityBase = SpiritTransferUtility(event_bus=self.event_bus, current_build=in_game_build, score_definition=ScorePerHealthGravityDefinition(9))
        self.great_dwarf_weapon_utility: CustomSkillUtilityBase = GreatDwarfWeaponUtility(event_bus=self.event_bus, current_build=in_game_build, score_definition=ScoreStaticDefinition(30))
        self.breath_of_the_great_dwarf_utility: CustomSkillUtilityBase = BreathOfTheGreatDwarfUtility(event_bus=self.event_bus, current_build=in_game_build, score_definition=ScorePerHealthGravityDefinition(9))
        self.mending_grip_utility: CustomSkillUtilityBase = MendingGripUtility(event_bus=self.event_bus, current_build=in_game_build)
        self.weaken_armor_utility: CustomSkillUtilityBase = WeakenArmorUtility(event_bus=self.event_bus, current_build=in_game_build)

        # common
        self.ebon_vanguard_assassin_support: CustomSkillUtilityBase = EbonVanguardAssassinSupportUtility(event_bus=self.event_bus, score_definition=ScoreStaticDefinition(71), current_build=in_game_build, mana_required_to_cast=15)
        self.ebon_battle_standard_of_wisdom: CustomSkillUtilityBase = EbonBattleStandardOfWisdom(event_bus=self.event_bus, score_definition=ScorePerAgentQuantityDefinition(lambda agent_qte: 80 if agent_qte >= 3 else 60 if agent_qte <= 2 else 40), current_build=in_game_build, mana_required_to_cast=18)
        self.you_are_all_weaklings_utility: CustomSkillUtilityBase = YouAreAllWeaklingsUtility(event_bus=self.event_bus, current_build=in_game_build)

    @property
    @override
    def custom_skills_in_behavior(self) -> list[CustomSkillUtilityBase]:
        return [
            self.xinraes_weapon_utility,
            self.mend_body_and_soul_utility,
            self.spirit_light_utility,
            self.protective_was_kaolai_utility,
            self.recuperation_utility,
            self.life_utility,
            self.spirit_transfer_utility,
            self.great_dwarf_weapon_utility,
            self.breath_of_the_great_dwarf_utility,
            self.mending_grip_utility,
            self.weaken_armor_utility,
            self.ebon_vanguard_assassin_support,
            self.ebon_battle_standard_of_wisdom,
            self.you_are_all_weaklings_utility,
        ]

    @property
    @override
    def skills_required_in_behavior(self) -> list[CustomSkill]:
        return [
            self.xinraes_weapon_utility.custom_skill,
        ]
