
import Py4GW

from Py4GWCoreLib.py4gwcorelib_src.Timer import ThrottledTimer
from Py4GW_widget_manager import get_widget_handler

class WidgetMonitor:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(WidgetMonitor, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, "_initialized") and self._initialized:
            return

        self._initialized = True
        self.throttler = ThrottledTimer(5_000)
        self.handler = get_widget_handler()
        
    def act(self):
        if self.throttler.IsExpired(): 
            self.throttler.Reset()
            if self.handler.is_widget_enabled("HeroAI"):
                self.handler.disable_widget("HeroAI")
                Py4GW.Console.Log("CustomBehaviors", "Using CustomBehaviors - HeroAI has been disabled.", Py4GW.Console.MessageType.Error)