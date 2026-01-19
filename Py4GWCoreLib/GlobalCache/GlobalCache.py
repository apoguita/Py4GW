
from Py4GWCoreLib import ThrottledTimer
from Py4GWCoreLib.Py4GWcorelib import ActionQueueManager

from Py4GWCoreLib import Map
from Py4GWCoreLib import Agent

from .CameraCache import CameraCache
from .EffectCache import EffectsCache
from .ItemCache import RawItemCache, ItemCache, ItemArray
from .InventoryCache import InventoryCache
from .MerchantCache import TradingCache
from .PartyCache import PartyCache
from .QuestCache import QuestCache
from .SkillCache import SkillCache
from .SkillbarCache import SkillbarCache
from .SharedMemory import Py4GWSharedMemoryManager

from typing import Generator, List

class GlobalCache:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(GlobalCache, cls).__new__(cls)
            cls._instance._init_namespaces()
        return cls._instance

    def _init_namespaces(self):
        self._ActionQueueManager = ActionQueueManager()
        self._TrottleTimers = self.TrottleTimers()

        self._RawItemCache = RawItemCache()

        self.Camera = CameraCache(self._ActionQueueManager)
        self.Effects = EffectsCache()
        self.Item = ItemCache(self._RawItemCache)
        self.ItemArray = ItemArray()
        self.Inventory = InventoryCache(self._ActionQueueManager, self._RawItemCache, self.Item)
        self.Trading = TradingCache(self._ActionQueueManager)
        self.Party = PartyCache(self._ActionQueueManager)
        self.Quest = QuestCache(self._ActionQueueManager)
        self.Skill = SkillCache()
        self.SkillBar = SkillbarCache(self._ActionQueueManager)
        self.ShMem = Py4GWSharedMemoryManager()
        self.Coroutines: List[Generator] = []
        
      
    def _reset(self):
        Agent._reset_cache()
        self.Effects._reset_cache()

        self.Item._reset_cache()
        self._TrottleTimers.Reset()
        
    def _update_cache(self):
        #this block is forcing an update when loading or in cinematic
        #to default everything to 0 
        if Map.IsMapLoading() or Map.IsInCinematic():
            self.Party._update_cache()

            self._RawItemCache.update()
            self.Item._update_cache()

            Agent._update_cache()

            self.SkillBar._update_cache()
        #end force update block
               
        if self._TrottleTimers._75ms.IsExpired():
            self._TrottleTimers._75ms.Reset()
            if self._TrottleTimers._500ms.IsExpired():
                self._TrottleTimers._500ms.Reset()
            
            if self._TrottleTimers._150ms.IsExpired():   
                self._TrottleTimers._150ms.Reset()
                self.Party._update_cache()

                self._RawItemCache.update()
                self.Item._update_cache()
                self.Camera._update_cache()

             
            Agent._update_cache()

            self.SkillBar._update_cache()
                       

    class TrottleTimers:
        def __init__(self):
            self._50ms = ThrottledTimer(50)
            self._63ms = ThrottledTimer(63) #4 frames
            self._75ms = ThrottledTimer(75)
            self._100ms = ThrottledTimer(100)
            self._150ms = ThrottledTimer(150)
            self._250ms = ThrottledTimer(250)
            self._500ms = ThrottledTimer(500)
            self._1_000ms = ThrottledTimer(1000)
            self._5_000ms = ThrottledTimer(5000)
            self._10_000ms = ThrottledTimer(10000)         

        def Reset(self):
            self._50ms.Reset()
            self._63ms.Reset()
            self._75ms.Reset()
            self._100ms.Reset()
            self._150ms.Reset()
            self._250ms.Reset()
            self._500ms.Reset()
            self._1_000ms.Reset()
            self._5_000ms.Reset()
            self._10_000ms.Reset()
    
        