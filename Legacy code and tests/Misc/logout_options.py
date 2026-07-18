from Py4GWCoreLib import *

MODULE_NAME = "tester for everything"

characters = []
pregame = None
def main():
    global characters, pregame
    
    if PyImGui.begin("timer test"):
        if PyImGui.button("logout"):
            Map.Pregame.LogoutToCharacterSelect()
            
        if PyImGui.button("get characters"):
            characters = Map.Pregame.GetAvailableCharacterList()
            
            
        PyImGui.same_line(0,-1)
        PyImGui.text_colored(f"info only available in character select screen", Color(255, 0, 0, 255).to_tuple())
            
        PyImGui.text_colored(f"is in character select screen : {Map.Pregame.InCharacterSelectScreen()}", 
                             Color(0, 255, 0,255).to_tuple() if Map.Pregame.InCharacterSelectScreen() else Color(255, 0, 0, 255).to_tuple())
        
        
            
        if characters:
            if PyImGui.collapsing_header("characters"):
                for i, character in enumerate(characters):
                    if PyImGui.collapsing_header(f"{character.player_name}"):
                        if PyImGui.collapsing_header(f"{i} -h0000"):
                            for h0000 in character.h0000:
                                PyImGui.text(f"{h0000}")
                        if PyImGui.collapsing_header(f"{i} -uuid"):
                            for uuid in character.uuid:
                                PyImGui.text(f"{uuid}")
                                
                        PyImGui.text(f"{i} -player_name: {character.player_name}")
                        if PyImGui.collapsing_header(f"{i} -props"):
                            for prop in character.props:
                                PyImGui.text(f"{prop}")
                                
                        PyImGui.text(f"{i} -map_id: {character.map_id} - {Map.GetMapName(character.map_id)}")
                        PyImGui.text(f"{i} - primary: {character.primary} - {Profession(character.primary).name}")
                        PyImGui.text(f"{i} -secondary: {character.secondary} - {Profession(character.secondary).name}")
                        PyImGui.text(f"{i} -campaign: {character.campaign} - {Campaign(character.campaign).name}")
                        PyImGui.text(f"{i} -level: {character.level}")
                        PyImGui.text(f"{i} -is_pvp: {character.is_pvp}")

        if Map.Pregame.InCharacterSelectScreen():
            if PyImGui.collapsing_header("pregame"):
                PyImGui.text(f"frame_id: {Map.Pregame.GetFrameID()}")

                PyImGui.text(f"chosen_character_index: {Map.Pregame.GetChosenCharacterIndex()}")

                PyImGui.text(f"chosen_character_index: {Map.Pregame.GetChosenCharacterIndex()}")
                if PyImGui.collapsing_header(f"chars: {Map.Pregame.GetCharList()}"):
                    for char in Map.Pregame.GetCharList():
                        PyImGui.text(f"{char}")

        
    PyImGui.end()
    
if __name__ == "__main__":
    main()
