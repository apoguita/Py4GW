from time import time

import Py4GW
import PyImGui
from HeroAI.utils import SameMapAsAccount, SameMapOrPartyAsAccount
from Py4GWCoreLib import ImGui, Quest
from Py4GWCoreLib import Utils
from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE
from Py4GWCoreLib.GlobalCache.SharedMemory import AccountStruct
from Py4GWCoreLib.HotkeyManager import HOTKEY_MANAGER, HotkeyManager
from Py4GWCoreLib.ImGui_src.types import Alignment
from Py4GWCoreLib.Map import Map
from Py4GWCoreLib.Party import Party
from Py4GWCoreLib.Player import Player
from Py4GWCoreLib.Routines import Routines
from Py4GWCoreLib.enums_src.IO_enums import Key, ModifierKey
from Py4GWCoreLib.py4gwcorelib_src import Console
from Py4GWCoreLib.py4gwcorelib_src.Color import Color
from Py4GWCoreLib.py4gwcorelib_src.Console import ConsoleLog

from Py4GWCoreLib.py4gwcorelib_src.Timer import ThrottledTimer
from Py4GWCoreLib.py4gwcorelib_src.WidgetManager import get_widget_handler
from Sources.ApoSource.account_data_src.quest_data_src import QuestNode

MODULE_NAME = "Party Quest Log"
MODULE_ICON = "Textures/Module_Icons/Party Quest Log.png"
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
previous_character = ""

throttle = ThrottledTimer(1000)
is_party_leader = False
accounts : dict[int, AccountStruct] = {}
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

def on_enable():
    global settings
    settings.load_settings()
        
    UI.QuestLogWindow.window_pos = (settings.LogPosX, settings.LogPosY)
    UI.QuestLogWindow.window_size = (settings.LogPosWidth, settings.LogPosHeight)

    settings.hotkey = HOTKEY_MANAGER.register_hotkey(
    key=settings.HotKeyKey,
    identifier=f"{MODULE_NAME}_OpenQuestLog",
    name="Open Party Quest Log",
    callback=open_quest_log_hotkey_callback,
    modifiers=settings.Modifiers
)
    
def on_disable():
    global settings
    HOTKEY_MANAGER.unregister_hotkey(f"{MODULE_NAME}_OpenQuestLog")

def configure():    
    UI.ConfigWindow.open = True
    UI.draw_configure(accounts)

def create_quest_node_generator(fresh_ids: list[int]):
    global quest_cache, previous_character
    
    for qid in fresh_ids:            
        if previous_character != Player.GetName():
            return
        
        quest_node = QuestNode(qid)
        quest_cache.quest_data.quest_log[qid] = quest_node
        
        yield from quest_node.coro_initialize()
        
def fetch_new_quests(fresh_ids: list[int]):
    GLOBAL_CACHE.Coroutines.append(create_quest_node_generator(fresh_ids))

def main():
    global quest_cache, accounts, previous_character, is_party_leader
     
    if not Map.IsMapReady() and not Map.IsInCinematic():
        return        
    
    if throttle.IsExpired():
        throttle.Reset()
        
        if Party.IsPartyLoaded():
            character_name = Player.GetName()
            quest_log = Quest.GetQuestLog()
            new_quest_ids = [q.quest_id for q in quest_log]
            
            if previous_quest_log != new_quest_ids:
                character_changed = character_name != previous_character and previous_character != "" and character_name != ""
                
                deleted_ids = [qid for qid in previous_quest_log if qid not in new_quest_ids] if not character_changed else previous_quest_log
                fresh_ids = [qid for qid in new_quest_ids if qid not in previous_quest_log] if not character_changed else new_quest_ids
                    
                for qid in deleted_ids:        
                    quest_cache.quest_data.quest_log.pop(qid, None)
                
                if fresh_ids:
                    fetch_new_quests(fresh_ids)
                
                previous_quest_log.clear()
                previous_quest_log.extend(new_quest_ids)
                previous_character = character_name
            
        accounts.clear()
        shmem_accounts = GLOBAL_CACHE.ShMem.GetAllAccountData()
        acc_mail = Player.GetAccountEmail()
        
        for acc in shmem_accounts:        
            if acc.AccountEmail != acc_mail and acc.IsSlotActive:
                if  SameMapOrPartyAsAccount(acc) and acc.AgentPartyData.PartyID == GLOBAL_CACHE.Party.GetPartyID():
                    accounts[acc.AgentData.AgentID] = acc     
        
        is_party_leader = GLOBAL_CACHE.Party.GetPartyLeaderID() == Player.GetAgentID()
            
        if fetch_and_handle_quests:    
            quest_cache.quest_data.update()
        
    settings.write_settings()  
    
    if settings.ShowOnlyOnLeader and not is_party_leader:
        return
    
    if settings.ShowOnlyInParty and not accounts:
        return
    
    UI.draw_overlays(accounts)
    
    if Map.WorldMap.IsWindowOpen():
        return
    
    UI.draw_log(quest_cache.quest_data, accounts)          


def tooltip():
    PyImGui.set_next_window_size((600, 0))
    PyImGui.begin_tooltip()

    # Title
    title_color = Color(255, 200, 100, 255)
    ImGui.image(MODULE_ICON, (32, 32))
    PyImGui.same_line(0, 10)
    ImGui.push_font("Regular", 20)
    ImGui.text_aligned(MODULE_NAME, alignment=Alignment.MidLeft, color=title_color.color_tuple, height=32)
    ImGui.pop_font()
    PyImGui.spacing()
    PyImGui.spacing()
    PyImGui.separator()

    # Description
    PyImGui.text_wrapped("This widget displays the active quests of your party members on your mission map and mini map (compass) and a detailed log window.\nIt helps you keep track of everyone's quests, making it easier to coordinate and complete them together.")
    
    PyImGui.spacing()

    # Features
    PyImGui.text_colored("Features:", title_color.to_tuple_normalized())
    PyImGui.bullet_text("Show active quests of party members on the mission map and mini map.")
    PyImGui.bullet_text("Detailed quest log window with quest names and completion status.")
    PyImGui.bullet_text("Configurable hotkey to open/close the quest log window.")
    PyImGui.bullet_text("Options to show the log only when in a party and/or only for the party leader.")

    PyImGui.spacing()
    PyImGui.separator()
    PyImGui.spacing()

    # Credits
    PyImGui.text_colored("Credits:", title_color.to_tuple_normalized())
    PyImGui.bullet_text("Developed by frenkey")

    PyImGui.end_tooltip()
    
    

__all__ = ['main', 'configure']