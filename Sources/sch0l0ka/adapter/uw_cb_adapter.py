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

    def _set_custom_utilities_enabled(
        self,
        enabled: bool,
        *,
        skill_names: tuple[str, ...] = (),
        class_names: tuple[str, ...] = (),
    ) -> int:
        """Like _set_custom_utility_enabled but toggles ALL matching skills, not just the first."""
        behavior = self._get_custom_behavior(initialize_if_needed=True)
        if behavior is None:
            return 0
        count = 0
        for utility in behavior.get_skills_final_list():
            skill_name = getattr(getattr(utility, "custom_skill", None), "skill_name", None)
            class_name = utility.__class__.__name__
            if skill_name in skill_names or class_name in class_names:
                utility.is_enabled = enabled
                count += 1
        return count

    def _ensure_custom_botting_skills_enabled(self) -> None:
        # Aggressive skills: only these three enabled, everything else disabled.
        _AGGRESSIVE_CONFIG = {
            "move_to_party_member_if_in_aggro":         True,
            "move_to_enemy_if_close_enough":            False,
            "move_to_party_member_if_dead":             True,
            "wait_if_party_member_mana_too_low":        False,
            "wait_if_party_member_too_far":             True,
            "wait_if_party_member_needs_to_loot":       False,
            "wait_if_in_aggro":                         True,
            "wait_if_lock_taken":                       False,
            "move_to_distant_chest_if_path_exists":     False,
        }
        # Automover skills: all disabled.
        _AUTOMOVER_CONFIG = {
            "move_to_party_member_if_in_aggro":         False,
            "move_to_enemy_if_close_enough":            False,
            "move_to_party_member_if_dead":             False,
            "wait_if_party_member_mana_too_low":        False,
            "wait_if_party_member_too_far":             False,
            "wait_if_party_member_needs_to_loot":       False,
            "wait_if_in_aggro":                         False,
            "wait_if_lock_taken":                       False,
        }
        manager = BottingManager()
        changed = False
        for entry in manager.aggressive_skills:
            desired = _AGGRESSIVE_CONFIG.get(entry.name)
            if desired is not None and entry.enabled != desired:
                entry.enabled = desired
                changed = True
        for entry in manager.automover_skills:
            desired = _AUTOMOVER_CONFIG.get(entry.name)
            if desired is not None and entry.enabled != desired:
                entry.enabled = desired
                changed = True
        if changed:
            manager.save()
            ConsoleLog(
                self._bot_name,
                "[CB] Botting skill configuration applied for Underworld bot.",
                Py4GW.Console.MessageType.Info,
            )

    def _ensure_party_defaults(self) -> None:
        """Ensure combat, following, and looting are enabled at each bot step start."""
        party = CustomBehaviorParty()
        party.set_party_is_combat_enabled(True)
        party.set_party_is_following_enabled(True)
        party.set_party_is_looting_enabled(True)

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

    def _disable_widget_locally(self, widget_name: str) -> None:
        """Disable a widget on the local (executing) account via the widget handler."""
        try:
            from Py4GWCoreLib.py4gwcorelib_src.WidgetManager import get_widget_handler
            handler = get_widget_handler()
            if handler.is_widget_enabled(widget_name):
                handler.disable_widget(widget_name)
                ConsoleLog(
                    self._bot_name,
                    f"[Startup] Disabled local widget '{widget_name}'.",
                    Py4GW.Console.MessageType.Info,
                )
        except Exception as e:
            ConsoleLog(
                self._bot_name,
                f"[Startup] Could not disable local widget '{widget_name}': {e}",
                Py4GW.Console.MessageType.Warning,
            )

    def _enable_widget_locally(self, widget_name: str) -> None:
        """Enable a widget on the local (executing) account via the widget handler."""
        try:
            from Py4GWCoreLib.py4gwcorelib_src.WidgetManager import get_widget_handler
            handler = get_widget_handler()
            if not handler.is_widget_enabled(widget_name):
                handler.enable_widget(widget_name)
                ConsoleLog(
                    self._bot_name,
                    f"[Startup] Enabled local widget '{widget_name}'.",
                    Py4GW.Console.MessageType.Info,
                )
        except Exception as e:
            ConsoleLog(
                self._bot_name,
                f"[Startup] Could not enable local widget '{widget_name}': {e}",
                Py4GW.Console.MessageType.Warning,
            )

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
        self._ensure_party_defaults()
        BottingFsmHelpers.SetBottingBehaviorAsAggressive(bot_instance)
        BottingFsmHelpers.UseCustomBehavior(
            bot_instance,
            on_player_critical_death=BottingHelpers.botting_unrecoverable_issue,
            on_party_death=BottingHelpers.botting_unrecoverable_issue,
            on_player_critical_stuck=BottingHelpers.botting_unrecoverable_issue,
        )
        self._bot_instance = bot_instance
        bot_instance.Events.OnPartyMemberBehindCallback(
            lambda: bot_instance.Templates.Routines.OnPartyMemberBehind() if self._wait_for_party_enabled else None
        )
        bot_instance.Events.OnPartyMemberInDangerCallback(
            lambda: bot_instance.Templates.Routines.OnPartyMemberInDanger() if self._in_danger_enabled else None
        )
        bot_instance.Events.OnPartyMemberDeadBehindCallback(
            lambda: bot_instance.Templates.Routines.OnPartyMemberDeathBehind() if self._dead_ally_rescue_enabled else None
        )

    def configure_startup_states(self, bot_instance) -> None:
        # ── Step 1: Disable HeroAI on all accounts ────────────────────────
        bot_instance.States.AddCustomState(
            lambda: ConsoleLog(
                self._bot_name,
                "[Startup] Disabling HeroAI widget on all accounts.",
                Py4GW.Console.MessageType.Info,
            ),
            "[Startup] Log Disable HeroAI",
        )
        bot_instance.States.AddCustomState(
            lambda: self._disable_widget_locally("HeroAI"),
            "Disable local HeroAI",
        )
        bot_instance.States.AddCustomState(
            lambda: self._broadcast_widget_command(
                "HeroAI", SharedCommandType.DisableWidget, "Broadcasted disable"
            ),
            "Disable HeroAI on active accounts",
        )
        bot_instance.Wait.ForTime(2000)
        # ── Step 2: Enable CustomBehaviors on all accounts ────────────────
        bot_instance.States.AddCustomState(
            lambda: ConsoleLog(
                self._bot_name,
                "[Startup] Enabling CustomBehaviors widget on all accounts.",
                Py4GW.Console.MessageType.Info,
            ),
            "[Startup] Log Enable CB Widgets",
        )
        bot_instance.States.AddCustomState(
            lambda: self._enable_widget_locally("CustomBehaviors"),
            "Enable local CustomBehaviors",
        )
        bot_instance.States.AddCustomState(
            lambda: self._broadcast_widget_command(
                "CustomBehaviors", SharedCommandType.EnableWidget, "Broadcasted enable"
            ),
            "Enable CustomBehaviors on active accounts",
        )
        # ── Step 3: Always enable Dhuum Helper on all accounts ────────────
        bot_instance.States.AddCustomState(
            lambda: self._enable_widget_locally("Dhuum Helper"),
            "Enable local Dhuum Helper",
        )
        bot_instance.States.AddCustomState(
            lambda: self._broadcast_widget_command(
                "Dhuum Helper", SharedCommandType.EnableWidget, "Broadcasted enable"
            ),
            "Enable Dhuum Helper on active accounts",
        )
        # ── Step 4: Always enable MerchantRules on all accounts ───────────
        bot_instance.States.AddCustomState(
            lambda: self._enable_widget_locally("MerchantRules"),
            "Enable local MerchantRules",
        )
        bot_instance.States.AddCustomState(
            lambda: self._broadcast_widget_command(
                "MerchantRules", SharedCommandType.EnableWidget, "Broadcasted enable"
            ),
            "Enable MerchantRules on active accounts",
        )
        # ── Step 5: Final startup confirmation ────────────────────────────
        def _log_startup_done() -> None:
            accounts = self._active_multibox_emails()
            ConsoleLog(
                self._bot_name,
                f"[Startup] Widget setup complete (CB mode). "
                f"HeroAI disabled, CustomBehaviors + DhuumHelper + MerchantRules enabled "
                f"on {len(accounts)} active account(s): {accounts}",
                Py4GW.Console.MessageType.Info,
            )
        bot_instance.States.AddCustomState(_log_startup_done, "[Startup] Log Startup Done")

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
        self._ensure_party_defaults()
        cb_config = BottingManager()
        behavior.clear_additionnal_utility_skills()
        cb_config.inject_enabled_skills(cb_config.get_enabled_aggressive_skills(), behavior)
        BottingFsmHelpers.UseCustomBehavior(
            bot_instance,
            on_player_critical_death=BottingHelpers.botting_unrecoverable_issue,
            on_party_death=BottingHelpers.botting_unrecoverable_issue,
            on_player_critical_stuck=BottingHelpers.botting_unrecoverable_issue,
        )
        # UseCustomBehavior → __reset_botting_behavior disables auto_inventory_management.
        # Re-enable it so the upkeep coroutine stays active for the entire run.
        bot_instance.Properties.Enable("auto_inventory_management")

    def sync_runtime(self) -> None:
        loader = CustomBehaviorLoader()
        loader.ensure_botting_daemon_running()
        if loader.custom_combat_behavior is None:
            loader.initialize_custom_behavior_candidate()

    # ── Utility skill toggles ────────────────────────────────────────────

    def toggle_wait_for_party(self, enabled: bool) -> None:
        super().toggle_wait_for_party(enabled)
        self._set_custom_utility_enabled(
            enabled,
            skill_names=("wait_if_party_member_too_far",),
            class_names=("WaitIfPartyMemberTooFarUtility",),
        )

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

    def toggle_local_following(self, enabled: bool) -> None:
        """Enable/disable the follow_party_leader and follow_flag utility skills on
        the local CB instance only.  Unlike set_following_enabled() this does NOT
        write to the party-wide shared memory, so other accounts are unaffected."""
        self._set_custom_utilities_enabled(
            enabled,
            skill_names=("follow_party_leader", "follow_flag"),
            class_names=("FollowPartyLeaderUtility", "FollowFlagUtility"),
        )

    def toggle_local_movement(self, enabled: bool) -> None:
        """Enable/disable ALL movement-issuing utility skills on the local CB
        instance: following skills AND automover/botting skills that reposition
        the player (move_to_party_member_if_in_aggro, wait_if_in_aggro, etc.).
        Does NOT touch shared memory — only this account is affected."""
        self._set_custom_utilities_enabled(
            enabled,
            skill_names=(
                "follow_party_leader",
                "follow_flag",
                "move_to_party_member_if_in_aggro",
                "move_to_enemy_if_close_enough",
                "move_to_party_member_if_dead",
                "wait_if_in_aggro",
                "move_to_distant_chest_if_path_exists",
            ),
            class_names=(
                "FollowPartyLeaderUtility",
                "FollowFlagUtility",
                "MoveToPartyMemberIfInAggroUtility",
                "MoveToEnemyIfCloseEnoughUtility",
                "MoveToPartyMemberIfDeadUtility",
                "WaitIfInAggroUtility",
                "MoveToDistantChestIfPathExistsUtility",
            ),
        )

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

    def batch_set_flags(
        self, assignments: list[tuple[str, int, float, float]]
    ) -> None:
        mgr = CustomBehaviorParty().party_flagging_manager
        config = mgr._memory_manager.GetFlaggingConfig()
        # Clear all 12 slots
        for i in range(12):
            mgr._set_c_wchar_array(config.FlagAccountEmails[i], "")
            config.FlagPositionsX[i] = 0.0
            config.FlagPositionsY[i] = 0.0
        # Set all assignments in one pass
        for email, idx, x, y in assignments:
            if 0 <= idx < 12:
                mgr._set_c_wchar_array(config.FlagAccountEmails[idx], email)
                config.FlagPositionsX[idx] = x
                config.FlagPositionsY[idx] = y
        # Single write to shared memory
        mgr._memory_manager.SetFlaggingConfig(config)
        GLOBAL_CACHE.Party.Heroes.UnflagAllHeroes()

    def auto_assign_flag_emails(self) -> None:
        CustomBehaviorParty().party_flagging_manager.auto_assign_emails_if_none_assigned()

    def update_flag_position_for_email(self, email: str, x: float, y: float) -> None:
        """Find the existing CB flag slot for *email* and update its position only.

        Uses set_flag_position (same code path as the CB panel) when the slot
        already has the email assigned, so only the coordinates are written without
        touching the email array.  If the email is not yet assigned to any slot the
        first free slot is used as a fallback via set_flag_data (email + position).
        """
        mgr = CustomBehaviorParty().party_flagging_manager
        # Try to find the slot that already belongs to this email.
        for i in range(12):
            if mgr.get_flag_account_email(i).lower() == email.lower():
                mgr.set_flag_position(i, x, y)
                return
        # Fallback: assign the first free slot (email assignment required here).
        for i in range(12):
            if not mgr.get_flag_account_email(i):
                self.set_flag_for_email(email, i, x, y)
                return
