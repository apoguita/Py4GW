"""
Minimal packet sniffer test widget.

One button toggles capture:
- First press: start StoC and CToS capture and buffer packets in memory.
- Second press: stop capture and print all buffered packet details to console.
"""

from __future__ import annotations

import Py4GW
import PyImGui

from Py4GWCoreLib import Color, ImGui
from Py4GWCoreLib.PacketSniffer import SNIFFER as PACKET_SNIFFER

MODULE_NAME = "Packet Sniffer Tester"
MODULE_ICON = "Textures/Module_Icons/Debug.png"

_capturing = False
_stoc_packets: list[tuple[int, int, bytes]] = []
_ctos_packets: list[tuple[int, int, bytes]] = []
_last_status = "Idle"

def _drain_into_buffers() -> None:
    logs = PACKET_SNIFFER.get_logs()
    for entry in logs:
        packet = (int(entry.header), int(entry.size), bytes(entry.data))
        if entry.direction == "StoC":
            _stoc_packets.append(packet)
        else:
            _ctos_packets.append(packet)
    if logs:
        PACKET_SNIFFER.clear_logs()


def _hex_preview(raw: bytes, limit: int = 24) -> str:
    return raw[:limit].hex(" ")


def _packet_name(direction: str, header: int) -> str:
    return PACKET_SNIFFER.get_packet_name(direction, header)


def _decode_packet(direction: str, header: int, size: int, raw: bytes) -> str:
    return PACKET_SNIFFER.decode_packet(direction, header, size, raw)


def _dump_packets() -> None:
    Py4GW.Console.Log(
        MODULE_NAME,
        f"Dumping capture: StoC={len(_stoc_packets)} CToS={len(_ctos_packets)}",
        Py4GW.Console.MessageType.Info,
    )

    for index, (header, size, raw) in enumerate(_stoc_packets):
        decoded = _decode_packet("StoC", header, size, raw)
        Py4GW.Console.Log(
            MODULE_NAME,
            f"[StoC #{index}] {decoded} copied={len(raw)} raw={_hex_preview(raw)}",
            Py4GW.Console.MessageType.Info,
        )

    for index, (header, size, raw) in enumerate(_ctos_packets):
        decoded = _decode_packet("CToS", header, size, raw)
        Py4GW.Console.Log(
            MODULE_NAME,
            f"[CToS #{index}] {decoded} copied={len(raw)} raw={_hex_preview(raw)}",
            Py4GW.Console.MessageType.Info,
        )


def _start_capture() -> None:
    global _capturing, _last_status

    _stoc_packets.clear()
    _ctos_packets.clear()
    PACKET_SNIFFER.clear_logs()

    started = PACKET_SNIFFER.initialize()
    if not started:
        _last_status = "Start failed: unified PacketSniffer initialization returned False"
        Py4GW.Console.Log(MODULE_NAME, _last_status, Py4GW.Console.MessageType.Error)
        PACKET_SNIFFER.terminate()
        return

    _capturing = True
    _last_status = "Capturing"
    Py4GW.Console.Log(MODULE_NAME, "Capture started.", Py4GW.Console.MessageType.Success)


def _stop_capture() -> None:
    global _capturing, _last_status

    _drain_into_buffers()
    PACKET_SNIFFER.terminate()
    _capturing = False
    _last_status = f"Stopped. StoC={len(_stoc_packets)} CToS={len(_ctos_packets)}"
    Py4GW.Console.Log(MODULE_NAME, _last_status, Py4GW.Console.MessageType.Info)
    _dump_packets()


def draw_window() -> None:
    global _last_status

    PyImGui.set_next_window_size((520, 180), PyImGui.ImGuiCond.FirstUseEver)
    if PyImGui.begin(MODULE_NAME, PyImGui.WindowFlags.AlwaysAutoResize):
        if _capturing:
            _drain_into_buffers()

        title_color = Color(255, 200, 100, 255).to_tuple_normalized()
        PyImGui.text_colored("Minimal Packet Capture", title_color)
        PyImGui.separator()

        label = "Stop Capture + Dump" if _capturing else "Start Capture"
        if PyImGui.button(label):
            if _capturing:
                _stop_capture()
            else:
                _start_capture()

        PyImGui.separator()
        PyImGui.text(f"Status: {_last_status}")
        PyImGui.text(f"Buffered StoC packets: {len(_stoc_packets)}")
        PyImGui.text(f"Buffered CToS packets: {len(_ctos_packets)}")
        PyImGui.text("Press once to start, press again to stop and print everything to console.")

    PyImGui.end()


def tooltip() -> None:
    PyImGui.begin_tooltip()
    title_color = Color(255, 200, 100, 255).to_tuple_normalized()
    ImGui.push_font("Regular", 20)
    PyImGui.text_colored("Packet Sniffer Tester", title_color)
    ImGui.pop_font()
    PyImGui.separator()
    PyImGui.text("Single-button packet capture test.")
    PyImGui.bullet_text("Start capture")
    PyImGui.bullet_text("Walk, interact, use skills")
    PyImGui.bullet_text("Stop capture and dump all details to console")
    PyImGui.end_tooltip()


def main() -> None:
    draw_window()
