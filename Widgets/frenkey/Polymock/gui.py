import importlib
from Py4GWCoreLib import *

from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE
from Py4GWCoreLib.Py4GWcorelib import ConsoleLog
from Widgets.frenkey.Core import utility
from Widgets.frenkey.Core.gui import GUI
from Widgets.frenkey.Polymock import combat, data, state
from datetime import datetime

importlib.reload(combat)
importlib.reload(data)

class UI:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(UI, cls).__new__(cls)
            cls.combat = combat.Combat()
            cls.widget_state = state.WidgetState()
            cls.expanded = False
            cls.gui_open = True
        
        return cls._instance
                    
    def draw(self):
    
        expanded, gui_open = PyImGui.begin_with_close("Polymock Assistant", self.gui_open, PyImGui.WindowFlags.AlwaysAutoResize)
        self.expanded = expanded
        self.gui_open = gui_open
        
        if gui_open:
            PyImGui.dummy(300, 0)
            # quest_index = PyImGui.combo("Quest", self.quest_index, self.quest_names)
            # if quest_index != self.quest_index:
            #     self.quest_index = quest_index
            #     self.widget_state.quest = combat.Polymock_Quests[self.quest_names[self.quest_index]]
            #     ConsoleLog("Polymock", f"Selected quest: {self.widget_state.quest.name}")        
                        
            current_map_id = Map.GetMapID()                        
        
            width, height = PyImGui.get_content_region_avail()
            button_width = (width - 10) / 2
                        
            if self.widget_state.quest:
                PyImGui.text_wrapped(self.widget_state.quest.name if self.widget_state.quest else "No Quest Detected")
                PyImGui.separator()
                
                quest_data = self.widget_state.quest.get_quest_data()
                
                if self.widget_state.has_polymock_piece:
                    PyImGui.text_colored("You have a Polymock Piece in your inventory!", (0.0, 1.0, 0.0, 1.0))
                    PyImGui.text_colored("Register them before we continue!", (0.0, 1.0, 0.0, 1.0))
                    
                    map_id = data.Polymock_Registration[0]
                    position = data.Polymock_Registration[1]
                    
                    if current_map_id == map_id:
                        if PyImGui.button("Move to Polymock Registration", width):
                            Player.Move(position[0], position[1])
                    else:
                        if PyImGui.button("Travel to Rata Sum", width):
                            Map.Travel(map_id)
                            
                elif quest_data and (not self.widget_state.in_arena or quest_data.is_completed):
                    if quest_data.is_completed:
                        PyImGui.text_colored("Quest completed!", (0.0, 1.0, 0.0, 1.0))
                        
                    map_name = ""
                    if quest_data:
                        map_name = Map.GetMapName(quest_data.map_to) if quest_data.map_to > 0 else "Unknown"                
                    
                        if current_map_id == quest_data.map_to:
                            if not self.widget_state.in_arena:
                                if PyImGui.button("Move to Quest Marker", width):
                                    position = (quest_data.marker_x, quest_data.marker_y) if quest_data.marker_x < 100000 and quest_data.marker_y < 100000 else (self.widget_state.quest.marker_x, self.widget_state.quest.marker_y)
                                    # ConsoleLog("Polymock", f"Moving to quest marker at {position}")
                                    Player.Move(position[0], position[1])
                        else:
                            if PyImGui.button(f"Travel to {map_name}", width):
                                Map.Travel(quest_data.map_to)   
                                
                elif PyImGui.is_rect_visible(0, 20) and self.widget_state.quest and self.widget_state.in_arena:       
                    if not self.widget_state.match_started:
                        PyImGui.text_colored("Please select the polymock pieces in the green order below!", (1.0, 0.0, 0.0, 1.0))
                    
                    PyImGui.begin_table("Quest Info", 2, PyImGui.TableFlags.Borders)
                    PyImGui.table_setup_column(self.widget_state.quest.opponent_name)
                    PyImGui.table_setup_column("Counter")
                    
                    PyImGui.table_headers_row()
                    PyImGui.table_next_row()
                    
                    for i in range(0 , 3):
                        PyImGui.table_next_column()
                        name = self.widget_state.quest.polymock_pieces[i].value.name if i < len(self.widget_state.quest.polymock_pieces) else "None"
                        is_current = True
                        GUI.vertical_centered_text(text = name, color = (0.946, 0.672, 0.324, 1.0 if is_current else 0.3))   
                                        
                        PyImGui.table_next_column()                    
                        name = self.widget_state.quest.counter_pieces[i].value.name if i < len(self.widget_state.quest.counter_pieces) else "None"

                        if self.widget_state.quest.counter_pieces[i].value.item_model_id != 0:
                            ImGui.DrawTexture(
                                get_texture_for_model(self.widget_state.quest.counter_pieces[i].value.item_model_id),
                                20, 20,
                            )
                        else:
                            PyImGui.dummy(20, 20)
                        
                        
                        PyImGui.same_line(0, 0)
                        GUI.vertical_centered_text(text = name, color = (0.0, 1.0, 0.0, 1.0))     
                    
                    PyImGui.end_table() 
            else:                 
                PyImGui.text_colored("No Quest Detected", (1.0, 0.0, 0.0, 1.0))
                PyImGui.text_colored("Please grab your quests in Rata Sum!", (1.0, 0.0, 0.0, 1.0))      
                
                if current_map_id == data.Polymock_Registration[0]:
                    if PyImGui.button("Move to Master Hoff", width):
                        position = data.Polymock_Registration[1]
                        Player.Move(data.Polymock_Quests.Master_Hoff.value.marker_x, data.Polymock_Quests.Master_Hoff.value.marker_y)
                
                elif PyImGui.button("Travel to Rata Sum", width):
                    Map.Travel(data.Polymock_Registration[0])
                                                             
                
            if PyImGui.is_rect_visible(0, 20) and self.widget_state.debug:
                PyImGui.begin_table("Debug Table", 2, PyImGui.TableFlags.Borders)
                PyImGui.table_setup_column("Key")
                PyImGui.table_setup_column("Value")
                
                PyImGui.table_headers_row()
                PyImGui.table_next_row()
                PyImGui.table_next_column()                
                        
                PyImGui.text("Map")
                PyImGui.table_next_column()
                PyImGui.text_wrapped(str(Map.GetMapName()) + " (ID: " + str(Map.GetMapID()) + ")")

                PyImGui.table_next_column()
                        
                PyImGui.text("QUEST ID")
                PyImGui.table_next_column()
                PyImGui.text_wrapped(str(GLOBAL_CACHE.Quest.GetActiveQuest()))
                PyImGui.table_next_column()
                        
                # PyImGui.text("Player")
                # PyImGui.table_next_column()
                # if self.combat.player_id:
                #     PyImGui.text_wrapped(str(self.combat.player_name) + " (ID: " + str(self.combat.player_id) + ")")
                # else:
                #     PyImGui.text("None")
                # PyImGui.table_next_column()
                    
                PyImGui.text("Player HP")
                PyImGui.table_next_column()
                if self.combat.player_hp is not None:
                    PyImGui.text_wrapped(f"{self.combat.player_hp:.2f} ({self.combat.player_hp_percent:.2f}%)")
                else:
                    PyImGui.text("None")
                PyImGui.table_next_column()
                    
                PyImGui.text("Player Energy")
                PyImGui.table_next_column()
                if self.combat.player_energy is not None:
                    PyImGui.text_wrapped(f"{self.combat.player_energy:.2f}")                    
                PyImGui.table_next_column()
                
                PyImGui.text("Agents")
                PyImGui.table_next_column()
                agents = AgentArray.GetAgentArray()
                if agents:
                    PyImGui.text_wrapped(f"{len(agents)}")
                else:
                    PyImGui.text("None")

                PyImGui.table_next_column()
                
                PyImGui.text("Target Agent")
                PyImGui.table_next_column()
                if self.combat.target_id:
                    PyImGui.text_wrapped(str(self.combat.target_name)+ " (ID: " + str(self.combat.target_id) + ")")
                else:
                    PyImGui.text("None")
                PyImGui.table_next_column()
                
                PyImGui.text("Target Skill ID")
                PyImGui.table_next_column()
                if self.combat.target_skill_id:
                    PyImGui.text_wrapped(GLOBAL_CACHE.Skill.GetName(self.combat.target_skill_id) + " (ID: " + str(self.combat.target_skill_id) + ")" if self.combat.target_skill_id > 0 else "None")
                else:
                    PyImGui.text("None")
                
                PyImGui.table_next_column()
                PyImGui.text("Block Ready")
                PyImGui.table_next_column()
                PyImGui.text_colored(str(self.combat.target_block_ready), (0.0, 1.0, 0.0, 1.0) if self.combat.target_block_ready else (1.0, 0.0, 0.0, 1.0))
                PyImGui.table_next_column()
                
                PyImGui.text("Interrupt Ready")
                PyImGui.table_next_column()
                PyImGui.text_colored(str(self.combat.target_interrupt_ready), (0.0, 1.0, 0.0, 1.0) if self.combat.target_interrupt_ready else (1.0, 0.0, 0.0, 1.0))
                PyImGui.table_next_column()
                
                PyImGui.text("Opener Used")
                PyImGui.table_next_column()
                PyImGui.text_colored(str(self.combat.opener_used), (0.0, 1.0, 0.0, 1.0) if self.combat.opener_used else (1.0, 0.0, 0.0, 1.0))
                PyImGui.table_next_column()
                    
                PyImGui.text("Target Model ID")
                PyImGui.table_next_column()
                if self.combat.target_model_id:
                    PyImGui.text(f"{self.combat.target_model_id}")
                else:
                    PyImGui.text("None")
                    
                PyImGui.table_next_column()
                PyImGui.text("RECHARGE")
                PyImGui.table_next_column()
                timestamp = datetime.now().timestamp()
                recharge = PySkillbar.Skillbar().GetSkill(8).get_recharge
                
                if recharge:
                    PyImGui.text(f"{recharge:.2f}")                
                
                PyImGui.end_table()
            
            PyImGui.separator()
            PyImGui.text_wrapped(self.widget_state.status_message if self.widget_state.status_message else "No status message")
            PyImGui.end()
       
        
        
        pass