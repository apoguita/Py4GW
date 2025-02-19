from Py4GWCoreLib import *
from datetime import datetime

widget_name = "Salvager"

## These functions live in a more centralized location however 
# that does not play well with bundling single purpose scripts
### --- LOGGING --- ###
# LogItem (text, Py4Gw.Console.MessageType)
class LogItem:
    """
        LogItem - Log window list item.
        text    - (str) text to show in log window, with timestamp optional
        msgType - (Py4GW.Console.MessageType) message type, changes color Info == White, Error == Red
    """
    def __init__(self, text, msgType):
        self.text = text
        self.msgType = msgType

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
                self.Log(log)
                if type(log) == LogItem:
                    self.Log(log)
                elif type(log) == str:
                    self.Log(log, Py4Gw.Console.MessageType.Info)
    def ClearLog(self):
        if self.output:
                self.output.clear()

    # check type of log, append or create LogItem
    def Log(self, logItem):
        if type(logItem) == LogItem:
            self.output.insert(0, logItem)
        elif type(logItem) == str:
            self.Log(logItem, Py4GW.Console.MessageType.Info)

    # create a new LogItem from string and apply message type.
    def Log(self, text, msgType):
        now = datetime.now()
        log_now = now.strftime("%H:%M:%S")
        text = f"[{log_now}] {text}"
        logItem = LogItem(text, msgType)
        self.output.insert(0, logItem)

    # Must be called from within a PyImGui.being()
    def DrawWindow(self):
        PyImGui.text("Logs:")
        PyImGui.begin_child("OutputLog", size=[0.0, -60.0], flags=PyImGui.WindowFlags.HorizontalScrollbar)        
        for _, logg in enumerate(self.output):
            if logg.msgType == Py4GW.Console.MessageType.Info:
                PyImGui.text_wrapped(logg.text)
            elif logg.msgType == Py4GW.Console.MessageType.Warning:
                PyImGui.push_style_color(PyImGui, (1, 1, 0, 1)) 
                PyImGui.text_wrapped(logg.text) #, [1, 1, 0, 1])
                PyImGui.pop_style_color(1)
            else:
                PyImGui.push_style_color(PyImGui.ImGuiCol.Text, (1, 0, 0, 1))
                PyImGui.text_wrapped(logg.text) #, [1 ,0, 0, 1])
                PyImGui.pop_style_color(1)
        PyImGui.end_child()
        
        if PyImGui.button("Clear"):            
            self.ClearLog()
### --- LOGGING --- ###

### --- BASIC WINDOW --- ###
class BasicWindow:
    name = "Basic Window"
    size = [350.0, 400.0]
    script_running = False
    script_status = "Stopped"
    current_state = "Idle"
    Logger = LogWindow()

    prev_action = 0
    salve_items = []
    salve_items_bag_one = []
    salve_items_bag_two = []
    salve_items_bag_three = []
    salve_items_bag_four = []
    salve_count = 0
    id_count = 0

    item_to_salvage = 0
    items_to_identify = []
    
    def __init__(self, window_name="Basic Window", window_size = [350.0, 440.0]):
        self.name = window_name
        self.size = window_size
        self.PopulateSalvageList()
        self.PopulateIdentifyList()
    
    def Show(self):
        # Start Basic Window
        PyImGui.begin(self.name, False, int(PyImGui.WindowFlags.AlwaysAutoResize))        
    
        # Start Main Content
        PyImGui.begin_child("Main Content", self.size, False, int(PyImGui.WindowFlags.AlwaysAutoResize))

        # Show the main control, like # drake flesh or skale fins to collect
        self.ShowMainControls()

        # Show the output log along the bottom always if enabled
        PyImGui.text("ID items and buy salv kits!")
        PyImGui.separator()
        self.Logger.DrawWindow()

        # Show current state of bot (e.g. Started, Outpost, Dungeon, Stopped) if enabled after logs.
        PyImGui.separator()
        PyImGui.text(f"Status: {self.script_status} \t|\t State: {self.current_state}")

        # End MAIN child.        
        PyImGui.end_child()

        # End Basic Window
        PyImGui.end()
    
    def DoneSalvaging(self, finSuccess):
        # check if open, close and then re-open
        self.PopulateSalvageList()

        if finSuccess:
            self.Log("Salvaging: Completed")
        else:
            self.Log("Salvaging: Stopped")

    def DoneIdentifying(self, finSuccess):
        # check if open, close and then re-open
        self.PopulateSalvageList()

        if finSuccess:
            self.Log("Identifying: Completed")
        else:
            self.Log("Identifying: Stopped")

    def UpdateStatus(self, newStatus):
        self.script_status = newStatus

    def UpdateState(self, newState):
        self.current_state = newState

    def ShowMainControls(self):
        PyImGui.text("=== Salvage Items ===")
        PyImGui.begin_child("Salvage Content", [350, 130], False, int(PyImGui.WindowFlags.HorizontalScrollbar))

        #self.Log(len(self.salve_items_bag_one))
        if len(self.salve_items_bag_one) > 0:
            if PyImGui.collapsing_header("Backpack", PyImGui.TreeNodeFlags.DefaultOpen):
                if PyImGui.begin_table("Back_Salv_table", 2, int(PyImGui.TableFlags.SizingStretchProp)):
                    PyImGui.table_setup_column("Item")
                    PyImGui.table_setup_column("Click to Salvage")
                    PyImGui.table_headers_row()
                    for item in self.salve_items_bag_one:
                        if Item.IsNameReady(item.item_id):
                            name = Item.GetName(item.item_id)

                            if name:                                
                                PyImGui.table_next_row()
                                PyImGui.table_next_column()
                                size = PyImGui.calc_text_size(name)

                                if size[0] < 200:
                                    PyImGui.dummy(0, 1) # comment out if not on version with dummy implementation
                                identified = Item.Usage.IsIdentified(item.item_id)
                                self.PrintTextByRarity(name, item.item_id)
                                PyImGui.table_next_column()
                                if identified:
                                    if SalvagerExecuting() or IdentifierExecuting():
                                        PyImGui.text("Working..")
                                    else:
                                        if PyImGui.button(f"Salvage ID: {item.item_id}"):
                                            # start salvage on item_id
                                            self.item_to_salvage = item.item_id
                                            StartSalvage(name, item.item_id)
                                else:
                                    PyImGui.dummy(0, 0) # comment out if not on version with dummy implementation
                                    self.PrintTextByRarity("(Unidentified)", item.item_id)
                    
                    PyImGui.table_next_row()
                    PyImGui.end_table()

        if len(self.salve_items_bag_two) > 0:
            if PyImGui.collapsing_header("Belt Pouch", PyImGui.TreeNodeFlags.DefaultOpen):
                if PyImGui.begin_table("Belt_Salv_table", 2, int(PyImGui.TableFlags.SizingStretchProp)):
                    PyImGui.table_setup_column("Item")
                    PyImGui.table_setup_column("Click to Salvage")
                    PyImGui.table_headers_row()
                    for item in self.salve_items_bag_two:
                        if Item.IsNameReady(item.item_id):
                            name = Item.GetName(item.item_id)

                            if name:
                                PyImGui.table_next_row()
                                PyImGui.table_next_column()
                                size = PyImGui.calc_text_size(name)

                                if size[0] < 200:
                                    PyImGui.dummy(0, 1) # comment out if not on version with dummy implementation
                                identified = Item.Usage.IsIdentified(item.item_id)
                                self.PrintTextByRarity(name, item.item_id)
                                PyImGui.table_next_column()
                                if identified:
                                    if SalvagerExecuting() or IdentifierExecuting():
                                        PyImGui.text("Working..")
                                    else:
                                        if PyImGui.button(f"Salvage ID: {item.item_id}"):
                                            # start salvage on item_id
                                            self.item_to_salvage = item.item_id
                                            StartSalvage(name, item.item_id)
                                else:
                                    PyImGui.dummy(0, 0) # comment out if not on version with dummy implementation
                                    self.PrintTextByRarity("(Unidentified)", item.item_id)
                    
                    PyImGui.table_next_row()
                    PyImGui.end_table()
            
        if len(self.salve_items_bag_three) > 0:
            if PyImGui.collapsing_header("Bag 1", PyImGui.TreeNodeFlags.DefaultOpen):
                if PyImGui.begin_table("Bag1_Salv_table", 2, int(PyImGui.TableFlags.SizingStretchProp)):
                    PyImGui.table_setup_column("Item")
                    PyImGui.table_setup_column("Click to Salvage")
                    PyImGui.table_headers_row()
                    for item in self.salve_items_bag_three:
                        if Item.IsNameReady(item.item_id):
                            name = Item.GetName(item.item_id)

                            if name:
                                PyImGui.table_next_row()
                                PyImGui.table_next_column()
                                size = PyImGui.calc_text_size(name)

                                if size[0] < 200:
                                    PyImGui.dummy(0, 1) # comment out if not on version with dummy implementation
                                identified = Item.Usage.IsIdentified(item.item_id)
                                self.PrintTextByRarity(name, item.item_id)
                                PyImGui.table_next_column()
                                if identified:
                                    if SalvagerExecuting() or IdentifierExecuting():
                                        PyImGui.text("Working..")
                                    else:
                                        if PyImGui.button(f"Salvage ID: {item.item_id}"):
                                            # start salvage on item_id
                                            self.item_to_salvage = item.item_id
                                            StartSalvage(name, item.item_id)
                                else:
                                    PyImGui.dummy(0, 0) # comment out if not on version with dummy implementation
                                    self.PrintTextByRarity("(Unidentified)", item.item_id)
                    
                    PyImGui.table_next_row()
                    PyImGui.end_table()
            
        if len(self.salve_items_bag_four) > 0:
            if PyImGui.collapsing_header("Bag 2", PyImGui.TreeNodeFlags.DefaultOpen):
                if PyImGui.begin_table("Bag2_Salv_table", 2, int(PyImGui.TableFlags.SizingStretchProp)):
                    PyImGui.table_setup_column("Item")
                    PyImGui.table_setup_column("Click to Salvage")
                    PyImGui.table_headers_row()
                    for item in self.salve_items_bag_four:
                        if Item.IsNameReady(item.item_id):
                            name = Item.GetName(item.item_id)

                            if name:
                                PyImGui.table_next_row()
                                PyImGui.table_next_column()
                                size = PyImGui.calc_text_size(name)

                                if size[0] < 200:
                                    PyImGui.dummy(0, 1) # comment out if not on version with dummy implementation
                                identified = Item.Usage.IsIdentified(item.item_id)
                                self.PrintTextByRarity(name, item.item_id)
                                PyImGui.table_next_column()
                                if identified:
                                    if SalvagerExecuting() or IdentifierExecuting():
                                        PyImGui.text("Working..")
                                    else:
                                        if PyImGui.button(f"Salvage ID: {item.item_id}"):
                                            # start salvage on item_id
                                            self.item_to_salvage = item.item_id
                                            StartSalvage(name, item.item_id)
                                else:
                                    PyImGui.dummy(0, 0) # comment out if not on version with dummy implementation
                                    self.PrintTextByRarity("(Unidentified)", item.item_id)
                    
                    PyImGui.table_next_row()
                    PyImGui.end_table()

        PyImGui.end_child()
        PyImGui.separator()

        PyImGui.text("=== Controls ===")
        PyImGui.text(f"Salvagable Slots: {self.salve_count}")
        PyImGui.text(f"Unidentified Slots: {self.id_count}")

        if PyImGui.button("ID All Items"):
            if len(self.items_to_identify) == 0:
                self.Log("Nothing to Id")
                return
            StartIdentify(self.items_to_identify)
                  
        PyImGui.same_line(90, -1.0)

        if PyImGui.button("Refresh Bags"):
            self.Log("Salvage & Id List Refreshed")
            self.PopulateSalvageList()
            self.PopulateIdentifyList()

        PyImGui.same_line(270, -1.0)
        if PyImGui.button("Stop Action"):
            Stop()
        
        PyImGui.separator()

    def PrintTextByRarity(self, name, item_id):
        if name:
            rarity = Item.Rarity.GetRarity(item_id)[1]
            if rarity == Rarity.White.name:
                PyImGui.text_wrapped(f"{name}")
            if rarity == Rarity.Blue.name:
                PyImGui.push_style_color(PyImGui.ImGuiCol.Text, (0, .64, 0.91, 1))
                PyImGui.text_wrapped(f"{name}") #, [0, .64, 0.91, 1])
            if rarity == Rarity.Purple.name:
                PyImGui.push_style_color(PyImGui.ImGuiCol.Text, (0.57, .25, 0.57, 1))
                PyImGui.text_wrapped(f"{name}") #, [0.57, .25, 0.57, 1])
            if rarity == Rarity.Gold.name:
                PyImGui.push_style_color(PyImGui.ImGuiCol.Text, (1, .79, 0.05, 1))
                PyImGui.text_wrapped(f"{name}") #, [1, .79, 0.05, 1])
            if rarity == Rarity.Green.name:
                PyImGui.push_style_color(PyImGui.ImGuiCol.Text, (.13, .68, 0.29, 1))
                PyImGui.text_wrapped(f"{name}") #, [.13, .68, 0.29, 1])
                
            PyImGui.pop_style_color(1)

    def PopulateSalvageList(self):
        self.salve_items_bag_one.clear()
        self.salve_items_bag_two.clear()
        self.salve_items_bag_three.clear()
        self.salve_items_bag_four.clear()
        self.salve_items = self.GetInventoryItemsByBagAndSlot()
        self.salve_count = len(self.salve_items)

        # Need to request the names
        for (bag, item) in self.salve_items:
            Item.RequestName(item.item_id)

            if bag == Bag.Backpack.value:
                self.salve_items_bag_one.append(item)
            if bag == Bag.Belt_Pouch.value:
                self.salve_items_bag_two.append(item)
            if bag == Bag.Bag_1.value:
                self.salve_items_bag_three.append(item)
            if bag == Bag.Bag_2.value:
                self.salve_items_bag_four.append(item)

    def PopulateIdentifyList(self):
        bags_to_check = ItemArray.CreateBagList(1,2,3,4)
        unidentified_items = ItemArray.GetItemArray(bags_to_check)
        unidentified_items = ItemArray.Filter.ByCondition(unidentified_items, lambda item_id: Item.Usage.IsIdentified(item_id) == False)
        unidentified_items = ItemArray.Filter.ByCondition(unidentified_items, lambda item_id: Item.Rarity.IsWhite(item_id) == False)

        self.items_to_identify = unidentified_items
        self.id_count = len(unidentified_items)

    def ValidateItemSelected(self, salvageItem):
        items = self.GetInventoryItemsByBagAndSlot()

        if items:
            for (_, item) in items:
                if item.item_id == salvageItem:
                    return True
                
        return False
    
    def GetItemToSalvageList(self):
        items = self.GetInventoryItemsByBagAndSlot()

        if items:
            all_items_to_salvage = []
            for (_, item) in items:
                if item.item_id == self.item_to_salvage:
                    all_items_to_salvage.append(item.item_id)
                    break
            
            return all_items_to_salvage
        return None
    
    def GetInventoryItemsByBagAndSlot(self):    
        all_item_ids = []  # To store item IDs from all bags

        bags = ItemArray.CreateBagList(1, 2, 3, 4)

        try:
            for bag_enum in bags:
                # Create a Bag instance
                bag_instance = PyInventory.Bag(bag_enum.value, bag_enum.name)
            
                # Get all items in the bag
                items_in_bag = bag_instance.GetItems()
                
                # this is a slot in the bag
                for item in items_in_bag:
                    if Item.Usage.IsSalvageable(item.item_id):
                        all_item_ids.append((bag_enum.value, item))

        except Exception as e:
            Py4GW.Console.Log("GetInventoryItems", f"error in function: {str(e)}", Py4GW.Console.MessageType.Error)

        return all_item_ids

    def StartBot(self):
        self.script_running = True
        self.UpdateStatus("Running")
        self.UpdateState("Running")

    def StopBot(self):
        self.script_running = False
        self.UpdateStatus("Stopped")
        self.UpdateState("Idle")
    
    def ClearLog(self):
        if self.Logger:
            self.Logger.ClearLog()
            
    def Log(self, logItem):
        if self.Logger:
           self.Logger.Log(logItem)
           
    def Log(self, text, msgType=Py4GW.Console.MessageType.Info):
        if self.Logger:
           self.Logger.Log(text, msgType)
### --- BASIC WINDOW --- ###

### --- SALVAGE ROUTINE --- ###
class SalvageFsm(FSM):
    inventoryHandler = PyInventory.PyInventory()   
    logFunc = None
    window = None
    salvage_Items = []
    current_salvage = 0
    current_quantity = 0
    confirmed = False
    pending_stop = False
    salvage_kit = False

    salvager_start = "Start Salvage"
    salvager_continue = "Continue Salvage"
    salvager_finish = "Finish Salvage"
    salvager_check_done = "Salvaging Done?"

    def __init__(self, window=None, name="SalvageFsm", logFunc=None):
        super().__init__(name)

        self.window = window
        self.name = name
        self.logFunc = logFunc

        self.AddState(self.salvager_start,
                        execute_fn=lambda: self.ExecuteStep(self.salvager_start, self.StartSalvage()),
                        transition_delay_ms=100)
        self.AddState(self.salvager_continue,
                        execute_fn=lambda: self.ExecuteStep(self.salvager_continue, self.ContinueSalvage()),
                        transition_delay_ms=100)
        self.AddState(self.salvager_finish,
                        execute_fn=lambda: self.ExecuteStep(self.salvager_finish, self.FinishSalvage()),
                        transition_delay_ms=100)
        self.AddState(self.salvager_check_done,
                        execute_fn=lambda: self.EndSalvageLoop(),
                        transition_delay_ms=100)
    
    def Log(self, text, msgType=Py4GW.Console.MessageType.Info):
        if issubclass(type(self.window), BasicWindow):            
            self.window.Log(text, msgType)

    def ExecuteStep(self, state, function):
        self.UpdateState(state)

        # Try to execute the function if present.        
        try:
            if callable(function):
                function()
        except Exception as e:
            self.Log(f"Calling function {function.__name__} failed. {str(e)}", Py4GW.Console.MessageType.Error)

    def UpdateState(self, state):
        if issubclass(type(self.window), BasicWindow):
            self.window.UpdateState(state)

    def IsExecuting(self):
        return self.is_started() and not self.is_finished()
    
    def SetSalvageItems(self, salvageItems):
        self.salvage_Items = salvageItems

    def StartSalvage(self):
        salvage_kit = Inventory.GetFirstSalvageKit()
        
        if salvage_kit == 0:
            self.Log("No Salvage Kit")
            self.salvage_kit = False
            self.confirmed = False
            return
        
        self.salvage_kit = True

        if self.current_salvage == 0 and self.salvage_Items and isinstance(self.salvage_Items, list) and len(self.salvage_Items) > 0:            
            self.current_salvage = self.salvage_Items.pop(0)
            self.current_quantity = Item.Properties.GetQuantity(self.current_salvage)

        if self.current_salvage == 0:
            return False        

        self.inventoryHandler.StartSalvage(salvage_kit, self.current_salvage)

    def ContinueSalvage(self):
        if not self.salvage_kit:
            return
        
        if not Item.Rarity.IsWhite(self.current_salvage):  
            self.confirmed = True
            Keystroke.PressAndRelease(Key.Y.value)
        #this is a fix for salvaging with a lesser kit, it will press Y to confirm the salvage
        #this produces the default key for minions to open, need to implenet an IF statement 
        #to check wich type os salvaging youre performing
        #the game itself wont salvage an unidentified item, so be aware of that   
        self.inventoryHandler.HandleSalvageUI()
        pass

    def FinishSalvage(self):
        if not self.salvage_kit:
            return
        
        self.inventoryHandler.FinishSalvage()
        pass

    def EndSalvageLoop(self):
        if not self.salvage_kit or self.pending_stop:
            try:
                if self.window:
                    self.window.DoneSalvaging(False)
            except:
                pass  

            return
        
        if not self.IsFinishedSalvage():
            if self.confirmed:  
                Keystroke.PressAndRelease(Key.Y.value)

            self.confirmed = False            
            self.jump_to_state_by_name(self.salvager_start)
        else:
            self.finished = True   
            try:
                if self.window:
                    self.window.DoneSalvaging(True)
            except:
                pass     
        
        return
    
    def IsFinishedSalvage(self): 
        salvage_kit = Inventory.GetFirstSalvageKit()
        
        if self.current_salvage != 0:
            self.current_quantity -= 1

            if self.current_quantity == 0:
                self.current_salvage = 0

        if self.current_salvage == 0:
            return True
        
        if salvage_kit == 0:
            self.Log("No Salvage Kit")
            return True

        return False
        
    def start(self):
        self.pending_stop = False
        super().start()
    def stop(self):
        self.current_salvage = 0
        self.pending_stop = True
### --- SALVAGE ROUTINE --- ###

class IdentifyFsm(FSM):
    logFunc = None
    window = None

    inventory_id_items = "ID Items"
    inventory_id_check = "ID Items Check"

    identifyItems = []
    has_id_kit = True

    def __init__(self, window=None, name="IdentifyFsm", logFunc=None):
        super().__init__(name)

        self.window = window
        self.logFunc = logFunc
        
        self.AddState(name=self.inventory_id_items,
            execute_fn=lambda: self.ExecuteStep(self.inventory_id_items, self.IdentifyItems()),
            transition_delay_ms=150)
        
        self.AddState(name=self.inventory_id_check,
            execute_fn=lambda: self.ExecuteStep(self.inventory_id_items, self.EndIdentifyLoop()),
            transition_delay_ms=150)
        
    def IsExecuting(self):
        return self.is_started() and not self.is_finished()
    
    def ExecuteStep(self, state, function):
        self.UpdateState(state)

        # Try to execute the function if present.        
        try:
            if callable(function):
                function()
        except Exception as e:
            self.window.Log(f"Calling function {function.__name__} failed. {str(e)}", Py4GW.Console.MessageType.Error)

    def UpdateState(self, state):
        if issubclass(type(self.window), BasicWindow):
            self.window.UpdateState(state)

    def SetIdentifyItems(self, identifyItems):
        self.identifyItems = identifyItems

    def IdentifyItems(self): 
        if not self.identifyItems or len(self.identifyItems) == 0:
            return

        id_kit = Inventory.GetFirstIDKit()

        if id_kit == 0:
            self.has_id_kit = False
            return

        idItem = self.identifyItems.pop(0)
        
        if idItem > 0:
            Inventory.IdentifyItem(idItem, id_kit)

    def EndIdentifyLoop(self):
        if not self.has_id_kit:
            if self.window:
                self.window.DoneIdentifying(False)
            
            return
        
        if len(self.identifyItems) == 0:
            if self.window:
                self.window.DoneIdentifying(True)
            
            return            
        
        self.jump_to_state_by_name(self.inventory_id_items)
    
window = BasicWindow("Nikons Salvage")
salvager = SalvageFsm(window)
identifier = IdentifyFsm(window)

def DrawWindow():
    window.Show()

def StartUseInput():
    if not SalvagerExecuting() and not IdentifierExecuting():
        window.prev_action = 1
        if window.item_to_salvage == 0:
            # continue identifying
            StartIdentify(window.items_to_identify)
        else:
            # continue salvaging
            StartSalvage("", window.item_to_salvage)

def StartSalvage(name, salvageItem):
    if not SalvagerExecuting() and not IdentifierExecuting():
        window.prev_action = 1
        if window.ValidateItemSelected(salvageItem):
            if name:
                window.Log(f"Salvaging: {name} started")
            else:
                window.Log(f"Salvaging Item ID: {salvageItem}")
            window.StartBot()
            salvager.SetSalvageItems([salvageItem])
            salvager.reset()
            salvager.start()
        else:
            window.Log("Invalid Item Id")

def StartIdentify(identifyItems):
    if not identifyItems or len(identifyItems) == 0:
        window.Log("No Items To Identify")
        return
    
    if not SalvagerExecuting() and not IdentifierExecuting():
        window.prev_action = 1
        window.item_to_salvage = 0
        window.Log("Identifying: Started")
        window.StartBot()
        identifier.SetIdentifyItems(identifyItems)
        identifier.reset()
        identifier.start()

def Stop():
    if SalvagerExecuting():
        window.StopBot()
        salvager.stop()

def SalvagerExecuting():
    return salvager and salvager.IsExecuting()

def IdentifierExecuting():
    return identifier and identifier.IsExecuting()

def main():
    try:
        if Map.IsMapReady() and Party.IsPartyLoaded():
            DrawWindow()

            if IdentifierExecuting():
                identifier.update()
            elif SalvagerExecuting():
                salvager.update()

    except Exception as e:
        Py4GW.Console.Log(widget_name, f"Error in main: {str(e)}", Py4GW.Console.MessageType.Debug)
        return False
    return True

def configure():
    """Required configuration function for the widget"""
    pass

# These functions need to be available at module level
__all__ = ['main', 'configure']

if __name__ == "__main__":
    main()
