"""
diagnostics module

This module is part of the modular runtime surface.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import json
import os
import threading
import time
import uuid
from typing import Any, Optional

from .paths import modular_logs_root


def _safe_name(value: str) -> str:
    raw = str(value or "").strip()
    safe = "".join(ch if ch.isalnum() or ch in ("-", "_") else "_" for ch in raw)
    while "__" in safe:
        safe = safe.replace("__", "_")
    safe = safe.strip("._")
    return safe or "modular_bot"


def _logs_root() -> str:
    return modular_logs_root()


def _iso_now() -> str:
    return datetime.now().isoformat(timespec="milliseconds")


def _enforce_retention(log_dir: str, max_files: int = 200, max_bytes: int = 500 * 1024 * 1024) -> None:
    if not os.path.isdir(log_dir):
        return

    entries: list[tuple[float, str, int]] = []
    for filename in os.listdir(log_dir):
        if not filename.lower().endswith(".jsonl"):
            continue
        path = os.path.join(log_dir, filename)
        try:
            st = os.stat(path)
        except OSError:
            continue
        entries.append((float(st.st_mtime), path, int(st.st_size)))

    if not entries:
        return

    entries.sort(key=lambda row: row[0], reverse=True)
    keep: set[str] = set()

    running_total = 0
    for idx, (_mtime, path, size) in enumerate(entries):
        if idx < int(max_files) and (running_total + size) <= int(max_bytes):
            keep.add(path)
            running_total += int(size)
            continue
        # Allow newest file even if very large.
        if idx == 0 and not keep:
            keep.add(path)
            running_total += int(size)

    for _mtime, path, _size in entries:
        if path in keep:
            continue
        try:
            os.remove(path)
        except OSError:
            pass
        summary_path = path[:-6] + ".summary.txt"
        try:
            if os.path.isfile(summary_path):
                os.remove(summary_path)
        except OSError:
            pass


@dataclass
class ModularRunDiagnostics:
    """
    M od ul ar Ru nD ia gn os ti cs class.
    
    Meta:
      Expose: true
      Audience: advanced
      Display: Modular Run Diagnostics
      Purpose: Provide explicit modular runtime behavior and metadata.
      UserDescription: Internal class used by modular orchestration and step execution.
      Notes: Keep behavior explicit and side effects contained.
    """
    widget: str
    bot_name: str
    run_id: str
    log_path: str
    summary_path: str

    def __post_init__(self) -> None:
        self._lock = threading.Lock()
        self._event_count = 0
        self._started_at = time.monotonic()
        self._started_iso = _iso_now()
        self._last_event: dict[str, Any] = {}
        self._closed = False

    @classmethod
    def start_run(cls, *, widget: str, bot_name: str = "") -> "ModularRunDiagnostics":
        log_dir = _logs_root()
        os.makedirs(log_dir, exist_ok=True)
        _enforce_retention(log_dir)

        run_id = uuid.uuid4().hex[:12]
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_widget = _safe_name(widget)
        filename = f"{ts}_{safe_widget}_{run_id}.jsonl"
        log_path = os.path.join(log_dir, filename)
        summary_path = log_path[:-6] + ".summary.txt"
        return cls(
            widget=str(widget or safe_widget),
            bot_name=str(bot_name or widget or safe_widget),
            run_id=run_id,
            log_path=log_path,
            summary_path=summary_path,
        )

    @property
    def closed(self) -> bool:
        return bool(self._closed)

    def write_event(
        self,
        *,
        event: str,
        phase: str = "",
        step_index: int | None = None,
        step_type: str = "",
        fsm_state: str = "",
        planner_status: str = "",
        map_id: int | None = None,
        party_state: str = "",
        message: str = "",
        traceback_text: str = "",
        extra: Optional[dict[str, Any]] = None,
    ) -> None:
        payload: dict[str, Any] = {
            "timestamp": _iso_now(),
            "run_id": self.run_id,
            "widget": self.widget,
            "bot_name": self.bot_name,
            "event": str(event or ""),
            "phase": str(phase or ""),
            "step_index": int(step_index) if step_index is not None else None,
            "step_type": str(step_type or ""),
            "fsm_state": str(fsm_state or ""),
            "planner_status": str(planner_status or ""),
            "map_id": int(map_id) if map_id is not None else None,
            "party_state": str(party_state or ""),
            "message": str(message or ""),
            "traceback": str(traceback_text or ""),
        }
        if isinstance(extra, dict) and extra:
            payload["extra"] = dict(extra)

        line = json.dumps(payload, ensure_ascii=True, default=str)
        with self._lock:
            if self._closed:
                return
            os.makedirs(os.path.dirname(self.log_path), exist_ok=True)
            with open(self.log_path, "a", encoding="utf-8") as handle:
                handle.write(line + "\n")
            self._event_count += 1
            self._last_event = payload

    def finalize(self, *, reason: str = "", last_stall_snapshot: Optional[dict[str, Any]] = None) -> None:
        with self._lock:
            if self._closed:
                return
            self._closed = True

            ended_iso = _iso_now()
            duration_s = max(0.0, time.monotonic() - self._started_at)
            lines = [
                f"run_id={self.run_id}",
                f"widget={self.widget}",
                f"bot_name={self.bot_name}",
                f"log_path={self.log_path}",
                f"started_at={self._started_iso}",
                f"ended_at={ended_iso}",
                f"duration_seconds={duration_s:.3f}",
                f"event_count={self._event_count}",
                f"reason={str(reason or '')}",
            ]

            if self._last_event:
                lines.append(f"last_event={self._last_event.get('event', '')}")
                lines.append(f"last_message={self._last_event.get('message', '')}")

            if isinstance(last_stall_snapshot, dict) and last_stall_snapshot:
                lines.append("last_stall_snapshot=" + json.dumps(last_stall_snapshot, ensure_ascii=True, default=str))

            os.makedirs(os.path.dirname(self.summary_path), exist_ok=True)
            with open(self.summary_path, "w", encoding="utf-8") as handle:
                handle.write("\n".join(lines).strip() + "\n")
