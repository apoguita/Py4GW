"""
ModularBot â€” Orchestrator that wires Phases into a Botting FSM.

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

from typing import Callable, Dict, List, Optional, Union, Any, Tuple
import re

from Py4GWCoreLib import Botting, Routines, ConsoleLog, Agent, Player

from .phase import Phase


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# Template name â†’ method name mapping
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

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


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# Helpers
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

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


def _is_header_name(value: str) -> bool:
    return value.startswith("[H]")


def _ensure_cb_loot_wait_enabled() -> None:
    """
    Force-enable CB loot wait utility for this runtime.
    """
    try:
        from Sources.oazix.CustomBehaviors.primitives.botting.botting_manager import BottingManager
    except Exception:
        return

    skill_name = "WaitIfPartyMemberNeedsToLootUtility"
    manager = BottingManager()
    changed = False
    for skills in (manager.aggressive_skills, manager.automover_skills):
        for skill in skills:
            if skill.name == skill_name and not skill.enabled:
                skill.enabled = True
                changed = True
    if changed:
        ConsoleLog("ModularBot", f"Enabled {skill_name} for custom behaviors runtime.")


def _modular_cb_skill_reinject_daemon():
    """
    ModularBot-only guard:
    re-inject enabled CB utility skills when CB swaps to a new behavior instance
    (e.g., during outpost/map transitions in multi-step setup flows).
    """
    try:
        from Sources.oazix.CustomBehaviors.primitives.botting.botting_manager import BottingManager
        from Sources.oazix.CustomBehaviors.primitives.custom_behavior_loader import CustomBehaviorLoader
        from Sources.oazix.CustomBehaviors.primitives.parties.custom_behavior_party import CustomBehaviorParty
    except Exception:
        while True:
            yield from Routines.Yield.wait(1000)

    loader = CustomBehaviorLoader()
    manager = BottingManager()
    injected_instance_id: Optional[int] = None

    while True:
        try:
            if loader.custom_combat_behavior is None:
                loader.initialize_custom_behavior_candidate()

            instance = loader.custom_combat_behavior
            if instance is not None:
                current_instance_id = id(instance)
                if injected_instance_id != current_instance_id:
                    skills = (
                        manager.get_enabled_aggressive_skills()
                        if CustomBehaviorParty().get_party_is_combat_enabled()
                        else manager.get_enabled_pacifist_skills()
                    )
                    manager.inject_enabled_skills(skills, instance)
                    injected_instance_id = current_instance_id
                    ConsoleLog(
                        "ModularBot",
                        "Re-injected CB utility skills after behavior refresh.",
                    )
        except Exception:
            pass

        yield from Routines.Yield.wait(250)


def _is_hero_ai_runtime_active(bot: Botting) -> bool:
    """
    Detect HeroAI runtime activity for callback wiring decisions.
    """
    try:
        if bot.Properties.exists("hero_ai") and bool(bot.Properties.IsActive("hero_ai")):
            return True
    except Exception:
        pass

    try:
        from Py4GWCoreLib.py4gwcorelib_src.WidgetManager import get_widget_handler

        return bool(get_widget_handler().is_widget_enabled("HeroAI"))
    except Exception:
        return False


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

        template:               Initial template â€” ``"aggressive"``,
                                ``"pacifist"``, or ``"multibox_aggressive"``.

        use_custom_behaviors:   If ``True``, call
                                ``bot.Templates.Routines.UseCustomBehaviors()``.
        cb_on_death:            Handler for CustomBehaviors
                                ``PLAYER_CRITICAL_DEATH`` event.
        cb_on_stuck:            Handler for CustomBehaviors
                                ``PLAYER_CRITICAL_STUCK`` event.
        cb_on_party_death:      Handler for CustomBehaviors
                                ``PARTY_DEATH`` event.

        on_party_wipe:          Recovery target â€” phase name (``str``) to
                                jump to on party wipe, *or* a callable
                                ``(bot: Botting) -> None`` for custom
                                recovery logic.
        on_death:               Same, for player death.

        background:             ``{name: coroutine_factory}`` â€” managed
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
        main_ui: Optional[Callable[[], None]] = None,
        icon_path: str = "",
        main_child_dimensions: Tuple[int, int] = (350, 275),
        settings_ui: Optional[Callable[[], None]] = None,
        help_ui: Optional[Callable[[], None]] = None,
        **botting_kwargs: Any,
    ) -> None:
        # Defensive: never forward modular-only UI sizing to Botting kwargs.
        botting_kwargs.pop("main_child_dimensions", None)
        # Defensive: icon path is for UI draw_window, not Botting constructor.
        legacy_icon_path = str(botting_kwargs.pop("icon_path", "") or "")
        # â”€â”€ Store config â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
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
        self._main_ui = main_ui
        self._icon_path = icon_path or legacy_icon_path
        self._main_child_dimensions = main_child_dimensions
        self._settings_ui = settings_ui
        self._help_ui = help_ui

        # â”€â”€ Phase header name tracking â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        self._phase_headers: Dict[str, str] = {}
        self._header_to_phase: Dict[str, str] = {}
        self._runtime_anchor_header: Optional[str] = None

        # â”€â”€ Create Botting instance â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        self._bot = Botting(_sanitize_bot_name(name), **botting_kwargs)
        setattr(self._bot, "_modular_owner", self)
        self._bot.SetMainRoutine(lambda bot: self._build_routine(bot))

        # â”€â”€ Apply GUI overrides â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        if self._settings_ui is not None:
            self._bot.UI.override_draw_config(self._settings_ui)
        if self._help_ui is not None:
            self._bot.UI.override_draw_help(self._help_ui)

    # â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    # Public API
    # â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

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
        self._bot.UI.draw_window(
            main_child_dimensions=self._main_child_dimensions,
            icon_path=self._icon_path,
            additional_ui=self._main_ui,
        )

    def get_phase_header(self, phase_name: str) -> Optional[str]:
        """
        Return the FSM header name for a phase, or ``None`` if not
        registered yet.  Useful for manual ``JumpToStepName`` calls.
        """
        return self._phase_headers.get(phase_name)

    def set_anchor(self, phase_or_header: str) -> bool:
        """
        Set runtime recovery anchor by phase name or internal header name.
        """
        value = str(phase_or_header or "").strip()
        if not value:
            return False

        if _is_header_name(value):
            header = value
            phase_name = self._header_to_phase.get(header, header)
        else:
            header = self._phase_headers.get(value)
            phase_name = value
            if header is None:
                value_l = value.lower()
                for known_phase, known_header in self._phase_headers.items():
                    kp = known_phase.lower()
                    if value_l == kp or value_l in kp or kp in value_l:
                        header = known_header
                        phase_name = known_phase
                        break

        if not header:
            ConsoleLog("ModularBot", f"Set anchor failed: {value!r} not found.")
            return False

        self._set_runtime_anchor(header, phase_name)
        return True

    # â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    # Routine builder (called once by Botting.Update on first frame)
    # â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    def _build_routine(self, bot: Botting) -> None:
        """
        Wires everything together.  Called automatically by
        ``Botting.Update()`` on the first frame.
        """
        if self._use_cb:
            _ensure_cb_loot_wait_enabled()

        # â”€â”€ 1. Template â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        _apply_template(bot, self._template)

        # â”€â”€ 2. CustomBehaviors â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        if self._use_cb:
            bot.Templates.Routines.UseCustomBehaviors(
                on_player_critical_death=self._cb_on_death,
                on_player_critical_stuck=self._cb_on_stuck,
                on_party_death=self._cb_on_party_death,
            )
            bot.States.AddManagedCoroutine(
                "ModularBot_CBSkillReinjectDaemon",
                _modular_cb_skill_reinject_daemon,
            )

        # Keep party cohesion in external engine modes (CB + HeroAI):
        # wait/recover if members are behind, in danger, or dead-behind.
        if self._use_cb or _is_hero_ai_runtime_active(bot):
            bot.Events.OnPartyMemberBehindCallback(
                lambda: bot.Templates.Routines.OnPartyMemberBehind()
            )
            bot.Events.OnPartyMemberInDangerCallback(
                lambda: bot.Templates.Routines.OnPartyMemberInDanger()
            )
            bot.Events.OnPartyMemberDeadBehindCallback(
                lambda: bot.Templates.Routines.OnPartyMemberDeathBehind()
            )

        # â”€â”€ 3. Event callbacks â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        if self._on_party_wipe is not None:
            bot.Events.OnPartyWipeCallback(
                lambda: self._handle_recovery(bot, self._on_party_wipe, "Party wipe")
            )
        if self._on_death is not None:
            bot.Events.OnDeathCallback(
                lambda: self._handle_recovery(bot, self._on_death, "Player death")
            )

        # â”€â”€ 4. Register phases â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        total_phases = len(self._phases)
        for phase_index, phase in enumerate(self._phases):
            self._register_phase(bot, phase, phase_index, total_phases)

        # â”€â”€ 5. Loop â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
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

        # â”€â”€ 6. Background coroutines â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        for coroutine_name, coroutine_factory in self._background.items():
            bot.States.AddManagedCoroutine(coroutine_name, coroutine_factory)

    # â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    # Phase registration
    # â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    def _register_phase(self, bot: Botting, phase: Phase, phase_index: int, total_phases: int) -> None:
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
        self._header_to_phase[header_name] = phase.name

        # Optional template switch at phase start
        if phase.template is not None:
            # Capture template name in closure
            tmpl = phase.template

            def _switch_template(_t=tmpl):
                _apply_template(bot, _t)

            bot.States.AddCustomState(_switch_template, f"Set {tmpl}")

        def _set_phase_anchor(h=header_name, n=phase.name):
            self._set_runtime_anchor(h, n)

        def _set_phase_progress(i=phase_index + 1, total=total_phases, name=phase.name):
            setattr(bot.config, "modular_phase_index", i)
            setattr(bot.config, "modular_phase_total", total)
            setattr(bot.config, "modular_phase_title", name)

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
                        _set_phase_progress()
                        if p.anchor:
                            _set_phase_anchor()
                        p.fn(b)

                return _check_and_run

            bot.States.AddCustomState(
                _make_conditional(phase, bot),
                f"[Check] {phase.name}",
            )
        else:
            bot.States.AddCustomState(_set_phase_progress, f"Set Phase Progress {phase.name}")
            if phase.anchor:
                bot.States.AddCustomState(_set_phase_anchor, f"Set Anchor {phase.name}")
            # Unconditional: register states at build time
            phase.fn(bot)

    def _set_runtime_anchor(self, header_name: str, phase_name: str) -> None:
        self._runtime_anchor_header = header_name
        ConsoleLog("ModularBot", f"Anchor set: {phase_name} ({header_name})")

    # â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    # Recovery handling
    # â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    def _handle_recovery(
        self,
        bot: Botting,
        target: Union[str, Callable],
        reason: str,
    ) -> None:
        """
        Handle a recovery event (wipe / death).

        If *target* is a string, it is treated as a phase name â€” the FSM
        is paused, a managed coroutine waits for the player to revive,
        then jumps to that phase's header.

        If *target* is a callable, it is invoked directly (it should
        handle FSM pause/resume itself).
        """
        if callable(target) and not isinstance(target, str):
            # Custom handler â€” user manages FSM lifecycle
            target()
            return

        # String target â†’ auto-recovery to named phase
        header, target_label = self._resolve_recovery_target(target)
        if header is None:
            ConsoleLog(
                "ModularBot",
                f"Recovery target not found (anchor={self._runtime_anchor_header!r}, target={target!r}). "
                f"Available: {list(self._phase_headers.keys())}",
            )
            return

        fsm = bot.config.FSM
        fsm.pause()

        def _recovery_coroutine():
            ConsoleLog("ModularBot", f"[{reason}] Recovery started â€” target: {target_label}")

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
                    ConsoleLog("ModularBot", f"[{reason}] Returned to outpost â€” restarting")
                    yield from Routines.Yield.wait(3000)
                    break

                yield from Routines.Yield.wait(1000)

            ConsoleLog("ModularBot", f"[{reason}] Recovered â€” jumping to {target_label}")
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

    def _resolve_recovery_target(self, target: Union[str, Callable]) -> Tuple[Optional[str], str]:
        """Resolve recovery destination with anchor-first fallback."""
        if self._runtime_anchor_header:
            anchor_header = self._runtime_anchor_header
            anchor_phase = self._header_to_phase.get(anchor_header, anchor_header)
            try:
                if self._bot.config.FSM.has_state(anchor_header):
                    return anchor_header, f"anchor:{anchor_phase}"
            except Exception:
                pass

        phase_name = str(target or "").strip()
        if not phase_name:
            return None, "<none>"

        header = self._phase_headers.get(phase_name)
        if header is None:
            return None, phase_name
        return header, phase_name

