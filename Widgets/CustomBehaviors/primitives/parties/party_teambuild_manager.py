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
from Widgets.CustomBehaviors.primitives import constants
from Widgets.CustomBehaviors.primitives.parties.custom_behavior_shared_memory import CustomBehaviorWidgetMemoryManager
from Widgets.CustomBehaviors.primitives.parties.pawned2.Pawned2TeamBuild import Pawned2TeamBuild

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

    def get_template_data(self, slot_index: int) -> tuple[str, str]:
        """Get complete template data: (account_email, skillbar_template)"""
        if slot_index < 0 or slot_index >= 12:
            raise ValueError(f"Slot index must be 0-11, got {slot_index}")
        config = self._memory_manager.GetTeamBuildConfig()
        return (
            self._get_c_wchar_array_as_str(config.TemplateAccountEmails[slot_index]),
            self._get_c_wchar_array_as_str(config.SkillbarTemplates[slot_index])
        )

    def set_template_data(self, slot_index: int, account_email: str, skillbar_template: str):
        """Set complete template data: account_email, skillbar_template"""
        if slot_index < 0 or slot_index >= 12:
            raise ValueError(f"Slot index must be 0-11, got {slot_index}")
        config = self._memory_manager.GetTeamBuildConfig()
        self._set_c_wchar_array(config.TemplateAccountEmails[slot_index], account_email)
        self._set_c_wchar_array(config.SkillbarTemplates[slot_index], skillbar_template)
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

    def set_template_for_account(self, account_email: str, skillbar_template: str):
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
                self._memory_manager.SetTeamBuildConfig(config)
                return

        # Account doesn't have a slot, find an empty one
        for i in range(12):
            email = self._get_c_wchar_array_as_str(config.TemplateAccountEmails[i])
            if not email:  # Empty slot
                self._set_c_wchar_array(config.TemplateAccountEmails[i], account_email)
                self._set_c_wchar_array(config.SkillbarTemplates[i], skillbar_template)
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
        self._memory_manager.SetTeamBuildConfig(config)

    def clear_all_slots(self):
        """Clear all template slots (both emails and templates)"""
        config = self._memory_manager.GetTeamBuildConfig()
        for i in range(12):
            self._set_c_wchar_array(config.TemplateAccountEmails[i], "")
            self._set_c_wchar_array(config.SkillbarTemplates[i], "")
        self._memory_manager.SetTeamBuildConfig(config)

    def update_my_template(self) -> bool:
        """
        Update my skillbar template in shared memory with current in-game skillbar.
        Returns True if successful, False otherwise.
        """
        try:
            # Get current skillbar template
            template = Yield.Skills.GenerateSkillbarTemplate()
            if not template:
                return False

            # Get my account email
            my_email = GLOBAL_CACHE.Player.GetAccountEmail()
            if not my_email:
                return False

            # Store in shared memory
            self.set_template_for_account(my_email, template)
            return True

        except Exception as e:
            print(f"Failed to update template: {e}")
            return False

    def __get_all_templates(self) -> dict[str, str]:
        """
        Get all templates as a dictionary mapping account_email -> skillbar_template.
        Only returns entries that have both email and template set.
        """
        result = {}
        config = self._memory_manager.GetTeamBuildConfig()
        for i in range(12):
            email = self._get_c_wchar_array_as_str(config.TemplateAccountEmails[i])
            template = self._get_c_wchar_array_as_str(config.SkillbarTemplates[i])
            if email and template:
                result[email] = template
        return result

    def encode_to_pawned2_teambuild_pwnd_file(self) -> str:
        """
        Encode 8 Guild Wars player build templates into a Pawned2-style team string.

        builds : list of 8 strings (each starting with 'O...')
        returns : single composite string ready to use (starting with '>a...')
        """
        builds:list[str] = [value for key, value in self.__get_all_templates().items()]
        result = Pawned2TeamBuild().encode(builds)
        return result

    def act(self):
        
        if not self.throttler.IsExpired(): return
        self.throttler.Reset()

        # Update In-memory
        account_email = GLOBAL_CACHE.Player.GetAccountEmail()
        template = Yield.Skills.GenerateSkillbarTemplate()
        self.set_template_for_account(account_email, template)

        if GLOBAL_CACHE.Party.IsPartyLeader():
            # deal with cleanup
            all_accounts = GLOBAL_CACHE.ShMem.GetAllAccountData()
            all_templates = self.__get_all_templates()

            slot = 0
            for email, template in all_templates.items():
                if email not in [account.AccountEmail for account in all_accounts]:
                    self.clear_slot(slot)
                slot += 1

        # Update object associated
        all_templates = self.__get_all_templates()
        skillbar_datas = self.skillbar_datas

        for email, template in all_templates.items():
            # get the skillbar_data from cache, or create if not exists
            if template not in skillbar_datas:
                skillbar_parsed = SkillbarParsed(*Yield.Skills.ParseSkillbarTemplate(template))
                skillbar_datas[email] = SkillbarData(email, template, skillbar_parsed)
            else:
                skillbar_data: SkillbarData = skillbar_datas[email]
                if skillbar_data.skillbar_template != template:
                    skillbar_data.skillbar_template = template
                    skillbar_parsed = SkillbarParsed(*Yield.Skills.ParseSkillbarTemplate(template))
                    skillbar_data.skillbar_parsed = skillbar_parsed

    def apply_skillbar_template(self, template_code: str, account_email: str):
        # let's ask a specific account to apply a skillbar template.
        sender_email = GLOBAL_CACHE.Player.GetAccountEmail()
        if constants.DEBUG: print(f"SendMessage {account_email} to {account_email}")
        extra_data: tuple[str, str, str, str] = self.__build_extra_data(template_code)
        GLOBAL_CACHE.ShMem.SendMessage(sender_email, account_email, SharedCommandType.ApplySkillbarTemplate, ExtraData = extra_data)

    def __build_extra_data(self, template_code: str) -> tuple[str, str, str, str]:
        # Split template into chunks of 19 characters (avoid truncation issues)

        # split template code into 4 chunks of 20 characters each
        # Split template into chunks of 19 characters (avoid truncation issues)
        chunk_size = 19  # Reduced from 20 to avoid string truncation
        chunks = []
        if template_code:  # Check if template_code is not empty
            chunks = [template_code[i:i+chunk_size] for i in range(0, len(template_code), chunk_size)]
        else:
            chunks = [""]  # Handle empty template case

        # Ensure we always have exactly 4 chunks (pad with empty strings if needed)
        while len(chunks) < 4:
            chunks.append("")
        
        return (chunks[0], chunks[1], chunks[2], chunks[3])

