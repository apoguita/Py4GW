import Py4GW
from Py4GWCoreLib import PyImGui, ImGui, GLOBAL_CACHE
from Py4GWCoreLib import ProfessionTextureMap

MODULE_NAME = "tester for everything"


def main():
    global _overlay
    try:
        window_flags=PyImGui.WindowFlags.AlwaysAutoResize 
        if PyImGui.begin("Tester for Everything", window_flags):
            
            python_logo = "python_icon.jpg"

            size = 32
            for size in [32, 64, 128, 256]:
                ImGui.DrawTexture(python_logo, size, size)
                PyImGui.same_line(0,-1)

            PyImGui.separator()
            ImGui.DrawTexturedRect(100,100, 128, 128, python_logo)

            skill_id = 826 #shadow form
            texture_file = GLOBAL_CACHE.Skill.ExtraData.GetTexturePath(skill_id)
    
            
            PyImGui.text(f"Texture for skill ID {skill_id}: {texture_file}")
            ImGui.DrawTexture(texture_file)
            
            if ImGui.ImageButton("##text_unique_name", texture_file, 64, 64):
                Py4GW.Console.Log(MODULE_NAME, "Button clicked!", Py4GW.Console.MessageType.Info)
              
            primary_path, secondary_path = GLOBAL_CACHE.Agent.GetProfessionsTexturePaths(GLOBAL_CACHE.Player.GetAgentID())
            
            ImGui.DrawTexture(primary_path, 64, 64)
            ImGui.DrawTexture(secondary_path, 64, 64)
            
            primary = 1
            secondary = 5
            primary_texture = f"Textures\\Profession_Icons\\{ProfessionTextureMap.get(primary, 'unknown')}"
            secondary_texture = f"Textures\\Profession_Icons\\{ProfessionTextureMap.get(secondary, 'unknown')}"
              
            size =  20
            ImGui.DrawTexture(primary_texture, size, size)
            ImGui.DrawTexture(secondary_texture, size, size)      
            
            
        PyImGui.end()
        


    except Exception as e:
        Py4GW.Console.Log(MODULE_NAME, f"Error: {str(e)}", Py4GW.Console.MessageType.Error)
        raise


    
if __name__ == "__main__":
    main()
