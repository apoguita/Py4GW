import enum
from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE
from Py4GWCoreLib.Player import Player
from Py4GWCoreLib.enums_src.Multiboxing_enums import SharedCommandType
from Py4GWCoreLib.py4gwcorelib_src.Console import Console, ConsoleLog
from Sources.frenkeyLib.MultiBoxing.enum import MultiBoxingMessageType

MODULE_NAME = __file__.split("\\")[-2]

def position_clients(account_mail, regions, accounts):
    for acc in accounts:
        if not acc.AccountEmail:
            continue
        
        ConsoleLog(MODULE_NAME, f"Positioning client for account: {acc.AccountEmail}")
        
        region = next(
            (r for r in regions if r.account == acc.AccountEmail), None) if regions else None

        if region:
            GLOBAL_CACHE.ShMem.SendMessage(account_mail, acc.AccountEmail, SharedCommandType.SetWindowGeometry, (region.x, region.y, region.w, region.h))

    pass


def set_borderless_clients(borderless: bool):
    from Sources.frenkeyLib.MultiBoxing.settings import Settings
    settings = Settings()
    
    regions = settings.regions

    for acc in settings.accounts:
        region = next(
            (r for r in regions if r.account == acc.AccountEmail), None)

        if region:
            GLOBAL_CACHE.ShMem.SendMessage(settings.get_account_mail(
            ), acc.AccountEmail, SharedCommandType.SetBorderless, (1 if borderless else 0, 0, 0, 0))

    pass

def send_reload_settings(settings):
    ConsoleLog(MODULE_NAME, "Sending reload settings command to all clients.", Console.MessageType.Info)
    for acc in settings.accounts:
        GLOBAL_CACHE.ShMem.SendMessage(settings.get_account_mail(
        ), acc.AccountEmail, SharedCommandType.MultiBoxing, (MultiBoxingMessageType.ReloadSettings.value, 0, 0, 0))
    pass


current_account = ""

def handle_reload_settings(index, message):
    from Sources.frenkeyLib.MultiBoxing.settings import Settings
            
    GLOBAL_CACHE.ShMem.MarkMessageAsRunning(current_account, index)
    Settings().load_settings()
    GLOBAL_CACHE.ShMem.MarkMessageAsFinished(current_account, index)

def HandleReceivedMessages():
    global current_account
    
    if not current_account or current_account != Player.GetAccountEmail():
        current_account = Player.GetAccountEmail()
        
        if not current_account:
            return
    
    messages = GLOBAL_CACHE.ShMem.GetAllMessages()
    messages = [msg for msg in messages if msg[1].Command == SharedCommandType.MultiBoxing and msg[1].ReceiverEmail == current_account]

    for index, message in messages:
        param = int(message.Params[0] if len(message.Params) > 0 else 0)        
        msg_type = MultiBoxingMessageType(param) if param in [e.value for e in MultiBoxingMessageType] else None    
        
        match msg_type:
            case MultiBoxingMessageType.ReloadSettings:
                handle_reload_settings(index, message)
            
            case _:
                GLOBAL_CACHE.ShMem.MarkMessageAsFinished(current_account, index)
                        