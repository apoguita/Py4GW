from Py4GWCoreLib import Profession
from Py4GWCoreLib import Routines
from Py4GWCoreLib.Builds.Any.AutoCombat import AutoCombat
from Py4GWCoreLib import BuildMgr
from Py4GWCoreLib.Skill import Skill
from Py4GWCoreLib.Agent import Agent
from Py4GWCoreLib.Player import Player
from HeroAI.custom_skill_src.skill_types import CustomSkill

Cyclone_Axe_ID = Skill.GetID("Cyclone_Axe")
Whirlwind_Attack_ID = Skill.GetID("Whirlwind_Attack")
Executioners_Strike_ID = Skill.GetID("Executioners_Strike")
Seven_Weapon_Stance_ID = Skill.GetID("Seven_Weapon_Stance")
#optional
Endure_Pain_ID = Skill.GetID("Endure_Pain")

class Seven_Weapon_Stance_Axe(BuildMgr):
    def __init__(self):
        super().__init__(
            name="Seven Weapon Stance Axe",
            required_primary=Profession.Warrior,
            template_code="OQITEZJZVSpYHEqQsGAAAAAAAAA",
            
            required_skills=[
                # Add required skill ids here.
                Cyclone_Axe_ID,
                Whirlwind_Attack_ID,
                Executioners_Strike_ID,
                Seven_Weapon_Stance_ID,
            ],
            optional_skills=[
                Endure_Pain_ID,
            ],
        )
        self.SetFallback("AutoCombat", AutoCombat())
        self.SetSkillCastingFn(self._run_local_skill_logic)

        self.endure_pain: CustomSkill = self.GetCustomSkill(Endure_Pain_ID)
        self.attack_priority = (
            Executioners_Strike_ID,
            Cyclone_Axe_ID,
            Whirlwind_Attack_ID,
        )

    def _run_local_skill_logic(self):
        """
        Single-phase local logic goes here.

        Use this space for:
        - upkeep / prebuff checks
        - target selection / maintenance
        - dagger-chain gating
        - custom skill decisions using HeroAI custom skill data
        """
        if not (Routines.Checks.Agents.InAggro()):
            return

        if not Routines.Checks.Skills.CanCast():
            yield from Routines.Yield.wait(100)
            return

        not_has_SWS = lambda: not Routines.Checks.Effects.HasBuff(Player.GetAgentID(), Seven_Weapon_Stance_ID)
        if not_has_SWS():
            if (yield from self.CastSkillID(
                skill_id=Seven_Weapon_Stance_ID,
                extra_condition=not_has_SWS,
                log=False,
                aftercast_delay=250,
            )):
                return
         
        def _should_cast_endure_pain():   
            if not self.IsSkillEquipped(Endure_Pain_ID): return False
            return Agent.GetHealth(Player.GetAgentID()) < self.endure_pain.Conditions.LessLife

        if _should_cast_endure_pain():
            if (yield from self.CastSkillID(
                skill_id=Endure_Pain_ID,
                extra_condition=_should_cast_endure_pain,
                log=False,
                aftercast_delay=250,
            )):
                return
            
        if not (yield from self.AcquireTarget(target_type="EnemyClustered")):
            return

        for skill_id in self.attack_priority:
            if (yield from self.CastSkillID(
                skill_id=skill_id,
                log=False,
                aftercast_delay=250,
            )):
                return
        
        
