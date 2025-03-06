from Py4GWCoreLib import *
from datetime import datetime

#### --- LOGGING ROUTINE --- ####
## LogItem (text, Py4Gw.Console.MessageType)
class LogItem:
    """
        LogItem - Log window list item.
        text    - (str) text to show in log window, with timestamp optional
        msgType - (Py4GW.Console.MessageType) message type, changes color Info == White, Error == Red
    """
    def __init__(self, text, msgType):
        self.text = text
        self.msgType = msgType

## LogWindow (optional List[LogItem])
class LogWindow:
    """
        Log Window for adding logs and showing the output section.

        Function:
        Log - (str)(LogItem) log to add, text or LogItem instance.
        Log - (str)(Py4GW.Console.MessageType) log text to add with optional message type.
        DrawWindow - (void) Draws the child window section, enumerating all LogItems showing them sorted by order of add (descending)
    """
    output = []

    def AddLogs(self, logs):
        if type(logs) == list:
            for _, log in enumerate(logs):
                if type(log) == LogItem:
                    self.Log(log.text, log.msgType)
                elif type(log) == str:
                    self.Log(log, Py4Gw.Console.MessageType.Info)
    def ClearLog(self):
        if self.output:
                self.output.clear()

    # create a new LogItem from string and apply message type.
    def Log(self, text, msgType=Py4GW.Console.MessageType.Info):
        now = datetime.now()
        log_now = now.strftime("%H:%M:%S")
        text = f"[{log_now}] {text}"
        logItem = LogItem(text, msgType)
        self.output.insert(0, logItem)

    # Must be called from within a PyImGui.being()
    def DrawWindow(self):
        PyImGui.text("Logs:")
        PyImGui.begin_child("OutputLog", (0.0, -60.0), False, int(PyImGui.WindowFlags.HorizontalScrollbar))        
        for _, logg in enumerate(self.output):
            if logg.msgType == Py4GW.Console.MessageType.Info:
                PyImGui.text(logg.text)
            elif logg.msgType == Py4GW.Console.MessageType.Warning:
                PyImGui.text_colored(logg.text, (1, 1, 0, 1))
            else:
                PyImGui.text_colored(logg.text, (1 ,0, 0, 1))
        PyImGui.end_child()
        
        if PyImGui.button("Clear"):            
            self.ClearLog()
#### --- LOGGING ROUTINE --- ####

#### --- BASIC WINDOW --- ####
class BasicWindow:
    name = "Basic Window"
    size = (300.0, 400.0)
    showLogger = True
    showState = True
    script_running = False
    script_status = "Stopped"
    current_state = "Idle"
    Logger = LogWindow()
    
    id_Items = True
    collect_coins = True
    collect_events = True
    collect_items_white = True
    collect_items_blue = True
    collect_items_grape = True
    collect_items_gold = True
    collect_dye = True
    sell_items = True
    sell_items_white = True
    sell_items_blue = True
    sell_items_grape = True
    sell_items_gold = True
    sell_items_green = True
    sell_materials = True
    salvage_items = False
    salvage_items_white = False
    salvage_items_blue = False
    salvage_items_grape = False
    salvage_items_gold = False

    def __init__(self, window_name="Basic Window", window_size = (300.0, 400.0), show_logger = True, show_state = True):
        self.name = window_name
        self.size = window_size
        self.showLogger = show_logger
        self.showState = show_state
    
    def Show(self):
        # Start Basic Window
        PyImGui.begin(self.name, False, int(PyImGui.WindowFlags.AlwaysAutoResize))        
    
        # Start Main Content
        PyImGui.begin_child("Main Content", self.size, False, int(PyImGui.WindowFlags.AlwaysAutoResize))

        # Show the main control, like # drake flesh or skale fins to collect
        self.ShowMainControls()

        # Show the looting, salvaging, sellting merchant controls
        self.ShowLootMerchantControls()

        # Show the results, override in extended
        self.ShowResults()

        # Show the bot controls, start/stop etc. override in extended
        self.ShowBotControls()

        # Show the output log along the bottom always if enabled
        if self.showLogger:
            PyImGui.separator()
            self.Logger.DrawWindow()

        # Show current state of bot (e.g. Started, Outpost, Dungeon, Stopped) if enabled after logs.
        if self.showState:
            PyImGui.separator()
            PyImGui.text(f"Status: {self.script_status} \t|\t State: {self.current_state}")

        # End MAIN child.        
        PyImGui.end_child()

        # End Basic Window
        PyImGui.end()

    def ChangeSize(self, window_size):
        self.size = window_size
        
    def UpdateStatus(self, newStatus):
        self.script_status = newStatus

    def UpdateState(self, newState):
        self.current_state = newState

    def SetIdleState(self):
        self.script_running = False
        self.current_state = "Idle"

    def ShowMainControls(self):
        PyImGui.text("-What to Collect? - Override This-")

    def ShowLootMerchantControls(self):        
        if PyImGui.collapsing_header("Setup"):          
            if PyImGui.begin_tab_bar("Collectables"):
                if PyImGui.begin_tab_item("Lootables"):
                    if PyImGui.begin_table("Lootables_table", 3):
                        PyImGui.table_next_row()
                        PyImGui.table_next_column()
                        self.collect_coins = PyImGui.checkbox("Money", self.collect_coins)
                        PyImGui.table_next_column()
                        self.collect_events = PyImGui.checkbox("Event Items", self.collect_events)
                        PyImGui.table_next_column()
                        self.collect_dye = PyImGui.checkbox("Dye - B & W", self.collect_dye)
                        PyImGui.table_next_row()
                        PyImGui.table_next_column()
                        self.collect_items_white = PyImGui.checkbox("White Items", self.collect_items_white)
                        PyImGui.table_next_column()
                        self.collect_items_blue = PyImGui.checkbox("Blue Items", self.collect_items_blue)
                        PyImGui.table_next_column()
                        self.collect_items_grape = PyImGui.checkbox("Purple Items", self.collect_items_grape)
                        PyImGui.table_next_row()
                        PyImGui.table_next_column()
                        self.collect_items_gold = PyImGui.checkbox("Gold Items", self.collect_items_gold)
                        PyImGui.table_next_column()
                        PyImGui.table_next_column()
                        PyImGui.table_next_row()
                        PyImGui.end_table()
                    PyImGui.end_tab_item()

                if PyImGui.begin_tab_item("Salvaging"):
                    if PyImGui.begin_table("Salvage_table", 3):
                        PyImGui.table_next_row()
                        PyImGui.table_next_column()
                        self.salvage_items = PyImGui.checkbox("Salvage", self.salvage_items)
                        PyImGui.table_next_column()
                        PyImGui.table_next_column()
                        PyImGui.table_next_row()
                        PyImGui.table_next_column()
                        self.salvage_items_white = PyImGui.checkbox("White Items", self.salvage_items_white)
                        PyImGui.table_next_column()
                        self.salvage_items_blue = PyImGui.checkbox("Blue Items", self.salvage_items_blue)
                        PyImGui.table_next_column()
                        self.salvage_items_grape = PyImGui.checkbox("Purple Items", self.salvage_items_grape)
                        PyImGui.table_next_row()
                        PyImGui.table_next_column()
                        self.salvage_items_gold = PyImGui.checkbox("Gold Items", self.salvage_items_gold)
                        PyImGui.table_next_column()
                        PyImGui.table_next_column()
                        PyImGui.table_next_row()
                        PyImGui.end_table()
                    PyImGui.end_tab_item()

                if PyImGui.begin_tab_item("Selling"):
                    if PyImGui.begin_table("Sell_table", 3):
                        PyImGui.table_next_row()
                        PyImGui.table_next_column()
                        self.sell_items = PyImGui.checkbox("Sell Items", self.sell_items)
                        PyImGui.table_next_column()
                        self.id_Items = PyImGui.checkbox("Id Items", self.id_Items)
                        PyImGui.table_next_column()
                        PyImGui.table_next_row()
                        PyImGui.table_next_column()
                        self.sell_materials = PyImGui.checkbox("Materials", self.sell_materials)
                        PyImGui.table_next_column()
                        self.sell_items_white = PyImGui.checkbox("White Items", self.sell_items_white)
                        PyImGui.table_next_column()
                        self.sell_items_blue = PyImGui.checkbox("Blue Items", self.sell_items_blue)
                        PyImGui.table_next_row()
                        PyImGui.table_next_column()
                        self.sell_items_grape = PyImGui.checkbox("Purple Items", self.sell_items_grape)
                        PyImGui.table_next_column()
                        self.sell_items_gold = PyImGui.checkbox("Gold Items", self.sell_items_gold)
                        PyImGui.table_next_row()
                        PyImGui.end_table()
                    PyImGui.end_tab_item()
                
                PyImGui.end_tab_bar()

    def ShowResults(self):
        PyImGui.text("-Show Results - Override This-")

    # Creates a text block wrapped and colored based on rarity.
    def PrintTextByRarity(self, name, rarity):
        if name:
            if rarity == Rarity.White.value:
                PyImGui.text_wrapped(f"{name}")
            if rarity == Rarity.Blue.value:
                PyImGui.push_style_color(PyImGui.ImGuiCol.Text, (0, .64, 0.91, 1))
                PyImGui.text_wrapped(f"{name}") #, [0, .64, 0.91, 1])
            if rarity == Rarity.Purple.value:
                PyImGui.push_style_color(PyImGui.ImGuiCol.Text, (0.57, .25, 0.57, 1))
                PyImGui.text_wrapped(f"{name}") #, [0.57, .25, 0.57, 1])
            if rarity == Rarity.Gold.value:
                PyImGui.push_style_color(PyImGui.ImGuiCol.Text, (1, .79, 0.05, 1))
                PyImGui.text_wrapped(f"{name}") #, [1, .79, 0.05, 1])
            # Greens aren't salvagable so should NOT get to this ever
            if rarity == Rarity.Green.value:
                PyImGui.push_style_color(PyImGui.ImGuiCol.Text, (.13, .68, 0.29, 1))
                PyImGui.text_wrapped(f"{name}") #, [.13, .68, 0.29, 1])
                
            PyImGui.pop_style_color(1)

    '''
    *   Override in extended classes to customize controls on window.
    '''
    def ShowBotControls(self):
        PyImGui.text("-Bot Controls-")

        if not self.script_running:
            if PyImGui.button("Start"):
                self.StartBot()
        else:   
            if PyImGui.button("Stop"):
                self.StopBot()

    def StartBot(self):
        self.script_running = True
        self.UpdateStatus("Running")
        self.UpdateState("Running")

    def StopBot(self):
        self.script_running = False
        self.UpdateStatus("Stopped")
        self.UpdateState("Idle")

    def ResetBot(self):
        self.SetIdleState()
        self.UpdateStatus("Stopped")
        self.UpdateState("Idle")
        self.Log("Bot Forced Reset")

    def IsBotRunning(self):
        return self.script_running
        
    def ClearLog(self):
        if self.Logger:
            self.Logger.ClearLog()
                       
    def Log(self, text, msgType=Py4GW.Console.MessageType.Info):
        if self.Logger:
           self.Logger.Log(text, msgType)

    def RefreshBags(self):
        pass
           
    def DoneSalvaging(self, finSuccess):
        # check if open, close and then re-open
        self.RefreshBags()

        if finSuccess:
            self.Log("Salvaging: Completed")
        else:
            self.Log("Salvaging: Stopped")

    def DoneIdentifying(self, finSuccess):
        # check if open, close and then re-open
        self.RefreshBags()

        if finSuccess:
            self.Log("Identifying: Completed")
        else:
            self.Log("Identifying: Stopped")
    
#### --- BASIC WINDOW --- ####