from Py4GWCoreLib import *
#do not ever disable this module, it is the main module for everything

MODULE_NAME = "tester for everything"

class WidgetConfig:
    def __init__(self):
        self.throttle = ThrottledTimer(25)
        self.action_queue_manager = ActionQueueManager()
        #LootConfig is kept alive by itself being an instance of LootConfig
        self.loot_config = LootConfig()
        self.raw_agent_array = RawAgentArray()

    
widget_config = WidgetConfig()

def reset_on_load():
    global widget_config
    widget_config.throttle.Reset()
    widget_config.action_queue_manager.ResetAllQueues()
    widget_config.raw_agent_array.reset()


def configure():
    pass

def main():
    global widget_config
    if Map.IsMapLoading():
        reset_on_load()
        return
    
    if not widget_config.throttle.IsExpired():
        return
    
    widget_config.throttle.Reset()
    #KEEPING ALIVE ALL ACTION QUEUES
    widget_config.action_queue_manager.ProcessAll()
    
    #Keeping alive teh RawAgentArray
    widget_config.raw_agent_array.update()
    
    
    
    
    
        
    
    
if __name__ == "__main__":
    main()
