from Py4GWCoreLib import *

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

            skill_id = 826
            texture_file = GLOBAL_CACHE.Skill.ExtraData.GetTexturePath(skill_id)
    
            
            PyImGui.text(f"Texture for skill ID {skill_id}: {texture_file}")
            ImGui.DrawTexture(texture_file)
            
            if ImGui.ImageButton("##text_unique_name", texture_file, 64, 64):
                Py4GW.Console.Log(MODULE_NAME, "Button clicked!", Py4GW.Console.MessageType.Info)
                
            PyImGui.text("Extended Texture Drawing:")
            ImGui.DrawTextureExtended(
                texture_file,
                size=(64, 64),
                uv0=(0.0, 0.0),
                uv1=(1.0, 1.0),
                tint=(255, 255, 255, 255),
                border_color=(0, 0, 0, 0)
            )
            PyImGui.same_line(0,-1)
            ImGui.DrawTextureExtended(
                texture_file,
                size=(64, 64),
                uv0=(0.0, 0.0),
                uv1=(1.0, 1.0),
                tint=(255, 0, 0, 255),
                border_color=(0, 0, 0, 0)
            )

            PyImGui.same_line(0,-1)
            ImGui.DrawTextureExtended(
                texture_file,
                size=(64, 64),
                uv0=(0.0, 0.0),
                uv1=(1.0, 1.0),
                tint=(0, 255, 0, 255),
                border_color=(0, 0, 0, 0)
            )
            PyImGui.same_line(0,-1)
            ImGui.DrawTextureExtended(
                texture_file,
                size=(64, 64),
                uv0=(0.0, 0.0),
                uv1=(1.0, 1.0),
                tint=(0, 0, 255, 255),
                border_color=(0, 0, 0, 0)
            )
            PyImGui.same_line(0,-1)
            ImGui.DrawTextureExtended(
                texture_file,
                size=(64, 64),
                uv0=(0.0, 0.0),
                uv1=(1.0, 1.0),
                tint=(64, 64, 64, 255),
                border_color=(0, 0, 0, 0)
            )
            
            ImGui.DrawTextureExtended(
                texture_file,
                size=(256, 256),
                uv0=(0.3, 0.3),
                uv1=(0.8, 0.8),
                tint=(255, 255, 255, 255),
                border_color=(0, 0, 0, 0)
            )
            
        PyImGui.end()
        


    except Exception as e:
        Py4GW.Console.Log(MODULE_NAME, f"Error: {str(e)}", Py4GW.Console.MessageType.Error)
        raise


    
if __name__ == "__main__":
    main()
