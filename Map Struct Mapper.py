import ctypes
import struct

import PyImGui
import PyPointers

from Py4GWCoreLib.native_src.context.InstanceInfoContext import (
    AreaInfoStruct,
    InstanceInfo,
    InstanceInfoStruct,
)
from Py4GWCoreLib.native_src.context.MapContext import MapContextStruct


MODULE_NAME = "Map Struct Mapper"
DUMP_BYTES = 0x100


def _safe_ptr(value: int | None) -> int:
    return int(value or 0)


def _read_bytes(address: int, size: int) -> bytes:
    if address <= 0 or size <= 0:
        return b""
    try:
        return ctypes.string_at(address, size)
    except Exception:
        return b""


def _u16(raw: bytes) -> str:
    return str(struct.unpack("<H", raw[:2])[0]) if len(raw) >= 2 else "-"


def _u32(raw: bytes) -> str:
    return str(struct.unpack("<I", raw[:4])[0]) if len(raw) >= 4 else "-"


def _i32(raw: bytes) -> str:
    return str(struct.unpack("<i", raw[:4])[0]) if len(raw) >= 4 else "-"


def _f32(raw: bytes) -> str:
    if len(raw) < 4:
        return "-"
    value = struct.unpack("<f", raw[:4])[0]
    return f"{value:.6g}" if -1e12 < value < 1e12 else "-"


def _field_map(struct_type: type[ctypes.Structure]) -> dict[int, str]:
    result: dict[int, str] = {}
    for field_name, _field_type in struct_type._fields_:
        result[int(getattr(struct_type, field_name).offset)] = field_name
    return result


AREA_INFO_FIELDS = _field_map(AreaInfoStruct)
INSTANCE_INFO_FIELDS = _field_map(InstanceInfoStruct)
MAP_CONTEXT_FIELDS = _field_map(MapContextStruct)


def _field_spans(struct_type: type[ctypes.Structure]) -> list[tuple[int, int, str]]:
    spans: list[tuple[int, int, str]] = []
    for field_name, _field_type in struct_type._fields_:
        descriptor = getattr(struct_type, field_name)
        spans.append((int(descriptor.offset), int(descriptor.size), field_name))
    return spans


AREA_INFO_SPANS = _field_spans(AreaInfoStruct)
INSTANCE_INFO_SPANS = _field_spans(InstanceInfoStruct)
MAP_CONTEXT_SPANS = _field_spans(MapContextStruct)


class State:
    TARGETS = [
        "CurrentMapInfo",
        "InstanceInfo",
        "MapContext",
        "GameContext",
        "WorldContext",
        "CharContext",
        "AgentContext",
        "Manual",
    ]

    def __init__(self) -> None:
        self.selected_target = 0
        self.manual_address = "0x0"

    def selected_name(self) -> str:
        return self.TARGETS[self.selected_target]

    def resolve_pointers(self) -> dict[str, int]:
        pointers = {name: 0 for name in self.TARGETS}
        try:
            pointers["CurrentMapInfo"] = _safe_ptr(PyPointers.PyPointers.GetAreaInfoPtr())
        except Exception:
            pass
        try:
            pointers["InstanceInfo"] = _safe_ptr(InstanceInfo.get_ptr())
        except Exception:
            pass
        try:
            pointers["MapContext"] = _safe_ptr(PyPointers.PyPointers.GetMapContextPtr())
        except Exception:
            pass
        try:
            pointers["GameContext"] = _safe_ptr(PyPointers.PyPointers.GetGameContextPtr())
        except Exception:
            pass
        try:
            pointers["WorldContext"] = _safe_ptr(PyPointers.PyPointers.GetWorldContextPtr())
        except Exception:
            pass
        try:
            pointers["CharContext"] = _safe_ptr(PyPointers.PyPointers.GetCharContextPtr())
        except Exception:
            pass
        try:
            pointers["AgentContext"] = _safe_ptr(PyPointers.PyPointers.GetAgentContextPtr())
        except Exception:
            pass
        try:
            pointers["Manual"] = int(self.manual_address.strip(), 0)
        except Exception:
            pointers["Manual"] = 0
        return pointers


STATE = State()


def _expected_fields(target_name: str) -> dict[int, str]:
    if target_name == "CurrentMapInfo":
        return AREA_INFO_FIELDS
    if target_name == "InstanceInfo":
        return INSTANCE_INFO_FIELDS
    if target_name == "MapContext":
        return MAP_CONTEXT_FIELDS
    return {}


def _expected_field_spans(target_name: str) -> list[tuple[int, int, str]]:
    if target_name == "CurrentMapInfo":
        return AREA_INFO_SPANS
    if target_name == "InstanceInfo":
        return INSTANCE_INFO_SPANS
    if target_name == "MapContext":
        return MAP_CONTEXT_SPANS
    return []


def _dump_size_for_target(target_name: str) -> int:
    if target_name == "CurrentMapInfo":
        return max(DUMP_BYTES, ctypes.sizeof(AreaInfoStruct))
    if target_name == "InstanceInfo":
        return max(DUMP_BYTES, ctypes.sizeof(InstanceInfoStruct))
    if target_name == "MapContext":
        return max(DUMP_BYTES, ctypes.sizeof(MapContextStruct))
    return DUMP_BYTES


def _field_label_for_offset(offset: int, field_spans: list[tuple[int, int, str]]) -> str:
    for field_offset, field_size, field_name in field_spans:
        if field_offset <= offset < field_offset + field_size:
            delta = offset - field_offset
            return f"{field_name}+{delta}"
    return ""


def draw_memory_table(
    address: int,
    raw: bytes,
    expected_fields: dict[int, str],
    field_spans: list[tuple[int, int, str]],
) -> None:
    flags = (
        PyImGui.TableFlags.BordersInnerV
        | PyImGui.TableFlags.RowBg
        | PyImGui.TableFlags.ScrollX
        | PyImGui.TableFlags.ScrollY
        | PyImGui.TableFlags.SizingFixedFit
    )
    if not PyImGui.begin_table("MapStructMemoryTable", 9, flags):
        return

    PyImGui.table_setup_column("Off", PyImGui.TableColumnFlags.WidthFixed, 70)
    PyImGui.table_setup_column("Addr", PyImGui.TableColumnFlags.WidthFixed, 92)
    PyImGui.table_setup_column("Field Start", PyImGui.TableColumnFlags.WidthFixed, 190)
    PyImGui.table_setup_column("Field Byte", PyImGui.TableColumnFlags.WidthFixed, 190)
    PyImGui.table_setup_column("Bytes", PyImGui.TableColumnFlags.WidthFixed, 140)
    PyImGui.table_setup_column("u16", PyImGui.TableColumnFlags.WidthFixed, 80)
    PyImGui.table_setup_column("u32", PyImGui.TableColumnFlags.WidthFixed, 110)
    PyImGui.table_setup_column("i32", PyImGui.TableColumnFlags.WidthFixed, 110)
    PyImGui.table_setup_column("f32", PyImGui.TableColumnFlags.WidthStretch)
    PyImGui.table_headers_row()

    for offset in range(len(raw)):
        chunk = raw[offset:offset + 8]
        PyImGui.table_next_row()
        PyImGui.table_next_column()
        PyImGui.text_unformatted(f"+0x{offset:04X}")
        PyImGui.table_next_column()
        PyImGui.text_unformatted(f"0x{address + offset:08X}")
        PyImGui.table_next_column()
        PyImGui.text_unformatted(expected_fields.get(offset, ""))
        PyImGui.table_next_column()
        PyImGui.text_unformatted(_field_label_for_offset(offset, field_spans))
        PyImGui.table_next_column()
        PyImGui.text_unformatted(chunk.hex(" ").upper())
        PyImGui.table_next_column()
        PyImGui.text_unformatted(_u16(chunk))
        PyImGui.table_next_column()
        PyImGui.text_unformatted(_u32(chunk))
        PyImGui.table_next_column()
        PyImGui.text_unformatted(_i32(chunk))
        PyImGui.table_next_column()
        PyImGui.text_unformatted(_f32(chunk))

    PyImGui.end_table()


def main() -> None:
    pointers = STATE.resolve_pointers()

    if PyImGui.begin(MODULE_NAME):
        new_target = PyImGui.combo("Pointer", STATE.selected_target, State.TARGETS)
        if new_target != STATE.selected_target:
            STATE.selected_target = new_target

        if STATE.selected_name() == "Manual":
            STATE.manual_address = PyImGui.input_text("Manual Address", STATE.manual_address)

        target_name = STATE.selected_name()
        target_addr = pointers.get(target_name, 0)
        dump_size = _dump_size_for_target(target_name)
        raw = _read_bytes(target_addr, dump_size)
        expected_fields = _expected_fields(target_name)
        field_spans = _expected_field_spans(target_name)

        PyImGui.text_unformatted(f"{target_name}: 0x{target_addr:08X}")
        PyImGui.text_unformatted(f"Dump Size: 0x{dump_size:X}")
        draw_memory_table(target_addr, raw, expected_fields, field_spans)

    PyImGui.end()


if __name__ == "__main__":
    main()
