from Py4GWCoreLib import Map
from Py4GWCoreLib import Routines
from Py4GWCoreLib import ConsoleLog
from Py4GWCoreLib import BuildMgr
from Py4GWCoreLib import SkillManager



#region SFAssassinVaettir
class AutoCombat(BuildMgr):
    def __init__(self, match_only: bool = False):
        super().__init__(
            name="AutoCombat",
            template_code="AUTOHANDLER",
            is_fallback_candidate=True,
        )
        if match_only:
            return
        self.auto_combat_handler: SkillManager.Autocombat = SkillManager.Autocombat()

    def ApplyBlockedSkillIDs(self, blocked_skill_ids: list[int] | None = None) -> None:
        from Py4GWCoreLib import GLOBAL_CACHE

        blocked_ids = {int(skill_id) for skill_id in (blocked_skill_ids or []) if int(skill_id) != 0}
        for slot in range(1, 9):
            skill_id = int(GLOBAL_CACHE.SkillBar.GetSkillIDBySlot(slot) or 0)
            self.auto_combat_handler.SetSkillEnabled(slot - 1, skill_id not in blocked_ids)

    
    def ProcessSkillCasting(self):
        global auto_attack_timer, auto_attack_threshold, is_expired
        self.auto_combat_handler.SetWeaponAttackAftercast()

        if not (Routines.Checks.Map.MapValid() and 
                Routines.Checks.Player.CanAct() and
                Map.IsExplorable() and
                not self.auto_combat_handler.InCastingRoutine()):
            yield from Routines.Yield.wait(100)
        else:
            self.auto_combat_handler.HandleCombat()
            #control vars
            auto_attack_timer = self.auto_combat_handler.auto_attack_timer.GetTimeElapsed()
            auto_attack_threshold = self.auto_combat_handler.auto_attack_timer.throttle_time
            is_expired = self.auto_combat_handler.auto_attack_timer.IsExpired()
        yield
