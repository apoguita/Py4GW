# ╔══════════════════════════════════════════════════════════════════════════════
# ║  File    : uw_combat_adapter.py
# ║  Purpose : Abstract base class for the Underworld bot's combat-system
# ║            integration.  Concrete subclasses implement every abstract
# ║            method so quest-section code never touches the combat system
# ║            directly.  Party-behind and dead-ally events are handled by
# ║            the framework's Templates.Routines callbacks.
# ╚══════════════════════════════════════════════════════════════════════════════

from abc import ABC, abstractmethod
import Py4GW
from Py4GWCoreLib import ConsoleLog


class UWCombatAdapter(ABC):
    """Abstract interface for the UW bot's combat-system integration.

    Concrete implementations swap between CustomBehavior and HeroAI without
    changing any quest-section code in underworld.py.
    """

    # ── Event callback configuration ────────────────────────────────────
    # All 3 party-event callbacks use bot_instance.Events.*Callback — the
    # framework event coroutines are re-registered every frame via _start_coroutines(),
    # so they survive FSM.start() / FSM.stop() which call _cleanup_coroutines().
    # Each concrete setup() must register:
    #   OnPartyMemberBehindCallback(lambda: bot_instance.Templates.Routines.OnPartyMemberBehind() if self._wait_for_party_enabled else None)
    #   OnPartyMemberInDangerCallback(lambda: bot_instance.Templates.Routines.OnPartyMemberInDanger())
    #   OnPartyMemberDeadBehindCallback(lambda: bot_instance.Templates.Routines.OnPartyMemberDeathBehind() if self._dead_ally_rescue_enabled else None)
    _WAIT_FOR_PARTY_MAX_DISTANCE: float = 2500.0
    _wait_for_party_enabled: bool = True   # instance-overridden by toggle_wait_for_party
    _dead_ally_rescue_enabled: bool = True  # instance-overridden by toggle_dead_ally_rescue
    _bot_name: str = "UWAdapter"            # overridden by each concrete __init__
    _bot_instance = None                    # set in setup()

    # ── Lifecycle ────────────────────────────────────────────────────────

    @abstractmethod
    def setup(self, bot_instance) -> None:
        """Called once from bot_routine before the FSM starts."""
        ...

    @abstractmethod
    def configure_startup_states(self, bot_instance) -> None:
        """Enqueue FSM states that enable/disable widgets at run start."""
        ...

    @abstractmethod
    def reactivate_for_step(self, bot_instance, step_label: str) -> None:
        """Re-initialize combat integration at the start of each quest section."""
        ...

    @abstractmethod
    def sync_runtime(self) -> None:
        """Called every frame while the FSM is running (heartbeat)."""
        ...

    # ── Utility skill toggles ────────────────────────────────────────────

    @abstractmethod
    def toggle_wait_if_aggro(self, enabled: bool) -> None: ...

    def toggle_wait_for_party(self, enabled: bool) -> None:
        """Enable or disable the party-behind handler.

        When disabled the OnPartyMemberBehind event callback is a no-op.
        """
        self._wait_for_party_enabled = enabled

    def toggle_dead_ally_rescue(self, enabled: bool) -> None:
        """Enable or disable the dead-ally event handler.

        When disabled the OnPartyMemberDeadBehind event is ignored.
        The _on_dead_behind_callback reads this flag.
        """
        self._dead_ally_rescue_enabled = enabled

    def toggle_move_to_party_member_if_dead(self, enabled: bool) -> None:
        self.toggle_dead_ally_rescue(enabled)

    _in_danger_enabled: bool = True  # instance-overridden by toggle_in_danger_callback

    def toggle_in_danger_callback(self, enabled: bool) -> None:
        """Enable or disable the OnPartyMemberInDanger event callback.

        Disable during scripted fight phases (e.g. Dhuum) where the CB daemon
        would immediately stomp any fsm.pause() the coroutine sets.
        """
        self._in_danger_enabled = enabled

    # ── Custom party-behind handler ──────────────────────────────────────

    def _is_any_party_account_behind(self) -> bool:
        """Check if any active same-party account is beyond _WAIT_FOR_PARTY_MAX_DISTANCE.

        Uses shared memory so agents beyond compass range are still detected.
        Falls back to the framework check if shared memory is unavailable.
        """
        from Py4GWCoreLib import Agent, GLOBAL_CACHE, Player, Routines
        from Py4GWCoreLib.Py4GWcorelib import Utils

        self_email = Player.GetAccountEmail()
        self_account = GLOBAL_CACHE.ShMem.GetAccountDataFromEmail(self_email)
        if self_account is None:
            return Routines.Checks.Party.IsPartyMemberBehind()

        me_x, me_y = Player.GetXY()
        for account in (GLOBAL_CACHE.ShMem.GetAllAccountData() or []):
            if not account.IsSlotActive or account.IsIsolated:
                continue
            if account.AccountEmail == self_email:
                continue
            if int(self_account.AgentPartyData.PartyID) != int(account.AgentPartyData.PartyID):
                continue
            if int(self_account.AgentData.Map.MapID) != int(account.AgentData.Map.MapID):
                continue
            if int(self_account.AgentData.Map.Region) != int(account.AgentData.Map.Region):
                continue
            if int(self_account.AgentData.Map.District) != int(account.AgentData.Map.District):
                continue
            ax = float(account.AgentData.Pos.x or 0)
            ay = float(account.AgentData.Pos.y or 0)
            if ax == 0 and ay == 0:
                continue
            dist = Utils.Distance((me_x, me_y), (ax, ay))
            if dist > self._WAIT_FOR_PARTY_MAX_DISTANCE:
                return True

        return False

    def on_party_member_behind(self, bot_instance) -> None:
        """Custom OnPartyMemberBehind handler for the UW bot.

        Pauses the FSM, emits pixelstack, and waits until all party accounts
        are back within range.  Uses shared memory for the distance check
        so accounts beyond compass range are not missed.
        """
        if not self._wait_for_party_enabled:
            return
        fsm = bot_instance.config.FSM
        fsm.pause()
        fsm.AddManagedCoroutine(
            "UW_OnBehind",
            self._coro_wait_for_party(bot_instance),
        )

    def _coro_wait_for_party(self, bot_instance):
        """Managed coroutine: stop, pixelstack, wait for party, resume."""
        from Py4GWCoreLib import Routines, GLOBAL_CACHE
        from Py4GWCoreLib.Py4GWcorelib import Utils

        try:
            ConsoleLog(self._bot_name, "Party member behind — stopping and waiting.", Py4GW.Console.MessageType.Info)
            yield from Routines.Yield.Movement.StopMovement()

            emit_count = 0
            last_emit_ts = Utils.GetBaseTimestamp()

            yield from bot_instance.helpers.Multibox._pixel_stack()
            emit_count += 1

            while self._is_any_party_account_behind():
                if not Routines.Checks.Map.MapValid():
                    ConsoleLog(self._bot_name, "Map invalid — aborting wait.", Py4GW.Console.MessageType.Warning)
                    return
                if Routines.Checks.Party.IsPartyWiped() or GLOBAL_CACHE.Party.IsPartyDefeated():
                    ConsoleLog(self._bot_name, "Party wiped — aborting wait.", Py4GW.Console.MessageType.Warning)
                    return

                yield from bot_instance.Wait._coro_for_time(500)

                # Re-emit pixelstack every 10 seconds
                now = Utils.GetBaseTimestamp()
                if now - last_emit_ts >= 10000:
                    yield from bot_instance.helpers.Multibox._pixel_stack()
                    last_emit_ts = now
                    emit_count += 1
                    if emit_count % 2 == 0:
                        yield from bot_instance.helpers.Multibox._brute_force_unstuck()
                    # Re-stop movement in case something else issued a move
                    yield from Routines.Yield.Movement.StopMovement()

            ConsoleLog(self._bot_name, "All party members in range — resuming.", Py4GW.Console.MessageType.Info)

        finally:
            bot_instance.config.FSM.resume()
            yield

    # ── Party control ────────────────────────────────────────────────────

    @abstractmethod
    def set_party_leader(self, email: str) -> None: ...

    @abstractmethod
    def set_following_enabled(self, enabled: bool) -> None: ...

    @abstractmethod
    def set_combat_enabled(self, enabled: bool) -> None: ...

    @abstractmethod
    def set_looting_enabled(self, enabled: bool) -> None: ...

    @abstractmethod
    def set_forced_state(self, state) -> None: ...

    @abstractmethod
    def set_blessing_enabled(self, enabled: bool) -> None: ...

    @abstractmethod
    def set_custom_target(self, agent_id: int) -> None: ...

    # ── Flag management ──────────────────────────────────────────────────

    @abstractmethod
    def set_flag(self, index: int, x: float, y: float) -> None:
        """Set a positional flag for the hero at 0-based slot *index* (CB)
        / party position *index + 1* (native GW)."""
        ...

    @abstractmethod
    def set_flag_for_email(
        self, email: str, flag_index: int, x: float, y: float
    ) -> None:
        """Set a positional flag for the account identified by *email*.

        Used by email-based multibox flag functions (_enqueue_imprisoned_spirits_flags,
        _flag_sacrifice_accounts, _flag_survivor_accounts).  Each adapter resolves
        how to map an email address to the right flag slot or shared-memory entry.
        """
        ...

    @abstractmethod
    def update_flag_position_for_email(self, email: str, x: float, y: float) -> None:
        """Move an already-assigned flag to a new position without changing slot ownership.

        Used by the Spirit Form watchdog to relocate a ghost account's flag to the
        designated ghost position.  Each adapter resolves the flag slot internally
        so callers do not need to know the slot index.
        """
        ...

    @abstractmethod
    def clear_flags(self) -> None: ...

    @abstractmethod
    def auto_assign_flag_emails(self) -> None: ...


