import Py4GW
from Py4GWCoreLib import PyImGui, ImGui, GLOBAL_CACHE

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
              

            
        PyImGui.end()
        


    except Exception as e:
        Py4GW.Console.Log(MODULE_NAME, f"Error: {str(e)}", Py4GW.Console.MessageType.Error)
        raise


    
if __name__ == "__main__":
    main()
