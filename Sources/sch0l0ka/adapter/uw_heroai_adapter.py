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
from Py4GWCoreLib import Player, GLOBAL_CACHE, ConsoleLog
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

    # ── Helpers ──────────────────────────────────────────────────────────

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

    # ── Lifecycle ────────────────────────────────────────────────────────

    def setup(self, bot_instance) -> None:
        ConsoleLog(
            self._bot_name,
            "[HeroAI] Adapter setup: HeroAI mode active.",
            Py4GW.Console.MessageType.Info,
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
        for widget_name in (
            "CustomBehaviors",
            "Custom Behavior",
            "Custom Behaviors: Utility AI",
        ):
            bot_instance.States.AddCustomState(
                lambda wn=widget_name: self._broadcast_widget_command(
                    wn, SharedCommandType.DisableWidget, "Broadcasted disable"
                ),
                f"Disable {widget_name} on active accounts",
            )
        bot_instance.States.AddCustomState(
            lambda: self._broadcast_widget_command(
                "HeroAI", SharedCommandType.EnableWidget, "Broadcasted enable"
            ),
            "Enable HeroAI on active accounts",
        )
        bot_instance.States.AddCustomState(
            lambda: self._broadcast_widget_command(
                "Dhuum Helper", SharedCommandType.EnableWidget, "Broadcasted enable"
            ),
            "Enable Dhuum Helper on active accounts",
        )

    def reactivate_for_step(self, bot_instance, step_label: str) -> None:
        # Re-broadcast "Enable HeroAI" so accounts whose widget was reset on map
        # load (entering UW) get re-enabled at the start of each section.
        self._broadcast_widget_command(
            "HeroAI", SharedCommandType.EnableWidget, f"Re-enable for step '{step_label}'"
        )
        # Explicitly restore all combat options in case HeroAI re-initialized with
        # defaults (Following=False, Combat=False, Looting=False) after the map load.
        self._set_all_heroai_options(following=True, combat=True, looting=True)
        ConsoleLog(
            self._bot_name,
            f"[HeroAI] Step '{step_label}' — re-enabled HeroAI and restored combat options.",
            Py4GW.Console.MessageType.Info,
        )

    def sync_runtime(self) -> None:
        self._sync_party_watchdog(self._bot_instance)

    # ── Utility skill toggles (no-ops for HeroAI) ────────────────────────
    # toggle_wait_for_party is inherited from UWCombatAdapter (watchdog-based).

    def toggle_wait_if_aggro(self, enabled: bool) -> None:
        pass

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
        if enabled:
            self._set_all_heroai_options(following=True)
        else:
            # Disable following but keep combat active so heroes still fight in place.
            self._set_all_heroai_options(following=False, combat=True)

    def set_combat_enabled(self, enabled: bool) -> None:
        self._set_all_heroai_options(combat=enabled)

    def set_looting_enabled(self, enabled: bool) -> None:
        self._set_all_heroai_options(looting=enabled)

    def set_forced_state(self, state) -> None:
        pass  # No direct equivalent in HeroAI.

    def set_blessing_enabled(self, enabled: bool) -> None:
        pass  # No direct equivalent in HeroAI.

    def set_custom_target(self, agent_id: int) -> None:
        Player.ChangeTarget(agent_id)

    # ── Flag management ──────────────────────────────────────────────────

    def set_flag_for_email(
        self, email: str, flag_index: int, x: float, y: float
    ) -> None:
        """Resolve *email* to a HeroAI shared-memory slot and set its flag.

        Resolution strategy:
          1. Iterate GetAllAccountData() to find the account whose email
             matches, and derive its 1-based party position from its list index.
          2. Call GetHeroAIOptionsByPartyNumber(party_pos) to obtain the
             HeroAI options struct and apply IsFlagged / FlagPos.
          3. Also call FlagHero for heroes that are in the local party.
        """
        all_accounts = GLOBAL_CACHE.ShMem.GetAllAccountData() or []
        party_pos: int | None = None
        for idx, account in enumerate(all_accounts):
            acct_email = str(getattr(account, "AccountEmail", "") or "").strip()
            if acct_email.lower() == email.lower():
                party_pos = idx + 1  # 1-based
                break

        if party_pos is None:
            ConsoleLog(
                self._bot_name,
                f"[HeroAI] set_flag_for_email: '{email}' not found in account data — flag skipped.",
                Py4GW.Console.MessageType.Warning,
            )
            return

        # HeroAI shared-memory flag (multibox accounts)
        options = GLOBAL_CACHE.ShMem.GetHeroAIOptionsByPartyNumber(party_pos)
        if options is not None:
            options.IsFlagged = True
            options.FlagPos.x = float(x)
            options.FlagPos.y = float(y)
            options.FlagFacingAngle = 0.0

        # Native GW hero flag (local party heroes)
        agent_id = GLOBAL_CACHE.Party.Heroes.GetHeroAgentIDByPartyPosition(party_pos)
        if agent_id:
            GLOBAL_CACHE.Party.Heroes.FlagHero(agent_id, x, y)

    def set_flag(self, index: int, x: float, y: float) -> None:
        party_pos = index + 1

        # Native GW hero flag (works for heroes in the local party)
        agent_id = GLOBAL_CACHE.Party.Heroes.GetHeroAgentIDByPartyPosition(party_pos)
        if agent_id:
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

    def auto_assign_flag_emails(self) -> None:
        pass  # Not applicable for HeroAI (no email-based flag assignment).

    def update_flag_position_for_email(self, email: str, x: float, y: float) -> None:
        """Move the HeroAI flag for *email* to (x, y).

        HeroAI resolves by party position and ignores the flag_index argument,
        so we delegate directly to set_flag_for_email.
        """
        self.set_flag_for_email(email, 0, x, y)
