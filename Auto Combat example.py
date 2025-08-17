from Py4GWCoreLib import *

MODULE_NAME = "Auto Combat example"
combat_handler:SkillManager.Autocombat = SkillManager.Autocombat()
def main():
    if not (Routines.Checks.Map.MapValid() and 
            Routines.Checks.Player.CanAct() and
            Map.IsExplorable() and
            not combat_handler.InCastingRoutine()):
            ActionQueueManager().ResetQueue("ACTION")
            return
        
    combat_handler.HandleCombat()    
    ActionQueueManager().ProcessQueue("ACTION")


if __name__ == "__main__":
    main()
