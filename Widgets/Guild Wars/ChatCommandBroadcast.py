import Py4GW
import PyImGui
from Py4GWCoreLib import ImGui, GLOBAL_CACHE, Player, Map
from Py4GWCoreLib.Py4GWcorelib import ConsoleLog
from Py4GWCoreLib.enums import Key
from Py4GWCoreLib.enums_src.Multiboxing_enums import SharedCommandType

MODULE_NAME = "Chat Command Broadcast"

window_module = ImGui.WindowModule(
    MODULE_NAME,
    window_name="Chat Command Broadcast",
    window_size=(300, 80),
    window_pos=(100, 100),
    window_flags=PyImGui.WindowFlags.AlwaysAutoResize,
    can_close=False,
)

message_text = ""

def broadcast(command: str):
    sender_email = Player.GetAccountEmail()
    all_accounts = GLOBAL_CACHE.ShMem.GetAllAccountData()
    """Send a slash command to all other accounts via shared memory."""
    for account in all_accounts:
        if account.AccountEmail == sender_email:
            continue
        GLOBAL_CACHE.ShMem.SendMessage(
            sender_email,
            account.AccountEmail,
            SharedCommandType.BroadcastChatCommand,
            (0, 0, 0, 0),
            (command,),
        )

def check_inbox():
    my_email = Player.GetAccountEmail()
    index, message = GLOBAL_CACHE.ShMem.PreviewNextMessage(my_email, include_running=False)
    if index == -1 or message is None:
        return
    if message.Command != SharedCommandType.BroadcastChatCommand:
        return  # not ours, leave it for other systems to handle
    extra = message.ExtraData
    if extra:
        command = "".join(ch for ch in extra[0] if ch != '\0').strip()
        if command:
            Player.SendChatCommand(command)
    GLOBAL_CACHE.ShMem.MarkMessageAsFinished(my_email, index)

def DrawWindow():
    global message_text
    try:
        if window_module.begin():
            message_text = PyImGui.input_text("##message", message_text)
            submitted = PyImGui.is_item_deactivated_after_edit()
            if submitted and message_text.strip():
                cmd = message_text.strip().lstrip("/")
                Player.SendChatCommand(cmd)   # send on this account
                broadcast(cmd)                # signal all others
                message_text = ""
            window_module.process_window()
        window_module.end()
    except Exception as e:
        Py4GW.Console.Log(MODULE_NAME, f"Error in DrawWindow: {str(e)}", Py4GW.Console.MessageType.Debug)

def configure():
    pass

def main():
    try:
        check_inbox()
        DrawWindow()
    except Exception as e:
        Py4GW.Console.Log(MODULE_NAME, f"Error in main: {str(e)}", Py4GW.Console.MessageType.Debug)
        return False
    return True

__all__ = ['main', 'configure']

if __name__ == "__main__":
    main()
