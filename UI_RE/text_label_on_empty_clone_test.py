import time

import Py4GW
import PyImGui

from Py4GWCoreLib import UIManager
from Py4GWCoreLib.GWUI import GWUI


MODULE_NAME = "Text Label On DevText Test"
SCRIPT_REVISION = "2026-03-08-text-label-on-devtext-test-11"
WINDOW_OPEN = True
INITIALIZED = False

READ_DELAY_SECONDS = 0.50
CREATE_TEXT = "Py4GW Text Label Test"
UPDATE_TEXT = "Py4GW Clock Style Update"
CREATED_LABEL = "PyDevTextCreatedTextLabel"
CREATED_FRAME_ID = 0
LAST_STATUS = "idle"
LAST_DEVTEXT_ROOT = 0
LAST_HOST_FRAME = 0
LAST_EXISTING_FRAME = 0
LAST_EXISTING_SUMMARY = "frame_id=0"
LAST_EXISTING_ENCODED = ""
LAST_EXISTING_DECODED = ""
LAST_EXISTING_BYTES_HEX = ""
LAST_CREATED_SUMMARY = "frame_id=0"
LAST_CREATED_ENCODED = ""
LAST_CREATED_DECODED = ""
LAST_CREATED_BYTES_HEX = ""
LAST_CREATE_DIAGNOSTICS = ""
PENDING_REPORTS: list[tuple[float, str]] = []


def _log(message: str) -> None:
    print(f"[{MODULE_NAME}] {message}")


def _schedule_report(prefix: str, delay_seconds: float | None = None) -> None:
    delay = READ_DELAY_SECONDS if delay_seconds is None else max(0.0, float(delay_seconds))
    PENDING_REPORTS.append((time.time() + delay, prefix))
    _log(f"scheduled report prefix='{prefix}' delay={delay:.2f}s")


def _process_pending_reports() -> None:
    if not PENDING_REPORTS:
        return
    now = time.time()
    ready: list[tuple[float, str]] = []
    pending: list[tuple[float, str]] = []
    for scheduled_at, prefix in PENDING_REPORTS:
        if scheduled_at <= now:
            ready.append((scheduled_at, prefix))
        else:
            pending.append((scheduled_at, prefix))
    PENDING_REPORTS[:] = pending
    for _, prefix in ready:
        _enqueue_state_snapshot(prefix)


def _normalize_input_int(result, current: int) -> int:
    if isinstance(result, tuple):
        if len(result) >= 2:
            return int(result[1])
        if len(result) == 1:
            return int(result[0])
    if result is None:
        return int(current)
    return int(result)


def _safe_child(parent_id: int, child_offset: int) -> int:
    if parent_id <= 0:
        return 0
    return int(UIManager.GetChildFrameByFrameId(parent_id, child_offset) or 0)


def _frame_summary(frame_id: int) -> str:
    frame_id = int(frame_id or 0)
    if frame_id <= 0:
        return "frame_id=0"
    try:
        frame = UIManager.GetFrameByID(frame_id)
        left, top, right, bottom = UIManager.GetFrameCoords(frame_id)
        return (
            f"frame_id={frame_id} "
            f"parent_id={int(frame.parent_id)} "
            f"child_offset_id={int(frame.child_offset_id)} "
            f"is_created={bool(frame.is_created)} "
            f"is_visible={bool(frame.is_visible)} "
            f"frame_state=0x{int(frame.frame_state):X} "
            f"rect=({left},{top})-({right},{bottom})"
        )
    except Exception as exc:
        return f"frame_id={frame_id} summary_error={exc}"


def _read_encoded(frame_id: int) -> str:
    if frame_id <= 0:
        return ""
    try:
        return str(GWUI.GetTextLabelEncodedByFrameId(frame_id) or "")
    except Exception as exc:
        return f"<encoded_error:{exc}>"


def _read_decoded(frame_id: int) -> str:
    if frame_id <= 0:
        return ""
    try:
        return str(GWUI.GetTextLabelDecodedByFrameId(frame_id) or "")
    except Exception as exc:
        return f"<decoded_error:{exc}>"


def _read_encoded_bytes_hex(frame_id: int) -> str:
    if frame_id <= 0:
        return ""
    try:
        raw = bytes(GWUI.GetTextLabelEncodedBytesByFrameId(frame_id) or b"")
        if not raw:
            return ""
        return " ".join(f"{b:02X}" for b in raw)
    except Exception as exc:
        return f"<bytes_error:{exc}>"


def _resolve_devtext_root() -> int:
    return int(GWUI.GetDevTextFrameID() or 0)


def _resolve_devtext_host() -> int:
    root = _resolve_devtext_root()
    if root <= 0:
        return 0
    return int(GWUI.ResolveObservedContentHostByFrameId(root) or 0)


def _resolve_existing_text_label() -> int:
    return _safe_child(_resolve_devtext_host(), 0)


def _resolve_created_frame() -> int:
    by_label = int(UIManager.GetFrameIDByLabel(CREATED_LABEL) or 0)
    if by_label > 0:
        return by_label
    return int(CREATED_FRAME_ID or 0)


def _update_cached_state() -> None:
    global LAST_DEVTEXT_ROOT
    global LAST_HOST_FRAME
    global LAST_EXISTING_FRAME
    global LAST_EXISTING_SUMMARY
    global LAST_EXISTING_ENCODED
    global LAST_EXISTING_DECODED
    global LAST_EXISTING_BYTES_HEX
    global LAST_CREATED_SUMMARY
    global LAST_CREATED_ENCODED
    global LAST_CREATED_DECODED
    global LAST_CREATED_BYTES_HEX

    LAST_DEVTEXT_ROOT = _resolve_devtext_root()
    LAST_HOST_FRAME = _resolve_devtext_host()
    LAST_EXISTING_FRAME = _resolve_existing_text_label()

    LAST_EXISTING_SUMMARY = _frame_summary(LAST_EXISTING_FRAME)
    LAST_EXISTING_ENCODED = _read_encoded(LAST_EXISTING_FRAME)
    LAST_EXISTING_DECODED = _read_decoded(LAST_EXISTING_FRAME)
    LAST_EXISTING_BYTES_HEX = _read_encoded_bytes_hex(LAST_EXISTING_FRAME)

    created = _resolve_created_frame()
    LAST_CREATED_SUMMARY = _frame_summary(created)
    LAST_CREATED_ENCODED = _read_encoded(created)
    LAST_CREATED_DECODED = _read_decoded(created)
    LAST_CREATED_BYTES_HEX = _read_encoded_bytes_hex(created)


def _format_create_diagnostics(diag: dict) -> str:
    if not diag:
        return "{}"
    parts = []
    if "template_frame_id" in diag:
        parts.extend(
            [
                f"template_frame_id={diag.get('template_frame_id', 0)}",
                f"template_exists={diag.get('template_exists', False)}",
                f"template_created={diag.get('template_created', False)}",
                f"template_has_text={diag.get('template_has_text', False)}",
                f"template_valid={diag.get('template_valid', False)}",
                f"template_encoded={diag.get('template_encoded', '')!r}",
            ]
        )
    parts.extend(
        [
            f"constructed_valid={diag.get('constructed_valid', False)}",
            f"constructed_encoded={diag.get('constructed_encoded', '')!r}",
            f"constructed_decoded={diag.get('constructed_decoded', '')!r}",
        ]
    )
    return " ".join(parts)


def _ensure_devtext() -> None:
    global LAST_STATUS

    def _invoke() -> None:
        _ = int(GWUI.OpenDevTextWindow() or 0)
        _update_cached_state()
        _log(f"ensure devtext invoke result frame_id={LAST_DEVTEXT_ROOT}")

    LAST_STATUS = "ensure devtext enqueued"
    Py4GW.Game.enqueue(_invoke)
    _log(LAST_STATUS)
    _schedule_report("state after ensure devtext")


def _enqueue_state_snapshot(prefix: str) -> None:
    global LAST_STATUS

    def _invoke() -> None:
        _update_cached_state()
        _log(
            f"{prefix} "
            f"devtext_root=({_frame_summary(LAST_DEVTEXT_ROOT)}) "
            f"host=({_frame_summary(LAST_HOST_FRAME)}) "
            f"existing=({LAST_EXISTING_SUMMARY}) "
            f"existing_encoded='{LAST_EXISTING_ENCODED}' "
            f"existing_decoded='{LAST_EXISTING_DECODED}' "
            f"existing_bytes_hex='{LAST_EXISTING_BYTES_HEX}' "
            f"created=({LAST_CREATED_SUMMARY}) "
            f"created_encoded='{LAST_CREATED_ENCODED}' "
            f"created_decoded='{LAST_CREATED_DECODED}' "
            f"created_bytes_hex='{LAST_CREATED_BYTES_HEX}'"
        )

    LAST_STATUS = f"snapshot enqueued prefix='{prefix}'"
    Py4GW.Game.enqueue(_invoke)


def _probe_existing() -> None:
    global LAST_STATUS

    def _invoke() -> None:
        _update_cached_state()
        _log(
            f"probe existing selected=({LAST_EXISTING_SUMMARY}) "
            f"encoded='{LAST_EXISTING_ENCODED}' "
            f"decoded='{LAST_EXISTING_DECODED}' "
            f"bytes_hex='{LAST_EXISTING_BYTES_HEX}'"
        )

    LAST_STATUS = "probe existing enqueued"
    Py4GW.Game.enqueue(_invoke)
    _log(LAST_STATUS)
    _schedule_report("state after probe existing")


def _create_literal_label() -> None:
    global LAST_STATUS
    global CREATED_FRAME_ID
    global LAST_CREATE_DIAGNOSTICS

    def _invoke() -> None:
        global CREATED_FRAME_ID
        global LAST_CREATE_DIAGNOSTICS
        try:
            root = _resolve_devtext_root()
            host = _resolve_devtext_host()
            existing = _resolve_existing_text_label()
            _log(
                f"create literal label invoke begin root={root} host={host} existing={existing}"
            )
            _update_cached_state()
            parent = int(host or 0)
            if parent <= 0:
                _log("create literal label invoke aborted: host unavailable")
                return
            child_offset = int(GWUI.FindAvailableChildSlot(parent, 0x20, 0xFE) or 0)
            _log(
                f"create literal label invoke slot parent={parent} child_offset=0x{child_offset:X}"
            )
            if child_offset <= 0:
                _log("create literal label invoke aborted: no child slot available")
                return
            diag = GWUI.GetTextLabelLiteralCreatePayloadDiagnostics(
                CREATE_TEXT,
            )
            LAST_CREATE_DIAGNOSTICS = _format_create_diagnostics(diag)
            _log(f"create literal label invoke diagnostics {LAST_CREATE_DIAGNOSTICS}")
            CREATED_FRAME_ID = int(
                GWUI.CreateTextLabelFrameWithPlainTextByFrameId(
                    parent,
                    0x300,
                    child_offset,
                    CREATE_TEXT,
                    CREATED_LABEL,
                )
                or 0
            )
            _log(
                f"create literal label invoke raw result parent={parent} child_offset=0x{child_offset:X} "
                f"created={CREATED_FRAME_ID}"
            )
            _update_cached_state()
            _log(
                f"create literal label invoke result created_summary=({LAST_CREATED_SUMMARY}) "
                f"created_encoded='{LAST_CREATED_ENCODED}' created_decoded='{LAST_CREATED_DECODED}' "
                f"created_bytes_hex='{LAST_CREATED_BYTES_HEX}'"
            )
        except Exception as exc:
            _log(f"create literal label invoke exception: {exc}")

    LAST_STATUS = "create literal label enqueued"
    Py4GW.Game.enqueue(_invoke)
    _log(LAST_STATUS)
    _schedule_report("state after create literal label")


def _clock_update_created() -> None:
    global LAST_STATUS

    def _invoke() -> None:
        _update_cached_state()
        created = _resolve_created_frame()
        if created <= 0:
            _log("clock update invoke aborted: created frame unavailable")
            return
        ok = bool(UIManager.SendFrameUIMessageWString(created, 0x4D, UPDATE_TEXT))
        _update_cached_state()
        _log(
            f"clock update invoke result created={created} ok={ok} "
            f"created_encoded='{LAST_CREATED_ENCODED}' created_decoded='{LAST_CREATED_DECODED}' "
            f"created_bytes_hex='{LAST_CREATED_BYTES_HEX}'"
        )

    LAST_STATUS = "clock update created enqueued"
    Py4GW.Game.enqueue(_invoke)
    _log(LAST_STATUS)
    _schedule_report("state after clock update created")


def _draw_window() -> None:
    global WINDOW_OPEN
    global READ_DELAY_SECONDS
    global CREATE_TEXT
    global UPDATE_TEXT

    if not PyImGui.begin(f"{MODULE_NAME}##{SCRIPT_REVISION}", WINDOW_OPEN):
        PyImGui.end()
        return

    PyImGui.text(f"revision: {SCRIPT_REVISION}")
    PyImGui.text("flow: Ensure DevText -> Probe existing -> Create Literal Label -> Clock Update Created")
    PyImGui.separator()

    READ_DELAY_SECONDS = float(
        _normalize_input_int(
            PyImGui.input_int("Read Delay (ms)", int(READ_DELAY_SECONDS * 1000.0)),
            int(READ_DELAY_SECONDS * 1000.0),
        )
    ) / 1000.0
    if PyImGui.button("Ensure DevText"):
        _ensure_devtext()
    PyImGui.same_line(0.0, 8.0)
    if PyImGui.button("Probe existing host[0]"):
        _probe_existing()
    PyImGui.same_line(0.0, 8.0)
    if PyImGui.button("Create Literal Label"):
        _create_literal_label()
    PyImGui.same_line(0.0, 8.0)
    if PyImGui.button("Clock Update Created"):
        _clock_update_created()

    if PyImGui.button("Use Short Create"):
        CREATE_TEXT = "Py4GW Text Label Test"
    PyImGui.same_line(0.0, 8.0)
    if PyImGui.button("Use Quote-Help Create"):
        CREATE_TEXT = 'Need to buy or sell in bulk? Hold Ctrl when clicking "Request Quote" to choose a quantity.'
    PyImGui.same_line(0.0, 8.0)
    if PyImGui.button("Use Short Update"):
        UPDATE_TEXT = "Py4GW Clock Style Update"
    PyImGui.same_line(0.0, 8.0)
    if PyImGui.button("Use Quote-Help Update"):
        UPDATE_TEXT = 'Need to buy or sell in bulk? Hold Ctrl when clicking "Request Quote" to choose a quantity.'
    PyImGui.same_line(0.0, 8.0)
    if PyImGui.button("Dump State"):
        _enqueue_state_snapshot("manual state report")

    PyImGui.separator()
    PyImGui.text(f"last_status={LAST_STATUS}")
    PyImGui.text(f"create_text={CREATE_TEXT!r}")
    PyImGui.text(f"update_text={UPDATE_TEXT!r}")
    PyImGui.text_wrapped(f"create_diagnostics={LAST_CREATE_DIAGNOSTICS}")
    PyImGui.text(f"devtext_root={LAST_DEVTEXT_ROOT}")
    PyImGui.text(f"host={LAST_HOST_FRAME}")
    PyImGui.text(f"existing={LAST_EXISTING_FRAME}")
    PyImGui.text(f"created={CREATED_FRAME_ID}")
    PyImGui.text(f"existing_decoded='{LAST_EXISTING_DECODED}'")
    PyImGui.text(f"created_decoded='{LAST_CREATED_DECODED}'")
    PyImGui.text_wrapped(f"existing_bytes_hex={LAST_EXISTING_BYTES_HEX}")
    PyImGui.text_wrapped(f"created_bytes_hex={LAST_CREATED_BYTES_HEX}")

    PyImGui.end()


def main() -> None:
    global INITIALIZED
    if not INITIALIZED:
        INITIALIZED = True
        _log(f"script revision={SCRIPT_REVISION}")
        _log("test flow:")
        _log("1) click 'Ensure DevText'")
        _log("2) click 'Probe existing host[0]'")
        _log("3) click 'Use Short Create' or 'Use Quote-Help Create'")
        _log("4) click 'Create Literal Label'")
        _log("5) click 'Use Short Update' or 'Use Quote-Help Update'")
        _log("6) click 'Clock Update Created'")
    _process_pending_reports()
    _draw_window()


if __name__ == "__main__":
    main()
