import Py4GW
import math
from typing import Tuple
from Py4GWCoreLib import Profession
from Py4GWCoreLib import GLOBAL_CACHE
from Py4GWCoreLib import Routines
from Py4GWCoreLib import ConsoleLog
from Py4GWCoreLib import Agent
from Py4GWCoreLib import AgentArray
from Py4GWCoreLib import Range
from Py4GWCoreLib import Utils
#from dangerous_models_runtime import can_cripple, can_knockdown

class Build:
    def __init__(
        self,
        name: str = "Generic Build",
        required_primary: Profession = Profession(0),
        required_secondary: Profession = Profession(0),
        template_code: str = "AAAAAAAAAAAAAAAA",
        skills: list[int] = []
    ):
        self.build_name = name
        self.required_primary: Profession = required_primary
        self.required_secondary: Profession = required_secondary
        self.template_code = template_code
        self.skills = skills

    def ValidatePrimary(self, profession: Profession) -> bool:
        return self.required_primary == profession

    def ValidateSecondary(self, profession: Profession) -> bool:
        return self.required_secondary == profession

    def ValidateSkills(self):
        skills: list[int] = []
        for i in range(8):
            skill = GLOBAL_CACHE.SkillBar.GetSkillIDBySlot(i + 1)
            if skill:
                skills.append(skill)

        all_valid = sorted(self.skills) == sorted(skills)
        yield from Routines.Yield.wait(0 if all_valid else 1000)
        return all_valid

    def EquipBuild(self):
        yield from Routines.Yield.Skills.LoadSkillbar(self.template_code, log=False)

    def LoadSkillBar(self):
        yield from Routines.Yield.Skills.LoadSkillbar(self.template_code, log=False)

    def ProcessSkillCasting(self):
        raise NotImplementedError
    
    def ValidateBuild(self):
        """
        Validates profession + skillbar for this build.
        Returns (success: bool, error_msg: str)
        """
        return True, ""

class OutpostRunnerDA(Build):
    def __init__(self):
        super().__init__(
            name="D/A Outpost Runner",
            required_primary=Profession.Dervish,
            required_secondary=Profession.Assassin,
            template_code="Ogej4NfMLTIQ0k6MHYjb3l4OHQA"
        )

        self.debug_logs = True

        # Skill IDs
        self.zealous_renewal = GLOBAL_CACHE.Skill.GetID("Zealous_Renewal")
        self.pious_haste = GLOBAL_CACHE.Skill.GetID("Pious_Haste")
        self.dwarven_stability = GLOBAL_CACHE.Skill.GetID("Dwarven_Stability")
        #self.i_am_unstoppable = GLOBAL_CACHE.Skill.GetID("I_Am_Unstoppable")
        self.shadow_form = GLOBAL_CACHE.Skill.GetID("Shadow_Form")
        self.heart_of_shadow = GLOBAL_CACHE.Skill.GetID("Heart_of_Shadow")
        self.shroud_of_distress = GLOBAL_CACHE.Skill.GetID("Shroud_of_Distress")
        self.deadly_paradox = GLOBAL_CACHE.Skill.GetID("Deadly_Paradox")

        self.skills = [
            self.deadly_paradox,
            self.shadow_form,
            self.heart_of_shadow,
            self.shroud_of_distress,
            #self.i_am_unstoppable,
            self.pious_haste,
            self.dwarven_stability,
            self.zealous_renewal
        ]




    def ProcessSkillCasting(self):
        while True:
            if not Routines.Checks.Map.MapValid():
                yield from Routines.Yield.wait(1000)
                continue
            
            if Agent.IsDead(GLOBAL_CACHE.Player.GetAgentID()):
                yield from Routines.Yield.wait(1000)
                continue
            
            if not Routines.Checks.Skills.CanCast():
                yield from Routines.Yield.wait(100)
                continue
            
            player_id = GLOBAL_CACHE.Player.GetAgentID()
            # === BUFF STATE ===
            total_range = Range.Spellcast
            in_danger = Routines.Checks.Agents.InDanger(total_range)
            has_shadow_form = Routines.Checks.Effects.HasBuff(player_id, self.shadow_form)
            shadow_time = GLOBAL_CACHE.Effects.GetEffectTimeRemaining(player_id, self.shadow_form) if has_shadow_form else 0
            has_deadly_paradox = Routines.Checks.Effects.HasBuff(player_id, self.deadly_paradox)
            has_shroud = Routines.Checks.Effects.HasBuff(player_id, self.shroud_of_distress)
            has_pious = Routines.Checks.Effects.HasBuff(player_id, self.pious_haste)
            has_dwarven = Routines.Checks.Effects.HasBuff(player_id, self.dwarven_stability)
            hp = Agent.GetHealth(player_id)
            
            current_target = GLOBAL_CACHE.Player.GetTargetID()
            if current_target != player_id:
                GLOBAL_CACHE.Player.ChangeTarget(player_id)
                yield from Routines.Yield.wait(250)

            # === 1. SHADOW FORM + PARADOX MAINTENANCE ===
            if in_danger and shadow_time <= 3500:
                # Force combo in one go
                aftercast = 200 #the skill has no aftercast itself but we need to wait for the server to process the cast
                GLOBAL_CACHE._ActionQueueManager.ResetQueue("ACTION")
                if Routines.Yield.Skills.CastSkillID(self.deadly_paradox,extra_condition=(not has_deadly_paradox), log=False, aftercast_delay=aftercast):
                    yield from Routines.Yield.wait(aftercast) #the queue itself casts wit the appropriate delay but we need 
                                                                #to wait so our logic matches
                # Immediately follow with SF
                aftercast = 1950 #SF cast 1000 + 750aftercast + assuming 200ms for something else
                GLOBAL_CACHE._ActionQueueManager.ResetQueue("ACTION")
                if Routines.Yield.Skills.CastSkillID(self.shadow_form, log=False, aftercast_delay=aftercast):
                    yield from Routines.Yield.wait(aftercast)
                    continue #nothing else to do this loop


            # === 2. LOW-HP EMERGENCY SHROUD ===
            
            if hp < 0.60 and not has_shroud:
                aftercast = 1950 #SF cast 1000 + 750aftercast + assuming 200ms for something else
                GLOBAL_CACHE._ActionQueueManager.ResetQueue("ACTION")
                if Routines.Yield.Skills.CastSkillID(self.shroud_of_distress, log =False, aftercast_delay=aftercast):
                    yield from Routines.Yield.wait(aftercast)
                    continue #nothing else to do this loop

            # === 4. MAINTAIN RUNNING STANCES ===
            if not has_dwarven and Routines.Checks.Skills.IsSkillIDReady(self.dwarven_stability):
                aftercast = 350 #1/4 sec + 100ms for something else
                if Routines.Yield.Skills.CastSkillID(self.dwarven_stability, log =False, aftercast_delay=aftercast):
                    yield from Routines.Yield.wait(aftercast)
                    continue #nothing else to do this loop

            both_ready = Routines.Checks.Skills.IsSkillIDReady(self.zealous_renewal) and Routines.Checks.Skills.IsSkillIDReady(self.pious_haste)

            if not has_pious and both_ready:
                # Zealous Renewal → Pious Haste combo
                aftercast = 200 #its instant but we need time
                if Routines.Yield.Skills.CastSkillID(self.zealous_renewal, log =False, aftercast_delay=aftercast):
                    yield from Routines.Yield.wait(aftercast)
                # Immediately follow with Pious Haste
                aftercast = 200 #PH cast 500 + 500 aftercast + assuming 200ms for something else
                if Routines.Yield.Skills.CastSkillID(self.pious_haste, log =False, aftercast_delay=aftercast):
                    yield from Routines.Yield.wait(aftercast)
                    continue


            # === IDLE WAIT ===
            yield from Routines.Yield.wait(150)
