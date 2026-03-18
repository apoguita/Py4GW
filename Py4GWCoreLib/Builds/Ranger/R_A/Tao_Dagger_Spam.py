from Py4GWCoreLib import BuildMgr, Profession
from Py4GWCoreLib import Profession
from Py4GWCoreLib import Routines
from Py4GWCoreLib.Builds.Any.AutoCombat import AutoCombat
from Py4GWCoreLib.Skill import Skill
from Py4GWCoreLib.Agent import Agent
from Py4GWCoreLib.Player import Player

Jagged_Strike_ID = Skill.GetID("Jagged_Strike")
Fox_Fangs_ID = Skill.GetID("Fox_Fangs")
Death_Blossom_ID = Skill.GetID("Death_Blossom")
Together_as_one_ID = Skill.GetID("Together_as_one")

class Tao_Dagger_Spam(BuildMgr):
    def __init__(self):
        super().__init__(
            name="TaO Dagger Spam",
            required_primary=Profession.Ranger,
            required_secondary=Profession.Assassin,
            template_code="OgcTYr72Xyhhh5gZsGAAAAAAAAA",
            
            required_skills=[
                # Add required skill ids here.
                Jagged_Strike_ID,
                Fox_Fangs_ID,
                Death_Blossom_ID,
                Together_as_one_ID,
            ],
            optional_skills=[
                # Add optional/supported skill ids here.
            ],
        )
        self.SetFallback("AutoCombat", AutoCombat())
        self.SetSkillCastingFn(self._run_local_skill_logic)

        self.current_target_id = 0


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
        
        if not (yield from self.AcquireTarget()):
            return

        #TaO 
        not_has_tao_buff = lambda: not Routines.Checks.Effects.HasBuff(Player.GetAgentID(), Together_as_one_ID)
        if not_has_tao_buff():
            if (yield from self.CastSkillID(
                skill_id=Together_as_one_ID,
                extra_condition=not_has_tao_buff,
                log=False,
                aftercast_delay=250,
            )):
                return
            
        enemy_dagger_status = Agent.GetDaggerStatus(self.current_target_id)
        desired_skill_id = 0
        if enemy_dagger_status == 2:
            desired_skill_id = Death_Blossom_ID
            cast_condition = lambda: Agent.GetDaggerStatus(self.current_target_id) == 2
        elif enemy_dagger_status == 1:
            desired_skill_id = Fox_Fangs_ID
            cast_condition = lambda: Agent.GetDaggerStatus(self.current_target_id) == 1
        else:
            desired_skill_id = Jagged_Strike_ID
            cast_condition = lambda: Agent.GetDaggerStatus(self.current_target_id) in (0, 3)

        if desired_skill_id == 0:
            yield from Routines.Yield.wait(100)
            return
        
        if (yield from self.CastSkillID(
            skill_id=desired_skill_id,
            extra_condition=cast_condition,
            log=False,
            aftercast_delay=250,
        )):
            return

