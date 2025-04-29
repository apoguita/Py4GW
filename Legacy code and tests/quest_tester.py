from Py4GWCoreLib import *

MODULE_NAME = "tester for everything"

quest_log = []

def main():
    global quest_log
    
    if PyImGui.begin("timer test"):
        if PyImGui.button("get quest log"):
            quest_log = Quest.GetQuestLog()

    for quest_id in quest_log:
        if PyImGui.collapsing_header(f"Quest ID: {quest_id}"):
            Quest.RequestQuestInfo(quest_id, update_marker=True)
            quest = Quest.GetQuestData(quest_id)

            PyImGui.text(f"Quest ID: {quest.quest_id}")
            PyImGui.text(f"Log State: {quest.log_state}")

            PyImGui.text(f"Map From: {quest.map_from}")
            PyImGui.text(f"Map To: {quest.map_to}")
            PyImGui.text(f"Marker X: {quest.marker_x}")
            PyImGui.text(f"Marker Y: {quest.marker_y}")
            PyImGui.text(f"H0024: {quest.h0024}")

            PyImGui.text(f"Is Completed: {quest.is_completed}")
            PyImGui.text(f"Is Current Mission Quest: {quest.is_current_mission_quest}")
            PyImGui.text(f"Is Area Primary: {quest.is_area_primary}")
            PyImGui.text(f"Is Primary: {quest.is_primary}")
            
        
    PyImGui.end()
    
if __name__ == "__main__":
    main()
