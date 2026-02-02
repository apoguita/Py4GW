from Py4GWCoreLib import *
import PyImGui

active_quest_id = 0
quest_name = ""
quest_info = None

def update():
    global active_quest_id
    active_quest_id = GLOBAL_CACHE.Quest.GetActiveQuest()
    if active_quest_id:
        quest = GLOBAL_CACHE.Quest.GetQuestName(active_quest_id)
        print(f"Active Quest ID: {active_quest_id}, Name: {quest.name}")


def draw():
    global counter
    if PyImGui.begin("hello world"):
        PyImGui.text("Hello World from Python!")
        PyImGui.text(f"Counter: {counter}")
    PyImGui.end()

if __name__ == "__main__":
    update()