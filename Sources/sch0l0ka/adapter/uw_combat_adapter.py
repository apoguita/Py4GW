# ╔══════════════════════════════════════════════════════════════════════════════
# ║  File    : uw_combat_adapter.py
# ║  Purpose : Abstract base class for the Underworld bot's combat-system
# ║            integration.  Concrete subclasses implement every abstract
# ║            method so quest-section code never touches the combat system
# ║            directly.  Also provides the shared party-distance watchdog
# ║            and dead-ally rescue coroutines used by both adapters.
# ╚══════════════════════════════════════════════════════════════════════════════

import time
from abc import ABC, abstractmethod
from Py4GWCoreLib import Agent, Player, ConsoleLog, Routines, Utils, GLOBAL_CACHE
import Py4GW


class UWCombatAdapter(ABC):
    """Abstract interface for the UW bot's combat-system integration.

    Concrete implementations swap between CustomBehavior and HeroAI without
    changing any quest-section code in UnderworldCB.py.
    """

    # ── Event callback configuration ────────────────────────────────────
    # All 3 party-event callbacks use bot_instance.Events.*Callback — the
    # framework event coroutines are re-registered every frame via _start_coroutines(),
    # so they survive FSM.start() / FSM.stop() which call _cleanup_coroutines().
    # Each concrete setup() must register:
    #   OnPartyMemberBehindCallback(lambda: self._on_party_behind_callback(bot_instance))
    #   OnPartyMemberInDangerCallback(lambda: bot_instance.Templates.Routines.OnPartyMemberInDanger())
    #   OnPartyMemberDeadBehindCallback(lambda: self._on_dead_behind_callback(bot_instance))
    _WAIT_FOR_PARTY_MAX_DISTANCE: float = 2500.0
    _WATCHDOG_INTERVAL_S: float = 1.0
    _WATCHDOG_HEARTBEAT_S: float = 10.0
    _wait_for_party_enabled: bool = True   # instance-overridden by toggle_wait_for_party
    _dead_ally_rescue_enabled: bool = True  # instance-overridden by toggle_dead_ally_rescue
    _bot_name: str = "UWAdapter"            # overridden by each concrete __init__
    _bot_instance = None                    # set in setup()
    _last_watchdog_check: float = 0.0      # instance-level timer for _sync_party_watchdog
    _last_heartbeat: float = 0.0           # instance-level timer for diagnostic heartbeat

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
        """Enable or disable the shared party-distance watchdog.

        When disabled the FSM is never paused for out-of-range allies.
        The _on_party_behind_callback callback reads this flag.
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

    # ── Party-distance watchdog (shared by CB and HeroAI) ────────────────

    def _log_lagging_party_members(self, player_pos, range_value: float) -> None:
        """Log every living party member that is currently beyond *range_value*."""
        def _check(members, get_id, label):
            for m in members:
                agent_id = get_id(m)
                if not Agent.IsValid(agent_id) or Agent.IsDead(agent_id):
                    continue
                dist = Utils.Distance(player_pos, Agent.GetXY(agent_id))
                if dist > range_value:
                    name = Agent.GetNameByID(agent_id) or f"ID:{agent_id}"
                    print(
                        f"[{self._bot_name}][Watchdog] {label} '{name}' too far: {dist:.0f} > {range_value:.0f}"
                    )

        _check(
            GLOBAL_CACHE.Party.GetPlayers(),
            lambda p: GLOBAL_CACHE.Party.Players.GetAgentIDByLoginNumber(p.login_number),
            "Player",
        )
        _check(GLOBAL_CACHE.Party.GetHeroes(), lambda h: h.agent_id, "Hero")
        _check(GLOBAL_CACHE.Party.GetHenchmen(), lambda h: h.agent_id, "Henchman")

    def _dump_party_distances(self, player_pos) -> None:
        """Print distances to all living party members (for heartbeat diagnostics)."""
        lines = []

        def _collect(members, get_id, label):
            for m in members:
                agent_id = get_id(m)
                valid = Agent.IsValid(agent_id)
                dead = Agent.IsDead(agent_id) if valid else True
                dist = Utils.Distance(player_pos, Agent.GetXY(agent_id)) if valid and not dead else -1
                name = (Agent.GetNameByID(agent_id) or f"ID:{agent_id}") if valid else f"ID:{agent_id}(invalid)"
                status = "dead" if dead else f"{dist:.0f}"
                lines.append(f"  {label} {name}: {status}")

        _collect(
            GLOBAL_CACHE.Party.GetPlayers(),
            lambda p: GLOBAL_CACHE.Party.Players.GetAgentIDByLoginNumber(p.login_number),
            "Player",
        )
        _collect(GLOBAL_CACHE.Party.GetHeroes(), lambda h: h.agent_id, "Hero")
        _collect(GLOBAL_CACHE.Party.GetHenchmen(), lambda h: h.agent_id, "Henchman")

        #if lines:
            #print(f"[{self._bot_name}][Watchdog] Party distances (threshold={int(self._WAIT_FOR_PARTY_MAX_DISTANCE)}):")
            #for line in lines:
                #print(line)
        #else:
            #print(f"[{self._bot_name}][Watchdog] Party: no members detected")

    def _sync_party_watchdog(self, bot_instance) -> None:
        if bot_instance is None:
            print(f"[{self._bot_name}][Watchdog] ERROR: bot_instance is None — setup() may have failed.")
            return
        if not bot_instance.config.fsm_running:
            return

        now = time.monotonic()

        # ── diagnostic heartbeat ──────────────────────────────────────────
        if now - self._last_heartbeat >= self._WATCHDOG_HEARTBEAT_S:
            self._last_heartbeat = now
            # print(
            #     f"[{self._bot_name}][Watchdog] Heartbeat — "
            #     f"wait_enabled={self._wait_for_party_enabled}  "
            #     f"fsm_paused={bot_instance.config.FSM.is_paused()}"
            # )
            self._dump_party_distances(Player.GetXY())

        if not self._wait_for_party_enabled:
            return

        if not Routines.Checks.Map.IsExplorable():
            return

        if now - self._last_watchdog_check < self._WATCHDOG_INTERVAL_S:
            return
        self._last_watchdog_check = now

        is_behind = Routines.Checks.Party.IsPartyMemberBehind(int(self._WAIT_FOR_PARTY_MAX_DISTANCE))
        # print(
        #     f"[{self._bot_name}][Watchdog] IsPartyMemberBehind({int(self._WAIT_FOR_PARTY_MAX_DISTANCE)}) = {is_behind}"
        # )
        if not is_behind:
            return

        self._log_lagging_party_members(Player.GetXY(), self._WAIT_FOR_PARTY_MAX_DISTANCE)
        added = bot_instance.config.FSM.AddManagedCoroutine(
            "UW_WaitForPartyBehind",
            lambda: self._coro_wait_for_party_behind(bot_instance),
        )
        print(f"[{self._bot_name}][Watchdog] AddManagedCoroutine('UW_WaitForPartyBehind') returned {added}")

    def _on_party_behind_callback(self, bot_instance) -> None:
        print(f"[{self._bot_name}][Watchdog] OnPartyMemberBehind event fired (Spirit range).")
        if not self._wait_for_party_enabled:
            return
        self._log_lagging_party_members(Player.GetXY(), self._WAIT_FOR_PARTY_MAX_DISTANCE)
        bot_instance.config.FSM.AddManagedCoroutine(
            "UW_WaitForPartyBehind",
            lambda: self._coro_wait_for_party_behind(bot_instance),
        )

    def _coro_wait_for_party_behind(self, bot_instance):
        """Block FSM progression until no party member is beyond _WAIT_FOR_PARTY_MAX_DISTANCE.

        Calls fsm.pause() on every frame.  Because this coroutine is registered
        after the CB botting daemon, it runs later in the managed_coroutines list
        during each FSM update() call.  The daemon may call fsm.resume() first, but
        our subsequent pause() overwrites that — keeping the FSM paused for the whole
        frame.  The FSM state machine only advances after all managed coroutines have
        run for that frame, so our last-in-order pause() wins reliably.
        """
        fsm = bot_instance.config.FSM
        last_pixel_stack = time.monotonic()

        try:
            # Emit initial pixel stack to call followers back
            # print(f"[{self._bot_name}][Watchdog] Party wait STARTED — emitting pixel stack.")
            yield from bot_instance.helpers.Multibox._pixel_stack()

            while True:
                # Re-pause every frame to outlast the CB daemon's periodic resume()
                fsm.pause()

                # If WaitIfPartyMemberTooFar was disabled while this coroutine
                # was already running (e.g. Imprisoned Spirits flags section),
                # exit cleanly so fsm.resume() is called via the finally block.
                if not self._wait_for_party_enabled:
                    return

                if GLOBAL_CACHE.Party.IsPartyDefeated() or Routines.Checks.Party.IsPartyWiped():
                    # print(f"[{self._bot_name}][Watchdog] Party wiped/defeated — aborting party wait.")
                    return

                if not Routines.Checks.Party.IsPartyMemberBehind(int(self._WAIT_FOR_PARTY_MAX_DISTANCE)):
                    # print(f"[{self._bot_name}][Watchdog] All party members back in range — resuming.")
                    return

                now = time.monotonic()
                if now - last_pixel_stack >= 10.0:
                    # print(f"[{self._bot_name}][Watchdog] Re-emitting pixel stack.")
                    yield from bot_instance.helpers.Multibox._pixel_stack()
                    last_pixel_stack = now

                yield

        finally:
            # print(f"[{self._bot_name}][Watchdog] Party wait coroutine ending — calling fsm.resume().")
            fsm.resume()
            yield

    def _on_dead_behind_callback(self, bot_instance) -> None:
        if not self._dead_ally_rescue_enabled:
            return
        bot_instance.config.FSM.AddManagedCoroutine(
            "UW_RescueDeadAlly",
            lambda: self._coro_rescue_dead_ally(bot_instance),
        )

    def _coro_rescue_dead_ally(self, bot_instance):
        """Move to the nearest dead party member while keeping FSM paused every frame.

        Uses the same per-frame fsm.pause() strategy as _coro_wait_for_party_behind
        to reliably outlast the CB daemon's periodic resume().
        """
        fsm = bot_instance.config.FSM

        def _step(gen) -> bool:
            """Advance a generator by one frame; return False when exhausted."""
            try:
                next(gen)
                return True
            except StopIteration:
                return False

        try:
            if Routines.Checks.Party.IsPartyWiped() or GLOBAL_CACHE.Party.IsPartyDefeated():
                return

            dead_player = Routines.Party.GetDeadPartyMemberID()
            if dead_player == 0:
                return

            # Wait until out of danger — pause FSM every frame
            while Routines.Checks.Agents.InDanger():
                fsm.pause()
                if Routines.Checks.Party.IsPartyWiped() or GLOBAL_CACHE.Party.IsPartyDefeated():
                    return
                yield

            # Re-check after combat clears
            dead_player = Routines.Party.GetDeadPartyMemberID()
            if dead_player == 0:
                return

            # Move to dead ally — pause FSM every frame
            pos = Agent.GetXY(dead_player)
            exit_cond = lambda: Routines.Checks.Party.IsPartyWiped() or GLOBAL_CACHE.Party.IsPartyDefeated()
            follow_gen = Routines.Yield.Movement.FollowPath(
                path_points=[pos],
                custom_exit_condition=exit_cond,
                tolerance=10,
                timeout=30000,
            )
            while True:
                fsm.pause()
                if not _step(follow_gen):
                    break
                yield

            # Emit pixel stack to call followers back
            pixel_gen = bot_instance.helpers.Multibox._pixel_stack()
            while True:
                fsm.pause()
                if not _step(pixel_gen):
                    break
                yield

        finally:
            fsm.resume()
            yield
