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
                if type(log) == LogItem:
                    self.Log(log.text, log.msgType)
                elif type(log) == str:
                    self.Log(log, Py4Gw.Console.MessageType.Info)
    def ClearLog(self):
        if self.output:
                self.output.clear()

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
        PyImGui.begin_child("OutputLog", (0.0, -60.0),False, int(PyImGui.WindowFlags.HorizontalScrollbar))        
        for _, logg in enumerate(self.output):
            if logg.msgType == Py4GW.Console.MessageType.Info:
                PyImGui.text_wrapped(logg.text)
            elif logg.msgType == Py4GW.Console.MessageType.Warning:
                PyImGui.push_style_color(PyImGui.ImGuiCol.Text, (1, 1, 0, 1)) 
                PyImGui.text_wrapped(logg.text)
                PyImGui.pop_style_color(1)
            else:
                PyImGui.push_style_color(PyImGui.ImGuiCol.Text, (1, 0, 0, 1))
                PyImGui.text_wrapped(logg.text)
                PyImGui.pop_style_color(1)
        PyImGui.end_child()
        
        if PyImGui.button("Clear"):            
            self.ClearLog()
### --- LOGGING --- ###

### --- BASIC WINDOW --- ###
class BasicWindow:
    name = "Basic Window"
    size = (350.0, 400.0)
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
    
    def __init__(self, window_name="Basic Window", window_size = (350.0, 440.0)):
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
        if PyImGui.collapsing_header("=== Salvage Items ===", int(PyImGui.TreeNodeFlags.DefaultOpen)):
            PyImGui.begin_child("Salvage Content", (0, 150), False, int(PyImGui.WindowFlags.AlwaysAutoResize))

            self.MakeTableAndItemList("Backpack", "Back_Salv_table", self.salve_items_bag_one)            
            self.MakeTableAndItemList("Belt Pouch", "Belt_Salv_table", self.salve_items_bag_two)            
            self.MakeTableAndItemList("Bag 1", "Bag1_Salv_table", self.salve_items_bag_three)                        
            self.MakeTableAndItemList("Bag 2", "Bag2_Salv_table", self.salve_items_bag_four)

            PyImGui.end_child()
        PyImGui.separator()

        if PyImGui.collapsing_header("=== Controls ==="):
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

            PyImGui.same_line(250, -1.0)
            if PyImGui.button("Stop Action"):
                Stop()
            
        # Show the output log along the bottom always if enabled
        PyImGui.text("ID items and buy salv kits!")
        PyImGui.separator()

    def MakeTableAndItemList(self, bag_collapse_name, table_name, bag_items):
        if not isinstance(bag_items, list) or len(bag_items) == 0:
            return
        
        if PyImGui.collapsing_header(bag_collapse_name, PyImGui.TreeNodeFlags.DefaultOpen):
            if PyImGui.begin_table(table_name, 2, int(PyImGui.TableFlags.SizingStretchProp)):
                PyImGui.table_setup_column("Item")
                PyImGui.table_setup_column("Click to Salvage")
                PyImGui.table_headers_row()
                for item in bag_items:
                    if Item.IsNameReady(item.item_id):
                        name = Item.GetName(item.item_id)

                        if name:                                
                            PyImGui.table_next_row()
                            PyImGui.table_next_column()
                            size = PyImGui.calc_text_size(name)

                            if size[0] < 200:
                                PyImGui.dummy(0, 1) # comment out if not on version with dummy implementation
                            identified = Item.Usage.IsIdentified(item.item_id)
                            rarity = Item.Rarity.GetRarity(item.item_id)[0]
                            isWhite = rarity == Rarity.White.value
                            self.PrintTextByRarity(name, rarity)
                            PyImGui.table_next_column()
                            if identified or isWhite:
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

    def PrintTextByRarity(self, name, rarity):
        if name:
            if rarity == Rarity.White.value:
                PyImGui.text_wrapped(f"{name}")
            if rarity == Rarity.Blue.value:
                PyImGui.push_style_color(PyImGui.ImGuiCol.Text, (0, .64, 0.91, 1))
                PyImGui.text_wrapped(f"{name}")
            if rarity == Rarity.Purple.value:
                PyImGui.push_style_color(PyImGui.ImGuiCol.Text, (0.76, .34, 0.76, 1))
                PyImGui.text_wrapped(f"{name}")
            if rarity == Rarity.Gold.value:
                PyImGui.push_style_color(PyImGui.ImGuiCol.Text, (1, .79, 0.05, 1))
                PyImGui.text_wrapped(f"{name}")
            # Greens aren't salvagable so should NOT get to this ever
            if rarity == Rarity.Green.value:
                PyImGui.push_style_color(PyImGui.ImGuiCol.Text, (.13, .68, 0.29, 1))
                PyImGui.text_wrapped(f"{name}")
                
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
                       
    def Log(self, text, msgType=Py4GW.Console.MessageType.Info):
        if self.Logger:
           self.Logger.Log(text, msgType)
### --- BASIC WINDOW --- ###

### --- SALVAGE ROUTINE --- ###
class SalvageFsm(FSM):
    inventoryHandler = PyInventory.PyInventory()   
    salvage_Items = []
    current_salvage = 0
    current_quantity = 0
    current_ping = 0
    default_base_ping = 100
    default_base_wait_no_ping = 350
    pending_stop = False
    salvage_kit = False
    needs_confirm = False

    salvager_start = "Start Salvage"
    salvager_continue = "Using Salvage Kit"
    salvager_ping_check_1 = "Salvaging"
    salvager_finish = "Finish Salvage"

    def __init__(self, window=BasicWindow(), name="SalvageFsm", logFunc=None, pingHandler=Py4GW.PingHandler()):
        super().__init__(name)

        self.window = window
        self.name = name
        self.logFunc = logFunc
        self.pingHandler = pingHandler        
        self.ping_timer = Timer()
        
        self.AddState(self.salvager_start,
                      execute_fn=lambda: self.ExecuteStep(self.salvager_start, self.SetMaxPing()),
                      transition_delay_ms=150)
        self.AddState(self.salvager_continue,
                        execute_fn=lambda: self.ExecuteStep(self.salvager_continue, self.StartSalvage()),
                        transition_delay_ms=150)
        self.AddState(self.salvager_ping_check_1,
                        execute_fn=lambda: self.ExecuteStep(self.salvager_ping_check_1, None),
                        exit_condition=lambda: self.CheckPingContinue(),
                        run_once=False)
        self.AddState(self.salvager_finish,
                        execute_fn=lambda: self.EndSalvageLoop(),
                        transition_delay_ms=150)
    
    def Log(self, text, msgType=Py4GW.Console.MessageType.Info):
        if isinstance(self.window, BasicWindow):
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
        if isinstance(self.window, BasicWindow):
            self.window.UpdateState(state)

    def IsExecuting(self):
        return self.is_started() and not self.is_finished()
    
    def SetMaxPing(self):        
        if self.pingHandler:
            self.current_ping = self.pingHandler.GetMaxPing()

    def CheckPingContinue(self):
        if self.ping_timer:
            if not self.ping_timer.IsRunning():
                self.ping_timer.Start()

            if not self.ping_timer.HasElapsed(self.current_ping*2):
                return False
            
            self.ping_timer.Stop()
        return True

    def SetSalvageItems(self, salvageItems):
        self.salvage_Items = salvageItems
        
    def GetSalvageItemCount(self) -> int:
        return len(self.salvage_Items)

    def StartSalvage(self):
        kitId = Inventory.GetFirstSalvageKit()
        
        if kitId == 0:
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

        Inventory.SalvageItem(self.current_salvage, kitId)
        
    def EndSalvageLoop(self):
        Inventory.AcceptSalvageMaterialsWindow()

        if not self.salvage_kit or self.pending_stop:
            try:
                if self.window:
                    self.window.DoneSalvaging(False)
            except:
                pass  

            return
        
        if not self.IsFinishedSalvage():   
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
        if self.current_salvage != 0:
            self.current_quantity -= 1

            if self.current_quantity <= 0:
                self.current_salvage = 0
        
        kitId = Inventory.GetFirstSalvageKit()
        
        if kitId == 0:
            self.Log("No Salvage Kit")
            self.salvage_kit = False
            return True

        return len(self.salvage_Items) == 0
        
    def start(self):
        self.pending_stop = False
        super().start()

    def stop(self):
        self.current_salvage = 0
        self.pending_stop = True

### --- SALVAGE ROUTINE --- ###
class IdentifyFsm(FSM):
    logFunc = None
    window = BasicWindow()

    inventory_id_items = "ID Items"
    inventory_id_check = "ID Items Check"

    identifyItems = []
    has_id_kit = True

    def __init__(self, window=BasicWindow(), name="IdentifyFsm", logFunc=None):
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

def tooltip():
    import PyImGui
    from Py4GWCoreLib import ImGui, Color
    PyImGui.begin_tooltip()

    # Title
    title_color = Color(255, 200, 100, 255)
    ImGui.push_font("Regular", 20)
    PyImGui.text_colored("Salvager Bot", title_color.to_tuple_normalized())
    ImGui.pop_font()
    PyImGui.spacing()
    PyImGui.separator()
    # Description
    PyImGui.text("Mass salvage items from your inventory")
    PyImGui.spacing()
    # Credits
    PyImGui.text_colored("Credits:", title_color.to_tuple_normalized())
    PyImGui.bullet_text("Developed by LordNikon360")
    PyImGui.end_tooltip()

# These functions need to be available at module level
__all__ = ['main']

if __name__ == "__main__":
    main()
