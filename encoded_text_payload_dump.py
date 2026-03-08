import ctypes
import time

import Py4GW
from Py4GWCoreLib import GWContext, PyImGui
from Py4GWCoreLib.native_src.internals.native_function import NativeFunction, ScannerSection
from Py4GWCoreLib.native_src.internals.prototypes import NativeFunctionPrototype, Prototypes


MODULE_NAME = "Encoded Text Payload Dump"
SCRIPT_REVISION = "2026-03-06-encoded-text-payload-dump-1"
WINDOW_OPEN = True
REVISION_LOGGED = False

READ_BYTES = 128
LITERAL_TEXT = "DlgDevText"
STRING_ID = 0x541

CREATE_ENCODED_TEXT_FN = None
CREATE_ENCODED_TEXT_FROM_ID_FN = None

LAST_STATUS = "idle"
LAST_RESULTS: list[str] = []


U32_U32_WCHARP_U32_RET_U32 = NativeFunctionPrototype(
    ctypes.c_uint32,
    ctypes.c_uint32,
    ctypes.c_uint32,
    ctypes.c_wchar_p,
    ctypes.c_uint32,
)


def _log(message: str) -> None:
    print(f"[{MODULE_NAME}] {message}")


def _append_result(message: str) -> None:
    LAST_RESULTS.append(message)
    _log(message)


def _resolve_functions() -> bool:
    global CREATE_ENCODED_TEXT_FN
    global CREATE_ENCODED_TEXT_FROM_ID_FN

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

    if CREATE_ENCODED_TEXT_FROM_ID_FN is None:
        CREATE_ENCODED_TEXT_FROM_ID_FN = NativeFunction(
            name="Ui_CreateEncodedTextFromStringId",
            pattern=b"\x55\x8B\xEC\x6A\x00\xFF\x75\x08\xE8\x13\x00\x00\x00\x83\xC4\x08\x5D\xC3",
            mask="xxxxxxxxxxxxxxxxxx",
            offset=0,
            section=ScannerSection.TEXT,
            prototype=NativeFunctionPrototype(ctypes.c_uint32, ctypes.c_uint32),
            use_near_call=False,
            report_success=True,
        )

    return CREATE_ENCODED_TEXT_FN.is_valid() and CREATE_ENCODED_TEXT_FROM_ID_FN.is_valid()


def _hex_dump(ptr: int, size: int) -> str:
    if ptr <= 0 or size <= 0:
        return ""
    data = ctypes.string_at(ptr, size)
    return " ".join(f"{byte:02X}" for byte in data)


def _u32_words(ptr: int, count: int) -> str:
    if ptr <= 0 or count <= 0:
        return ""
    values = []
    for index in range(count):
        try:
            value = ctypes.c_uint32.from_address(ptr + index * 4).value
        except (ValueError, OSError):
            break
        values.append(f"+0x{index * 4:02X}=0x{value:08X}")
    return " ".join(values)


def _wstring_at_offset(ptr: int, offset: int, max_chars: int = 64) -> str:
    if ptr <= 0:
        return ""
    try:
        value = ctypes.wstring_at(ptr + offset, max_chars)
    except (ValueError, OSError):
        return ""
    return value.split("\x00", 1)[0]


def _dump_payload(label: str, ptr: int) -> None:
    _append_result(f"{label} ptr=0x{ptr:X}")
    if ptr <= 0:
        return
    _append_result(f"{label} words {_u32_words(ptr, 12)}")
    _append_result(f"{label} bytes {_hex_dump(ptr, READ_BYTES)}")
    for offset in (0x0, 0x4, 0x8, 0x10, 0x18, 0x20, 0x28, 0x30):
        text = _wstring_at_offset(ptr, offset)
        if text:
            _append_result(f"{label} wstring@+0x{offset:X}='{text}'")


def _run_literal_dump() -> None:
    global LAST_STATUS
    if GWContext.Char.GetContext() is None:
        LAST_STATUS = "char_context_unavailable"
        _log(LAST_STATUS)
        return
    if not _resolve_functions():
        LAST_STATUS = "native functions unresolved"
        _log(LAST_STATUS)
        return

    text = LITERAL_TEXT

    def _work() -> None:
        ptr = int(CREATE_ENCODED_TEXT_FN.directCall(8, 7, text, 0) or 0)
        _dump_payload(f"literal '{text}'", ptr)

    Py4GW.Game.enqueue(_work)
    LAST_STATUS = f"literal dump enqueued text='{text}'"
    _log(LAST_STATUS)


def _run_compare_dump() -> None:
    global LAST_STATUS
    if GWContext.Char.GetContext() is None:
        LAST_STATUS = "char_context_unavailable"
        _log(LAST_STATUS)
        return
    if not _resolve_functions():
        LAST_STATUS = "native functions unresolved"
        _log(LAST_STATUS)
        return

    text_a = "DlgDevText"
    text_b = LITERAL_TEXT

    def _work() -> None:
        ptr_a = int(CREATE_ENCODED_TEXT_FN.directCall(8, 7, text_a, 0) or 0)
        ptr_b = int(CREATE_ENCODED_TEXT_FN.directCall(8, 7, text_b, 0) or 0)
        _dump_payload(f"compare A '{text_a}'", ptr_a)
        _dump_payload(f"compare B '{text_b}'", ptr_b)

    Py4GW.Game.enqueue(_work)
    LAST_STATUS = f"compare dump enqueued a='{text_a}' b='{text_b}'"
    _log(LAST_STATUS)


def _run_string_id_dump() -> None:
    global LAST_STATUS
    if GWContext.Char.GetContext() is None:
        LAST_STATUS = "char_context_unavailable"
        _log(LAST_STATUS)
        return
    if not _resolve_functions():
        LAST_STATUS = "native functions unresolved"
        _log(LAST_STATUS)
        return

    string_id = int(STRING_ID)

    def _work() -> None:
        ptr = int(CREATE_ENCODED_TEXT_FROM_ID_FN.directCall(string_id) or 0)
        _dump_payload(f"string_id 0x{string_id:X}", ptr)

    Py4GW.Game.enqueue(_work)
    LAST_STATUS = f"string-id dump enqueued id=0x{string_id:X}"
    _log(LAST_STATUS)


def _run_compare_string_ids_dump() -> None:
    global LAST_STATUS
    if GWContext.Char.GetContext() is None:
        LAST_STATUS = "char_context_unavailable"
        _log(LAST_STATUS)
        return
    if not _resolve_functions():
        LAST_STATUS = "native functions unresolved"
        _log(LAST_STATUS)
        return

    string_id_a = 0x541
    string_id_b = int(STRING_ID)

    def _work() -> None:
        ptr_a = int(CREATE_ENCODED_TEXT_FROM_ID_FN.directCall(string_id_a) or 0)
        ptr_b = int(CREATE_ENCODED_TEXT_FROM_ID_FN.directCall(string_id_b) or 0)
        _dump_payload(f"string_id A 0x{string_id_a:X}", ptr_a)
        _dump_payload(f"string_id B 0x{string_id_b:X}", ptr_b)

    Py4GW.Game.enqueue(_work)
    LAST_STATUS = f"compare string-id dump enqueued a=0x{string_id_a:X} b=0x{string_id_b:X}"
    _log(LAST_STATUS)


def main() -> None:
    global WINDOW_OPEN
    global REVISION_LOGGED
    global READ_BYTES
    global LITERAL_TEXT
    global STRING_ID

    if not WINDOW_OPEN:
        return

    if not REVISION_LOGGED:
        REVISION_LOGGED = True
        _log(f"script revision={SCRIPT_REVISION}")
        _log("test flow:")
        _log("1) click 'Dump Literal Payload'")
        _log("2) click 'Compare DlgDevText vs Literal'")
        _log("3) click 'Dump String ID Payload'")
        _log("4) click 'Compare String ID Payloads'")

    if PyImGui.begin(f"{MODULE_NAME}##{MODULE_NAME}", WINDOW_OPEN):
        PyImGui.text("Dump returned encoded-text payload objects directly from Python")
        LITERAL_TEXT = str(PyImGui.input_text("Literal Text", LITERAL_TEXT))
        STRING_ID = int(PyImGui.input_int("String ID", int(STRING_ID)))
        READ_BYTES = int(PyImGui.input_int("Read Bytes", int(READ_BYTES)))

        if PyImGui.button("Dump Literal Payload"):
            _run_literal_dump()
        PyImGui.same_line(0.0, -1.0)
        if PyImGui.button("Compare DlgDevText vs Literal"):
            _run_compare_dump()
        PyImGui.same_line(0.0, -1.0)
        if PyImGui.button("Dump String ID Payload"):
            _run_string_id_dump()
        PyImGui.same_line(0.0, -1.0)
        if PyImGui.button("Compare String ID Payloads"):
            _run_compare_string_ids_dump()

        PyImGui.separator()
        PyImGui.text("Paste the console log back after each dump.")
        PyImGui.text(f"Status: {LAST_STATUS}")
        if LAST_RESULTS:
            PyImGui.text(f"Last Result: {LAST_RESULTS[-1]}")

    PyImGui.end()


if __name__ == "__main__":
    main()
