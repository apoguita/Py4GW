"""BT-native ModularBot orchestration."""
from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Tuple, Union
import time
import traceback

from Py4GWCoreLib import Agent, Botting, Console, ConsoleLog, Player, Routines
from Py4GWCoreLib.py4gwcorelib_src.BehaviorTree import BehaviorTree
from .diagnostics import ModularRunDiagnostics
from .phase import Phase
from . import bot_diagnostics_support as _diag_support
from . import bot_recovery_support as _recovery_support
from . import bot_runtime_support as _runtime_support
from .runtime_native import (
    NativeBlockPhaseRunner,
    NativeBlockSpec,
    PendingRecovery,
    extract_native_block_spec,
    is_widget_enabled,
    modular_planner_compiler,
    resolve_botting_tree_ctor,
    sanitize_bot_name,
)

_FAILURE_MODE_SKIP = "skip"
_FAILURE_MODE_FAIL = "fail"
class ModularBot:
    """Coordinate modular phase compilation, runtime execution, and recovery."""
    def __init__(
        self,
        name: str,
        phases: List[Phase],
        *,
        loop: bool = True,
        loop_to: Optional[str] = None,
        template: str = "aggressive",
        on_party_wipe: Optional[Union[str, Callable]] = None,
        on_death: Optional[Union[str, Callable]] = None, background: Optional[Dict[str, Callable]] = None,
        start_coroutines_once: bool = False, main_ui: Optional[Callable[[], None]] = None, icon_path: str = "",
        main_child_dimensions: Tuple[int, int] = (350, 275),
        settings_ui: Optional[Callable[[], None]] = None, help_ui: Optional[Callable[[], None]] = None,
        diagnostics_enabled: bool = False, diagnostics_label: Optional[str] = None,
        debug_logging: bool = False,
        disable_headless_hero_ai_on_init: bool = False, manage_hero_ai_widget: bool = False,
        enforce_local_native_engine: bool = True, **botting_kwargs: Any,
    ) -> None:
        debug_logging = bool(debug_logging or botting_kwargs.get("debug_logging", False))
        botting_kwargs = self._prepare_botting_kwargs(botting_kwargs)
        self._init_core_config(
            name=name, phases=phases, loop=loop, loop_to=loop_to, template=template,
            enforce_local_native_engine=enforce_local_native_engine,
            on_party_wipe=on_party_wipe,
            on_death=on_death,
            background=background,
            start_coroutines_once=start_coroutines_once,
            main_ui=main_ui,
            icon_path=icon_path,
            main_child_dimensions=main_child_dimensions,
            settings_ui=settings_ui,
            help_ui=help_ui,
            diagnostics_enabled=diagnostics_enabled,
            diagnostics_label=diagnostics_label,
            debug_logging=debug_logging,
            disable_headless_hero_ai_on_init=disable_headless_hero_ai_on_init,
            manage_hero_ai_widget=manage_hero_ai_widget,
        )
        self._init_runtime_state()
        self._init_diagnostics_state()
        self._init_bot_instances(name, botting_kwargs)

    def _prepare_botting_kwargs(self, botting_kwargs: dict[str, Any]) -> dict[str, Any]:
        kwargs = dict(botting_kwargs)
        for key in ("main_child_dimensions", "icon_path", "debug_logging", "diagnostics_enabled", "diagnostics_label"):
            kwargs.pop(key, None)
        if "upkeep_hero_ai_active" not in kwargs:
            kwargs["upkeep_hero_ai_active"] = is_widget_enabled("HeroAI")
        return kwargs

    def _init_core_config(
        self,
        *,
        name: str,
        phases: List[Phase],
        loop: bool,
        loop_to: Optional[str],
        template: str,
        enforce_local_native_engine: bool,
        on_party_wipe: Optional[Union[str, Callable]],
        on_death: Optional[Union[str, Callable]],
        background: Optional[Dict[str, Callable]],
        start_coroutines_once: bool,
        main_ui: Optional[Callable[[], None]],
        icon_path: str,
        main_child_dimensions: Tuple[int, int],
        settings_ui: Optional[Callable[[], None]],
        help_ui: Optional[Callable[[], None]],
        diagnostics_enabled: bool,
        diagnostics_label: Optional[str],
        debug_logging: bool,
        disable_headless_hero_ai_on_init: bool,
        manage_hero_ai_widget: bool,
    ) -> None:
        self._name = str(name)
        self._phases = list(phases or [])
        self._loop = bool(loop)
        self._loop_to = loop_to
        self._template = str(template)
        self._enforce_local_native_engine = bool(enforce_local_native_engine)
        self._on_party_wipe = on_party_wipe
        self._on_death = on_death
        self._background = dict(background or {})
        self._start_coroutines_once = bool(start_coroutines_once)
        self._bot_coroutines_started = False
        self._main_ui = main_ui
        self._icon_path = str(icon_path or "")
        self._main_child_dimensions = main_child_dimensions
        self._settings_ui = settings_ui
        self._help_ui = help_ui
        self._debug_logging = bool(debug_logging)
        self._diagnostics_enabled = bool(diagnostics_enabled or debug_logging)
        self._diagnostics_label = str(diagnostics_label or name or "ModularBot")
        self._disable_headless_hero_ai_on_init = bool(disable_headless_hero_ai_on_init)
        self._manage_hero_ai_widget = bool(manage_hero_ai_widget)
        self._failure_mode = _FAILURE_MODE_FAIL

    def _init_runtime_state(self) -> None:
        self._phase_headers: Dict[str, str] = {}
        self._header_to_phase: Dict[str, str] = {}
        self._active_phase_name: Optional[str] = None
        self._phase_restart_state_overrides: Dict[str, str] = {}
        self._runtime_anchor_phase: Optional[str] = None
        self._runtime_anchor_state: str = ""
        self._party_member_hooks_enabled = True
        self._party_hook_state: Optional[tuple[bool, str, bool]] = None
        self._suppress_recovery_until: float = 0.0
        self._suppress_recovery_events_remaining: int = 0
        self._suppress_recovery_until_outpost: bool = False
        self._recovery_active = False
        self._pending_recovery: Optional[PendingRecovery] = None
        self._manual_stop_requested = False
        self._planner_compiled = False
        self._planner_step_names: list[str] = []
        self._loop_target_phase_name: Optional[str] = None
        self._background_generators: Dict[str, Any] = {}

    def _init_diagnostics_state(self) -> None:
        self._diagnostics: Optional[ModularRunDiagnostics] = None
        self._last_run_log_path: Optional[str] = None
        self._last_stall_snapshot: Optional[dict[str, Any]] = None
        self._diag_last_heartbeat_at: float = 0.0
        self._diag_last_progress_at: float = 0.0
        self._diag_last_stall_warning_at: float = 0.0
        self._diag_last_snapshot_key: Optional[tuple[str, int, str, str]] = None

    def _init_bot_instances(self, name: str, botting_kwargs: dict[str, Any]) -> None:
        self._bot = Botting(sanitize_bot_name(name), **botting_kwargs)
        self._bot.Start = self.start
        self._bot.Stop = self.stop
        setattr(self._bot.config, "modular_debug_logging", bool(self._debug_logging))
        if not self._manage_hero_ai_widget:
            try:
                self._bot.config.FSM.RemoveManagedCoroutine("keep_hero_ai")
            except Exception:
                pass
        setattr(self._bot, "_modular_owner", self)
        if self._settings_ui is not None:
            self._bot.UI.override_draw_config(self._settings_ui)
        if self._help_ui is not None:
            self._bot.UI.override_draw_help(self._help_ui)
        self._botting_tree = resolve_botting_tree_ctor()(pause_on_combat=False, isolation_enabled=False)
        if self._disable_headless_hero_ai_on_init:
            try:
                self._botting_tree.DisableHeadlessHeroAI(reset_runtime=True)
            except Exception:
                pass

    def _enforce_native_local_widgets(self) -> None:
        return

    def _suppress_keep_hero_ai_coroutine(self) -> bool:
        try:
            fsm = self._bot.config.FSM
            removed = bool(fsm.RemoveManagedCoroutine("keep_hero_ai"))
            if bool(fsm.HasManagedCoroutine("keep_hero_ai")):
                removed = bool(fsm.RemoveManagedCoroutine("keep_hero_ai")) or removed
            return bool(removed or (not bool(fsm.HasManagedCoroutine("keep_hero_ai"))))
        except Exception as exc:
            ConsoleLog("ModularBot", f"Native leader policy warning: keep_hero_ai suppression failed: {exc}", Console.MessageType.Warning)
            self.record_diagnostics_event(
                "native_policy_warning",
                message=f"keep_hero_ai suppression failed: {exc}",
            )
            return False

    def _enforce_native_headless_off(self) -> bool:
        try:
            if self._botting_tree.IsHeadlessHeroAIEnabled():
                self._botting_tree.DisableHeadlessHeroAI(reset_runtime=False)
            return not bool(self._botting_tree.IsHeadlessHeroAIEnabled())
        except Exception as exc:
            ConsoleLog("ModularBot", f"Native leader policy warning: headless HeroAI enforcement failed: {exc}", Console.MessageType.Warning)
            self.record_diagnostics_event(
                "native_policy_warning",
                message=f"headless HeroAI enforcement failed: {exc}",
            )
            return False

    def _enforce_native_leader_policy_runtime(self) -> None:
        if not self._enforce_local_native_engine:
            return
        self._enforce_native_headless_off()
        self._suppress_keep_hero_ai_coroutine()

    def _log_native_leader_policy_startup(self) -> None:
        if not self._enforce_local_native_engine:
            return
        heroai_widget = bool(is_widget_enabled("HeroAI"))
        headless_ok = self._enforce_native_headless_off()
        keep_ok = self._suppress_keep_hero_ai_coroutine()
        msg = (
            "native_leader_policy: widgets_untouched "
            f"heroai_widget={'on' if heroai_widget else 'off'} "
            f"headless={'off' if headless_ok else 'unknown'} "
            f"keep_hero_ai={'suppressed' if keep_ok else 'unknown'}"
        )
        self._debug_log(msg)
        self.record_diagnostics_event(
            "native_leader_policy",
            message=msg,
            extra={
                "widgets_untouched": True,
                "heroai_widget": bool(heroai_widget),
                "leader_headless_off": bool(headless_ok),
                "keep_hero_ai_suppressed": bool(keep_ok),
            },
        )
        if (not headless_ok) or (not keep_ok):
            ConsoleLog(
                "ModularBot",
                "Native leader policy warning: partial enforcement failure; continuing runtime.",
                Console.MessageType.Warning,
            )

    def _initialize_desired_auto_state_defaults(self) -> dict[str, bool] | None:
        try:
            from Py4GWCoreLib.routines_src.behaviourtrees_src.modular_core.actions_party_toggles import (
                initialize_desired_auto_state_defaults,
            )

            return initialize_desired_auto_state_defaults(
                self._bot,
                combat=True,
                looting=True,
                following=True,
            )
        except Exception:
            return None

    def _apply_desired_auto_state_defaults(self, *, reason: str = "startup") -> dict[str, dict] | None:
        try:
            from Py4GWCoreLib.routines_src.behaviourtrees_src.modular_core.actions_party_toggles import (
                apply_desired_auto_state_defaults,
            )

            return apply_desired_auto_state_defaults(self._bot, reason=reason)
        except Exception:
            return None

    def _log_toggle_apply_summary(self, summary: dict[str, dict], *, reason: str) -> None:
        try:
            parts: list[str] = []
            for toggle_name in ("combat", "looting", "following"):
                toggle_summary = summary.get(toggle_name, {}) if isinstance(summary, dict) else {}
                results = list(toggle_summary.get("results", []) or [])
                hero_ai_result = {}
                for result in results:
                    if str(result.get("backend", "")) == "hero_ai":
                        hero_ai_result = result
                        break
                selector = str(hero_ai_result.get("selector", "none") or "none")
                targeted = int(hero_ai_result.get("targeted", 0) or 0)
                updated = int(hero_ai_result.get("updated", 0) or 0)
                parts.append(
                    f"{toggle_name}={str(bool(toggle_summary.get('enabled', True))).lower()}"
                    f"(selector={selector},targeted={targeted},updated={updated})"
                )
            self._debug_log(f"toggle_apply[{reason}] " + " ".join(parts))
        except Exception:
            return

    def _tick_desired_auto_state_reconcile(self) -> None:
        try:
            from Py4GWCoreLib.routines_src.behaviourtrees_src.modular_core.actions_party_toggles import (
                reconcile_desired_auto_states,
            )

            reconcile_desired_auto_states(self._bot, throttle_seconds=1.0)
        except Exception:
            return

    @property
    def bot(self) -> Botting: return self._bot

    def is_debug_logging_enabled(self) -> bool: return _runtime_support.is_debug_logging_enabled(self)
    def set_debug_logging(self, enabled: bool) -> None: _runtime_support.set_debug_logging(self, enabled)
    def _debug_log(self, message: str, message_type: Console.MessageType = Console.MessageType.Info) -> None: _runtime_support.debug_log(self, message, message_type)
    @property
    def tree(self) -> BottingTree: return self._botting_tree

    def bind_diagnostics_session(self, diagnostics: Optional[ModularRunDiagnostics]) -> None: _diag_support.bind_diagnostics_session(self, diagnostics)

    def get_run_log_path(self) -> str | None: return _diag_support.get_run_log_path(self)

    def get_last_stall_snapshot(self) -> dict | None: return _diag_support.get_last_stall_snapshot(self)

    def _ensure_diagnostics_session(self) -> None:
        _diag_support.ensure_diagnostics_session(self)

    def _finalize_diagnostics(self, reason: str) -> None:
        _diag_support.finalize_diagnostics(self, reason)

    def _runtime_context(self) -> dict[str, Any]:
        return _diag_support.runtime_context(self)

    def record_diagnostics_event(
        self,
        event: str,
        *,
        phase: str = "",
        step_index: int | None = None,
        step_type: str = "",
        message: str = "",
        traceback_text: str = "",
        extra: Optional[dict[str, Any]] = None,
        autostart_session: bool = False,
    ) -> None:
        _diag_support.record_diagnostics_event(
            self,
            event,
            phase=phase,
            step_index=step_index,
            step_type=step_type,
            message=message,
            traceback_text=traceback_text,
            extra=extra,
            autostart_session=autostart_session,
        )

    def _tick_diagnostics_runtime(self) -> None:
        _diag_support.tick_diagnostics_runtime(self)

    def _phase_failure_state(self) -> BehaviorTree.NodeState:
        if self._failure_mode == _FAILURE_MODE_SKIP:
            return BehaviorTree.NodeState.SUCCESS
        return BehaviorTree.NodeState.FAILURE

    def _reset_step_fsm(self) -> None:
        fsm = self._bot.config.FSM
        try:
            fsm.RemoveAllManagedCoroutines()
            self._bot_coroutines_started = False
        except Exception:
            pass
        try:
            fsm.stop()
        except Exception:
            pass
        try:
            fsm.states.clear()
            fsm.state_counter = 0
            fsm.current_state = None
            fsm.finished = False
            fsm.paused = False
        except Exception:
            pass

    def _consume_phase_restart_state(self, phase_name: str) -> str:
        return str(self._phase_restart_state_overrides.pop(str(phase_name), "") or "")

    def _set_runtime_anchor(self, phase_name: str, state_name: str = "") -> None:
        self._runtime_anchor_phase = str(phase_name or "").strip() or None
        self._runtime_anchor_state = str(state_name or "").strip()
        if self._runtime_anchor_phase:
            if self._runtime_anchor_state:
                self._debug_log(
                    f"Anchor set: phase={self._runtime_anchor_phase}, state={self._runtime_anchor_state}",
                )
            else:
                self._debug_log(f"Anchor set: phase={self._runtime_anchor_phase}")

    def _phase_exists(self, phase_name: str) -> bool:
        return str(phase_name or "") in self._phase_headers

    def _build_phase_step(self, phase: Phase, phase_index: int, total_phases: int) -> Callable[[], BehaviorTree]:
        native_spec = extract_native_block_spec(phase)

        def _builder() -> BehaviorTree:
            if native_spec is None:
                def _unsupported_phase_action(_node=None) -> BehaviorTree.NodeState:
                    ConsoleLog(
                        "ModularBot",
                        f"Non-native phase is not supported: {phase.name!r}.",
                        Console.MessageType.Error,
                    )
                    self.record_diagnostics_event(
                        "exception",
                        phase=str(phase.name),
                        message=f"Non-native phase is not supported: {phase.name!r}",
                    )
                    return self._phase_failure_state()

                return BehaviorTree(
                    BehaviorTree.ActionNode(
                        name=f"RunPhase::{phase.name}::Unsupported",
                        action_fn=_unsupported_phase_action,
                        aftercast_ms=0,
                    )
                )

            runner = NativeBlockPhaseRunner(
                self,
                phase,
                phase_index,
                total_phases,
                native_spec,
            )
            return BehaviorTree(
                BehaviorTree.ActionNode(
                    name=f"RunPhase::{phase.name}",
                    action_fn=lambda _node=None, _runner=runner: _runner.tick(),
                    aftercast_ms=0,
                )
            )

        return _builder

    def _build_runtime_service_tree(self) -> BehaviorTree:
        def _tick_runtime_services() -> BehaviorTree.NodeState:
            self._enforce_native_leader_policy_runtime()
            _runtime_support.tick_cinematic_guard(self)
            self._apply_party_member_hooks(self._bot)
            self._process_pending_recovery()
            self._tick_desired_auto_state_reconcile()
            self._tick_bot_coroutines()
            self._tick_background_coroutines()
            return BehaviorTree.NodeState.RUNNING

        return BehaviorTree(
            BehaviorTree.ActionNode(
                name="ModularRuntimeService",
                action_fn=_tick_runtime_services,
                aftercast_ms=0,
            )
        )

    def _tick_bot_coroutines(self) -> None:
        _runtime_support.tick_bot_coroutines(self)

    def _tick_background_coroutines(self) -> None:
        _runtime_support.tick_background_coroutines(self)

    def _is_player_dead(self) -> bool:
        try:
            player_id = int(Player.GetAgentID() or 0)
            return bool(player_id and Agent.IsDead(player_id))
        except Exception:
            return False

    def _is_recovery_ready(self, pending: PendingRecovery) -> bool:
        if (time.monotonic() - pending.requested_at) >= 60.0:
            return True
        try:
            map_valid = bool(Routines.Checks.Map.MapValid())
            if not map_valid:
                return False
            if not bool(Routines.Checks.Map.IsExplorable()):
                return True
            return not self._is_player_dead()
        except Exception:
            return not self._is_player_dead()

    def _process_pending_recovery(self) -> None:
        pending = self._pending_recovery
        if pending is None:
            return

        if not self._is_recovery_ready(pending):
            self.record_diagnostics_event(
                "recovery_deferred",
                phase=str(pending.phase_name or ""),
                message=f"[{pending.reason}] Pending recovery not ready yet.",
            )
            return

        if self._restart_from_phase(
            pending.phase_name,
            state_name=pending.state_name,
            reason=pending.reason,
        ):
            self._pending_recovery = None
            self._recovery_active = False
            self.suppress_recovery_for(ms=3000, max_events=4, until_outpost=False)
            return

        ConsoleLog(
            "ModularBot",
            (
                f"[{pending.reason}] Recovery restart failed for phase={pending.phase_name!r}, "
                f"state={pending.state_name!r}; clearing pending recovery."
            ),
            Console.MessageType.Warning,
        )
        self.record_diagnostics_event(
            "recovery_failed",
            phase=str(pending.phase_name or ""),
            message=f"[{pending.reason}] Restart failed for pending recovery target.",
        )
        self._pending_recovery = None
        self._recovery_active = False

    def _restart_from_phase(self, phase_name: str, state_name: str = "", reason: str = "") -> bool:
        phase_key = str(phase_name or "").strip()
        if not phase_key:
            return False
        if not self._phase_exists(phase_key):
            return False

        state_key = str(state_name or "").strip()
        if state_key:
            self._phase_restart_state_overrides[phase_key] = state_key

        restarted = bool(
            self._botting_tree.RestartFromNamedPlannerStep(
                phase_key,
                auto_start=True,
                name="ModularPlanner",
            )
        )
        if restarted:
            self._bot.config.fsm_running = True
            if reason:
                self._debug_log(f"[{reason}] Restarted planner at phase {phase_key!r} (state={state_key!r}).")
            self.record_diagnostics_event(
                "recovery_restarted",
                phase=phase_key,
                message=f"[{reason}] Restarted planner at phase {phase_key!r} (state={state_key!r}).",
            )
            return True
        self.record_diagnostics_event(
            "recovery_failed",
            phase=phase_key,
            message=f"[{reason}] Planner restart call returned false for phase {phase_key!r}.",
        )
        return False

    def _ensure_phase_headers(self) -> None:
        self._phase_headers.clear()
        self._header_to_phase.clear()
        for phase in self._phases:
            phase_name = str(phase.name)
            self._phase_headers[phase_name] = phase_name
            self._header_to_phase[phase_name] = phase_name

    def _resolve_loop_target_phase_name(self) -> str:
        if not self._phases:
            return ""
        target_name = str(self._loop_to or self._phases[0].name or "").strip()
        if target_name in self._phase_headers:
            return target_name

        target_name_l = target_name.lower()
        for phase_name in self._phase_headers:
            phase_l = phase_name.lower()
            if target_name_l == phase_l or target_name_l in phase_l or phase_l in target_name_l:
                return phase_name
        return str(self._phases[0].name)

    def _compile_planner_impl(self) -> None:
        self.record_diagnostics_event(
            "compile_started",
            message="Compiling modular planner phases.",
        )
        compiled = modular_planner_compiler().compile_phases(
            self._phases,
            build_phase_step=self._build_phase_step,
        )
        self._planner_step_names = list(compiled.step_names)
        self._botting_tree.SetNamedPlannerSteps(
            compiled.steps,
            name="ModularPlanner",
        )
        self._botting_tree.SetServiceTrees(
            [
                ("ModularRuntimeService", self._build_runtime_service_tree),
            ]
        )
        self._planner_compiled = True
        self.record_diagnostics_event(
            "compile_finished",
            message=f"Compiled planner with {len(self._planner_step_names)} steps.",
            extra={"planner_steps": len(self._planner_step_names)},
        )

    def _build_routine(self, bot: Botting) -> None:
        _runtime_support.build_routine(self, bot)

    def start(self) -> None:
        self._start_impl()

    def _start_impl(self) -> None:
        self._ensure_diagnostics_session()
        self.record_diagnostics_event(
            "start_clicked",
            message="Start requested.",
        )
        try:
            if not self._planner_compiled:
                self._build_routine(self._bot)

            if self._botting_tree.IsStarted():
                return

            self._manual_stop_requested = False
            self._pending_recovery = None
            self._recovery_active = False
            self._active_phase_name = None
            self._bot_coroutines_started = False
            self._initialize_desired_auto_state_defaults()
            startup_toggle_summary = self._apply_desired_auto_state_defaults(reason="startup")
            self._botting_tree.Start()
            self._enforce_native_leader_policy_runtime()
            self._bot.config.fsm_running = True
            self._bot.config.state_description = "Running"
            self.record_diagnostics_event(
                "start",
                message="Planner started.",
            )
            self._log_native_leader_policy_startup()
            if isinstance(startup_toggle_summary, dict):
                self._log_toggle_apply_summary(startup_toggle_summary, reason="startup")
                self.record_diagnostics_event(
                    "toggle_defaults_applied",
                    message="Applied startup defaults for auto toggles.",
                    extra={"reason": "startup", "defaults": startup_toggle_summary},
                )
        except Exception as exc:
            self.record_diagnostics_event(
                "exception",
                message=f"Start failed: {exc}",
                traceback_text=traceback.format_exc(),
            )
            self._finalize_diagnostics(f"start_failed:{exc}")
            raise

    def stop(self, reason: str = "Manual stop") -> None:
        self._stop_impl(reason=reason)

    def _stop_impl(self, reason: str = "Manual stop") -> None:
        self._manual_stop_requested = True
        if self._botting_tree.IsStarted():
            self._botting_tree.Stop()
        stop_toggle_summary = self._apply_desired_auto_state_defaults(reason="stop_restore")
        if isinstance(stop_toggle_summary, dict):
            self._log_toggle_apply_summary(stop_toggle_summary, reason="stop_restore")
        self._reset_step_fsm()
        self._pending_recovery = None
        self._recovery_active = False
        self._active_phase_name = None
        self._background_generators.clear()
        self._bot_coroutines_started = False
        self._bot.config.fsm_running = False
        self._bot.config.state_description = "Stopped"
        self.record_diagnostics_event(
            "stop",
            message=f"Stopped: {reason}",
            extra=(
                {"reason": str(reason), "toggle_restore": stop_toggle_summary}
                if isinstance(stop_toggle_summary, dict)
                else {"reason": str(reason)}
            ),
        )
        self._finalize_diagnostics(str(reason or "Stopped"))

    def is_running(self) -> bool:
        return bool(self._botting_tree.IsStarted())

    def set_loop(self, enabled: bool, loop_to: Optional[str] = None) -> None:
        self._loop = bool(enabled)
        self._loop_to = None if loop_to is None else str(loop_to)
        if self._planner_compiled:
            self._ensure_phase_headers()
            self._loop_target_phase_name = self._resolve_loop_target_phase_name() if self._loop else None

    def restart_from_phase(self, phase_name: str, state_name: str = "", reason: str = "Manual restart") -> bool:
        return self._restart_from_phase(phase_name, state_name=state_name, reason=reason)

    def rebuild_runtime(self) -> None:
        self._rebuild_runtime_impl()

    def _rebuild_runtime_impl(self) -> None:
        was_running = self.is_running()
        self._stop_impl(reason="Rebuild runtime")
        self._planner_compiled = False
        self._bot.config.initialized = False
        self._build_routine(self._bot)
        if was_running:
            self._start_impl()

    def invalidate_runtime(self) -> None:
        self._planner_compiled = False
        self._bot.config.initialized = False

    def update(self) -> None:
        self._update_impl()

    def _update_impl(self) -> None:
        _runtime_support.update_impl(self)

    def get_phase_header(self, phase_name: str) -> Optional[str]:
        return self._phase_headers.get(str(phase_name))

    def get_current_step_name(self) -> str:
        fsm = self._bot.config.FSM
        try:
            current_state = getattr(fsm, "current_state", None)
            current_name = str(getattr(current_state, "name", "") or "").strip()
            if current_name:
                return current_name
        except Exception:
            pass

        if self._active_phase_name:
            return str(self._active_phase_name)

        return str(self._botting_tree.GetBlackboardValue("PLANNER_STATUS", "") or "")

    def get_phase_progress(self) -> tuple[int, int, str]:
        cfg = self._bot.config
        phase_index = int(getattr(cfg, "modular_phase_index", 0) or 0)
        phase_total = int(getattr(cfg, "modular_phase_total", len(self._phases)) or 0)
        phase_title = str(getattr(cfg, "modular_phase_title", "") or "")
        if not phase_title and self._active_phase_name:
            phase_title = str(self._active_phase_name)
        return (phase_index, phase_total, phase_title)

    def get_step_progress(self) -> tuple[int, int, str, str]:
        cfg = self._bot.config
        return (
            int(getattr(cfg, "modular_step_index", 0) or 0),
            int(getattr(cfg, "modular_step_total", 0) or 0),
            str(getattr(cfg, "modular_recipe_title", "") or ""),
            str(getattr(cfg, "modular_step_title", "") or ""),
        )

    def set_anchor(self, phase_or_header: str) -> bool:
        return _recovery_support.set_anchor(self, phase_or_header)

    def set_party_member_hooks_enabled(self, enabled: bool) -> None:
        _recovery_support.set_party_member_hooks_enabled(self, enabled)

    def suppress_recovery_for(self, ms: int = 45000, max_events: int = 20, until_outpost: bool = False) -> None:
        _recovery_support.suppress_recovery_for(self, ms=ms, max_events=max_events, until_outpost=until_outpost)

    def _should_defer_recovery_callback(self, reason: str) -> bool:
        return _recovery_support.should_defer_recovery_callback(self, reason)

    def _resolve_recovery_target(self, target: Union[str, Callable]) -> tuple[Optional[str], str, str]:
        return _recovery_support.resolve_recovery_target(self, target)

    def _resolve_party_hook_engine(self, bot: Botting) -> str:
        return _recovery_support.resolve_party_hook_engine(self, bot)

    def _apply_party_member_hooks(self, bot: Botting, *, force: bool = False) -> None:
        _recovery_support.apply_party_member_hooks(self, bot, force=force)

    def _handle_recovery(self, bot: Botting, target: Union[str, Callable], reason: str) -> None:
        _recovery_support.handle_recovery(self, bot, target, reason)
