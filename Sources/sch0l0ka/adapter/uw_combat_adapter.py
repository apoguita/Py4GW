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


