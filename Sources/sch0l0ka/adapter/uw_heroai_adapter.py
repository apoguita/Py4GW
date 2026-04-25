# ╔══════════════════════════════════════════════════════════════════════════════
# ║  File    : uw_heroai_adapter.py
# ║  Purpose : HeroAI implementation of UWCombatAdapter.
# ║            Most skill-toggle methods are intentional no-ops because
# ║            HeroAI manages aggro/follow behaviour automatically.
# ║            Flag management writes to both native GW hero flags and
# ║            HeroAI shared-memory options so heroes and multibox followers
# ║            respect the flagged positions.
# ╚══════════════════════════════════════════════════════════════════════════════

import Py4GW
from Py4GWCoreLib import Agent, Player, Utils, GLOBAL_CACHE, ConsoleLog, Routines
from Py4GWCoreLib.enums_src.Multiboxing_enums import SharedCommandType

from Sources.sch0l0ka.adapter.uw_combat_adapter import UWCombatAdapter


class UWHeroAIAdapter(UWCombatAdapter):
    """HeroAI implementation of the UW combat adapter.

    Utility-skill toggles are no-ops because HeroAI manages aggro/follow
    behaviour automatically through its own settings.  Flag management drives
    both native GW hero flags and HeroAI shared-memory options so that both
    native heroes and multibox-account HeroAI followers honour the positions.
    """

    def __init__(self, bot_name: str) -> None:
        self._bot_name = bot_name
        self._bot_instance = None
        # Desired HeroAI option state — pushed to all accounts every frame by
        # sync_runtime() so the Messaging snapshot/restore cycle can never
        # silently re-enable an option the leader has explicitly disabled.
        self._enforced_combat: bool = True
        self._enforced_following: bool = True
        self._enforced_looting: bool = True
        # Tracks whether movement should be paused while enemies are in aggro range.
        self._wait_if_aggro_enabled: bool = True
        self._last_aggro_check: float = 0.0

    # ── Helpers ──────────────────────────────────────────────────────────

    def _active_multibox_emails(self) -> list[str]:
        """Return emails of all reachable multibox accounts (excludes local account)."""
        local_email = (Player.GetAccountEmail() or "").strip()
        emails: list[str] = []
        for account in (GLOBAL_CACHE.ShMem.GetAllAccountData() or []):
            email = str(getattr(account, "AccountEmail", "") or "").strip()
            if not email or email == local_email:
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
        sent = 0
        for email in recipients:
            result = GLOBAL_CACHE.ShMem.SendMessage(
                sender_email,
                email,
                command,
                (0, 0, 0, 0),
                (widget_name, "", "", ""),
            )
            if result >= 0:
                sent += 1
        ConsoleLog(
            self._bot_name,
            f"[Startup] {action_label} '{widget_name}': {sent}/{len(recipients)} account(s) reached.",
            Py4GW.Console.MessageType.Info,
        )

    def _set_all_heroai_options(
        self,
        *,
        following: bool | None = None,
        combat: bool | None = None,
        looting: bool | None = None,
    ) -> None:
        """Apply option flags to every active HeroAI account in shared memory."""
        for _, options in GLOBAL_CACHE.ShMem.GetAllActiveAccountHeroAIPairs(sort_results=False):
            if following is not None:
                options.Following = following
            if combat is not None:
                options.Combat = combat
            if looting is not None:
                options.Looting = looting

    def _reset_enforced_defaults(self) -> None:
        """Reset all enforced flags to True (default section-start state)."""
        self._enforced_following = True
        self._enforced_combat = True
        self._enforced_looting = True

    # ── Lifecycle ────────────────────────────────────────────────────────

    def setup(self, bot_instance) -> None:
        ConsoleLog(
            self._bot_name,
            "[HeroAI] Adapter setup: HeroAI mode active.",
            Py4GW.Console.MessageType.Info,
        )
        self._bot_instance = bot_instance
        bot_instance.Events.OnPartyMemberBehindCallback(
            lambda: self.on_party_member_behind(bot_instance)
        )
        bot_instance.Events.OnPartyMemberInDangerCallback(
            lambda: bot_instance.Templates.Routines.OnPartyMemberInDanger()
        )
        bot_instance.Events.OnPartyMemberDeadBehindCallback(
            lambda: bot_instance.Templates.Routines.OnPartyMemberDeathBehind() if self._dead_ally_rescue_enabled else None
        )

    def _disable_widget_locally(self, widget_name: str) -> None:
        """Disable a widget on the local (executing) account via the widget handler."""
        try:
            from Py4GWCoreLib.py4gwcorelib_src.WidgetManager import get_widget_handler
            handler = get_widget_handler()
            if handler.is_widget_enabled(widget_name):
                handler.disable_widget(widget_name)
                ConsoleLog(
                    self._bot_name,
                    f"[HeroAI] Disabled local widget '{widget_name}'.",
                    Py4GW.Console.MessageType.Info,
                )
        except Exception as e:
            ConsoleLog(
                self._bot_name,
                f"[HeroAI] Could not disable local widget '{widget_name}': {e}",
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
                    f"[HeroAI] Enabled local widget '{widget_name}'.",
                    Py4GW.Console.MessageType.Info,
                )
        except Exception as e:
            ConsoleLog(
                self._bot_name,
                f"[HeroAI] Could not enable local widget '{widget_name}': {e}",
                Py4GW.Console.MessageType.Warning,
            )

    def configure_startup_states(self, bot_instance) -> None:
        bot_instance.States.AddCustomState(
            lambda: ConsoleLog(
                self._bot_name,
                "[Startup] Enforcing HeroAI widget on all accounts.",
                Py4GW.Console.MessageType.Info,
            ),
            "[Startup] Log HeroAI Enforcement",
        )
        bot_instance.States.AddCustomState(
            lambda: ConsoleLog(
                self._bot_name,
                "[Startup] Enabling HeroAI widget on all accounts.",
                Py4GW.Console.MessageType.Info,
            ),
            "[Startup] Log Enable HeroAI",
        )
        bot_instance.States.AddCustomState(
            lambda: self._enable_widget_locally("HeroAI"),
            "Enable local HeroAI",
        )
        bot_instance.States.AddCustomState(
            lambda: self._broadcast_widget_command(
                "HeroAI", SharedCommandType.EnableWidget, "Broadcasted enable"
            ),
            "Enable HeroAI on active accounts",
        )
        bot_instance.States.AddCustomState(
            lambda: self._reset_enforced_defaults(),
            "Set HeroAI options on all accounts",
        )
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
        # ── Always enable MerchantRules on all accounts ───────────────────
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
        # ── Final startup confirmation ─────────────────────────────────────
        def _log_startup_done() -> None:
            accounts = self._active_multibox_emails()
            ConsoleLog(
                self._bot_name,
                f"[Startup] Widget setup complete (HeroAI mode). "
                f"HeroAI + DhuumHelper + MerchantRules enabled "
                f"on {len(accounts)} active account(s): {accounts}",
                Py4GW.Console.MessageType.Info,
            )
        bot_instance.States.AddCustomState(_log_startup_done, "[Startup] Log Startup Done")

    def reactivate_for_step(self, bot_instance, step_label: str) -> None:
        # Restore all enforced flags to their defaults for the new section.
        # sync_runtime() will push these to all accounts on the next frame.
        self._enforced_following = True
        self._enforced_combat = True
        self._enforced_looting = True
        hero_ai_prop = bot_instance.config.upkeep.hero_ai.is_active() if hasattr(bot_instance.config, 'upkeep') else '?'
        ConsoleLog(
            self._bot_name,
            f"[HeroAI] Step '{step_label}' — options restored (F=True C=True L=True). hero_ai={hero_ai_prop}",
            Py4GW.Console.MessageType.Info,
        )

    def sync_runtime(self) -> None:
        # Push the enforced option state to all accounts every frame.
        # The Messaging system on followers may restore Combat/Following/Looting
        # to True via RestoreHeroAISnapshot / EnableHeroAIOptions after completing
        # shared commands.  Continuous enforcement ensures the leader always wins.
        self._set_all_heroai_options(
            following=self._enforced_following,
            combat=self._enforced_combat,
            looting=self._enforced_looting,
        )
        if self._wait_if_aggro_enabled and self._bot_instance is not None:
            self._sync_aggro_watchdog(self._bot_instance)
        # Debug: ensure hero_ai property stays True
        if self._bot_instance is not None and hasattr(self._bot_instance.config, 'upkeep'):
            if not self._bot_instance.config.upkeep.hero_ai.is_active():
                ConsoleLog(
                    self._bot_name,
                    "[HeroAI] WARNING: hero_ai property was False — forcing True.",
                    Py4GW.Console.MessageType.Warning,
                )
                self._bot_instance.config.upkeep.hero_ai._apply("active", True)

    def _any_enemy_in_aggro_range(self) -> bool:
        """Return True if at least one alive, non-blacklisted enemy is within aggro range."""
        from Py4GWCoreLib import AgentArray
        from Py4GWCoreLib.EnemyBlacklist import EnemyBlacklist
        bl = EnemyBlacklist()
        player_pos = Player.GetXY()
        aggro_range = 1100.0
        for agent_id in (AgentArray.GetEnemyArray() or []):
            if bl.is_blacklisted(agent_id):
                continue
            if Agent.IsAlive(agent_id) and Utils.Distance(player_pos, Agent.GetXY(agent_id)) <= aggro_range:
                return True
        return False

    def _sync_aggro_watchdog(self, bot_instance) -> None:
        """Add the aggro-pause coroutine when enemies enter Spellcast range."""
        import time
        if not bot_instance.config.fsm_running:
            return
        if not Routines.Checks.Map.IsExplorable():
            return
        now = time.monotonic()
        if now - self._last_aggro_check < 0.5:
            return
        self._last_aggro_check = now
        if self._any_enemy_in_aggro_range():
            bot_instance.config.FSM.AddManagedCoroutine(
                "UW_WaitIfAggro",
                lambda: self._coro_wait_if_no_aggro(bot_instance),
            )

    def _coro_wait_if_no_aggro(self, bot_instance):
        """Pause the FSM every frame until no alive enemy is within Spellcast range."""
        fsm = bot_instance.config.FSM
        try:
            while True:
                fsm.pause()
                if not self._wait_if_aggro_enabled:
                    return
                if not self._any_enemy_in_aggro_range():
                    return
                yield
        finally:
            fsm.resume()

    # ── Utility skill toggles (no-ops for HeroAI) ────────────────────────
    # toggle_wait_for_party is inherited from UWCombatAdapter (watchdog-based).

    def toggle_wait_if_aggro(self, enabled: bool) -> None:
        self._wait_if_aggro_enabled = enabled

    def toggle_move_if_aggro(self, enabled: bool) -> None:
        pass

    def toggle_move_to_enemy_if_close_enough(self, enabled: bool) -> None:
        pass

    # toggle_move_to_party_member_if_dead is inherited from UWCombatAdapter
    # (calls toggle_dead_ally_rescue — no CB skill to toggle in HeroAI mode).

    def toggle_wait_if_party_member_needs_to_loot(self, enabled: bool) -> None:
        pass

    def toggle_lock(self, enabled: bool) -> None:
        pass

    def toggle_wait_if_party_member_mana_too_low(self, enabled: bool) -> None:
        pass

    # ── Party control ────────────────────────────────────────────────────

    def set_party_leader(self, email: str) -> None:
        pass  # HeroAI auto-detects the party leader.

    def set_following_enabled(self, enabled: bool) -> None:
        self._enforced_following = enabled
        if enabled:
            # Clear flags so DistanceSafe uses the leader position again and
            # following resumes normally.
            self.clear_flags()
        else:
            # Flag every account at its current position so the headless-tree
            # DistanceSafe guard (which checks distance-to-destination) always
            # sees distance = 0 and never blocks combat while standing still.
            for account, options in GLOBAL_CACHE.ShMem.GetAllActiveAccountHeroAIPairs(sort_results=False):
                try:
                    x = float(account.AgentData.Pos.x)
                    y = float(account.AgentData.Pos.y)
                except Exception:
                    x, y = 0.0, 0.0
                options.IsFlagged = True
                options.FlagPos.x = x
                options.FlagPos.y = y
                options.FlagFacingAngle = 0.0
        # sync_runtime() will push the new state on the next frame.

    def set_combat_enabled(self, enabled: bool) -> None:
        self._enforced_combat = enabled
        # Push immediately so the effect is visible within the same tick.
        self._set_all_heroai_options(combat=enabled)

    def set_looting_enabled(self, enabled: bool) -> None:
        self._enforced_looting = enabled
        self._set_all_heroai_options(looting=enabled)

    def set_forced_state(self, state) -> None:
        pass  # No direct equivalent in HeroAI.

    def set_blessing_enabled(self, enabled: bool) -> None:
        pass  # No direct equivalent in HeroAI.

    def set_custom_target(self, agent_id: int) -> None:
        if agent_id and Agent.IsValid(agent_id):
            Player.ChangeTarget(agent_id)

    # ── Flag management ──────────────────────────────────────────────────

    def set_flag_for_email(
        self, email: str, flag_index: int, x: float, y: float
    ) -> None:
        """Resolve *email* to a HeroAI shared-memory slot and set its flag.

        Resolution strategy:
          1. Use GetHeroAIOptionsFromEmail to find the HeroAI options for the
             account directly via its shared-memory slot index.
          2. Also resolve the account's party position from its AccountData to
             call FlagHero for heroes in the local party.
        """
        # HeroAI shared-memory flag (multibox accounts)
        options = GLOBAL_CACHE.ShMem.GetHeroAIOptionsFromEmail(email)
        if options is not None:
            options.IsFlagged = True
            options.FlagPos.x = float(x)
            options.FlagPos.y = float(y)
            options.FlagFacingAngle = 0.0
        else:
            ConsoleLog(
                self._bot_name,
                f"[HeroAI] set_flag_for_email: '{email}' not found in account data — flag skipped.",
                Py4GW.Console.MessageType.Warning,
            )
            return

        # Native GW hero flag (local party heroes) — resolve party position from account data
        account_data = GLOBAL_CACHE.ShMem.GetAccountDataFromEmail(email)
        if account_data is not None:
            party_pos = int(account_data.AgentPartyData.PartyPosition)
            if party_pos > 0:
                agent_id = GLOBAL_CACHE.Party.Heroes.GetHeroAgentIDByPartyPosition(party_pos)
                if agent_id and Agent.IsValid(agent_id):
                    GLOBAL_CACHE.Party.Heroes.FlagHero(agent_id, x, y)

    def set_flag(self, index: int, x: float, y: float) -> None:
        party_pos = index + 1

        # Native GW hero flag (works for heroes in the local party)
        agent_id = GLOBAL_CACHE.Party.Heroes.GetHeroAgentIDByPartyPosition(party_pos)
        if agent_id and Agent.IsValid(agent_id):
            GLOBAL_CACHE.Party.Heroes.FlagHero(agent_id, x, y)

        # HeroAI shared-memory flag (works for multibox-account followers)
        options = GLOBAL_CACHE.ShMem.GetHeroAIOptionsByPartyNumber(party_pos)
        if options is not None:
            options.IsFlagged = True
            options.FlagPos.x = float(x)
            options.FlagPos.y = float(y)
            options.FlagFacingAngle = 0.0

    def clear_flags(self) -> None:
        GLOBAL_CACHE.Party.Heroes.UnflagAllHeroes()
        for _, options in GLOBAL_CACHE.ShMem.GetAllActiveAccountHeroAIPairs(sort_results=False):
            options.IsFlagged = False
            options.FlagPos.x = 0.0
            options.FlagPos.y = 0.0
            options.AllFlag.x = 0.0
            options.AllFlag.y = 0.0

    def batch_set_flags(
        self, assignments: list[tuple[str, int, float, float]]
    ) -> None:
        self.clear_flags()
        for email, flag_index, x, y in assignments:
            self.set_flag_for_email(email, flag_index, x, y)

    def auto_assign_flag_emails(self) -> None:
        pass  # Not applicable for HeroAI (no email-based flag assignment).

    def update_flag_position_for_email(self, email: str, x: float, y: float) -> None:
        """Move the HeroAI flag for *email* to (x, y).

        HeroAI resolves by party position and ignores the flag_index argument,
        so we delegate directly to set_flag_for_email.
        """
        self.set_flag_for_email(email, 0, x, y)
