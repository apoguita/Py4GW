from Py4GWCoreLib import *

MODULE_NAME = "tester for everything"
combat_handler:SkillManager.Autocombat = SkillManager.Autocombat()
hero_ai_combat_handler:SkillManager.HeroAICombat = SkillManager.HeroAICombat()
def main():
    if PyImGui.begin("mini map checker"):
        frame_id_hash = UIManager.GetFrameIDByHash(3268554015)
        PyImGui.text(f"Frame ID by hash: {frame_id_hash}")
        frame_id = Map.MiniMap.GetFrameID()
        PyImGui.text(f"Frame ID: {frame_id}")
        is_locked = Map.MiniMap.IsLocked()
        PyImGui.text(f"Is Locked: {is_locked}")
        
    PyImGui.end()
if __name__ == "__main__":
    main()
