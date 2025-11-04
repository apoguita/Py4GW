from Py4GWCoreLib import GLOBAL_CACHE

import PyImGui



def draw_window():
    MIN_WIDTH = 400
    MIN_HEIGHT = 600

    if PyImGui.begin("quest data"):
        window_size = PyImGui.get_window_size()
        new_width = max(window_size[0], MIN_WIDTH)
        new_height = max(window_size[1], MIN_HEIGHT)

        # only update size if it changed
        if new_width != window_size[0] or new_height != window_size[1]:
            PyImGui.set_window_size(new_width, new_height, PyImGui.ImGuiCond.Always)

        # child region adjusts automatically
        if PyImGui.begin_child("AccountInfoChild", (new_width - 20, 0), True, PyImGui.WindowFlags.NoFlag):
            active_quest = GLOBAL_CACHE.Quest.GetActiveQuest()
            active_quest = -1
            PyImGui.text(f"Active Quest ID: {active_quest}")
            if PyImGui.button("request  quest name"):
                GLOBAL_CACHE.Quest.RequestQuestName(active_quest)
                GLOBAL_CACHE.Quest.RequestQuestDescription(active_quest)
                GLOBAL_CACHE.Quest.RequestQuestObjectives(active_quest)
                GLOBAL_CACHE.Quest.RequestQuestLocation(active_quest)
                GLOBAL_CACHE.Quest.RequestQuestNPC(active_quest)
                
            if GLOBAL_CACHE.Quest.IsQuestNameReady(active_quest):
                quest_name = GLOBAL_CACHE.Quest.GetQuestName(active_quest)
                PyImGui.text(f"Quest Name: {quest_name}")

            if GLOBAL_CACHE.Quest.IsQuestDescriptionReady(active_quest):
                quest_info = GLOBAL_CACHE.Quest.GetQuestDescription(active_quest)
                PyImGui.text(f"Quest Info: {quest_info}")
                
            if GLOBAL_CACHE.Quest.IsQuestObjectivesReady(active_quest):
                objectives = GLOBAL_CACHE.Quest.GetQuestObjectives(active_quest)
                PyImGui.text(f"Objectives: {objectives}")
                if  PyImGui.button("print objectives"):
                    print(f"{objectives}")

            if GLOBAL_CACHE.Quest.IsQuestLocationReady(active_quest):
                location = GLOBAL_CACHE.Quest.GetQuestLocation(active_quest)
                PyImGui.text(f"Location: {location}")

            if GLOBAL_CACHE.Quest.IsQuestNPCReady(active_quest):
                npc = GLOBAL_CACHE.Quest.GetQuestNPC(active_quest)
                PyImGui.text(f"NPC: {npc}")

            
                
                
            PyImGui.end_child()
        PyImGui.end()

def main():
    draw_window()


if __name__ == "__main__":
    main()
