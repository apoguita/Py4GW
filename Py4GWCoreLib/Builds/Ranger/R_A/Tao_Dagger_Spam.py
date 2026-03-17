import Py4GW
from Py4GWCoreLib import BuildMgr, Profession, Range
from Py4GWCoreLib import Routines
from Py4GWCoreLib import ConsoleLog
from Py4GWCoreLib.Builds.Any.AutoCombat import AutoCombat
from HeroAI.custom_skill import CustomSkill
from HeroAI.targeting import GetEnemyInjured
from Py4GWCoreLib.Skill import Skill
from Py4GWCoreLib.Agent import Agent
from Py4GWCoreLib.Player import Player
from Py4GWCoreLib.Party import Party

class Tao_Dagger_Spam(BuildMgr):
    def __init__(self):
        super().__init__(
            name="TaO Dagger Spam",
            required_primary=Profession.Ranger,
            required_secondary=Profession.Assassin,
            template_code="OgcTYr72Xyhhh5gZsGAAAAAAAAA",
            required_skills=[
                # Add required skill ids here.
                Skill.GetID("Jagged_Strike"),
                Skill.GetID("Fox_Fangs"),
                Skill.GetID("Death_Blossom"),
                Skill.GetID("Together_as_one"),
            ],
            optional_skills=[
                # Add optional/supported skill ids here.
            ],
        )
        self.SetFallback("AutoCombat", AutoCombat())
        self.SetSkillCastingFn(self._run_local_skill_logic)

        self.jagged_strike = Skill.GetID("Jagged_Strike") 
        self.fox_fangs = Skill.GetID("Fox_Fangs")
        self.death_blossom = Skill.GetID("Death_Blossom")
        self.together_as_one = Skill.GetID("Together_as_one")
        
        self.skill_data:dict[int, CustomSkill] = {}
        self.skill_data[self.jagged_strike] = self._get_custom_skill(self.jagged_strike)
        self.skill_data[self.fox_fangs] = self._get_custom_skill(self.fox_fangs)
        self.skill_data[self.death_blossom] = self._get_custom_skill(self.death_blossom)
        self.skill_data[self.together_as_one] = self._get_custom_skill(self.together_as_one)
        
        self.db_combo_type = Skill.Data.GetCombo(self.death_blossom)
        self.ff_combo_type = Skill.Data.GetCombo(self.fox_fangs)
        self.js_combo_type = Skill.Data.GetCombo(self.jagged_strike)
        
        self.current_target_id = 0

    def _debug(self, message: str) -> None:
        ConsoleLog(self.build_name, message, Py4GW.Console.MessageType.Info, log=True)

    def _pick_fallback_target(self) -> int:
        injured_target = GetEnemyInjured(Range.Earshot.value)
        if (
            Agent.IsValid(injured_target)
            and not Agent.IsDead(injured_target)
            and Agent.GetHealth(injured_target) < 1.0
        ):
            return injured_target

        nearest_target = Routines.Agents.GetNearestEnemy(Range.Earshot.value)
        if Agent.IsValid(nearest_target) and not Agent.IsDead(nearest_target):
            return nearest_target

        return 0

    def _acquire_target(self):
        party_target = Party.GetPartyTarget()
        self._debug(f"_acquire_target start current={self.current_target_id} party_target={party_target}")

        if Agent.IsValid(party_target) and not Agent.IsDead(party_target):
            desired_target = party_target
            target_source = "party"
        elif Agent.IsValid(self.current_target_id) and not Agent.IsDead(self.current_target_id):
            desired_target = self.current_target_id
            target_source = "current"
        else:
            desired_target = self._pick_fallback_target()
            target_source = "fallback"

        if Agent.IsValid(desired_target) and not Agent.IsDead(desired_target):
            target_changed = desired_target != self.current_target_id
            self.current_target_id = desired_target
            if target_changed:
                self._debug(f"Selected new {target_source} target {self.current_target_id}")
            else:
                self._debug(f"Keeping {target_source} target {self.current_target_id}")
            return True, target_changed

        self.current_target_id = 0
        self._debug("No valid target acquired")
        return False, False

    def _run_local_skill_logic(self):
        """
        Single-phase local logic goes here.

        Use this space for:
        - upkeep / prebuff checks
        - target selection / maintenance
        - dagger-chain gating
        - custom skill decisions using HeroAI custom skill data
        """
        in_aggro = Routines.Checks.Agents.InAggro()
        self._debug(f"Tick start in_aggro={in_aggro} current_target={self.current_target_id}")
        if not in_aggro:
            self._debug("Skipping local logic because player is not in aggro")
            return

        if not Routines.Checks.Skills.CanCast():
            self._debug("Skipping local logic because player cannot cast right now")
            yield from Routines.Yield.wait(100)
            return
        
        target_acquired, target_changed = self._acquire_target()
        if not target_acquired:
            self._debug("Target acquisition failed, waiting 100ms")
            yield from Routines.Yield.wait(100)
            return

        if target_changed or Player.GetTargetID() != self.current_target_id:
            self._debug(
                f"Settling target desired={self.current_target_id} "
                f"player_target={Player.GetTargetID()} changed={target_changed}"
            )
            yield from Routines.Yield.Agents.ChangeTarget(self.current_target_id)
            return

        has_tao_buff = Routines.Checks.Effects.HasBuff(Player.GetAgentID(), self.together_as_one)
        if not has_tao_buff:
            self._debug(
                f"Trying Together as One buff_missing=True "
                f"ready={Routines.Checks.Skills.IsSkillIDReady(self.together_as_one)} "
                f"energy={Routines.Checks.Skills.HasEnoughEnergy(Player.GetAgentID(), self.together_as_one)}"
            )
            if (yield from self.CastSkillID(
                skill_id=self.together_as_one,
                extra_condition=lambda: not Routines.Checks.Effects.HasBuff(Player.GetAgentID(), self.together_as_one),
                log=False,
                aftercast_delay=250,
            )):
                self._debug("Together as One cast succeeded")
                return
            self._debug("Together as One cast failed")
            
        enemy_dagger_status = Agent.GetDaggerStatus(self.current_target_id)
        self._debug(f"Acquired target={self.current_target_id} dagger_status={enemy_dagger_status} player_target={Player.GetTargetID()}")
        
        if enemy_dagger_status == 2:
            desired_skill_id = self.death_blossom
            desired_skill_name = "Death Blossom"
            cast_condition = lambda: Agent.GetDaggerStatus(self.current_target_id) == 2
        elif enemy_dagger_status == 1:
            desired_skill_id = self.fox_fangs
            desired_skill_name = "Fox Fangs"
            cast_condition = lambda: Agent.GetDaggerStatus(self.current_target_id) == 1
        else:
            desired_skill_id = self.jagged_strike
            desired_skill_name = "Jagged Strike"
            cast_condition = lambda: Agent.GetDaggerStatus(self.current_target_id) in (0, 3)

        self._debug(
            f"Trying {desired_skill_name} target={self.current_target_id} "
            f"condition={cast_condition()} "
            f"ready={Routines.Checks.Skills.IsSkillIDReady(desired_skill_id)} "
            f"energy={Routines.Checks.Skills.HasEnoughEnergy(Player.GetAgentID(), desired_skill_id)}"
        )
        if (yield from self.CastSkillID(
            skill_id=desired_skill_id,
            extra_condition=cast_condition,
            log=False,
            aftercast_delay=250,
        )):
            self._debug(f"{desired_skill_name} cast succeeded")
            return
        self._debug(f"{desired_skill_name} cast failed")
