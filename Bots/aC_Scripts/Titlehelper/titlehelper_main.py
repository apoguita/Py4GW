from Py4GWCoreLib import *
from Bots.aC_Scripts.aC_api.Titles import display_title_progress
from Bots.aC_Scripts.Titlehelper import ItemSelector

sweet_tooth_tiers = [
    (1000, "Sweet Tooth"),
    (10_000, "Connoisseur of Confectionaries")
]

party_animal_tiers = [
    (1000, "Party Animal"),
    (10_000, "Life of the Party")
]

drunkard_tiers = [
    (1000, "Drunkard"),
    (10_000, "Incorrigible Ale-Hound")
]

# Define title IDs for the game API
TITLE_SWEET_TOOTH = 34
TITLE_PARTY_ANIMAL = 43
TITLE_DRUNKARD = 7


class TitleHelper:
    def __init__(self):

        self.use_all = False
        self.started = False

        self.alcohol_used_count = 0
        self.sweets_used_count = 0
        self.party_used_count = 0

        self.alcohol_empty = False
        self.sweets_empty = False
        self.party_empty = False

        self.start_points = {
            TITLE_DRUNKARD: 0,
            TITLE_SWEET_TOOTH: 0,
            TITLE_PARTY_ANIMAL: 0
        }

    def reset_state(self):
        self.alcohol_used_count = 0
        self.sweets_used_count = 0
        self.party_used_count = 0

        self.started = True
        self.alcohol_empty = False
        self.sweets_empty = False
        self.party_empty = False

        self._cache_starting_points()

        Py4GW.Console.Log("TitleHelper", "Helper state has been reset.")

    def _cache_starting_points(self):
        for title_id in self.start_points:
            title = GLOBAL_CACHE.Player.GetTitle(title_id)
            if title:
                self.start_points[title_id] = title.current_points

    def _is_title_maxed(self, title_id):
        title = GLOBAL_CACHE.Player.GetTitle(title_id)
        if title:
            return title.current_points >= 10_000
        return False

    def get_points_gained(self, title_id: int) -> int:
        if not self.started:
            return 0
        current = GLOBAL_CACHE.Player.GetTitle(title_id)
        if current:
            return max(0, current.current_points - self.start_points.get(title_id, 0))
        return 0

    def _use_item_group(self, model_ids, counter_attr, empty_attr):
        for model_id in model_ids:
            Py4GW.Console.Log("TitleHelper", f"Trying modelid: {model_id} ({model_id.value})")
            item_id = GLOBAL_CACHE.Inventory.GetFirstModelID(model_id.value)
            if item_id:
                Py4GW.Console.Log("TitleHelper", f"Using item id: {item_id} for modelid: {model_id}")
                GLOBAL_CACHE.Inventory.UseItem(item_id)
                setattr(self, counter_attr, getattr(self, counter_attr) + 1)
                return True
        setattr(self, empty_attr, True)
        Py4GW.Console.Log("TitleHelper", "No items found in inventory for this category.")
        return False
    
    def run(self):
        while True:
            if not Routines.Checks.Map.MapValid():
                yield from Routines.Yield.wait(50)
                continue

            if not self.use_all:
                yield from Routines.Yield.wait(50)
                continue

            if Agent.IsDead(GLOBAL_CACHE.Player.GetAgentID()):
                yield from Routines.Yield.wait(50)
                continue

            did_something = False


            alcohol_selected = [model_id for model_id, selected in ItemSelector.toggle_state["Alcohol"].items() if selected]
            sweets_selected = [model_id for model_id, selected in ItemSelector.toggle_state["Sweets"].items() if selected]
            party_selected = [model_id for model_id, selected in ItemSelector.toggle_state["Party"].items() if selected]

            if not self.alcohol_empty and not self._is_title_maxed(TITLE_DRUNKARD):
                did_something |= self._use_item_group(alcohol_selected, "alcohol_used_count", "alcohol_empty")
            else:
                self.alcohol_empty = True

            if not self.sweets_empty and not self._is_title_maxed(TITLE_SWEET_TOOTH):
                did_something |= self._use_item_group(sweets_selected, "sweets_used_count", "sweets_empty")
            else:
                self.sweets_empty = True

            if not self.party_empty and not self._is_title_maxed(TITLE_PARTY_ANIMAL):
                did_something |= self._use_item_group(party_selected, "party_used_count", "party_empty")
            else:
                self.party_empty = True

            yield from Routines.Yield.wait(50 if did_something else 100)

def draw_title_helper_window(helper: TitleHelper):
    PyImGui.push_style_color(PyImGui.ImGuiCol.Text,(0.6, 0.9, 1.0, 1.0)) 
    if PyImGui.button("Start"):
        helper.reset_state()
        helper.use_all = True
    PyImGui.pop_style_color(1)

    PyImGui.same_line(0, 10)
    PyImGui.push_style_color(PyImGui.ImGuiCol.Text,(0.6, 0.9, 1.0, 1.0)) 
    if PyImGui.button("Stop"):
        helper.use_all = False
        helper.reset_state()
    PyImGui.pop_style_color(1)

    PyImGui.same_line(0, 10)
    PyImGui.push_style_color(PyImGui.ImGuiCol.Text,(1.0, 1.0, 0.3, 1.0)) 
    if PyImGui.button("Options"):
        ItemSelector.show_item_selector = True
    PyImGui.pop_style_color(1)

    PyImGui.separator()

    points = helper.get_points_gained(TITLE_DRUNKARD)
    PyImGui.text_colored(f"Alcohol Points Gained: {points}", (0.6, 0.9, 1.0, 1.0))
    display_title_progress("Drunkard", TITLE_DRUNKARD, drunkard_tiers)
    if helper.alcohol_empty:
        PyImGui.text_colored("No more alcohol items!", (1.0, 0.3, 0.3, 1.0))

    points = helper.get_points_gained(TITLE_SWEET_TOOTH)
    PyImGui.text_colored(f"Sweets Points Gained: {points}", (0.6, 0.9, 1.0, 1.0))
    display_title_progress("Sweet Tooth", TITLE_SWEET_TOOTH, sweet_tooth_tiers)
    if helper.sweets_empty:
        PyImGui.text_colored("No more sweets items!", (1.0, 0.3, 0.3, 1.0))

    points = helper.get_points_gained(TITLE_PARTY_ANIMAL)
    PyImGui.text_colored(f"Party Points Gained: {points}", (0.6, 0.9, 1.0, 1.0))
    display_title_progress("Party Animal", TITLE_PARTY_ANIMAL, party_animal_tiers)
    if helper.party_empty:
        PyImGui.text_colored("No more party items!", (1.0, 0.3, 0.3, 1.0))
  
    PyImGui.end()


# === Instantiate and Start ===
title_helper = TitleHelper()
title_helper_runner = title_helper.run()  # get coroutine

def main():

    draw_title_helper_window(title_helper)

    if ItemSelector.show_item_selector:
        ItemSelector.draw_item_selector_window()

    try:
        next(title_helper_runner)
    except StopIteration:
        pass
