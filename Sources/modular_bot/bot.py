"""
ModularBot — Orchestrator that wires Phases into a Botting FSM.

Handles all the boilerplate every bot repeats:
- Template application
- CustomBehaviors setup
- Event-driven recovery (wipe / death / stuck)
- Phase header tracking & automatic looping
- Background coroutines
- Custom GUI panels

Usage:
    from modular_bot import ModularBot, Phase

    bot = ModularBot(
        name="My Farm",
        phases=[
            Phase("Travel", travel_fn),
            Phase("Farm",   farm_fn),
            Phase("Resign", resign_fn),
        ],
        loop=True,
        template="multibox_aggressive",
        use_custom_behaviors=True,
        on_party_wipe="Travel",
    )

    def main():
        bot.update()
"""

from __future__ import annotations

from typing import Callable, Dict, List, Optional, Union, Any
import re

from Py4GWCoreLib import Botting, Routines, ConsoleLog, Agent, Player

from .phase import Phase


# ──────────────────────────────────────────────────────────────────────────────
# Template name → method name mapping
# ──────────────────────────────────────────────────────────────────────────────

_TEMPLATE_MAP: Dict[str, str] = {
    "aggressive":            "Aggressive",
    "pacifist":              "Pacifist",
    "multibox_aggressive":   "Multibox_Aggressive",
}


def _sanitize_bot_name(name: str) -> str:
    """
    Return a filesystem-safe bot name for settings/INI paths on Windows.
    """
    safe = re.sub(r'[<>:"/\\|?*]+', "_", name).strip(" .")
    return safe or "Bot"


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def _apply_template(bot: Botting, template_name: str) -> None:
    """Apply a named template to the bot."""
    method_name = _TEMPLATE_MAP.get(template_name)
    if method_name is None:
        raise ValueError(
            f"Unknown template {template_name!r}. "
            f"Choose from: {list(_TEMPLATE_MAP.keys())}"
        )
    getattr(bot.Templates, method_name)()


def _predict_next_header_name(bot: Botting, phase_name: str) -> str:
    """
    Predict the FSM header name that ``bot.States.AddHeader(phase_name)``
    will create, WITHOUT actually adding the header.

    Headers are named ``[H]{name}_{counter}`` where counter comes from
    ``bot.config.counters.next_index("HEADER_COUNTER")``.
    We peek at the current value and add 1.
    """
    current = bot.config.counters.get_index("HEADER_COUNTER")
    return f"[H]{phase_name}_{current + 1}"


# ──────────────────────────────────────────────────────────────────────────────
# ModularBot
# ──────────────────────────────────────────────────────────────────────────────

class ModularBot:
    """
    A bot composed of :class:`Phase` objects, built on top of
    :class:`Botting`.

    All ``**botting_kwargs`` are forwarded verbatim to the ``Botting``
    constructor (upkeep flags, config flags, etc.).

    Args:
        name:                   Bot / window title.
        phases:                 Ordered list of :class:`Phase` objects.

        loop:                   If ``True``, jump back to *loop_to* after the
                                last phase completes.
        loop_to:                Phase name to loop to (default: first phase).

        template:               Initial template — ``"aggressive"``,
                                ``"pacifist"``, or ``"multibox_aggressive"``.

        use_custom_behaviors:   If ``True``, call
                                ``bot.Templates.Routines.UseCustomBehaviors()``.
        cb_on_death:            Handler for CustomBehaviors
                                ``PLAYER_CRITICAL_DEATH`` event.
        cb_on_stuck:            Handler for CustomBehaviors
                                ``PLAYER_CRITICAL_STUCK`` event.
        cb_on_party_death:      Handler for CustomBehaviors
                                ``PARTY_DEATH`` event.

        on_party_wipe:          Recovery target — phase name (``str``) to
                                jump to on party wipe, *or* a callable
                                ``(bot: Botting) -> None`` for custom
                                recovery logic.
        on_death:               Same, for player death.

        background:             ``{name: coroutine_factory}`` — managed
                                coroutines that run alongside the FSM.

        settings_ui:            Callable rendered in the Settings tab.
        help_ui:                Callable rendered in the Help tab.

        **botting_kwargs:       Forwarded to ``Botting()``.
    """

    def __init__(
        self,
        name: str,
        phases: List[Phase],
        *,
        loop: bool = True,
        loop_to: Optional[str] = None,
        template: str = "aggressive",
        use_custom_behaviors: bool = False,
        cb_on_death: Optional[Callable] = None,
        cb_on_stuck: Optional[Callable] = None,
        cb_on_party_death: Optional[Callable] = None,
        on_party_wipe: Optional[Union[str, Callable]] = None,
        on_death: Optional[Union[str, Callable]] = None,
        background: Optional[Dict[str, Callable]] = None,
        settings_ui: Optional[Callable[[], None]] = None,
        help_ui: Optional[Callable[[], None]] = None,
        **botting_kwargs: Any,
    ) -> None:
        # ── Store config ──────────────────────────────────────────────
        self._name = name
        self._phases = phases
        self._loop = loop
        self._loop_to = loop_to
        self._template = template
        self._use_cb = use_custom_behaviors
        self._cb_on_death = cb_on_death
        self._cb_on_stuck = cb_on_stuck
        self._cb_on_party_death = cb_on_party_death
        self._on_party_wipe = on_party_wipe
        self._on_death = on_death
        self._background = background or {}
        self._settings_ui = settings_ui
        self._help_ui = help_ui

        # ── Phase header name tracking ────────────────────────────────
        self._phase_headers: Dict[str, str] = {}

        # ── Create Botting instance ───────────────────────────────────
        self._bot = Botting(_sanitize_bot_name(name), **botting_kwargs)
        self._bot.SetMainRoutine(lambda bot: self._build_routine(bot))

        # ── Apply GUI overrides ───────────────────────────────────────
        if self._settings_ui is not None:
            self._bot.UI.override_draw_config(self._settings_ui)
        if self._help_ui is not None:
            self._bot.UI.override_draw_help(self._help_ui)

    # ──────────────────────────────────────────────────────────────────
    # Public API
    # ──────────────────────────────────────────────────────────────────

    @property
    def bot(self) -> Botting:
        """Direct access to the underlying ``Botting`` instance."""
        return self._bot

    def update(self) -> None:
        """
        Call this from your script's ``main()`` function every frame.

        Handles map validation, FSM ticking, and UI rendering.
        """
        self._bot.Update()
        self._bot.UI.draw_window()

    def get_phase_header(self, phase_name: str) -> Optional[str]:
        """
        Return the FSM header name for a phase, or ``None`` if not
        registered yet.  Useful for manual ``JumpToStepName`` calls.
        """
        return self._phase_headers.get(phase_name)

    # ──────────────────────────────────────────────────────────────────
    # Routine builder (called once by Botting.Update on first frame)
    # ──────────────────────────────────────────────────────────────────

    def _build_routine(self, bot: Botting) -> None:
        """
        Wires everything together.  Called automatically by
        ``Botting.Update()`` on the first frame.
        """
        # ── 1. Template ───────────────────────────────────────────────
        _apply_template(bot, self._template)

        # ── 2. CustomBehaviors ────────────────────────────────────────
        if self._use_cb:
            bot.Templates.Routines.UseCustomBehaviors(
                on_player_critical_death=self._cb_on_death,
                on_player_critical_stuck=self._cb_on_stuck,
                on_party_death=self._cb_on_party_death,
            )

        # ── 3. Event callbacks ────────────────────────────────────────
        if self._on_party_wipe is not None:
            bot.Events.OnPartyWipeCallback(
                lambda: self._handle_recovery(bot, self._on_party_wipe, "Party wipe")
            )
        if self._on_death is not None:
            bot.Events.OnDeathCallback(
                lambda: self._handle_recovery(bot, self._on_death, "Player death")
            )

        # ── 4. Register phases ────────────────────────────────────────
        for phase in self._phases:
            self._register_phase(bot, phase)

        # ── 5. Loop ───────────────────────────────────────────────────
        if self._loop and self._phases:
            target_name = self._loop_to or self._phases[0].name
            target_header = self._phase_headers.get(target_name)
            if target_header:
                bot.States.JumpToStepName(target_header)
            else:
                ConsoleLog(
                    "ModularBot",
                    f"Loop target phase {target_name!r} not found! "
                    f"Available: {list(self._phase_headers.keys())}",
                )

        # ── 6. Background coroutines ──────────────────────────────────
        for coroutine_name, coroutine_factory in self._background.items():
            bot.States.AddManagedCoroutine(coroutine_name, coroutine_factory)

    # ──────────────────────────────────────────────────────────────────
    # Phase registration
    # ──────────────────────────────────────────────────────────────────

    def _register_phase(self, bot: Botting, phase: Phase) -> None:
        """
        Register a single phase on the bot's FSM.

        - Adds a header and tracks the generated name.
        - If the phase has a ``template``, inserts a template-switch state.
        - If the phase has a ``condition``, wraps execution in a runtime
          check (the *_enqueue_section* pattern from UW).
        - Otherwise, calls ``phase.fn(bot)`` at build time to register
          states directly.
        """
        # Track header name before AddHeader increments the counter
        header_name = _predict_next_header_name(bot, phase.name)
        bot.States.AddHeader(phase.name)
        self._phase_headers[phase.name] = header_name

        # Optional template switch at phase start
        if phase.template is not None:
            # Capture template name in closure
            tmpl = phase.template

            def _switch_template(_t=tmpl):
                _apply_template(bot, _t)

            bot.States.AddCustomState(_switch_template, f"Set {tmpl}")

        # Register phase states
        if phase.condition is not None:
            # Conditional: defer state registration to runtime.
            # At runtime the FSM executes the check state; if condition()
            # returns True, phase.fn(bot) is called which appends its
            # states to the FSM.  If False, nothing happens (phase skipped).
            #
            # NOTE: This follows the exact same pattern used by UW's
            # _enqueue_section.  Conditional phases should be placed after
            # all unconditional phases to preserve execution order.
            def _make_conditional(p: Phase, b: Botting):
                def _check_and_run():
                    if p.condition():
                        p.fn(b)

                return _check_and_run

            bot.States.AddCustomState(
                _make_conditional(phase, bot),
                f"[Check] {phase.name}",
            )
        else:
            # Unconditional: register states at build time
            phase.fn(bot)

    # ──────────────────────────────────────────────────────────────────
    # Recovery handling
    # ──────────────────────────────────────────────────────────────────

    def _handle_recovery(
        self,
        bot: Botting,
        target: Union[str, Callable],
        reason: str,
    ) -> None:
        """
        Handle a recovery event (wipe / death).

        If *target* is a string, it is treated as a phase name — the FSM
        is paused, a managed coroutine waits for the player to revive,
        then jumps to that phase's header.

        If *target* is a callable, it is invoked directly (it should
        handle FSM pause/resume itself).
        """
        if callable(target) and not isinstance(target, str):
            # Custom handler — user manages FSM lifecycle
            target()
            return

        # String target → auto-recovery to named phase
        phase_name = str(target)
        header = self._phase_headers.get(phase_name)
        if header is None:
            ConsoleLog(
                "ModularBot",
                f"Recovery target phase {phase_name!r} not found! "
                f"Available: {list(self._phase_headers.keys())}",
            )
            return

        fsm = bot.config.FSM
        fsm.pause()

        def _recovery_coroutine():
            ConsoleLog("ModularBot", f"[{reason}] Recovery started — target: {phase_name}")

            # Wait for player to be alive (or map to change to outpost)
            while True:
                try:
                    player_id = Player.GetAgentID()
                    if not Agent.IsDead(player_id):
                        break
                except Exception:
                    pass

                # If we got kicked back to outpost, just restart
                if not Routines.Checks.Map.MapValid():
                    ConsoleLog("ModularBot", f"[{reason}] Returned to outpost — restarting")
                    yield from Routines.Yield.wait(3000)
                    break

                yield from Routines.Yield.wait(1000)

            ConsoleLog("ModularBot", f"[{reason}] Recovered — jumping to {phase_name}")
            yield from Routines.Yield.wait(1000)

            try:
                fsm.jump_to_state_by_name(header)
            except (ValueError, KeyError):
                ConsoleLog(
                    "ModularBot",
                    f"[{reason}] Header {header!r} not found, restarting from step 0",
                )
                fsm.jump_to_state_by_step_number(0)
            finally:
                fsm.resume()

        coroutine_name = f"ModularBot_Recovery_{reason.replace(' ', '_')}"
        fsm.AddManagedCoroutine(coroutine_name, _recovery_coroutine)

