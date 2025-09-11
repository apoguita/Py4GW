
from Py4GWCoreLib import GLOBAL_CACHE
from Py4GWCoreLib import Routines
from Py4GWCoreLib import ConsoleLog
from Py4GWCoreLib import BuildMgr
from Py4GWCoreLib import SkillManager



#region SFAssassinVaettir
class AutoCombat(BuildMgr):
    def __init__(self):
        super().__init__(name="AutoCombat Build")  # minimal init
        self.auto_combat_handler: SkillManager.Autocombat = SkillManager.Autocombat()

    
    def ProcessSkillCasting(self):
        global auto_attack_timer, auto_attack_threshold, is_expired
        self.auto_combat_handler.SetWeaponAttackAftercast()

        if not (Routines.Checks.Map.MapValid() and 
                Routines.Checks.Player.CanAct() and
                GLOBAL_CACHE.Map.IsExplorable() and
                not self.auto_combat_handler.InCastingRoutine()):
            yield from Routines.Yield.wait(100)
        else:
            self.auto_combat_handler.HandleCombat()
            #control vars
            auto_attack_timer = self.auto_combat_handler.auto_attack_timer.GetTimeElapsed()
            auto_attack_threshold = self.auto_combat_handler.auto_attack_timer.throttle_time
            is_expired = self.auto_combat_handler.auto_attack_timer.IsExpired()
        yield