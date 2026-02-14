"""
Configuration class for botting utility skills that can be injected.
Provides a configurable list of utility skills with enabled/disabled state.
"""
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Callable, Type

if TYPE_CHECKING:
    from Sources.oazix.CustomBehaviors.primitives.bus.event_bus import EventBus
    from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
    from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase


@dataclass
class UtilitySkillEntry:
    """Represents a single utility skill with its enabled state."""
    name: str
    display_name: str
    enabled: bool = True
    factory: Callable[["EventBus", list["CustomSkill"]], "CustomSkillUtilityBase"] | None = None


class BottingManager:
    """
    Singleton configuration class for botting utility skills.
    Holds the list of available utility skills with their enabled/disabled state.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(BottingManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    # Section names for INI file
    SECTION_PACIFIST = "PacifistSkills"
    SECTION_AGGRESSIVE = "AggressiveSkills"
    SECTION_AUTOMOVER = "AutomoverSkills"

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True

        # Initialize the skill configurations
        self._pacifist_skills: list[UtilitySkillEntry] = []
        self._aggressive_skills: list[UtilitySkillEntry] = []
        self._automover_skills: list[UtilitySkillEntry] = []

        self._setup_default_skills()
        self._load_from_persistence()

    def _setup_default_skills(self):
        """Setup the default skill configurations."""
        # Lazy imports to avoid circular dependencies
        from Sources.oazix.CustomBehaviors.skills.botting.move_if_stuck import MoveIfStuckUtility
        from Sources.oazix.CustomBehaviors.skills.botting.move_to_distant_chest_if_path_exists import MoveToDistantChestIfPathExistsUtility
        from Sources.oazix.CustomBehaviors.skills.botting.move_to_enemy_if_close_enough import MoveToEnemyIfCloseEnoughUtility
        from Sources.oazix.CustomBehaviors.skills.botting.move_to_party_member_if_dead import MoveToPartyMemberIfDeadUtility
        from Sources.oazix.CustomBehaviors.skills.botting.move_to_party_member_if_in_aggro import MoveToPartyMemberIfInAggroUtility
        from Sources.oazix.CustomBehaviors.skills.botting.wait_if_in_aggro import WaitIfInAggroUtility
        from Sources.oazix.CustomBehaviors.skills.botting.wait_if_lock_taken import WaitIfLockTakenUtility
        from Sources.oazix.CustomBehaviors.skills.botting.wait_if_party_member_mana_too_low import WaitIfPartyMemberManaTooLowUtility
        from Sources.oazix.CustomBehaviors.skills.botting.wait_if_party_member_needs_to_loot import WaitIfPartyMemberNeedsToLootUtility
        from Sources.oazix.CustomBehaviors.skills.botting.wait_if_party_member_too_far import WaitIfPartyMemberTooFarUtility

        # Pacifist skills (minimal set)
        self._pacifist_skills = [
            UtilitySkillEntry("WaitIfPartyMemberTooFarUtility", "Wait If Party Member Too Far", True, 
                              lambda eb, build: WaitIfPartyMemberTooFarUtility(eb, build)),
        ]

        # Aggressive skills (full set)
        self._aggressive_skills = [
            UtilitySkillEntry("MoveToPartyMemberIfInAggroUtility", "Move To Party Member If In Aggro", True,
                              lambda eb, build: MoveToPartyMemberIfInAggroUtility(eb, build)),
            UtilitySkillEntry("MoveToEnemyIfCloseEnoughUtility", "Move To Enemy If Close Enough", True,
                              lambda eb, build: MoveToEnemyIfCloseEnoughUtility(eb, build)),
            UtilitySkillEntry("MoveToPartyMemberIfDeadUtility", "Move To Party Member If Dead", True,
                              lambda eb, build: MoveToPartyMemberIfDeadUtility(eb, build)),
            UtilitySkillEntry("WaitIfPartyMemberManaTooLowUtility", "Wait If Party Member Mana Too Low", True,
                              lambda eb, build: WaitIfPartyMemberManaTooLowUtility(eb, build)),
            UtilitySkillEntry("WaitIfPartyMemberTooFarUtility", "Wait If Party Member Too Far", True,
                              lambda eb, build: WaitIfPartyMemberTooFarUtility(eb, build)),
            UtilitySkillEntry("WaitIfPartyMemberNeedsToLootUtility", "Wait If Party Member Needs To Loot", True,
                              lambda eb, build: WaitIfPartyMemberNeedsToLootUtility(eb, build)),
            UtilitySkillEntry("WaitIfInAggroUtility", "Wait If In Aggro", True,
                              lambda eb, build: WaitIfInAggroUtility(eb, build)),
            UtilitySkillEntry("WaitIfLockTakenUtility", "Wait If Lock Taken", True,
                              lambda eb, build: WaitIfLockTakenUtility(eb, build)),
            UtilitySkillEntry("MoveToDistantChestIfPathExistsUtility", "Move To Distant Chest If Path Exists", False,
                              lambda eb, build: MoveToDistantChestIfPathExistsUtility(eb, build)),
        ]

        # Automover skills (same as aggressive but can be configured separately)
        self._automover_skills = [
            UtilitySkillEntry("MoveToPartyMemberIfInAggroUtility", "Move To Party Member If In Aggro", True,
                              lambda eb, build: MoveToPartyMemberIfInAggroUtility(eb, build)),
            UtilitySkillEntry("MoveToEnemyIfCloseEnoughUtility", "Move To Enemy If Close Enough", True,
                              lambda eb, build: MoveToEnemyIfCloseEnoughUtility(eb, build)),
            UtilitySkillEntry("MoveToPartyMemberIfDeadUtility", "Move To Party Member If Dead", True,
                              lambda eb, build: MoveToPartyMemberIfDeadUtility(eb, build)),
            UtilitySkillEntry("WaitIfPartyMemberManaTooLowUtility", "Wait If Party Member Mana Too Low", True,
                              lambda eb, build: WaitIfPartyMemberManaTooLowUtility(eb, build)),
            UtilitySkillEntry("WaitIfPartyMemberTooFarUtility", "Wait If Party Member Too Far", True,
                              lambda eb, build: WaitIfPartyMemberTooFarUtility(eb, build)),
            UtilitySkillEntry("WaitIfPartyMemberNeedsToLootUtility", "Wait If Party Member Needs To Loot", True,
                              lambda eb, build: WaitIfPartyMemberNeedsToLootUtility(eb, build)),
            UtilitySkillEntry("WaitIfInAggroUtility", "Wait If In Aggro", True,
                              lambda eb, build: WaitIfInAggroUtility(eb, build)),
            UtilitySkillEntry("WaitIfLockTakenUtility", "Wait If Lock Taken", True,
                              lambda eb, build: WaitIfLockTakenUtility(eb, build)),
        ]

    # Properties to access skill lists
    @property
    def pacifist_skills(self) -> list[UtilitySkillEntry]:
        return self._pacifist_skills

    @property
    def aggressive_skills(self) -> list[UtilitySkillEntry]:
        return self._aggressive_skills

    @property
    def automover_skills(self) -> list[UtilitySkillEntry]:
        return self._automover_skills

    def get_enabled_pacifist_skills(self) -> list[UtilitySkillEntry]:
        """Return only enabled pacifist skills."""
        return [s for s in self._pacifist_skills if s.enabled]

    def get_enabled_aggressive_skills(self) -> list[UtilitySkillEntry]:
        """Return only enabled aggressive skills."""
        return [s for s in self._aggressive_skills if s.enabled]

    def get_enabled_automover_skills(self) -> list[UtilitySkillEntry]:
        """Return only enabled automover skills."""
        return [s for s in self._automover_skills if s.enabled]

    def inject_enabled_skills(self, skill_list: list[UtilitySkillEntry], instance) -> None:
        """
        Inject all enabled skills from a list into the custom behavior instance.

        Args:
            skill_list: List of UtilitySkillEntry to check and inject
            instance: The CustomBehaviorBaseUtility instance to inject skills into
        """
        for entry in skill_list:
            if entry.enabled and entry.factory is not None:
                skill = entry.factory(instance.event_bus, instance.in_game_build)
                instance.inject_additionnal_utility_skills(skill)

    # Persistence methods

    def _load_from_persistence(self) -> None:
        """Load skill enabled states from the INI file."""
        from Sources.oazix.CustomBehaviors.PersistenceLocator import PersistenceLocator
        botting = PersistenceLocator().botting

        # Load pacifist skills
        for skill in self._pacifist_skills:
            value = botting.read(self.SECTION_PACIFIST, skill.name)
            if value is not None:
                skill.enabled = value.lower() == "true"

        # Load aggressive skills
        for skill in self._aggressive_skills:
            value = botting.read(self.SECTION_AGGRESSIVE, skill.name)
            if value is not None:
                skill.enabled = value.lower() == "true"

        # Load automover skills
        for skill in self._automover_skills:
            value = botting.read(self.SECTION_AUTOMOVER, skill.name)
            if value is not None:
                skill.enabled = value.lower() == "true"

    def save(self) -> None:
        """Save all skill enabled states to the INI file (global)."""
        from Sources.oazix.CustomBehaviors.PersistenceLocator import PersistenceLocator
        botting = PersistenceLocator().botting

        # Save pacifist skills
        for skill in self._pacifist_skills:
            botting.write(self.SECTION_PACIFIST, skill.name, str(skill.enabled).lower())

        # Save aggressive skills
        for skill in self._aggressive_skills:
            botting.write(self.SECTION_AGGRESSIVE, skill.name, str(skill.enabled).lower())

        # Save automover skills
        for skill in self._automover_skills:
            botting.write(self.SECTION_AUTOMOVER, skill.name, str(skill.enabled).lower())

    def delete_configuration(self) -> None:
        """Delete all saved configuration from the INI file and reset to defaults."""
        from Sources.oazix.CustomBehaviors.PersistenceLocator import PersistenceLocator
        botting = PersistenceLocator().botting

        # Delete all sections
        botting.delete_section(self.SECTION_PACIFIST)
        botting.delete_section(self.SECTION_AGGRESSIVE)
        botting.delete_section(self.SECTION_AUTOMOVER)

        # Reset to defaults
        self._setup_default_skills()

