from time import time

import PyImGui
from HeroAI.utils import SameMapAsAccount, SameMapOrPartyAsAccount
from Py4GWCoreLib import Quest
from Py4GWCoreLib import Utils
from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE
from Py4GWCoreLib.GlobalCache.SharedMemory import AccountData
from Py4GWCoreLib.HotkeyManager import HOTKEY_MANAGER, HotkeyManager
from Py4GWCoreLib.Map import Map
from Py4GWCoreLib.Player import Player
from Py4GWCoreLib.enums_src.IO_enums import Key, ModifierKey
from Py4GWCoreLib.py4gwcorelib_src import Console
from Py4GWCoreLib.py4gwcorelib_src.Console import ConsoleLog

from Py4GWCoreLib.py4gwcorelib_src.WidgetManager import get_widget_handler
from Sources.ApoSource.account_data_src.quest_data_src import QuestNode

MODULE_NAME = "PartyQuestLog"
Utils.ClearSubModules(MODULE_NAME.replace(" ", ""), log=False)
from Sources.frenkeyLib.PartyQuestLog.ui import UI
from Sources.frenkeyLib.PartyQuestLog.settings import Settings
from Sources.frenkeyLib.PartyQuestLog.quest import QuestCache
        
settings = Settings()

UI.QuestLogWindow.window_pos = (settings.LogPosX, settings.LogPosY)
UI.QuestLogWindow.window_size = (settings.LogPosWidth, settings.LogPosHeight)

quest_cache = QuestCache()
fetch_and_handle_quests = True
previous_quest_log : list[int] = [quest.quest_id for quest in quest_cache.quest_data.quest_log.values()]

accounts : dict[int, AccountData] = {}
widget_handler = get_widget_handler()
module_info = None

def open_quest_log_hotkey_callback():    
    if UI.QuestLogWindow.open:
        UI.QuestLogWindow.open = False
        settings.LogOpen = False
        settings.save_settings()
        
    else:
        UI.QuestLogWindow.open = True
        settings.LogOpen = True
        settings.save_settings()

def on_enabled():
    global settings
    settings.load_settings()
    
    settings.hotkey = HOTKEY_MANAGER.register_hotkey(
    key=settings.HotKeyKey,
    identifier=f"{MODULE_NAME}_OpenQuestLog",
    name="Open Party Quest Log",
    callback=open_quest_log_hotkey_callback,
    modifiers=settings.Modifiers
)
    
def on_disabled():
    global settings
    HOTKEY_MANAGER.unregister_hotkey(f"{MODULE_NAME}_OpenQuestLog")

def configure():    
    UI.ConfigWindow.open = True
    UI.draw_configure(accounts)

def create_quest_node_generator(fresh_ids: list[int]):
    for qid in fresh_ids:            
        quest_node = QuestNode(qid)
        quest_cache.quest_data.quest_log[qid] = quest_node
        yield from quest_node.coro_initialize()
        
def fetch_new_quests(fresh_ids: list[int]):
    GLOBAL_CACHE.Coroutines.append(create_quest_node_generator(fresh_ids))

def main():
    global quest_cache, accounts
    
    if not Map.IsMapReady():
        return
        
    shmem_accounts = GLOBAL_CACHE.ShMem.GetAllAccountData()
    quest_log = Quest.GetQuestLog()
    acc_mail = Player.GetAccountEmail()
    new_quest_ids = [q.quest_id for q in quest_log]
    
    if previous_quest_log != new_quest_ids:
        deleted_ids = [qid for qid in previous_quest_log if qid not in new_quest_ids]
        fresh_ids = [qid for qid in new_quest_ids if qid not in previous_quest_log]
            
        for qid in deleted_ids:        
            quest_cache.quest_data.quest_log.pop(qid, None)
            
        if fresh_ids:
            fetch_new_quests(fresh_ids)
        
        previous_quest_log.clear()
        previous_quest_log.extend(new_quest_ids)
    
    accounts.clear()
    for acc in shmem_accounts:        
        if acc.AccountEmail != acc_mail and acc.IsSlotActive:
            if  SameMapOrPartyAsAccount(acc) and acc.PartyID == GLOBAL_CACHE.Party.GetPartyID():
                accounts[acc.PlayerID] = acc     

    if settings.ShowOnlyInParty and not accounts:
        return
    
    if settings.ShowOnlyOnLeader and not GLOBAL_CACHE.Party.GetPartyLeaderID() == Player.GetAgentID():
        return
    
    if fetch_and_handle_quests:    
        quest_cache.quest_data.update()
    
    UI.draw_overlays(accounts)
    
    if Map.WorldMap.IsWindowOpen():
        return
    
    UI.draw_log(quest_cache.quest_data, accounts)
    settings.write_settings()            
    

__all__ = ['main', 'configure']