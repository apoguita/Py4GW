from __future__ import annotations

from typing import TYPE_CHECKING

from Py4GWCoreLib.BuildMgr import BuildCoroutine
from Py4GWCoreLib import Player, Routines
from Py4GWCoreLib.Skill import Skill

if TYPE_CHECKING:
    from Py4GWCoreLib.BuildMgr import BuildMgr

__all__ = ["Leadership"]


class Leadership:
    def __init__(self, build: BuildMgr) -> None:
        self.build: BuildMgr = build

    def _get_leadership_level(self) -> int:
        from Py4GWCoreLib import Agent

        player_agent_id = Player.GetAgentID()
        attributes = Agent.GetAttributes(player_agent_id)
        leadership = next((attribute for attribute in attributes if attribute.GetName() == "Leadership"), None)
        return int(getattr(leadership, "level", 0) or 0)

    #region H
    def Heroic_Refrain(self) -> BuildCoroutine:
        heroic_refrain_id: int = Skill.GetID("Heroic_Refrain")
        heroic_refrain = self.build.GetCustomSkill(heroic_refrain_id)

        if not self.build.IsSkillEquipped(heroic_refrain_id):
            return False

        player_agent_id = Player.GetAgentID()

        player_has_hr = Routines.Checks.Agents.HasEffect(
            player_agent_id,
            heroic_refrain_id,
        )

        # Lorsque l'option "Should Leadership lvl 20" est activée,
        # HR doit d'abord être appliqué au lanceur pour atteindre le niveau 20.
        if self._get_leadership_level() < 20:
            if not player_has_hr:
                return (yield from self.build.CastSkillIDAndRestoreTarget(
                    skill_id=heroic_refrain_id,
                    target_agent_id=player_agent_id,
                    log=False,
                    aftercast_delay=250,
                ))

            # HR est déjà actif : ne pas le relancer inutilement.
            return False

        # Même sans l'option niveau 20, le lanceur doit recevoir HR en priorité.
        if not player_has_hr:
            return (yield from self.build.CastSkillIDAndRestoreTarget(
                skill_id=heroic_refrain_id,
                target_agent_id=player_agent_id,
                log=False,
                aftercast_delay=250,
            ))

        # Chercher ensuite un membre du groupe à renforcer.
        target_agent_id = self.build.ResolveAllyTarget(
            heroic_refrain_id,
            heroic_refrain,
        )

        if not target_agent_id:
            return False

        # Ne pas relancer HR sur une cible qui possède déjà l'effet.
        if Routines.Checks.Agents.HasEffect(
            target_agent_id,
            heroic_refrain_id,
        ):
            return False

        return (yield from self.build.CastSkillIDAndRestoreTarget(
            skill_id=heroic_refrain_id,
            target_agent_id=target_agent_id,
            log=False,
            aftercast_delay=250,
        ))
    #endregion

    #region A
    def Aggressive_Refrain(self) -> BuildCoroutine:
        aggressive_refrain_id: int = Skill.GetID("Aggressive_Refrain")
        player_agent_id = Player.GetAgentID()

        if not self.build.IsSkillEquipped(aggressive_refrain_id):
            return False
        if not (self.build.IsInAggro() or self.build.IsCloseToAggro()):
            return False
        if Routines.Checks.Agents.HasEffect(player_agent_id, aggressive_refrain_id):
            return False

        return (yield from self.build.CastSkillID(
            skill_id=aggressive_refrain_id,
            target_agent_id=player_agent_id,
            log=False,
            aftercast_delay=250,
        ))

    def Angelic_Protection(
        self,
        *,
        health_threshold: float | None = None,
    ) -> BuildCoroutine:
        from Py4GWCoreLib.Agent import Agent

        angelic_protection_id: int = Skill.GetID("Angelic_Protection")
        angelic_protection = self.build.GetCustomSkill(angelic_protection_id)

        if not self.build.IsSkillEquipped(angelic_protection_id):
            return False
        if not self.build.IsInAggro():
            return False

        threshold: float = (
            health_threshold
            if health_threshold is not None
            else float(angelic_protection.Conditions.LessLife or 0.75)
        )
        threshold = max(0.0, min(1.0, threshold))

        target_agent_id = self.build.ResolvePreferredAllyTarget(
            angelic_protection_id,
            angelic_protection,
            validator=lambda agent_id: Agent.IsAlive(agent_id) and Agent.GetHealth(agent_id) < threshold,
        )
        if not target_agent_id:
            return False

        return (yield from self.build.CastSkillIDAndRestoreTarget(
            skill_id=angelic_protection_id,
            target_agent_id=target_agent_id,
            log=False,
            aftercast_delay=250,
        ))
    #endregion

    #region M
    def Make_Your_Time(self) -> BuildCoroutine:
        from Py4GWCoreLib import Agent, AgentArray, Range
        from HeroAI.utils import IsPartyMember

        make_your_time_id: int = Skill.GetID("Make_Your_Time")
        player_agent_id = Player.GetAgentID()

        if not self.build.IsSkillEquipped(make_your_time_id):
            return False

        if not (self.build.IsInAggro() or self.build.IsCloseToAggro()):
            return False

        candidates = AgentArray.GetAllyArray() + AgentArray.GetSpiritPetArray()
        candidates = AgentArray.Filter.ByDistance(candidates, Player.GetXY(), Range.Earshot.value)
        candidates = AgentArray.Filter.ByCondition(candidates, lambda a: Agent.IsAlive(a) and IsPartyMember(a))
        if len(candidates) < 3:
            return False

        return (yield from self.build.CastSkillID(
            skill_id=make_your_time_id,
            target_agent_id=player_agent_id,
            log=False,
            aftercast_delay=250,
        ))
    #endregion

    #region T
    def Theyre_on_Fire(self) -> BuildCoroutine:
        theyre_on_fire_id: int = Skill.GetID("Theyre_on_Fire")
        player_agent_id = Player.GetAgentID()

        if not self.build.IsSkillEquipped(theyre_on_fire_id):
            return False
        if Routines.Checks.Agents.HasEffect(player_agent_id, theyre_on_fire_id):
            return False

        return (yield from self.build.CastSkillID(
            skill_id=theyre_on_fire_id,
            target_agent_id=player_agent_id,
            log=False,
            aftercast_delay=250,
        ))
    #endregion
