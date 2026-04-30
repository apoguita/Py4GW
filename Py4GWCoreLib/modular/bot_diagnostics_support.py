"""
bot diagnostics support module

This module provides extracted diagnostics helpers for ModularBot.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
import time

from .diagnostics import ModularRunDiagnostics


def bind_diagnostics_session(self, diagnostics: Optional[ModularRunDiagnostics]) -> None:
    if diagnostics is None:
        return
    self._diagnostics = diagnostics
    self._last_run_log_path = str(diagnostics.log_path)


def get_run_log_path(self) -> str | None:
    if self._diagnostics is not None:
        return str(self._diagnostics.log_path)
    return str(self._last_run_log_path) if self._last_run_log_path else None


def get_last_stall_snapshot(self) -> dict | None:
    if isinstance(self._last_stall_snapshot, dict):
        return dict(self._last_stall_snapshot)
    return None


def ensure_diagnostics_session(self) -> None:
    if not self._diagnostics_enabled:
        return
    if self._diagnostics is not None and not self._diagnostics.closed:
        return
    self._diagnostics = ModularRunDiagnostics.start_run(
        widget=self._diagnostics_label,
        bot_name=self._name,
    )
    self._last_run_log_path = str(self._diagnostics.log_path)
    self._diag_last_heartbeat_at = 0.0
    self._diag_last_progress_at = time.monotonic()
    self._diag_last_stall_warning_at = 0.0
    self._diag_last_snapshot_key = None
    self._last_stall_snapshot = None


def finalize_diagnostics(self, reason: str) -> None:
    if self._diagnostics is None:
        return
    try:
        self._diagnostics.finalize(
            reason=str(reason or ""),
            last_stall_snapshot=self._last_stall_snapshot,
        )
    finally:
        self._last_run_log_path = str(self._diagnostics.log_path)
        self._diagnostics = None


def runtime_context(self) -> dict[str, Any]:
    phase_index, phase_total, phase_title = self.get_phase_progress()
    step_index, step_total, _recipe_title, step_title = self.get_step_progress()
    planner_status = str(self._botting_tree.GetBlackboardValue("PLANNER_STATUS", "") or "")
    fsm_state = str(self.get_current_step_name() or "")

    map_id = None
    try:
        from Py4GWCoreLib import Map

        map_id = int(Map.GetMapID() or 0)
    except Exception:
        map_id = None

    party_state = ""
    try:
        from Py4GWCoreLib import Party

        party_state = (
            f"loaded={bool(Party.IsPartyLoaded())};"
            f"count={int(Party.GetPlayerCount() or 0)};"
            f"leader={bool(Party.IsPartyLeader())}"
        )
    except Exception:
        party_state = ""

    return {
        "phase": str(phase_title or self._active_phase_name or ""),
        "step_index": int(step_index or 0),
        "step_type": str(step_title or ""),
        "fsm_state": fsm_state,
        "planner_status": planner_status,
        "map_id": map_id,
        "party_state": party_state,
        "phase_index": int(phase_index or 0),
        "phase_total": int(phase_total or 0),
        "step_total": int(step_total or 0),
    }


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
    if not self._diagnostics_enabled:
        return
    if self._diagnostics is None or self._diagnostics.closed:
        if autostart_session:
            ensure_diagnostics_session(self)
        else:
            return
    if self._diagnostics is None:
        return

    runtime = runtime_context(self)
    self._diagnostics.write_event(
        event=str(event or ""),
        phase=str(phase or runtime.get("phase", "") or ""),
        step_index=(
            int(step_index)
            if step_index is not None
            else int(runtime.get("step_index", 0) or 0)
        ),
        step_type=str(step_type or runtime.get("step_type", "") or ""),
        fsm_state=str(runtime.get("fsm_state", "") or ""),
        planner_status=str(runtime.get("planner_status", "") or ""),
        map_id=runtime.get("map_id"),
        party_state=str(runtime.get("party_state", "") or ""),
        message=str(message or ""),
        traceback_text=str(traceback_text or ""),
        extra=dict(extra or {}),
    )


def _emit_stall_warning(self, now: float, runtime: dict[str, Any]) -> None:
    elapsed = now - float(self._diag_last_progress_at or now)
    if elapsed < 120.0:
        return

    should_emit = (
        self._diag_last_stall_warning_at <= 0.0
        or (now - self._diag_last_stall_warning_at) >= 30.0
    )
    if not should_emit:
        return

    self._diag_last_stall_warning_at = now
    self._last_stall_snapshot = {
        "detected_at": datetime.now().isoformat(timespec="milliseconds"),
        "elapsed_seconds": round(elapsed, 3),
        "phase": runtime.get("phase", ""),
        "step_index": runtime.get("step_index", 0),
        "step_type": runtime.get("step_type", ""),
        "fsm_state": runtime.get("fsm_state", ""),
        "planner_status": runtime.get("planner_status", ""),
    }
    self._diagnostics.write_event(
        event="STALL_WARNING",
        phase=str(runtime.get("phase", "") or ""),
        step_index=int(runtime.get("step_index", 0) or 0),
        step_type=str(runtime.get("step_type", "") or ""),
        fsm_state=str(runtime.get("fsm_state", "") or ""),
        planner_status=str(runtime.get("planner_status", "") or ""),
        map_id=runtime.get("map_id"),
        party_state=str(runtime.get("party_state", "") or ""),
        message=f"No phase/step progress for {elapsed:.1f}s.",
        extra={"snapshot": dict(self._last_stall_snapshot)},
    )


def _emit_heartbeat(self, now: float, runtime: dict[str, Any]) -> None:
    if (now - float(self._diag_last_heartbeat_at or 0.0)) < 1.0:
        return
    self._diag_last_heartbeat_at = now
    self._diagnostics.write_event(
        event="heartbeat",
        phase=str(runtime.get("phase", "") or ""),
        step_index=int(runtime.get("step_index", 0) or 0),
        step_type=str(runtime.get("step_type", "") or ""),
        fsm_state=str(runtime.get("fsm_state", "") or ""),
        planner_status=str(runtime.get("planner_status", "") or ""),
        map_id=runtime.get("map_id"),
        party_state=str(runtime.get("party_state", "") or ""),
        message="Runtime heartbeat.",
    )


def tick_diagnostics_runtime(self) -> None:
    if not self._diagnostics_enabled or self._diagnostics is None:
        return
    if not self._botting_tree.IsStarted():
        return

    now = time.monotonic()
    runtime = runtime_context(self)
    snapshot_key = (
        str(runtime.get("phase", "") or ""),
        int(runtime.get("step_index", 0) or 0),
        str(runtime.get("step_type", "") or ""),
        str(runtime.get("fsm_state", "") or ""),
    )

    if snapshot_key != self._diag_last_snapshot_key:
        self._diag_last_snapshot_key = snapshot_key
        self._diag_last_progress_at = now
        self._diag_last_stall_warning_at = 0.0
    else:
        _emit_stall_warning(self, now, runtime)

    _emit_heartbeat(self, now, runtime)

