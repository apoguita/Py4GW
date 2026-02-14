import datetime
from Py4GWCoreLib.enums_src.Py4GW_enums import Console
from Py4GWCoreLib.py4gwcorelib_src.WidgetManager import get_widget_handler
from Sources.frenkeyLib.LootEx import enum, inventory_handling, settings
from Py4GWCoreLib import Inventory, Player
from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE
from Py4GWCoreLib.Py4GWcorelib import ActionQueueNode, ConsoleLog
from Py4GWCoreLib.enums import SharedCommandType

action_node = ActionQueueNode(150)


start : datetime.datetime = datetime.datetime.now()
is_collecting = False

def ResetMessages():
    messages = GLOBAL_CACHE.ShMem.GetAllMessages()
    messages = [msg for msg in messages if msg[1].Command == SharedCommandType.LootEx]
    
    for index, message in messages:
        receiverEmail = message.ReceiverEmail
        GLOBAL_CACHE.ShMem.MarkMessageAsFinished(receiverEmail, index)

def SendReloadProfiles():
    ResetMessages()
    
    for acc in GLOBAL_CACHE.ShMem.GetAllAccountData():
        if acc.AccountEmail == Player.GetAccountEmail():
            continue
        
        if not acc.AccountEmail:
            continue
    
        GLOBAL_CACHE.ShMem.SendMessage(Player.GetAccountEmail(), acc.AccountEmail, SharedCommandType.LootEx, (enum.MessageActions.ReloadProfiles, 0, 0))

def SendMergingMessage():
    global is_collecting
    
    ResetMessages()
    account_email = Player.GetAccountEmail()
    
    if not account_email:
        ConsoleLog("LootEx", "No current account set, cannot send merging message.", False)
        return
    
    for acc in GLOBAL_CACHE.ShMem.GetAllAccountData():
        if acc.AccountEmail == account_email:
            continue
    
        GLOBAL_CACHE.ShMem.SendMessage(account_email, acc.AccountEmail, SharedCommandType.LootEx, (enum.MessageActions.PauseDataCollection, 0, 0))
        
    MergeWhenCollectionPaused()
        
def MergeWhenCollectionPaused():    
    from Sources.frenkeyLib.LootEx.data import Data
    data = Data()
    
    messages = GLOBAL_CACHE.ShMem.GetAllMessages()
    messages = [msg for msg in messages if msg[1].Command == SharedCommandType.LootEx]
    account_email = Player.GetAccountEmail()
    
    for index, message in messages:
        if message.Command == SharedCommandType.LootEx:
            param = int(message.Params[0] if len(message.Params) > 0 else 0)
            
            if param == enum.MessageActions.PauseDataCollection:      
                if message.ReceiverEmail == account_email:
                    GLOBAL_CACHE.ShMem.MarkMessageAsFinished(account_email, index)   
                else:                  
                    ConsoleLog("LootEx", f"Waiting for account '{message.ReceiverEmail}' to pause data collection... Current Account {account_email}", Console.MessageType.Info)     
                    action_node.add_action(
                        MergeWhenCollectionPaused
                    )                
                    return False
    
    data.MergeDiffItems()
    
    for acc in GLOBAL_CACHE.ShMem.GetAllAccountData():
        if acc.AccountEmail == account_email:
            continue
        
        GLOBAL_CACHE.ShMem.SendMessage(account_email, acc.AccountEmail, SharedCommandType.LootEx, (enum.MessageActions.ReloadData, 0, 0))
        GLOBAL_CACHE.ShMem.SendMessage(account_email, acc.AccountEmail, SharedCommandType.LootEx, (enum.MessageActions.StartDataCollection, 0, 0))
    
    from Sources.frenkeyLib.LootEx import settings
    settings = settings.Settings()
    settings.collect_items = True
    
    return True

def SendStart(exclude_self: bool = False):    
    for acc in GLOBAL_CACHE.ShMem.GetAllAccountData():
        if exclude_self and acc.AccountEmail == Player.GetAccountEmail():
            continue
    
        GLOBAL_CACHE.ShMem.SendMessage(Player.GetAccountEmail(), acc.AccountEmail, SharedCommandType.LootEx, (enum.MessageActions.Start, 0, 0))

def SendStop(exclude_self: bool = False):    
    for acc in GLOBAL_CACHE.ShMem.GetAllAccountData():
        if exclude_self and acc.AccountEmail == Player.GetAccountEmail():
            continue
    
        GLOBAL_CACHE.ShMem.SendMessage(Player.GetAccountEmail(), acc.AccountEmail, SharedCommandType.LootEx, (enum.MessageActions.Stop, 0, 0))

def SendLootingStart(exclude_self: bool = False):    
    for acc in GLOBAL_CACHE.ShMem.GetAllAccountData():
        if exclude_self and acc.AccountEmail == Player.GetAccountEmail():
            continue
    
        GLOBAL_CACHE.ShMem.SendMessage(Player.GetAccountEmail(), acc.AccountEmail, SharedCommandType.LootEx, (enum.MessageActions.LootStart, 0, 0))

def SendLootingStop(exclude_self: bool = False):    
    for acc in GLOBAL_CACHE.ShMem.GetAllAccountData():
        if exclude_self and acc.AccountEmail == Player.GetAccountEmail():
            continue
    
        GLOBAL_CACHE.ShMem.SendMessage(Player.GetAccountEmail(), acc.AccountEmail, SharedCommandType.LootEx, (enum.MessageActions.LootStop, 0, 0))

def SendShowLootExWindow(exclude_self: bool = False):
    for acc in GLOBAL_CACHE.ShMem.GetAllAccountData():
        if exclude_self and acc.AccountEmail == Player.GetAccountEmail():
            continue
    
        GLOBAL_CACHE.ShMem.SendMessage(Player.GetAccountEmail(), acc.AccountEmail, SharedCommandType.LootEx, (enum.MessageActions.ShowLootExWindow, 0, 0))
        
def SendHideLootExWindow(exclude_self: bool = False):
    for acc in GLOBAL_CACHE.ShMem.GetAllAccountData():
        if exclude_self and acc.AccountEmail == Player.GetAccountEmail():
            continue
    
        GLOBAL_CACHE.ShMem.SendMessage(Player.GetAccountEmail(), acc.AccountEmail, SharedCommandType.LootEx, (enum.MessageActions.HideLootExWindow, 0, 0))

def SendOpenXunlai(exclude_self: bool = False):
    for acc in GLOBAL_CACHE.ShMem.GetAllAccountData():
        if exclude_self and acc.AccountEmail == Player.GetAccountEmail():
            continue
    
        GLOBAL_CACHE.ShMem.SendMessage(Player.GetAccountEmail(), acc.AccountEmail, SharedCommandType.LootEx, (enum.MessageActions.OpenXunlai, 0, 0))

def SendStartDataCollection(exclude_self: bool = False):
    global is_collecting
    
    for acc in GLOBAL_CACHE.ShMem.GetAllAccountData():
        if exclude_self and acc.AccountEmail == Player.GetAccountEmail():
            continue
    
        GLOBAL_CACHE.ShMem.SendMessage(Player.GetAccountEmail(), acc.AccountEmail, SharedCommandType.LootEx, (enum.MessageActions.StartDataCollection, 0, 0))
    
def SendPauseDataCollection(exclude_self: bool = False):
    global is_collecting
    
    for acc in GLOBAL_CACHE.ShMem.GetAllAccountData():
        if exclude_self and acc.AccountEmail == Player.GetAccountEmail():
            continue
    
        GLOBAL_CACHE.ShMem.SendMessage(Player.GetAccountEmail(), acc.AccountEmail, SharedCommandType.LootEx, (enum.MessageActions.PauseDataCollection, 0, 0))
        
def SendReloadWidgets(exclude_self: bool = False):
    for acc in GLOBAL_CACHE.ShMem.GetAllAccountData():
        if exclude_self and acc.AccountEmail == Player.GetAccountEmail():
            continue
    
        GLOBAL_CACHE.ShMem.SendMessage(Player.GetAccountEmail(), acc.AccountEmail, SharedCommandType.LootEx, (enum.MessageActions.ReloadWidgets, 0, 0))

def ReloadWidgets():    
    widgetHandler = get_widget_handler()
    widgetHandler.discover()

def HandleMessages():
    action_node.ProcessQueue()    
    HandleReceivedMessages()
    
def HandleReceivedMessages():
    from Sources.frenkeyLib.LootEx.settings import Settings
    settings = Settings()
    
    global is_collecting
    account_email = Player.GetAccountEmail()
    
    if not account_email:
        ConsoleLog("LootEx", "No current account set, cannot handle messages.", False)
        return
    
    messages = GLOBAL_CACHE.ShMem.GetAllMessages()
    messages = [msg for msg in messages if msg[1].Command == SharedCommandType.LootEx]

    for index, message in messages:
        if message.Command == SharedCommandType.LootEx:
            if message.ReceiverEmail == account_email:
                param = int(message.Params[0] if len(message.Params) > 0 else 0)
                
                if param > 0:
                    # action : enum.MessageActions = enum.MessageActions(param)
                    
                    match param:
                        case enum.MessageActions.ReloadProfiles:
                            GLOBAL_CACHE.ShMem.MarkMessageAsRunning(Player.GetAccountEmail(), index)
                            
                            if settings.current_character:
                                ConsoleLog("LootEx", "Reloading profiles...")
                                settings.ReloadProfiles()
                                settings.SetProfile(settings.character_profiles[settings.current_character])
                            else:
                                ConsoleLog("LootEx", "Reloading profiles failed because no current character is set ...")
                                
                            GLOBAL_CACHE.ShMem.MarkMessageAsFinished(Player.GetAccountEmail(), index)
                            
                        case enum.MessageActions.PauseDataCollection:
                            ConsoleLog("LootEx", f"Pausing data collection as requested by account '{message.SenderEmail}'...", Console.MessageType.Info)
                            
                            GLOBAL_CACHE.ShMem.MarkMessageAsRunning(Player.GetAccountEmail(), index) 
                            is_collecting = settings.collect_items    
                            settings.collect_items = False
                            GLOBAL_CACHE.ShMem.MarkMessageAsFinished(Player.GetAccountEmail(), index)
                            
                        case enum.MessageActions.ResumeDataCollection:
                            GLOBAL_CACHE.ShMem.MarkMessageAsRunning(Player.GetAccountEmail(), index)                           
                            settings.collect_items = is_collecting                            
                            GLOBAL_CACHE.ShMem.MarkMessageAsFinished(Player.GetAccountEmail(), index)
                            
                        case enum.MessageActions.StartDataCollection:
                            GLOBAL_CACHE.ShMem.MarkMessageAsRunning(Player.GetAccountEmail(), index)
                            settings.collect_items = True                            
                            GLOBAL_CACHE.ShMem.MarkMessageAsFinished(Player.GetAccountEmail(), index)
                        
                        case enum.MessageActions.Start:
                            inventory_handling.InventoryHandler().Start()
                            GLOBAL_CACHE.ShMem.MarkMessageAsFinished(Player.GetAccountEmail(), index)
                            
                        case enum.MessageActions.Stop:
                            inventory_handling.InventoryHandler().Stop()
                            GLOBAL_CACHE.ShMem.MarkMessageAsFinished(Player.GetAccountEmail(), index)
                            
                        case enum.MessageActions.LootStart:
                            inventory_handling.loot_handling.LootHandler().Start()
                            GLOBAL_CACHE.ShMem.MarkMessageAsFinished(Player.GetAccountEmail(), index)
                            
                        case enum.MessageActions.LootStop:
                            inventory_handling.loot_handling.LootHandler().Stop()
                            GLOBAL_CACHE.ShMem.MarkMessageAsFinished(Player.GetAccountEmail(), index)
                                
                        case enum.MessageActions.ReloadData:
                            GLOBAL_CACHE.ShMem.MarkMessageAsRunning(Player.GetAccountEmail(), index)
                            
                            ConsoleLog("LootEx", "Reloading data...")
                            from Sources.frenkeyLib.LootEx.data import Data
                            data = Data()
                            data.Reload()
                            GLOBAL_CACHE.ShMem.MarkMessageAsFinished(Player.GetAccountEmail(), index)
                            
                        case enum.MessageActions.ShowLootExWindow:
                            settings.window_visible = True
                            GLOBAL_CACHE.ShMem.MarkMessageAsFinished(Player.GetAccountEmail(), index)
                            
                        case enum.MessageActions.HideLootExWindow:
                            settings.window_visible = False
                            GLOBAL_CACHE.ShMem.MarkMessageAsFinished(Player.GetAccountEmail(), index)
                            
                        case enum.MessageActions.OpenXunlai:    
                            Inventory.OpenXunlaiWindow()                            
                            GLOBAL_CACHE.ShMem.MarkMessageAsFinished(Player.GetAccountEmail(), index)
                                                
                        case enum.MessageActions.ReloadWidgets:
                            GLOBAL_CACHE.ShMem.MarkMessageAsFinished(Player.GetAccountEmail(), index)
                            ReloadWidgets()
                        
                        case _:
                            GLOBAL_CACHE.ShMem.MarkMessageAsFinished(Player.GetAccountEmail(), index)
                            return