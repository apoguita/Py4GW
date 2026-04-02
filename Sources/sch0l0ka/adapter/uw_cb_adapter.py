# ╔══════════════════════════════════════════════════════════════════════════════
# ║  File    : uw_cb_adapter.py
# ║  Purpose : CustomBehaviors (CB) implementation of UWCombatAdapter.
# ║            Bridges the Underworld bot with the oazix CB system:
# ║            skill toggles via BottingManager, party control via
# ║            CustomBehaviorParty, multibox flags via the CB flagging
# ║            manager, and per-run widget broadcasting via ShMem.
# ╚══════════════════════════════════════════════════════════════════════════════

import Py4GW
from Py4GWCoreLib import Agent, Player, GLOBAL_CACHE, ConsoleLog
from Py4GWCoreLib.enums_src.Multiboxing_enums import SharedCommandType

from Sources.oazix.CustomBehaviors.primitives.custom_behavior_loader import CustomBehaviorLoader
from Sources.oazix.CustomBehaviors.primitives.botting.botting_manager import BottingManager
from Sources.oazix.CustomBehaviors.primitives.parties.custom_behavior_party import CustomBehaviorParty
from Sources.oazix.CustomBehaviors.primitives.botting.botting_helpers import BottingHelpers
from Sources.oazix.CustomBehaviors.primitives.botting.botting_fsm_helper import BottingFsmHelpers

from Sources.sch0l0ka.adapter.uw_combat_adapter import UWCombatAdapter


class UWCBAdapter(UWCombatAdapter):
    """CustomBehavior implementation of the UW combat adapter."""

    def __init__(self, bot_name: str) -> None:
        self._bot_name = bot_name

    # ── Helpers ──────────────────────────────────────────────────────────

    def _get_custom_behavior(self, initialize_if_needed: bool = True):
        loader = CustomBehaviorLoader()
        behavior = loader.custom_combat_behavior
        if behavior is None and initialize_if_needed:
            loader.initialize_custom_behavior_candidate()
            behavior = loader.custom_combat_behavior
        return behavior

    def _set_custom_utility_enabled(
        self,
        enabled: bool,
        *,
        skill_names: tuple[str, ...] = (),
        class_names: tuple[str, ...] = (),
    ) -> bool:
        behavior = self._get_custom_behavior(initialize_if_needed=True)
        if behavior is None:
            return False
        for utility in behavior.get_skills_final_list():
            skill_name = getattr(getattr(utility, "custom_skill", None), "skill_name", None)
            class_name = utility.__class__.__name__
            if skill_name in skill_names or class_name in class_names:
                utility.is_enabled = enabled
                return True
        return False

    def _ensure_custom_botting_skills_enabled(self) -> None:
        manager = BottingManager()
        required_skill_keys = {
            "wait_if_in_aggro",
            "move_to_party_member_if_in_aggro",
            "move_to_party_member_if_dead",
        }
        changed = False
        for entry in manager.aggressive_skills:
            if entry.name in required_skill_keys and not entry.enabled:
                entry.enabled = True
                changed = True
        if changed:
            manager.save()
            ConsoleLog(
                self._bot_name,
                "[CB] Required botting skills were enabled for this bot.",
                Py4GW.Console.MessageType.Info,
            )

    def _active_multibox_emails(self) -> list[str]:
        emails: list[str] = []
        for account in (GLOBAL_CACHE.ShMem.GetAllAccountData() or []):
            email = str(getattr(account, "AccountEmail", "") or "").strip()
            if not email:
                continue
            if not bool(getattr(account, "IsSlotActive", True)):
                continue
            if bool(getattr(account, "IsIsolated", False)):
                continue
            emails.append(email)
        return emails

    def _broadcast_widget_command(
        self,
        widget_name: str,
        command: SharedCommandType,
        action_label: str,
    ) -> None:
        sender_email = Player.GetAccountEmail()
        recipients = self._active_multibox_emails()
        for email in recipients:
            GLOBAL_CACHE.ShMem.SendMessage(
                sender_email,
                email,
                command,
                (0, 0, 0, 0),
                (widget_name, "", "", ""),
            )
        ConsoleLog(
            self._bot_name,
            f"[Startup] {action_label} '{widget_name}' for {len(recipients)} active account(s).",
            Py4GW.Console.MessageType.Info,
        )

    # ── Lifecycle ────────────────────────────────────────────────────────

    def setup(self, bot_instance) -> None:
        behavior = self._get_custom_behavior(initialize_if_needed=True)
        if behavior is None:
            ConsoleLog(
                self._bot_name,
                "[CB] No custom behavior found. Bot runs without CB integration.",
                Py4GW.Console.MessageType.Warning,
            )
            return
        self._ensure_custom_botting_skills_enabled()
        BottingFsmHelpers.SetBottingBehaviorAsAggressive(bot_instance)
        BottingFsmHelpers.UseCustomBehavior(
            bot_instance,
            on_player_critical_death=BottingHelpers.botting_unrecoverable_issue,
            on_party_death=BottingHelpers.botting_unrecoverable_issue,
            on_player_critical_stuck=BottingHelpers.botting_unrecoverable_issue,
        )
        self._bot_instance = bot_instance
        bot_instance.Events.OnPartyMemberBehindCallback(
            lambda: self._on_party_behind_callback(bot_instance)
        )
        bot_instance.Events.OnPartyMemberInDangerCallback(
            lambda: bot_instance.Templates.Routines.OnPartyMemberInDanger()
        )
        bot_instance.Events.OnPartyMemberDeadBehindCallback(
            lambda: self._on_dead_behind_callback(bot_instance)
        )

    def configure_startup_states(self, bot_instance) -> None:
        bot_instance.States.AddCustomState(
            lambda: ConsoleLog(
                self._bot_name,
                "[Startup] Disabling HeroAI widget on all accounts.",
                Py4GW.Console.MessageType.Info,
            ),
            "[Startup] Log Disable HeroAI",
        )
        bot_instance.States.AddCustomState(
            lambda: self._broadcast_widget_command(
                "HeroAI", SharedCommandType.DisableWidget, "Broadcasted disable"
            ),
            "Disable HeroAI on active accounts",
        )
        bot_instance.Wait.ForTime(2000)
        bot_instance.States.AddCustomState(
            lambda: ConsoleLog(
                self._bot_name,
                "[Startup] Enabling CustomBehavior widgets on all accounts.",
                Py4GW.Console.MessageType.Info,
            ),
            "[Startup] Log Enable CB Widgets",
        )
        for widget_name in (
            "CustomBehaviors",
            "Custom Behavior",
            "Custom Behaviors: Utility AI",
        ):
            bot_instance.States.AddCustomState(
                lambda wn=widget_name: self._broadcast_widget_command(
                    wn, SharedCommandType.EnableWidget, "Broadcasted enable"
                ),
                f"Enable {widget_name} on active accounts",
            )
        bot_instance.States.AddCustomState(
            lambda: self._broadcast_widget_command(
                "Dhuum Helper", SharedCommandType.EnableWidget, "Broadcasted enable"
            ),
            "Enable Dhuum Helper on active accounts",
        )

    def reactivate_for_step(self, bot_instance, step_label: str) -> None:
        behavior = self._get_custom_behavior(initialize_if_needed=True)
        if behavior is None:
            ConsoleLog(
                self._bot_name,
                f"[CB] No behavior found for step '{step_label}'. Skipping CB setup.",
                Py4GW.Console.MessageType.Warning,
            )
            return
        self._ensure_custom_botting_skills_enabled()
        cb_config = BottingManager()
        behavior.clear_additionnal_utility_skills()
        cb_config.inject_enabled_skills(cb_config.get_enabled_aggressive_skills(), behavior)
        BottingFsmHelpers.UseCustomBehavior(
            bot_instance,
            on_player_critical_death=BottingHelpers.botting_unrecoverable_issue,
            on_party_death=BottingHelpers.botting_unrecoverable_issue,
            on_player_critical_stuck=BottingHelpers.botting_unrecoverable_issue,
        )

    def sync_runtime(self) -> None:
        self._sync_party_watchdog(self._bot_instance)
        loader = CustomBehaviorLoader()
        loader.ensure_botting_daemon_running()
        if loader.custom_combat_behavior is None:
            loader.initialize_custom_behavior_candidate()

    # ── Utility skill toggles ────────────────────────────────────────────
    # toggle_wait_for_party is inherited from UWCombatAdapter (watchdog-based).

    def toggle_wait_if_aggro(self, enabled: bool) -> None:
        self._set_custom_utility_enabled(
            enabled,
            skill_names=("wait_if_in_aggro",),
            class_names=("WaitIfInAggroUtility",),
        )

    def toggle_move_to_party_member_if_dead(self, enabled: bool) -> None:
        self._set_custom_utility_enabled(
            enabled,
            skill_names=("move_to_party_member_if_dead",),
            class_names=("MoveToPartyMemberIfDeadUtility",),
        )
        self.toggle_dead_ally_rescue(enabled)

    # ── Party control ────────────────────────────────────────────────────

    def set_party_leader(self, email: str) -> None:
        CustomBehaviorParty().set_party_leader_email(email)

    def set_following_enabled(self, enabled: bool) -> None:
        CustomBehaviorParty().set_party_is_following_enabled(enabled)

    def set_combat_enabled(self, enabled: bool) -> None:
        CustomBehaviorParty().set_party_is_combat_enabled(enabled)

    def set_looting_enabled(self, enabled: bool) -> None:
        CustomBehaviorParty().set_party_is_looting_enabled(enabled)

    def set_forced_state(self, state) -> None:
        CustomBehaviorParty().set_party_forced_state(state)

    def set_blessing_enabled(self, enabled: bool) -> None:
        CustomBehaviorParty().set_party_is_blessing_enabled(enabled)

    def set_custom_target(self, agent_id: int) -> None:
        CustomBehaviorParty().set_party_custom_target(agent_id)

    # ── Flag management ──────────────────────────────────────────────────

    def set_flag(self, index: int, x: float, y: float) -> None:
        # CB shared-memory flag (used by multibox CB accounts)
        CustomBehaviorParty().party_flagging_manager.set_flag_position(index, x, y)
        # Native GW flag (used for heroes in the local party)
        party_pos = index + 1
        agent_id = GLOBAL_CACHE.Party.Heroes.GetHeroAgentIDByPartyPosition(party_pos)
        if agent_id and Agent.IsValid(agent_id):
            GLOBAL_CACHE.Party.Heroes.FlagHero(agent_id, x, y)

    def set_flag_for_email(
        self, email: str, flag_index: int, x: float, y: float
    ) -> None:
        """Assign flag slot *flag_index* to *email* and position it at (x, y)."""
        mgr = CustomBehaviorParty().party_flagging_manager
        mgr.set_flag_data(flag_index, email, x, y)

    def clear_flags(self) -> None:
        CustomBehaviorParty().party_flagging_manager.clear_all_flags()
        GLOBAL_CACHE.Party.Heroes.UnflagAllHeroes()

    def auto_assign_flag_emails(self) -> None:
        CustomBehaviorParty().party_flagging_manager.auto_assign_emails_if_none_assigned()

    def update_flag_position_for_email(self, email: str, x: float, y: float) -> None:
        """Find the existing CB flag slot for *email* and update its position only.

        If the email is not yet assigned to any slot, the first free slot is used
        as a fallback so the account still gets flagged.
        """
        mgr = CustomBehaviorParty().party_flagging_manager
        # Try to find the slot that already belongs to this email.
        for i in range(12):
            if mgr.get_flag_account_email(i).lower() == email.lower():
                mgr.set_flag_data(i, email, x, y)
                return
        # Fallback: assign the first free slot.
        for i in range(12):
            if not mgr.get_flag_account_email(i):
                mgr.set_flag_data(i, email, x, y)
                return
