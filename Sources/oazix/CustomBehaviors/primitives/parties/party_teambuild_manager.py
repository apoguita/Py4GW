"""
Singleton manager for party team build configuration.
Stores skillbar templates in shared RAM memory for cross-process access.
Manages skillbar templates for up to 12 party members.
"""

from dataclasses import dataclass
from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE
from Py4GWCoreLib.enums_src.Multiboxing_enums import SharedCommandType
from Py4GWCoreLib.py4gwcorelib_src.Timer import ThrottledTimer
from Py4GWCoreLib.routines_src.Yield import Yield
from Py4GWCoreLib import Utils, Player
from Sources.oazix.CustomBehaviors.primitives import constants
from Sources.oazix.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Sources.oazix.CustomBehaviors.primitives.parties.pawned2.Pawned2TeamBuild import Pawned2TeamBuild
from Sources.oazix.CustomBehaviors.primitives.parties.custom_behavior_shared_memory import CustomBehaviorWidgetMemoryManager

class SkillbarParsed:
    primary_profession_id: int
    secondary_profession_id: int
    attributes: dict
    skills: list[int]

    def __init__(self, primary_profession_id: int, secondary_profession_id: int, attributes: dict, skills: list[int]):
        self.primary_profession_id = primary_profession_id
        self.secondary_profession_id = secondary_profession_id
        self.attributes = attributes
        self.skills = skills
    
@dataclass
class SkillbarData:
    account_email: str
    skillbar_template: str
    skillbar_parsed: SkillbarParsed
    custom_behavior_skillbar_used: str

class PartyTeamBuildManager:
    """
    Singleton class to manage party team build configuration.
    All party members can access and modify these shared settings via RAM.
    Direct property access - always reads/writes from shared memory (no caching).

    Team build data structure:
    - templates[0-11]: Array of 12 skillbar template slots
    - Each slot contains: account_email (or "" for unassigned), skillbar_template
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(PartyTeamBuildManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        # Only initialize once
        if self._initialized:
            return

        self._initialized = True
        self._memory_manager = CustomBehaviorWidgetMemoryManager()
        self.skillbar_datas : dict[str, SkillbarData] = {}
        self.throttler = ThrottledTimer(1000)

    @staticmethod
    def _set_c_wchar_array(arr, value: str):
        """Helper to set a c_wchar array from a Python string"""
        # Clear the array first
        for i in range(len(arr)):
            arr[i] = '\0'
        # Copy the string characters
        for i, ch in enumerate(value):
            if i >= len(arr) - 1:  # Leave room for null terminator
                break
            arr[i] = ch

    @staticmethod
    def _get_c_wchar_array_as_str(arr) -> str:
        """Helper to convert a c_wchar array to a Python string"""
        # Convert to string, stopping at null terminator
        result = []
        for ch in arr:
            if ch == '\0':
                break
            result.append(ch)
        return ''.join(result)

    # --- Template Access (0-11) ---
    def get_template_account_email(self, slot_index: int) -> str:
        """Get the account email assigned to a template slot ("" = unassigned)"""
        if slot_index < 0 or slot_index >= 12:
            raise ValueError(f"Slot index must be 0-11, got {slot_index}")
        config = self._memory_manager.GetTeamBuildConfig()
        return self._get_c_wchar_array_as_str(config.TemplateAccountEmails[slot_index])

    def set_template_account_email(self, slot_index: int, account_email: str):
        """Set the account email for a template slot ("" = unassigned)"""
        if slot_index < 0 or slot_index >= 12:
            raise ValueError(f"Slot index must be 0-11, got {slot_index}")
        config = self._memory_manager.GetTeamBuildConfig()
        self._set_c_wchar_array(config.TemplateAccountEmails[slot_index], account_email)
        self._memory_manager.SetTeamBuildConfig(config)

    def get_skillbar_template(self, slot_index: int) -> str:
        """Get the skillbar template for a slot"""
        if slot_index < 0 or slot_index >= 12:
            raise ValueError(f"Slot index must be 0-11, got {slot_index}")
        config = self._memory_manager.GetTeamBuildConfig()
        return self._get_c_wchar_array_as_str(config.SkillbarTemplates[slot_index])

    def set_skillbar_template(self, slot_index: int, template: str):
        """Set the skillbar template for a slot"""
        if slot_index < 0 or slot_index >= 12:
            raise ValueError(f"Slot index must be 0-11, got {slot_index}")
        config = self._memory_manager.GetTeamBuildConfig()
        self._set_c_wchar_array(config.SkillbarTemplates[slot_index], template)
        self._memory_manager.SetTeamBuildConfig(config)

    def get_custom_behavior_skillbar_used(self, slot_index: int) -> str:
        """Get the custom behavior skillbar class name for a slot"""
        if slot_index < 0 or slot_index >= 12:
            raise ValueError(f"Slot index must be 0-11, got {slot_index}")
        config = self._memory_manager.GetTeamBuildConfig()
        return self._get_c_wchar_array_as_str(config.CustomBehaviorSkillbarUsed[slot_index])

    def set_custom_behavior_skillbar_used(self, slot_index: int, skillbar_class_name: str):
        """Set the custom behavior skillbar class name for a slot"""
        if slot_index < 0 or slot_index >= 12:
            raise ValueError(f"Slot index must be 0-11, got {slot_index}")
        config = self._memory_manager.GetTeamBuildConfig()
        self._set_c_wchar_array(config.CustomBehaviorSkillbarUsed[slot_index], skillbar_class_name)
        self._memory_manager.SetTeamBuildConfig(config)

    def get_template_data(self, slot_index: int) -> tuple[str, str, str]:
        """Get complete template data: (account_email, skillbar_template, custom_behavior_skillbar_used)"""
        if slot_index < 0 or slot_index >= 12:
            raise ValueError(f"Slot index must be 0-11, got {slot_index}")
        config = self._memory_manager.GetTeamBuildConfig()
        return (
            self._get_c_wchar_array_as_str(config.TemplateAccountEmails[slot_index]),
            self._get_c_wchar_array_as_str(config.SkillbarTemplates[slot_index]),
            self._get_c_wchar_array_as_str(config.CustomBehaviorSkillbarUsed[slot_index])
        )

    def set_template_data(self, slot_index: int, account_email: str, skillbar_template: str, custom_behavior_skillbar_used: str = ""):
        """Set complete template data: account_email, skillbar_template, custom_behavior_skillbar_used"""
        if slot_index < 0 or slot_index >= 12:
            raise ValueError(f"Slot index must be 0-11, got {slot_index}")
        config = self._memory_manager.GetTeamBuildConfig()
        self._set_c_wchar_array(config.TemplateAccountEmails[slot_index], account_email)
        self._set_c_wchar_array(config.SkillbarTemplates[slot_index], skillbar_template)
        self._set_c_wchar_array(config.CustomBehaviorSkillbarUsed[slot_index], custom_behavior_skillbar_used)
        self._memory_manager.SetTeamBuildConfig(config)

    # --- Utility Methods ---
    def get_my_slot_index(self, my_account_email: str) -> int | None:
        """Find which slot index is assigned to my account email (returns None if not assigned)"""
        config = self._memory_manager.GetTeamBuildConfig()
        for i in range(12):
            email = self._get_c_wchar_array_as_str(config.TemplateAccountEmails[i])
            if email == my_account_email:
                return i
        return None

    def get_template_for_account(self, account_email: str) -> str | None:
        """Get the skillbar template for a specific account email (returns None if not found)"""
        config = self._memory_manager.GetTeamBuildConfig()
        for i in range(12):
            email = self._get_c_wchar_array_as_str(config.TemplateAccountEmails[i])
            if email == account_email:
                template = self._get_c_wchar_array_as_str(config.SkillbarTemplates[i])
                return template if template else None
        return None

    def get_custom_behavior_skillbar_used_for_account(self, account_email: str) -> str | None:
        """Get the custom behavior skillbar class name for a specific account email (returns None if not found)"""
        config = self._memory_manager.GetTeamBuildConfig()
        for i in range(12):
            email = self._get_c_wchar_array_as_str(config.TemplateAccountEmails[i])
            if email == account_email:
                skillbar_used = self._get_c_wchar_array_as_str(config.CustomBehaviorSkillbarUsed[i])
                return skillbar_used if skillbar_used else None
        return None

    def set_custom_behavior_skillbar_used_for_account(self, account_email: str, skillbar_class_name: str):
        """Set the custom behavior skillbar class name for a specific account email."""
        config = self._memory_manager.GetTeamBuildConfig()
        for i in range(12):
            email = self._get_c_wchar_array_as_str(config.TemplateAccountEmails[i])
            if email == account_email:
                self._set_c_wchar_array(config.CustomBehaviorSkillbarUsed[i], skillbar_class_name)
                self._memory_manager.SetTeamBuildConfig(config)
                return

    def set_template_for_account(self, account_email: str, skillbar_template: str, custom_behavior_skillbar_used: str = ""):
        """
        Set the skillbar template for a specific account email.
        If the account already has a slot, update it. Otherwise, find an empty slot.
        """
        config = self._memory_manager.GetTeamBuildConfig()

        # First, check if account already has a slot
        for i in range(12):
            email = self._get_c_wchar_array_as_str(config.TemplateAccountEmails[i])
            if email == account_email:
                # Update existing slot
                self._set_c_wchar_array(config.SkillbarTemplates[i], skillbar_template)
                self._set_c_wchar_array(config.CustomBehaviorSkillbarUsed[i], custom_behavior_skillbar_used)
                self._memory_manager.SetTeamBuildConfig(config)
                return

        # Account doesn't have a slot, find an empty one
        for i in range(12):
            email = self._get_c_wchar_array_as_str(config.TemplateAccountEmails[i])
            if not email:  # Empty slot
                self._set_c_wchar_array(config.TemplateAccountEmails[i], account_email)
                self._set_c_wchar_array(config.SkillbarTemplates[i], skillbar_template)
                self._set_c_wchar_array(config.CustomBehaviorSkillbarUsed[i], custom_behavior_skillbar_used)
                self._memory_manager.SetTeamBuildConfig(config)
                return

        # No empty slots available - this shouldn't happen with 12 slots for party
        raise RuntimeError("No available template slots (all 12 slots are occupied)")

    def clear_slot(self, slot_index: int):
        """Clear a template slot"""
        if slot_index < 0 or slot_index >= 12:
            raise ValueError(f"Slot index must be 0-11, got {slot_index}")
        config = self._memory_manager.GetTeamBuildConfig()
        self._set_c_wchar_array(config.TemplateAccountEmails[slot_index], "")
        self._set_c_wchar_array(config.SkillbarTemplates[slot_index], "")
        self._set_c_wchar_array(config.CustomBehaviorSkillbarUsed[slot_index], "")
        self._memory_manager.SetTeamBuildConfig(config)

    def clear_all_slots(self):
        """Clear all template slots (emails, templates, and custom behavior skillbar used)"""
        config = self._memory_manager.GetTeamBuildConfig()
        for i in range(12):
            self._set_c_wchar_array(config.TemplateAccountEmails[i], "")
            self._set_c_wchar_array(config.SkillbarTemplates[i], "")
            self._set_c_wchar_array(config.CustomBehaviorSkillbarUsed[i], "")
        self._memory_manager.SetTeamBuildConfig(config)

    def update_my_template(self) -> bool:
        """
        Update my skillbar template in shared memory with current in-game skillbar.
        Returns True if successful, False otherwise.
        """
        try:
            # Get current skillbar template
            template = Utils.GenerateSkillbarTemplate()
            if not template:
                return False

            # Get my account email
            my_email = Player.GetAccountEmail()
            if not my_email:
                return False

            # Store in shared memory
            self.set_template_for_account(my_email, template)
            return True

        except Exception as e:
            print(f"Failed to update template: {e}")
            return False

    def __get_all_templates(self) -> dict[str, tuple[str, str]]:
        """
        Get all templates as a dictionary mapping account_email -> (skillbar_template, custom_behavior_skillbar_used).
        Only returns entries that have both email and template set.
        """
        result = {}
        config = self._memory_manager.GetTeamBuildConfig()
        for i in range(12):
            email = self._get_c_wchar_array_as_str(config.TemplateAccountEmails[i])
            template = self._get_c_wchar_array_as_str(config.SkillbarTemplates[i])
            skillbar_used = self._get_c_wchar_array_as_str(config.CustomBehaviorSkillbarUsed[i])
            if email and template:
                result[email] = (template, skillbar_used)
        return result

    def encode_to_pawned2_teambuild_pwnd_file(self) -> str:
        """
        Encode 8 Guild Wars player build templates into a Pawned2-style team string.

        builds : list of 8 strings (each starting with 'O...')
        returns : single composite string ready to use (starting with '>a...')
        """
        builds:list[str] = [template for template, _ in self.__get_all_templates().values()]
        result = Pawned2TeamBuild().encode(builds)
        return result

    def act(self):

        if not self.throttler.IsExpired(): return
        self.throttler.Reset()

        # Update In-memory - get current custom behavior skillbar class name
        account_email = Player.GetAccountEmail()
        template = Utils.GenerateSkillbarTemplate()

        # Get the current custom behavior class name if available
        from Sources.oazix.CustomBehaviors.primitives.custom_behavior_loader import CustomBehaviorLoader
        custom_behavior = CustomBehaviorLoader().custom_combat_behavior
        skillbar_class_name = custom_behavior.__class__.__name__ if custom_behavior is not None else ""

        self.set_template_for_account(account_email, template, skillbar_class_name)


        if custom_behavior_helpers.CustomBehaviorHelperParty.is_party_leader():
            # deal with cleanup
            all_accounts = GLOBAL_CACHE.ShMem.GetAllAccountData()
            all_templates = self.__get_all_templates()

            slot = 0
            for email, (template, skillbar_used) in all_templates.items():
                if email not in [account.AccountEmail for account in all_accounts]:
                    self.clear_slot(slot)
                slot += 1

        # Update object associated
        all_templates = self.__get_all_templates()
        skillbar_datas = self.skillbar_datas

        for email, (template, skillbar_used) in all_templates.items():
            # get the skillbar_data from cache, or create if not exists
            if email not in skillbar_datas:
                skillbar_parsed = SkillbarParsed(*Utils.ParseSkillbarTemplate(template))
                skillbar_datas[email] = SkillbarData(email, template, skillbar_parsed, skillbar_used)
            else:
                skillbar_data: SkillbarData = skillbar_datas[email]
                if skillbar_data.skillbar_template != template:
                    skillbar_data.skillbar_template = template
                    skillbar_parsed = SkillbarParsed(*Utils.ParseSkillbarTemplate(template))
                    skillbar_data.skillbar_parsed = skillbar_parsed
                # Update skillbar_used if changed
                if skillbar_data.custom_behavior_skillbar_used != skillbar_used:
                    skillbar_data.custom_behavior_skillbar_used = skillbar_used

    def apply_skillbar_template(self, template_code: str, account_email: str):
        # let's ask a specific account to apply a skillbar template.
        sender_email = Player.GetAccountEmail()
        if constants.DEBUG: print(f"SendMessage {account_email} to {account_email}")
        extra_data: tuple[str, str, str, str] = self.__build_extra_data(template_code)
        GLOBAL_CACHE.ShMem.SendMessage(sender_email, account_email, SharedCommandType.LoadSkillTemplate, ExtraData = extra_data)

    def __build_extra_data(self, template_code: str) -> tuple[str, str, str, str]:
        # Split template into chunks of X characters (avoid truncation issues)
        chunk_size = 29
        chunks = []
        if template_code:  # Check if template_code is not empty
            chunks = [template_code[i:i+chunk_size] for i in range(0, len(template_code), chunk_size)]
        else:
            chunks = [""]  # Handle empty template case

        # Ensure we always have exactly 4 chunks (pad with empty strings if needed)
        while len(chunks) < 4:
            chunks.append("")
        
        return (chunks[0], chunks[1], chunks[2], chunks[3])

