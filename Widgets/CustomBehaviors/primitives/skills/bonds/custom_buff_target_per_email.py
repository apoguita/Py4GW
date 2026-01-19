from dataclasses import dataclass
import threading

from typing import Callable, override
from Py4GWCoreLib import GLOBAL_CACHE, ThrottledTimer, Agent
from Py4GWCoreLib.Routines import Routines
from Py4GWCoreLib import Player
from Widgets.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Widgets.CustomBehaviors.primitives.skills.bonds.custom_buff_target import CustomBuffTarget
from Widgets.CustomBehaviors.primitives.skills.custom_skill import CustomSkill


@dataclass
class BuffEmailEntry:
    account_email: str
    is_activated: bool = False
    character_name: str | None = None
    profession_prefix: str | None = None
    agent_id: int | None = None


class BuffConfigurationPerPlayerEmail(CustomBuffTarget):
    """
    Buff target configuration keyed by player account email.
    Mirrors BuffConfigurationPerProfession but filters using the owning
    account's email address for a given agent_id.
    """

    def __init__(self, custom_skill: CustomSkill):

        self.custom_skill: CustomSkill = custom_skill
        self.__lock = threading.RLock()

        # Single dictionary storing state per email
        self.__entries_by_email: dict[str, BuffEmailEntry] = {}

        # Throttled timers for periodic refresh
        self.__scan_timer = ThrottledTimer(3000)    # scan accounts every 3s
        self.__refresh_timer = ThrottledTimer(2000) # refresh char/prof every 2s

    def get_by_email(self, email: str) -> BuffEmailEntry:
        with self.__lock:
            if email in self.__entries_by_email:
                return self.__entries_by_email[email]
        raise Exception(f"BuffConfigurationPerPlayerEmail: {email} not found")

    def is_activated(self, email: str) -> bool:
        with self.__lock:
            entry = self.__entries_by_email.get(email)
            return bool(entry and entry.is_activated)

    def activate(self, email: str) -> None:
        with self.__lock:
            entry = self.__entries_by_email.get(email)
            if entry is None:
                self.__entries_by_email[email] = BuffEmailEntry(account_email=email, is_activated=True)
            else:
                entry.is_activated = True

    def deactivate(self, email: str) -> None:
        with self.__lock:
            entry = self.__entries_by_email.get(email)
            if entry is None:
                self.__entries_by_email[email] = BuffEmailEntry(account_email=email, is_activated=False)
            else:
                entry.is_activated = False

    @override
    def get_agent_id_predicate(self) -> Callable[[int], bool]:
        return lambda agent_id: self.__should_apply_effect(agent_id)

    def __should_apply_effect(self, agent_id: int) -> bool:
        # Fast path: use stored agent_id mapping
        try:
            with self.__lock:
                for entry in self.__entries_by_email.values():
                    if entry.agent_id and int(entry.agent_id) == int(agent_id):
                        return bool(entry.is_activated and self.__should_apply_effect_on_agent_id(agent_id))
        except Exception:
            pass

        # Fallback: resolve via SharedMemory (email lookup)
        email = self.__get_email_for_agent(agent_id)
        if not email:
            return False
        with self.__lock:
            entry = self.__entries_by_email.get(email)
            return bool(entry and entry.is_activated and self.__should_apply_effect_on_agent_id(agent_id))

    def __should_apply_effect_on_agent_id(self, agent_id: int) -> bool:
        # Align effect-check logic with profession-based configuration
        if agent_id == Player.GetAgentID():
            has_buff: bool = Routines.Checks.Effects.HasBuff(Player.GetAgentID(), self.custom_skill.skill_id)
            return not has_buff
        else:
            has_effect: bool = custom_behavior_helpers.Resources.is_ally_under_specific_effect(agent_id, self.custom_skill.skill_id)
            return not has_effect

    def __get_email_for_agent(self, agent_id: int) -> str | None:
        """Map agent_id to account email; prefer stored mapping, fall back to SharedMemory."""
        try:
            with self.__lock:
                for entry in self.__entries_by_email.values():
                    if entry.agent_id and int(entry.agent_id) == int(agent_id):
                        return entry.account_email
        except Exception:
            pass
        try:
            for account in GLOBAL_CACHE.ShMem.GetAllAccountData():
                if int(getattr(account, "PlayerID", 0) or 0) == int(agent_id):
                    return getattr(account, "AccountEmail", None)
        except Exception:
            pass
        return None

    def __get_char_and_prof_for_email(self, email: str) -> tuple[str | None, str | None, int | None]:
        """Return (character_name, profession_prefix, agent_id) for the given email using one lookup."""
        try:
            account = GLOBAL_CACHE.ShMem.GetAccountDataFromEmail(email)
            if account is None:
                return None, None, None
            char_name = getattr(account, "CharacterName", None)
            agent_id_int = int(getattr(account, "PlayerID", 0) or 0)
            agent_id: int | None = agent_id_int if agent_id_int > 0 else None
            prof_prefix: str | None = None
            if agent_id:
                try:
                    primary, secondary = Agent.GetProfessionShortNames(agent_id)
                    primary = (primary or "").strip()
                    secondary = (secondary or "").strip()
                    if secondary and secondary.lower() not in ("none", "n/a", "0"):
                        prof_prefix = f"{primary}/{secondary}" if primary else secondary
                    else:
                        prof_prefix = primary or None
                except Exception:
                    prof_prefix = None
            return char_name, prof_prefix, agent_id
        except Exception:
            return None, None, None

    def initialize_buff_according_to_professions(self, profession_config=None) -> None:
        """Sync email activation flags to match the provided per-profession configuration.
        If profession_config is None, exits without changes.
        """
        if profession_config is None:
            return
        try:
            # Build set of active profession IDs based on the profession configuration
            from Py4GWCoreLib.enums import Profession
            active_profession_ids: set[int] = set()
            for prof in Profession:
                if getattr(prof, "name", "") == "_None":
                    continue
                try:
                    if profession_config.is_activated(prof):
                        active_profession_ids.add(int(prof.value))
                except Exception:
                    continue

            # Map emails to their current primary profession IDs
            email_to_prof_id: dict[str, int] = {}
            for acc in GLOBAL_CACHE.ShMem.GetAllAccountData():
                email = getattr(acc, "AccountEmail", "")
                if not email:
                    continue
                agent_id = int(getattr(acc, "PlayerID", 0) or 0)
                if agent_id <= 0:
                    continue
                try:
                    primary_prof_id: int | None = Agent.GetProfessionIDs(agent_id)[0]
                    if primary_prof_id is None:
                        continue
                    email_to_prof_id[email] = primary_prof_id
                except Exception:
                    continue

            # Ensure entries exist and apply activation according to active professions
            with self.__lock:
                for email, prof_id in email_to_prof_id.items():
                    entry = self.__entries_by_email.get(email)
                    if entry is None:
                        entry = BuffEmailEntry(account_email=email, is_activated=False)
                        self.__entries_by_email[email] = entry
                    entry.is_activated = (prof_id in active_profession_ids)
        except Exception:
            # Fail-safe: do not throw if cache not ready
            pass

    def reset(self) -> None:
        """Recalculate agent IDs for all known emails (e.g., after map change)."""
        try:
            with self.__lock:
                emails = list(self.__entries_by_email.keys())
            for email in emails:
                new_id: int | None = None
                try:
                    account = GLOBAL_CACHE.ShMem.GetAccountDataFromEmail(email)
                    if account is not None:
                        val = int(getattr(account, "PlayerID", 0) or 0)
                        new_id = val if val > 0 else None
                except Exception:
                    new_id = None
                finally:
                    with self.__lock:
                        entry = self.__entries_by_email.get(email)
                        if entry is not None:
                            entry.agent_id = new_id
        except Exception:
            pass

    def render_buff_configuration(self,  py4gw_root_directory: str):
        """Render toggle buttons per account email.
        - Every 3s: scan SharedMemory accounts and add missing emails (default deactivated)
        - Every 2s: refresh character name and profession prefix per email
        - Each frame: render buttons reflecting is_activated state
        """
        import PyImGui
        from Py4GWCoreLib import ImGui
        from Py4GWCoreLib.py4gwcorelib_src.Utils import Utils

        # Periodic: discover new accounts (3s)
        if self.__scan_timer.IsExpired():
            try:
                accounts = GLOBAL_CACHE.ShMem.GetAllAccountData()
                with self.__lock:
                    for acc in accounts:
                        email = getattr(acc, "AccountEmail", "")
                        if not email:
                            continue
                        if email not in self.__entries_by_email:
                            agent_id = int(getattr(acc, "PlayerID", 0) or 0)
                            self.__entries_by_email[email] = BuffEmailEntry(
                                account_email=email,
                                is_activated=False,
                                agent_id=agent_id if agent_id > 0 else None
                            )
            except Exception:
                pass
            finally:
                self.__scan_timer.Reset()

        # Periodic: refresh character/prof info (2s)
        if self.__refresh_timer.IsExpired():
            try:
                with self.__lock:
                    emails = list(self.__entries_by_email.keys())
                for email in emails:
                    char_name, prof_prefix, agent_id = self.__get_char_and_prof_for_email(email)
                    with self.__lock:
                        entry = self.__entries_by_email.get(email)
                        if entry is not None:
                            entry.character_name = char_name
                            entry.profession_prefix = prof_prefix
                            entry.agent_id = agent_id
            except Exception:
                pass
            finally:
                self.__refresh_timer.Reset()

        PyImGui.bullet_text("Buff configuration : ")

        with self.__lock:
            entries_snapshot = list(self.__entries_by_email.values())
        if len(entries_snapshot) == 0:
            PyImGui.text("No known players yet.")
            return

        # Stable ordering to avoid flicker: sort by email
        sorted_entries = sorted(entries_snapshot, key=lambda e: (e.account_email or "").lower())

        for entry in sorted_entries:
            email = entry.account_email or "(unknown)"
            char_name = entry.character_name or "Unknown"
            prof_prefix = entry.profession_prefix
            label = f"{prof_prefix} | {char_name} | {email}" if prof_prefix else f"{char_name} | {email}"
            stable_id = f"##buff_toggle_{self.custom_skill.skill_name}_{email}"

            if entry.is_activated:
                # Draw an emphasized bordered small button when active (consistent height)
                PyImGui.push_style_var(ImGui.ImGuiStyleVar.FrameBorderSize, 3)
                PyImGui.push_style_color(PyImGui.ImGuiCol.Border, Utils.ColorToTuple(Utils.RGBToColor(3, 244, 60, 255)))
                if PyImGui.small_button(f"{label}{stable_id}"):
                    with self.__lock:
                        entry.is_activated = False
                ImGui.show_tooltip(f"Deactivate buff for {email}")
                PyImGui.pop_style_var(1)
                PyImGui.pop_style_color(1)
            else:
                if PyImGui.small_button(f"{label}{stable_id}"):
                    with self.__lock:
                        entry.is_activated = True
                ImGui.show_tooltip(f"Activate buff for {email}")
