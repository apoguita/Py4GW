import Py4GW
import PyImGui
from typing import Callable
from Py4GWCoreLib import ImGui, ColorPalette, GLOBAL_CACHE, Routines, Utils
from typing import Dict, Tuple, List
#region QuestData
class QuestNode:
    def __init__(self, quest_id):
        self.quest_id: int = quest_id
        self.name: str = ""
        self.quest_location: str = ""
        self.npc_quest_giver: str = ""
        self.description: str = ""
        self.objectives: str = ""
        self.map_from: int = 0
        self.map_to: int = 0
        self.quest_marker: tuple[float, float] = (0.0, 0.0)
        self.is_completed: bool = False
        self.is_primary: bool = False
        self.is_area_primary: bool = False
        self.is_current_mission_quest: bool = False
        
        self.force_update: bool = True
        self.partial_data_fetched: bool = False
        self.complete_data_fetched: bool = False
        
    def coro_initialize(self):
        def _wait_until_active(qid):
            while GLOBAL_CACHE.Quest.GetActiveQuest() != qid:
                yield from Routines.Yield.wait(50)
                
        def _fetch_with_retries(req_fn, is_ready_fn, get_fn, attr_name):
            for _ in range(5):
                req_fn(self.quest_id)
                setattr(self, attr_name, "Requesting...")
                yield from Routines.Yield.wait(50)
                while not is_ready_fn(self.quest_id):
                    yield from Routines.Yield.wait(50)
                value = get_fn(self.quest_id)
                setattr(self, attr_name, value)
                if value != "Timeout":
                    break
                
        current = GLOBAL_CACHE.Quest.GetActiveQuest()
        if self.quest_id != current:
            GLOBAL_CACHE.Quest.SetActiveQuest(self.quest_id)
            yield from Routines.Yield.wait(50)
            yield from _wait_until_active(self.quest_id)
            GLOBAL_CACHE.Quest.RequestQuestInfo(self.quest_id, update_marker=True)
            yield from Routines.Yield.wait(100)
            
        quest = GLOBAL_CACHE.Quest.GetQuestData(self.quest_id)
        if quest:
            self.map_from = quest.map_from
            self.map_to = quest.map_to
            self.quest_marker = (quest.marker_x, quest.marker_y)
            self.is_completed = quest.is_completed
            self.is_primary = quest.is_primary
            self.is_area_primary = quest.is_area_primary
            self.is_current_mission_quest = quest.is_current_mission_quest
                
        yield from _fetch_with_retries(
            GLOBAL_CACHE.Quest.RequestQuestName,
            GLOBAL_CACHE.Quest.IsQuestNameReady,
            GLOBAL_CACHE.Quest.GetQuestName,
            "name",
        )
        yield from _fetch_with_retries(
            GLOBAL_CACHE.Quest.RequestQuestLocation,
            GLOBAL_CACHE.Quest.IsQuestLocationReady,
            GLOBAL_CACHE.Quest.GetQuestLocation,
            "quest_location",
        )
        yield from _fetch_with_retries(
            GLOBAL_CACHE.Quest.RequestQuestDescription,
            GLOBAL_CACHE.Quest.IsQuestDescriptionReady,
            GLOBAL_CACHE.Quest.GetQuestDescription,
            "description",
        )
        yield from _fetch_with_retries(
            GLOBAL_CACHE.Quest.RequestQuestObjectives,
            GLOBAL_CACHE.Quest.IsQuestObjectivesReady,
            GLOBAL_CACHE.Quest.GetQuestObjectives,
            "objectives",
        )
        yield from _fetch_with_retries(
            GLOBAL_CACHE.Quest.RequestQuestNPC,
            GLOBAL_CACHE.Quest.IsQuestNPCReady,
            GLOBAL_CACHE.Quest.GetQuestNPC,
            "npc_quest_giver",
        )
            
        # --- restore original active quest ---
        GLOBAL_CACHE.Quest.SetActiveQuest(current)
        yield from Routines.Yield.wait(50)
        yield from _wait_until_active(current)

class QuestData:
    # ===============================
    # COLOR MAPS for quest markup tags
    # ===============================
    COLOR_MAP: Dict[str, Tuple[float, float, float, float]] = {
        "@warning": ColorPalette.GetColor("red").to_tuple_normalized(),
        "@Warning": ColorPalette.GetColor("red").to_tuple_normalized(),
        "@Quest":   ColorPalette.GetColor("bright_green").to_tuple_normalized(),
        "@quest":   ColorPalette.GetColor("bright_green").to_tuple_normalized(),
        "Header":  ColorPalette.GetColor("creme").to_tuple_normalized(),   
    }
    
    def __init__(self):
        self.quest_log: Dict[int, 'QuestNode'] = {}
        self.active_quest_id = 0
        self.initialized = False
        self.initializing = False
        self.mission_map_quest = None
        self.mission_map_quest_initialized = False
        self.mission_map_quest_force_update = False
        
    def coro_initialize(self):
        quest_log_ids = GLOBAL_CACHE.Quest.GetQuestLogIds()
        for qid in quest_log_ids:
            quest_node = QuestNode(qid)
            self.quest_log[qid] = quest_node
            yield from quest_node.coro_initialize()
        self.initializing = False
        self.initialized = True
        
    def coro_initialize_mission_map_quest(self):
        if self.mission_map_quest is None:
            self.mission_map_quest = QuestNode(-1)
            yield from self.mission_map_quest.coro_initialize()
        self.mission_map_quest_loaded = True
        self.mission_map_quest_force_update = False
        yield
        
    def update(self):
        self.active_quest_id = GLOBAL_CACHE.Quest.GetActiveQuest()

        if not GLOBAL_CACHE.Quest.IsMissionMapQuestAvailable():
            if self.mission_map_quest is not None:
                self.mission_map_quest = None
                self.mission_map_quest_initialized = False
                self.mission_map_quest_force_update = False
                print("Mission map quest data cleared.")
        else:
            if self.mission_map_quest is None:
                print("Mission map quest now available.")
            if not self.mission_map_quest_initialized or self.mission_map_quest_force_update:
                self.mission_map_quest_initialized = True
                self.mission_map_quest_force_update = False
                GLOBAL_CACHE.Coroutines.append(self.coro_initialize_mission_map_quest())
                print("Initializing mission map quest data...")

                

        if not self.initialized:
            if not self.initializing:
                self.initializing = True
                GLOBAL_CACHE.Coroutines.append(self.coro_initialize())

    def draw_content(self, window_width: float, window_height: float):
        if not self.initialized:
            ImGui.text("Initializing quest data...")
            PyImGui.text(f"Active Quest ID: {self.active_quest_id}")
            return
        
        PyImGui.push_style_color(PyImGui.ImGuiCol.Text, self.COLOR_MAP["Header"])
        ImGui.text("Active Quests:", font_size=18) 
        PyImGui.same_line(0, -1)
        PyImGui.text(f"Active Quest ID: {self.active_quest_id}")
        PyImGui.pop_style_color(1)
        PyImGui.same_line(0, -1)
        if PyImGui.button("Refresh Quest Info"):
            for quest in self.quest_log.values():
                GLOBAL_CACHE.Quest.RequestQuestInfo(quest.quest_id, update_marker=True)
                quest.force_update = True
                
        if PyImGui.begin_child("QuestTreeChild", (window_width - 20, 250), True, PyImGui.WindowFlags.NoFlag):
            grouped_quests: Dict[str, List[int]] = {}
            
            if self.mission_map_quest is not None:
                grouped_quests.setdefault(self.mission_map_quest.quest_location, []).append(self.mission_map_quest.quest_id)
            
            for quest in self.quest_log.values():
                if quest.is_primary:
                    grouped_quests.setdefault("Primary", []).append(quest.quest_id)
                else:
                    grouped_quests.setdefault(quest.quest_location, []).append(quest.quest_id)
                    
            ordered_groups: list[tuple[str, list[int]]] = []
            if self.mission_map_quest is not None:
                ordered_groups.append((self.mission_map_quest.quest_location, grouped_quests.pop(self.mission_map_quest.quest_location)))
                   
            if "Primary" in grouped_quests:
                ordered_groups.append(("Primary", grouped_quests.pop("Primary")))   
            # Sort other groups alphabetically by location name
            for loc in sorted(grouped_quests.keys(), key=lambda s: s.lower()):
                ordered_groups.append((loc, grouped_quests[loc]))
                
            # --- Draw the tree ---
            for location, quest_ids in ordered_groups:
                # Sort quest IDs alphabetically by name
                sorted_qids = sorted(
                    quest_ids,
                    key=lambda qid: (
                        self.quest_log[qid].name
                    ).lower()
                )
                
                ImGui.push_font("Regular", 18)
                PyImGui.push_style_color(PyImGui.ImGuiCol.Text, self.COLOR_MAP["Header"])
                opened = PyImGui.tree_node(f"{location} Quests ({len(sorted_qids)})")
                PyImGui.pop_style_color(1)
                ImGui.pop_font()
                
                if opened:
                    for qid in sorted_qids:
                        if qid == self.active_quest_id:
                            PyImGui.push_style_color(PyImGui.ImGuiCol.Text, self.COLOR_MAP["Header"])
                            
                        PyImGui.text(f"{self.quest_log[qid].name} (ID: {qid})")
                        text_size = PyImGui.calc_text_size(self.quest_log[qid].name)
                        text_pos = PyImGui.get_item_rect_min()
                        total_width = text_size[0]
                        max_height = text_size[1]
                        if self.quest_log[qid].is_completed:
                            PyImGui.same_line(0, 5)
                            PyImGui.push_style_color(PyImGui.ImGuiCol.Text, self.COLOR_MAP["Header"])
                            completed_text = "(Completed)"
                            PyImGui.text(completed_text)
                            PyImGui.pop_style_color(1)
                            total_width += 5 + PyImGui.calc_text_size(completed_text)[0]
                            
                        if qid == self.active_quest_id:
                            PyImGui.pop_style_color(1)
                            
                        # === highlight active quest ===
                        if qid == self.active_quest_id:
                            style = PyImGui.StyleConfig()
                            style.Pull()
                            padding_x = style.CellPadding[0] if style.CellPadding else 0.0
                            style.Push()

                            # get full child dimensions
                            child_pos = PyImGui.get_window_pos()
                            child_size = PyImGui.get_window_size()

                            # margin in pixels around the text (controls vertical overflow)
                            v_margin = 3.0  # expand highlight up/down by 3px each side

                            rect_min = (child_pos[0] + padding_x, text_pos[1] - v_margin)
                            rect_max = (
                                child_pos[0] + child_size[0] - padding_x,
                                text_pos[1] + max_height + v_margin
                            )

                            color = ColorPalette.GetColor("white").copy()
                            color.a = 50
                            PyImGui.draw_list_add_rect_filled(
                                rect_min[0], rect_min[1],
                                rect_max[0], rect_max[1],
                                color.to_color(),
                                0, 0
                            )

                        # overlay invisible button covering both texts
                        PyImGui.set_cursor_screen_pos(*text_pos)
                        if PyImGui.invisible_button(f"quest_btn_{qid}", total_width, max_height):
                            GLOBAL_CACHE.Quest.SetActiveQuest(qid)
                            GLOBAL_CACHE.Quest.RequestQuestInfo(self.active_quest_id, update_marker=True)
                            self.quest_log[qid].force_update = True
                            
                    PyImGui.tree_pop()
            PyImGui.end_child()
        if PyImGui.begin_child("AccountInfoChild", (window_width - 20, 0), False, PyImGui.WindowFlags.NoFlag):
            child_width = PyImGui.get_content_region_avail()[0]
            PyImGui.push_style_color(PyImGui.ImGuiCol.Text, self.COLOR_MAP["Header"])
            ImGui.text(f"ID: {self.active_quest_id} - {self.quest_log[self.active_quest_id].name}", font_size=20)
            ImGui.text("Quest Summary:", font_size=18)
            PyImGui.pop_style_color(1)
            
            tokens = Utils.TokenizeMarkupText(self.quest_log[self.active_quest_id].objectives, max_width=child_width)
            ImGui.render_tokenized_markup(tokens, max_width=child_width, COLOR_MAP=self.COLOR_MAP)

            PyImGui.push_style_color(PyImGui.ImGuiCol.Text, self.COLOR_MAP["Header"])
            PyImGui.text_wrapped(f"{self.quest_log[self.active_quest_id].npc_quest_giver}")
            PyImGui.pop_style_color(1)

            tokens = Utils.TokenizeMarkupText(self.quest_log[self.active_quest_id].description, max_width=child_width)
            ImGui.render_tokenized_markup(tokens, max_width=child_width, COLOR_MAP=self.COLOR_MAP)

            PyImGui.separator()
            PyImGui.text(f"From: {GLOBAL_CACHE.Map.GetMapName(self.quest_log[self.active_quest_id].map_from)}")
            PyImGui.text(f"To: {GLOBAL_CACHE.Map.GetMapName(self.quest_log[self.active_quest_id].map_to)}")
            PyImGui.text(f"Marker X,Y: ({self.quest_log[self.active_quest_id].quest_marker[0]}, {self.quest_log[self.active_quest_id].quest_marker[1]})")
            PyImGui.end_child()