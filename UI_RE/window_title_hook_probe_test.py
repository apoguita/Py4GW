import ctypes

import PyImGui

from Py4GWCoreLib import Scanner
from Py4GWCoreLib.native_src.internals.native_function import NativeFunction, ScannerSection
from Py4GWCoreLib.native_src.internals.prototypes import NativeFunctionPrototype, Prototypes


MODULE_NAME = "Window Title Hook Probe"
SCRIPT_REVISION = "2026-03-09-window-title-hook-probe-1"
WINDOW_OPEN = True
INITIALIZED = False

MAX_XREFS = 8
SCAN_AHEAD = 0x40
LAST_STATUS = "idle"
RESULT_LINES: list[str] = []

STATIC_UI_DEVTEXT_DIALOG_PROC = 0x00864170
STATIC_UI_BUILD_COMPOSITE_WINDOW_THEN_SET_TITLE = 0x0055DCF0
STATIC_UI_POSTBUILD_SET_FRAME_TITLE_AND_RESOURCE = 0x0055E0C0
STATIC_UI_SET_FRAME_TEXT = 0x00610B00
STATIC_UI_SET_FRAME_ENCODED_TEXT_RESOURCE = 0x00610B70
STATIC_UI_CREATE_ENCODED_TEXT = 0x007A1560

CREATE_ENCODED_TEXT_FN = None
SET_FRAME_TEXT_FN = None
SET_FRAME_ENCODED_TEXT_RESOURCE_FN = None

U32_U32_WCHARP_U32_RET_U32 = NativeFunctionPrototype(
    ctypes.c_uint32,
    ctypes.c_uint32,
    ctypes.c_uint32,
    ctypes.c_wchar_p,
    ctypes.c_uint32,
)


def _log(message: str) -> None:
    print(f"[{MODULE_NAME}] {message}")


def _push(message: str) -> None:
    RESULT_LINES.append(message)
    _log(message)


def _read_u8(address: int) -> int:
    return int(ctypes.c_ubyte.from_address(address).value)


def _read_i32(address: int) -> int:
    return int(ctypes.c_int32.from_address(address).value)


def _hex_bytes(address: int, size: int) -> str:
    if address <= 0 or size <= 0:
        return ""
    raw = ctypes.string_at(address, size)
    return " ".join(f"{b:02X}" for b in raw)


def _resolve_relative_call_target(call_addr: int) -> int:
    if call_addr <= 0:
        return 0
    try:
        if _read_u8(call_addr) != 0xE8:
            return 0
        rel = _read_i32(call_addr + 1)
        return int(call_addr + 5 + rel)
    except (ValueError, OSError):
        return 0


def _resolve_support_functions() -> bool:
    global CREATE_ENCODED_TEXT_FN
    global SET_FRAME_TEXT_FN
    global SET_FRAME_ENCODED_TEXT_RESOURCE_FN

    if CREATE_ENCODED_TEXT_FN is None:
        CREATE_ENCODED_TEXT_FN = NativeFunction(
            name="Ui_CreateEncodedText",
            pattern=(
                b"\x55\x8B\xEC\x51\x56\x57\xE8\x00\x00\x00\x00\x8B\x48\x18"
                b"\xE8\x00\x00\x00\x00\x8B\xF8"
            ),
            mask="xxxxxxx????xxxx????xx",
            offset=0,
            section=ScannerSection.TEXT,
            prototype=U32_U32_WCHARP_U32_RET_U32,
            use_near_call=False,
            report_success=True,
        )

    if SET_FRAME_TEXT_FN is None:
        SET_FRAME_TEXT_FN = NativeFunction(
            name="Ui_SetFrameText",
            pattern=b"\x55\x8B\xEC\x53\x56\x57\x8B\x7D\x08\x8B\xF7\xF7\xDE\x1B\xF6\x85",
            mask="xxxxxxxxxxxxxxxx",
            offset=0,
            section=ScannerSection.TEXT,
            prototype=Prototypes["Void_U32_U32"],
            use_near_call=False,
            report_success=True,
        )

    if SET_FRAME_ENCODED_TEXT_RESOURCE_FN is None:
        SET_FRAME_ENCODED_TEXT_RESOURCE_FN = NativeFunction(
            name="Ui_SetFrameEncodedTextResource",
            pattern=bytes.fromhex(
                "55 8B EC 53 56 57 8B 7D 08 8B F7 F7 DE 1B F6 85 FF 75 14 68 D2 0B 00 00"
            ),
            mask="x" * 24,
            offset=0,
            section=ScannerSection.TEXT,
            prototype=Prototypes["Void_U32_U32"],
            use_near_call=False,
            report_success=True,
        )

    return (
        CREATE_ENCODED_TEXT_FN.is_valid()
        and SET_FRAME_TEXT_FN.is_valid()
        and SET_FRAME_ENCODED_TEXT_RESOURCE_FN.is_valid()
    )


def _probe_xrefs() -> None:
    create_addr = int(CREATE_ENCODED_TEXT_FN.get_address() or 0)
    set_text_addr = int(SET_FRAME_TEXT_FN.get_address() or 0)
    set_resource_addr = int(SET_FRAME_ENCODED_TEXT_RESOURCE_FN.get_address() or 0)

    _push(
        "support functions "
        f"create=0x{create_addr:X} "
        f"set_text=0x{set_text_addr:X} "
        f"set_resource=0x{set_resource_addr:X}"
    )

    any_match = False
    runtime_slide = 0
    for xref_index in range(MAX_XREFS):
        try:
            use_addr = int(Scanner.FindNthUseOfStringW("DlgDevText", xref_index, 0, 0) or 0)
        except Exception:
            use_addr = 0
        if use_addr <= 0:
            _push(f"xref[{xref_index}] use=0x0")
            continue

        try:
            proc_addr = int(Scanner.ToFunctionStart(use_addr, 0x1200) or 0)
        except Exception:
            proc_addr = 0
        if proc_addr > 0 and runtime_slide == 0:
            runtime_slide = int(proc_addr - STATIC_UI_DEVTEXT_DIALOG_PROC)

        _push(
            f"xref[{xref_index}] use=0x{use_addr:X} "
            f"proc=0x{proc_addr:X} "
            f"bytes={_hex_bytes(use_addr, 24)}"
        )

        found_create_return = 0
        found_set_text_return = 0
        found_set_resource_return = 0
        call_summaries: list[str] = []

        for addr in range(use_addr, use_addr + SCAN_AHEAD):
            try:
                target = _resolve_relative_call_target(addr)
            except Exception:
                target = 0
            if target <= 0:
                continue

            call_summaries.append(f"call@0x{addr:X}->0x{target:X}")
            if target == create_addr and not found_create_return:
                found_create_return = addr + 5
            if target == set_text_addr and not found_set_text_return:
                found_set_text_return = addr + 5
            if target == set_resource_addr and not found_set_resource_return:
                found_set_resource_return = addr + 5

        if call_summaries:
            _push(f"xref[{xref_index}] calls {' | '.join(call_summaries)}")

        _push(
            f"xref[{xref_index}] returns "
            f"create=0x{found_create_return:X} "
            f"set_text=0x{found_set_text_return:X} "
            f"set_resource=0x{found_set_resource_return:X}"
        )

        if found_create_return and found_set_text_return and found_set_resource_return:
            any_match = True

    _push(f"resolver_summary all_three_found={any_match}")
    if runtime_slide:
        _push(
            "runtime slide "
            f"0x{runtime_slide:X} "
            f"devtext=0x{STATIC_UI_DEVTEXT_DIALOG_PROC + runtime_slide:X} "
            f"build_composite=0x{STATIC_UI_BUILD_COMPOSITE_WINDOW_THEN_SET_TITLE + runtime_slide:X} "
            f"postbuild=0x{STATIC_UI_POSTBUILD_SET_FRAME_TITLE_AND_RESOURCE + runtime_slide:X}"
        )
        _probe_runtime_functions(runtime_slide)


def _collect_calls(start_addr: int, size: int) -> list[tuple[int, int]]:
    calls: list[tuple[int, int]] = []
    if start_addr <= 0 or size <= 0:
        return calls
    for addr in range(start_addr, start_addr + size):
        target = _resolve_relative_call_target(addr)
        if target > 0:
            calls.append((addr, target))
    return calls


def _format_call_list(label: str, calls: list[tuple[int, int]]) -> None:
    if not calls:
        _push(f"{label} no_calls")
        return
    joined = " | ".join(f"call@0x{addr:X}->0x{target:X}" for addr, target in calls)
    _push(f"{label} {joined}")


def _probe_runtime_functions(runtime_slide: int) -> None:
    build_runtime = STATIC_UI_BUILD_COMPOSITE_WINDOW_THEN_SET_TITLE + runtime_slide
    postbuild_runtime = STATIC_UI_POSTBUILD_SET_FRAME_TITLE_AND_RESOURCE + runtime_slide
    expected_create = STATIC_UI_CREATE_ENCODED_TEXT + runtime_slide
    expected_set_text = STATIC_UI_SET_FRAME_TEXT + runtime_slide
    expected_set_resource = STATIC_UI_SET_FRAME_ENCODED_TEXT_RESOURCE + runtime_slide

    _push(
        "expected runtimes "
        f"create=0x{expected_create:X} "
        f"set_text=0x{expected_set_text:X} "
        f"set_resource=0x{expected_set_resource:X}"
    )

    build_calls = _collect_calls(build_runtime, 0x1C0)
    postbuild_calls = _collect_calls(postbuild_runtime, 0x120)

    _format_call_list("build_composite_calls", build_calls)
    _format_call_list("postbuild_calls", postbuild_calls)

    build_set_text = [addr + 5 for addr, target in build_calls if target == expected_set_text]
    build_set_resource = [addr + 5 for addr, target in build_calls if target == expected_set_resource]
    postbuild_create = [addr + 5 for addr, target in postbuild_calls if target == expected_create]
    postbuild_set_text = [addr + 5 for addr, target in postbuild_calls if target == expected_set_text]
    postbuild_set_resource = [addr + 5 for addr, target in postbuild_calls if target == expected_set_resource]

    _push(
        "build_composite_expected_matches "
        f"set_text={','.join(f'0x{x:X}' for x in build_set_text) or 'none'} "
        f"set_resource={','.join(f'0x{x:X}' for x in build_set_resource) or 'none'}"
    )
    _push(
        "postbuild_expected_matches "
        f"create={','.join(f'0x{x:X}' for x in postbuild_create) or 'none'} "
        f"set_text={','.join(f'0x{x:X}' for x in postbuild_set_text) or 'none'} "
        f"set_resource={','.join(f'0x{x:X}' for x in postbuild_set_resource) or 'none'}"
    )


def _run_probe() -> None:
    global LAST_STATUS
    RESULT_LINES.clear()

    if not _resolve_support_functions():
        LAST_STATUS = "support function resolution failed"
        _push(LAST_STATUS)
        return

    _probe_xrefs()
    LAST_STATUS = "probe complete"


def _draw_window() -> None:
    global WINDOW_OPEN
    global SCAN_AHEAD
    global MAX_XREFS

    if not PyImGui.begin(f"{MODULE_NAME}##{SCRIPT_REVISION}", WINDOW_OPEN):
        PyImGui.end()
        return

    MAX_XREFS = max(1, int(PyImGui.input_int("Max Xrefs", int(MAX_XREFS))))
    SCAN_AHEAD = max(8, int(PyImGui.input_int("Scan Ahead", int(SCAN_AHEAD))))

    if PyImGui.button("Run Probe"):
        _run_probe()

    PyImGui.separator()
    PyImGui.text(f"revision: {SCRIPT_REVISION}")
    PyImGui.text("goal: verify the Python-visible support patterns and the DlgDevText xref call chain")
    PyImGui.text(f"last_status={LAST_STATUS}")
    PyImGui.text(f"result_lines={len(RESULT_LINES)}")

    if PyImGui.begin_child("results", [0.0, 300.0], True):
        for line in RESULT_LINES[-80:]:
            PyImGui.text_wrapped(line)
        PyImGui.end_child()

    PyImGui.end()


def main() -> None:
    global INITIALIZED
    if not INITIALIZED:
        INITIALIZED = True
        _log(f"script revision={SCRIPT_REVISION}")
        _log("use 'Run Probe' and paste the resulting console output")
    _draw_window()


if __name__ == "__main__":
    main()
