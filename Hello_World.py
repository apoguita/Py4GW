from Py4GWCoreLib import *

MODULE_NAME = "tester for everything"
combat_handler:SkillManager.Autocombat = SkillManager.Autocombat()
hero_ai_combat_handler:SkillManager.HeroAICombat = SkillManager.HeroAICombat()
def main():
    color = Color(255, 255,255, 255)
    #DXOverlay().DrawLine(200, 200, 500, 500, color.to_color())
    DXOverlay().DrawLine(500, 200, 200, 500, color.to_color(), thickness=5)
    DXOverlay().DrawLine3D(1, 1,Overlay().FindZ(1,1,0)-150, 500, 500, Overlay().FindZ(500,500,0)-150, color.to_color())
        
    
if __name__ == "__main__":
    main()
