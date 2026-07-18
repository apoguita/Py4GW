MODULE_NAME = "Active Dialog Viewer"
MODULE_ICON = "Textures/Module_Icons/Script Runner.png"

import traceback

import Py4GW
import PyImGui
from Py4GWCoreLib import Dialog

_dialog_was_active = False


def configure():
    pass


def tooltip():
    PyImGui.begin_tooltip()
    PyImGui.text(MODULE_NAME)
    PyImGui.separator()
    PyImGui.text_wrapped("Displays the current active Guild Wars dialog, the tracked context dialog, and the currently visible dialog buttons.")
    PyImGui.end_tooltip()


def _draw_active_dialog() -> None:
    active = Dialog.get_active_dialog()
    if active is None:
        PyImGui.text("Dialog active: False")
        PyImGui.text("Last selected dialog id: 0x0")
        PyImGui.separator()
        PyImGui.text("<no active dialog>")
        return

    last_selected_dialog_id = 0
    try:
        last_selected_dialog_id = int(Dialog._call_native_dialog_method("get_last_selected_dialog_id", 0) or 0)
    except Exception:
        last_selected_dialog_id = 0

    PyImGui.text("Dialog active: True")
    PyImGui.text(f"Last selected dialog id: 0x{last_selected_dialog_id:X}")
    PyImGui.separator()

    PyImGui.text("Active dialog")
    PyImGui.text(f"dialog_id: 0x{active.dialog_id:X} ({active.dialog_id})")
    PyImGui.text(f"context_dialog_id: 0x{active.context_dialog_id:X} ({active.context_dialog_id})")
    PyImGui.text(f"agent_id: {active.agent_id}")
    PyImGui.text(f"dialog_id_authoritative: {active.dialog_id_authoritative}")
    PyImGui.separator()
    PyImGui.text("Message")
    if active.message:
        PyImGui.text_wrapped(active.message)
    else:
        PyImGui.text("<empty>")
        
    if PyImGui.button("print active dialog to console"):
        Py4GW.Console.Log(MODULE_NAME, f"{active.message}", Py4GW.Console.MessageType.Info)


def _draw_buttons() -> None:
    buttons = Dialog.get_active_dialog_buttons()
    visible_buttons = [button for button in buttons if getattr(button, "dialog_id", 0) != 0]

    PyImGui.separator()
    PyImGui.text(f"Buttons: {len(visible_buttons)}")

    if not visible_buttons:
        PyImGui.text("<no dialog buttons>")
        return

    for index, button in enumerate(visible_buttons):
        PyImGui.separator()
        PyImGui.text(f"Button #{index}")
        PyImGui.text(f"dialog_id: 0x{button.dialog_id:X} ({button.dialog_id})")
        PyImGui.text(f"button_icon: {button.button_icon}")
        PyImGui.text(f"decode_pending: {button.message_decode_pending}")
        if  PyImGui.button(f"copy dialog to clipboard##copy_button_{index}"):
            PyImGui.set_clipboard_text(f"0x{button.dialog_id:X}")
            
        if PyImGui.button(f"Send##dialog_button_{index}"):
            from Py4GWCoreLib.Player import Player
            Player.SendAutomaticDialog(index)
        label = button.message_decoded or button.message
        if label:
            PyImGui.text_wrapped(label)
        else:
            PyImGui.text("<empty>")


def main():
    from Py4GWCoreLib.Routines import Checks
    if not Checks.Map.MapValid():
        return
    
    global _dialog_was_active
    try:
        dialog_active = Dialog.get_active_dialog() is not None
        if _dialog_was_active and not dialog_active:
            try:
                import PyDialog
                PyDialog.PyDialog.clear_cache()
            except Exception:
                pass
        _dialog_was_active = dialog_active

        if PyImGui.begin(MODULE_NAME, PyImGui.WindowFlags.AlwaysAutoResize):
            _draw_active_dialog()
            _draw_buttons()
        PyImGui.end()
    except Exception as e:
        Py4GW.Console.Log(MODULE_NAME, f"Error: {e}", Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log(MODULE_NAME, traceback.format_exc(), Py4GW.Console.MessageType.Error)


if __name__ == "__main__":
    main()
