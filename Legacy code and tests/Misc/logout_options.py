from Py4GWCoreLib import *

MODULE_NAME = "tester for everything"

characters = []
pregame = None
def main():
    global characters, pregame
    
    if PyImGui.begin("timer test"):
        if PyImGui.button("logout"):
            Player.LogoutToCharacterSelect()
            
        if PyImGui.button("get characters"):
            characters = Player.GetLoginCharacters()
            
        if PyImGui.button("get pregame"):
            pregame = Player.GetPreGameContext()
            
        PyImGui.same_line(0,-1)
        PyImGui.text_colored(f"info only available in character select screen", Color(255, 0, 0, 255).to_tuple())
            
        PyImGui.text_colored(f"is in character select screen : {Player.InCharacterSelectScreen()}", 
                             Color(0, 255, 0,255).to_tuple() if Player.InCharacterSelectScreen() else Color(255, 0, 0, 255).to_tuple())
        
        
            
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

        if pregame:
            if PyImGui.collapsing_header("pregame"):
                PyImGui.text(f"frame_id: {pregame.frame_id}")

                PyImGui.text(f"chosen_character_index: {pregame.chosen_character_index}")

                PyImGui.text(f"index_1: {pregame.index_1}")
                PyImGui.text(f"index_2: {pregame.index_2}")
                if PyImGui.collapsing_header(f"chars: {pregame.chars}"):
                    for char in pregame.chars:
                        PyImGui.text(f"{char}")
                        
                if PyImGui.collapsing_header(f"h0004: {pregame.h0004}"):
                    for h0004 in pregame.h0004:
                        PyImGui.text(f"{h0004}")
                if PyImGui.collapsing_header(f"h0128: {pregame.h0128}"):
                    for h0128 in pregame.h0128:
                        PyImGui.text(f"{h0128}")
        
    PyImGui.end()
    
if __name__ == "__main__":
    main()
