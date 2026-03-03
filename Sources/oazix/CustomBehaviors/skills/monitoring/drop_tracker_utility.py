import json
import os
import re
import time
from typing import Any

from Py4GWCoreLib import GLOBAL_CACHE, Item, Map, Party, Player
from Py4GWCoreLib.Py4GWcorelib import ThrottledTimer
from Py4GWCoreLib.enums import SharedCommandType
from Sources.oazix.CustomBehaviors.primitives import constants
from Sources.oazix.CustomBehaviors.primitives.helpers.custom_behavior_helpers_party import CustomBehaviorHelperParty
from Sources.oazix.CustomBehaviors.primitives.helpers.map_instance_helper import (
    classify_map_instance_transition,
    read_current_map_instance,
)
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_protocol import (
    build_drop_meta,
    build_name_chunks,
    encode_name_chunk_meta,
    make_event_id,
)
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_inventory_runtime import (
    buffer_pending_slot_delta,
    make_orphan_pending_slot_key,
    process_inventory_deltas,
    take_inventory_snapshot,
)
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_world_items import (
    build_world_item_state,
    consume_recent_world_item_confirmation,
    poll_world_item_disappearances,
    prune_recent_world_item_disappearances,
    world_item_names_compatible,
)
from Sources.oazix.CustomBehaviors.skills.monitoring.item_mod_render_utils import (
    build_known_spellcasting_mod_lines,
    prune_generic_attribute_bonus_lines,
    render_mod_description_template,
    sort_stats_lines_like_ingame,
)
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_item_stats_runtime import (
    build_identified_name_from_modifiers,
    build_item_stats_text,
    build_known_spellcast_mod_lines as build_known_spellcast_mod_lines_runtime,
    collect_fallback_mod_lines,
    collect_fallback_rune_lines,
    entry_item_identity_matches,
    extract_parsed_mod_name_parts,
    format_attribute_name,
    load_mod_database,
    match_mod_definition_against_raw,
    normalize_stats_lines,
    prune_generic_attribute_bonus_lines_local,
    render_mod_description_template_local,
    resolve_best_live_item_name,
    resolve_event_item_id_for_stats,
    weapon_mod_type_matches,
)
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_tick_runtime import run_sender_tick
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_sender_state import (
    advance_sender_session_id,
    arm_reset_trace,
    begin_new_session,
    clear_cached_event_stats,
    clear_cached_event_stats_for_item,
    get_cached_event_identity,
    get_cached_event_stats_text,
    log_reset_trace,
    prune_sent_event_stats_cache,
    remember_event_identity,
    remember_event_stats_snapshot,
    reset_trace_active,
    reset_trace_actor_label,
    reset_tracking_state,
    resolve_live_item_id_for_event,
    should_track_name_refresh,
)
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_sender_transport import (
    flush_outbox,
    is_party_leader_client,
    load_runtime_config,
    log_name_trace,
    next_event_id,
    poll_ack_messages,
    process_pending_name_refreshes,
    queue_drop,
    resolve_party_leader_email,
    schedule_name_refresh_for_entry,
    schedule_name_refresh_for_item,
    send_drop,
    send_name_chunks,
    send_stats_chunks,
)
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_live_debug import (
    append_live_debug_log,
    clear_live_debug_log,
    get_live_debug_log_path,
)

EXPECTED_RUNTIME_ERRORS = (TypeError, ValueError, RuntimeError, AttributeError, IndexError, KeyError, OSError)


class DropTrackerSender:
    """
    Non-blocking shared-memory drop sender.
    Runs from daemon() and never participates in utility score arbitration.
    """

    _instance = None
    _STATE_VERSION = 18

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DropTrackerSender, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            # Hot-reload/session safety: if schema/version changed, force a clean baseline.
            if getattr(self, "state_version", 0) != self._STATE_VERSION:
                if not hasattr(self, "pending_slot_deltas"):
                    self.pending_slot_deltas = {}
                if not hasattr(self, "outbox_queue"):
                    self.outbox_queue = []
                if not hasattr(self, "pending_name_refresh_by_event"):
                    self.pending_name_refresh_by_event = {}
                if not hasattr(self, "carryover_inventory_snapshot"):
                    self.carryover_inventory_snapshot = {}
                if not hasattr(self, "carryover_suppression_until"):
                    self.carryover_suppression_until = 0.0
                if not hasattr(self, "stable_snapshot_count"):
                    self.stable_snapshot_count = 0
                if not hasattr(self, "session_startup_pending"):
                    self.session_startup_pending = False
                if not hasattr(self, "warmup_grace_seconds"):
                    self.warmup_grace_seconds = 3.0
                if not hasattr(self, "warmup_grace_until"):
                    self.warmup_grace_until = 0.0
                if not hasattr(self, "pending_ttl_seconds"):
                    self.pending_ttl_seconds = 6.0
                if not hasattr(self, "debug_pipeline_logs"):
                    self.debug_pipeline_logs = False
                if not hasattr(self, "max_outbox_size"):
                    self.max_outbox_size = 2000
                if not hasattr(self, "max_snapshot_size_jump"):
                    self.max_snapshot_size_jump = 40
                if not hasattr(self, "last_known_is_leader"):
                    self.last_known_is_leader = False
                if not hasattr(self, "current_world_item_agents"):
                    self.current_world_item_agents = {}
                if not hasattr(self, "recent_world_item_disappearances"):
                    self.recent_world_item_disappearances = []
                if not hasattr(self, "world_item_seen_since_reset"):
                    self.world_item_seen_since_reset = False
                if not hasattr(self, "world_item_disappearance_ttl_seconds"):
                    self.world_item_disappearance_ttl_seconds = 5.0
                if not hasattr(self, "require_world_item_confirmation"):
                    self.require_world_item_confirmation = True
                if not hasattr(self, "last_world_item_scan_count"):
                    self.last_world_item_scan_count = 0
                if not hasattr(self, "enable_delivery_ack"):
                    self.enable_delivery_ack = True
                if not hasattr(self, "retry_interval_seconds"):
                    self.retry_interval_seconds = 1.0
                if not hasattr(self, "max_retry_attempts"):
                    self.max_retry_attempts = 12
                if not hasattr(self, "enable_perf_logs"):
                    self.enable_perf_logs = False
                if not hasattr(self, "event_sequence"):
                    self.event_sequence = 0
                if not hasattr(self, "last_seen_map_id"):
                    self.last_seen_map_id = 0
                if not hasattr(self, "last_seen_instance_uptime_ms"):
                    self.last_seen_instance_uptime_ms = 0
                if not hasattr(self, "sender_session_id"):
                    self.sender_session_id = 1
                if not hasattr(self, "last_session_transition_reason"):
                    self.last_session_transition_reason = ""
                if not hasattr(self, "runtime_config_path"):
                    self.runtime_config_path = os.path.join(
                        os.path.dirname(constants.DROP_LOG_PATH),
                        "drop_tracker_runtime_config.json",
                    )
                if not hasattr(self, "last_inventory_activity_ts"):
                    self.last_inventory_activity_ts = 0.0
                if not hasattr(self, "sent_event_stats_cache"):
                    self.sent_event_stats_cache = {}
                if not hasattr(self, "sent_event_stats_ttl_seconds"):
                    self.sent_event_stats_ttl_seconds = 600.0
                if not hasattr(self, "max_stats_builds_per_tick"):
                    self.max_stats_builds_per_tick = 2
                if not hasattr(self, "name_refresh_ttl_seconds"):
                    self.name_refresh_ttl_seconds = 4.0
                if not hasattr(self, "name_refresh_poll_interval_seconds"):
                    self.name_refresh_poll_interval_seconds = 0.25
                if not hasattr(self, "max_name_refresh_per_tick"):
                    self.max_name_refresh_per_tick = 4
                if not hasattr(self, "world_item_poll_timer"):
                    self.world_item_poll_timer = ThrottledTimer(150)
                self.debug_enabled = False
                self.inventory_poll_timer = ThrottledTimer(250)
                self.state_version = self._STATE_VERSION
                self._reset_tracking_state()
            return
        self._initialized = True
        self.state_version = self._STATE_VERSION
        self.inventory_poll_timer = ThrottledTimer(250)
        self.world_item_poll_timer = ThrottledTimer(150)
        self.last_inventory_snapshot: dict[tuple[int, int], tuple[str, str, int, int, int]] = {}
        self.enabled = True
        self.gold_regex = re.compile(r"^(?:\[([\d: ]+[ap]m)\] )?Your party shares ([\d,]+) gold\.$")
        self.warn_timer = ThrottledTimer(3000)
        self.debug_timer = ThrottledTimer(5000)
        self.snapshot_error_timer = ThrottledTimer(5000)
        self.debug_enabled = False
        self.last_snapshot_total = 0
        self.last_snapshot_ready = 0
        self.last_snapshot_not_ready = 0
        self.last_sent_count = 0
        self.last_candidate_count = 0
        self.last_enqueued_count = 0
        self.is_warmed_up = False
        self.stable_snapshot_count = 0
        self.pending_slot_deltas: dict[tuple[int, int], dict] = {}
        self.carryover_inventory_snapshot: dict[tuple[int, int], tuple[str, str, int, int, int]] = {}
        self.carryover_suppression_until = 0.0
        self.current_world_item_agents: dict[int, dict[str, Any]] = {}
        self.recent_world_item_disappearances: list[dict[str, Any]] = []
        self.world_item_seen_since_reset = False
        self.world_item_disappearance_ttl_seconds = 5.0
        self.require_world_item_confirmation = True
        self.last_world_item_scan_count = 0
        self.outbox_queue: list[dict] = []
        self.pending_name_refresh_by_event: dict[str, dict] = {}
        self.max_send_per_tick = 12
        self.max_outbox_size = 2000
        self.max_snapshot_size_jump = 40
        self.warmup_grace_seconds = 3.0
        self.warmup_grace_until = 0.0
        self.session_startup_pending = False
        self.pending_ttl_seconds = 6.0
        self.debug_pipeline_logs = False
        self.last_known_is_leader = False
        self.enable_delivery_ack = True
        self.retry_interval_seconds = 1.0
        self.max_retry_attempts = 12
        self.enable_perf_logs = False
        self.event_sequence = 0
        self.last_seen_map_id = 0
        self.last_seen_instance_uptime_ms = 0
        self.sender_session_id = 1
        self.last_session_transition_reason = ""
        self.last_process_duration_ms = 0.0
        self.last_ack_count = 0
        self.last_inventory_activity_ts = 0.0
        self.sent_event_stats_cache: dict[str, dict] = {}
        self.sent_event_stats_ttl_seconds = 600.0
        self.max_stats_builds_per_tick = 2
        self.name_refresh_ttl_seconds = 4.0
        self.name_refresh_poll_interval_seconds = 0.25
        self.max_name_refresh_per_tick = 4
        self.debug_reset_trace_until = 0.0
        self.debug_reset_trace_snapshot_logs_remaining = 0
        self.debug_reset_trace_event_logs_remaining = 0
        self.debug_reset_trace_lines: list[str] = []
        self.runtime_config_path = os.path.join(
            os.path.dirname(constants.DROP_LOG_PATH),
            "drop_tracker_runtime_config.json",
        )
        self.live_debug_log_path = get_live_debug_log_path(constants.DROP_LOG_PATH)
        self.ack_poll_timer = ThrottledTimer(250)
        self.config_poll_timer = ThrottledTimer(2000)
        self.mod_db = None
        self._load_mod_database()

    def _load_mod_database(self):
        return load_mod_database(self)

    def _format_attribute_name(self, attr_name: str) -> str:
        return format_attribute_name(self, attr_name)

    def _render_mod_description_template(
        self,
        description: str,
        matched_modifiers: list[tuple[int, int, int]],
        default_value: int = 0,
        attribute_name: str = "",
    ) -> list[str]:
        return render_mod_description_template_local(
            self,
            description,
            matched_modifiers,
            default_value=default_value,
            attribute_name=attribute_name,
        )

    def _match_mod_definition_against_raw(self, definition_modifiers, raw_mods) -> list[tuple[int, int, int]]:
        return match_mod_definition_against_raw(self, definition_modifiers, raw_mods)

    def _weapon_mod_type_matches(self, weapon_mod, item_type) -> bool:
        return weapon_mod_type_matches(self, weapon_mod, item_type)

    def _collect_fallback_mod_lines(self, raw_mods, item_attr_txt: str, item_type=None) -> list[str]:
        return collect_fallback_mod_lines(self, raw_mods, item_attr_txt, item_type)

    def _collect_fallback_rune_lines(self, raw_mods, item_attr_txt: str) -> list[str]:
        return collect_fallback_rune_lines(self, raw_mods, item_attr_txt)

    def _build_known_spellcast_mod_lines(self, raw_mods, item_attr_txt: str, item_type=None) -> list[str]:
        return build_known_spellcast_mod_lines_runtime(self, raw_mods, item_attr_txt, item_type)

    def _prune_generic_attribute_bonus_lines(self, lines: list[str]) -> list[str]:
        return prune_generic_attribute_bonus_lines_local(self, lines)

    def _normalize_stats_lines(self, lines: list[str]) -> list[str]:
        return normalize_stats_lines(self, lines)

    def _extract_parsed_mod_name_parts(self, parsed_result) -> tuple[str, str, str]:
        prefix = ""
        suffix = ""
        inherent = ""
        try:
            parsed_prefix = getattr(parsed_result, "prefix", None)
            if parsed_prefix is not None:
                prefix = str(
                    getattr(getattr(parsed_prefix, "weapon_mod", None), "name", "")
                    or getattr(getattr(parsed_prefix, "rune", None), "name", "")
                    or ""
                ).strip()
            parsed_suffix = getattr(parsed_result, "suffix", None)
            if parsed_suffix is not None:
                suffix = str(
                    getattr(getattr(parsed_suffix, "weapon_mod", None), "name", "")
                    or getattr(getattr(parsed_suffix, "rune", None), "name", "")
                    or ""
                ).strip()
            parsed_inherent = getattr(parsed_result, "inherent", None)
            if parsed_inherent is not None:
                inherent = str(
                    getattr(getattr(parsed_inherent, "weapon_mod", None), "name", "")
                    or getattr(getattr(parsed_inherent, "rune", None), "name", "")
                    or ""
                ).strip()
        except EXPECTED_RUNTIME_ERRORS:
            return "", "", ""
        return prefix, suffix, inherent

    def _build_identified_name_from_modifiers(self, *args, **kwargs) -> str:
        return build_identified_name_from_modifiers(self, *args, **kwargs)

    def _resolve_best_live_item_name(self, item_id: int, fallback_name: str = "") -> str:
        return resolve_best_live_item_name(self, item_id, fallback_name)

    def _build_item_stats_text(self, item_id: int, item_name: str = "") -> str:
        return build_item_stats_text(self, item_id, item_name)

    def _entry_item_identity_matches(self, item_id: int, expected_model_id: int, expected_name_signature: str) -> bool:
        return entry_item_identity_matches(self, item_id, expected_model_id, expected_name_signature)

    def _resolve_event_item_id_for_stats(self, entry: dict) -> int:
        return resolve_event_item_id_for_stats(self, entry)

    def _reset_tracking_state(self, clear_outbox: bool = True):
        return reset_tracking_state(self, clear_outbox=clear_outbox)

    def _arm_reset_trace(self, reason: str, current_map_id: int = 0, current_instance_uptime_ms: int = 0):
        return arm_reset_trace(self, reason, current_map_id=current_map_id, current_instance_uptime_ms=current_instance_uptime_ms)

    def _reset_trace_active(self) -> bool:
        return reset_trace_active(self)

    def _reset_trace_actor_label(self) -> str:
        return reset_trace_actor_label(self)

    def _advance_sender_session_id(self) -> int:
        return advance_sender_session_id(self)

    def _begin_new_session(self, reason: str, current_map_id: int = 0, current_instance_uptime_ms: int = 0):
        carryover_snapshot = dict(self.last_inventory_snapshot) if self.last_inventory_snapshot else {}
        begin_new_session(self, reason, current_map_id=current_map_id, current_instance_uptime_ms=current_instance_uptime_ms)
        self.carryover_inventory_snapshot = carryover_snapshot
        self.session_startup_pending = bool(carryover_snapshot)
        grace_seconds = max(6.0, float(getattr(self, "warmup_grace_seconds", 3.0) or 3.0) + 9.0)
        self.carryover_suppression_until = time.time() + grace_seconds if carryover_snapshot else 0.0
        self._append_live_debug_log(
            "sender_session_reset",
            f"transition={str(reason or '').strip() or 'unknown'}",
            reason=str(reason or "").strip() or "unknown",
            current_map_id=int(current_map_id or 0),
            current_instance_uptime_ms=int(current_instance_uptime_ms or 0),
            sender_session_id=int(getattr(self, "sender_session_id", 0) or 0),
            carryover_count=len(carryover_snapshot),
            startup_pending=bool(self.session_startup_pending),
            carryover_suppression_until=float(getattr(self, "carryover_suppression_until", 0.0) or 0.0),
        )

    def _append_live_debug_log(self, event: str, message: str, **fields: Any):
        return append_live_debug_log(
            actor="sender",
            event=event,
            message=message,
            drop_log_path=constants.DROP_LOG_PATH,
            **fields,
        )

    def _clear_live_debug_log(self):
        return clear_live_debug_log(constants.DROP_LOG_PATH)

    def _log_reset_trace(
        self,
        message: str,
        consume_snapshot: bool = False,
        consume_event: bool = False,
        level=None,
    ):
        if consume_event:
            remaining = int(getattr(self, "debug_reset_trace_event_logs_remaining", 0) or 0)
            if remaining > 0:
                self.debug_reset_trace_event_logs_remaining = remaining - 1
        trace_lines = getattr(self, "debug_reset_trace_lines", None)
        if not isinstance(trace_lines, list):
            self.debug_reset_trace_lines = []
            trace_lines = self.debug_reset_trace_lines
        trace_lines.append(str(message or ""))
        if len(trace_lines) > 120:
            del trace_lines[:-120]
        return log_reset_trace(self, message, consume_snapshot=consume_snapshot)

    def _strip_tags(self, text: str) -> str:
        return re.sub(r"<[^>]+>", "", text or "")

    def _prune_recent_world_item_disappearances(self, now_ts: float | None = None):
        prune_recent_world_item_disappearances(self, now_ts)

    def _build_world_item_state(self, agent_id: int) -> dict[str, Any] | None:
        return build_world_item_state(self, agent_id)

    def _poll_world_item_disappearances(self):
        poll_world_item_disappearances(self)

    def _world_item_names_compatible(self, world_name: str, event_name: str) -> bool:
        return world_item_names_compatible(world_name, event_name)

    def _consume_recent_world_item_confirmation(self, event: dict[str, Any]) -> bool:
        return consume_recent_world_item_confirmation(self, event)

    def _prune_sent_event_stats_cache(self, now_ts: float | None = None):
        return prune_sent_event_stats_cache(self, now_ts)

    def _remember_event_identity(
        self,
        event_id: str,
        item_id: int,
        model_id: int,
        item_name: str,
        name_signature: str = "",
        rarity: str = "",
        last_receiver_email: str = "",
    ):
        return remember_event_identity(
            self,
            event_id,
            item_id,
            model_id,
            item_name,
            name_signature=name_signature,
            rarity=rarity,
            last_receiver_email=last_receiver_email,
        )

    def get_cached_event_identity(self, event_id: str) -> dict:
        return get_cached_event_identity(self, event_id)

    def resolve_live_item_id_for_event(self, event_id: str, preferred_item_id: int = 0) -> int:
        return resolve_live_item_id_for_event(self, event_id, preferred_item_id=preferred_item_id)

    def clear_cached_event_stats(self, event_id: str, item_id: int = 0):
        return clear_cached_event_stats(self, event_id, item_id=item_id)

    def clear_cached_event_stats_for_item(self, item_id: int = 0, model_id: int = 0):
        return clear_cached_event_stats_for_item(self, item_id=item_id, model_id=model_id)

    def _remember_event_stats_snapshot(
        self,
        event_id: str,
        item_id: int,
        model_id: int,
        item_name: str,
        stats_text: str,
        name_signature: str = "",
        rarity: str = "",
        last_receiver_email: str = "",
    ):
        return remember_event_stats_snapshot(
            self,
            event_id,
            item_id,
            model_id,
            item_name,
            stats_text,
            name_signature=name_signature,
            rarity=rarity,
            last_receiver_email=last_receiver_email,
        )

    def _should_track_name_refresh(self, item_name: str = "", rarity: str = "") -> bool:
        return should_track_name_refresh(self, item_name=item_name, rarity=rarity)

    def get_cached_event_stats_text(self, event_id: str, item_id: int = 0, model_id: int = 0) -> str:
        return get_cached_event_stats_text(self, event_id, item_id=item_id, model_id=model_id)

    def _make_orphan_pending_slot_key(self, item_id: int, now_ts: float) -> tuple[int, int]:
        return make_orphan_pending_slot_key(self, item_id, now_ts)

    def _buffer_pending_slot_delta(
        self,
        slot_key: tuple[int, int],
        delta_qty: int,
        model_id: int,
        item_id: int,
        rarity: str,
        now_ts: float,
    ):
        return buffer_pending_slot_delta(
            self,
            slot_key,
            delta_qty,
            model_id,
            item_id,
            rarity,
            now_ts,
        )

    def _resolve_party_leader_email(self) -> str | None:
        return resolve_party_leader_email(self)

    def _is_party_leader_client(self) -> bool:
        return is_party_leader_client(self)

    def _next_event_id(self) -> str:
        return next_event_id(self)

    def _load_runtime_config(self):
        return load_runtime_config(self)

    def _send_name_chunks(self, receiver_email: str, my_email: str, name_signature: str, full_name: str) -> bool:
        return send_name_chunks(self, receiver_email, my_email, name_signature, full_name)

    def _log_name_trace(self, message: str) -> None:
        return log_name_trace(self, message)

    def _schedule_name_refresh_for_entry(self, entry: dict, receiver_email: str = "") -> None:
        return schedule_name_refresh_for_entry(self, entry, receiver_email=receiver_email)

    def _process_pending_name_refreshes(self) -> int:
        return process_pending_name_refreshes(self)

    def schedule_name_refresh_for_item(self, item_id: int = 0, model_id: int = 0) -> int:
        return schedule_name_refresh_for_item(self, item_id=item_id, model_id=model_id)

    def _send_stats_chunks(self, receiver_email: str, my_email: str, event_id: str, stats_text: str) -> bool:
        return send_stats_chunks(self, receiver_email, my_email, event_id, stats_text)

    def _send_drop(
        self,
        item_name: str,
        quantity: int,
        rarity: str,
        display_time: str = "",
        item_id: int = 0,
        model_id: int = 0,
        slot_bag: int = 0,
        slot_index: int = 0,
        is_leader_sender: bool = False,
        event_id: str = "",
        name_signature: str = "",
        sender_session_id: int = 0,
    ) -> bool:
        return send_drop(
            self,
            item_name,
            quantity,
            rarity,
            display_time=display_time,
            item_id=item_id,
            model_id=model_id,
            slot_bag=slot_bag,
            slot_index=slot_index,
            is_leader_sender=is_leader_sender,
            event_id=event_id,
            name_signature=name_signature,
            sender_session_id=sender_session_id,
        )

    def _queue_drop(
        self,
        item_name: str,
        quantity: int,
        rarity: str,
        display_time: str,
        item_id: int = 0,
        model_id: int = 0,
        slot_key: tuple[int, int] | None = None,
        reason: str = "delta",
        is_leader_sender: bool = False,
    ):
        return queue_drop(
            self,
            item_name,
            quantity,
            rarity,
            display_time,
            item_id=item_id,
            model_id=model_id,
            slot_key=slot_key,
            reason=reason,
            is_leader_sender=is_leader_sender,
        )

    def _poll_ack_messages(self) -> int:
        return poll_ack_messages(self)

    def _flush_outbox(self) -> int:
        return flush_outbox(self)

    def _take_inventory_snapshot(self) -> dict[tuple[int, int], tuple[str, str, int, int, int]]:
        return take_inventory_snapshot(self)

    def _process_inventory_deltas(self):
        return process_inventory_deltas(self)

    def act(self):
        return run_sender_tick(self)


