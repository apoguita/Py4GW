from __future__ import annotations

from typing import TYPE_CHECKING

from Py4GWCoreLib.BuildMgr import BuildCoroutine
from Py4GWCoreLib import AgentArray, Player, Range, Routines, SpiritModelID, Utils
from Py4GWCoreLib.Agent import Agent
from Py4GWCoreLib.Skill import Skill

if TYPE_CHECKING:
    from HeroAI.custom_skill_src.skill_types import CustomSkill
    from Py4GWCoreLib.BuildMgr import BuildMgr

__all__ = ["NoAttribute"]


class NoAttribute:
    def __init__(self, build: BuildMgr) -> None:
        self.build: BuildMgr = build

    #region B
    def Breath_of_the_Great_Dwarf(self) -> BuildCoroutine:
        breath_of_the_great_dwarf_id: int = Skill.GetID("Breath_of_the_Great_Dwarf")
        breath_of_the_great_dwarf: CustomSkill = self.build.GetCustomSkill(breath_of_the_great_dwarf_id)
        burning_id: int = Skill.GetID("Burning")

        def _party_has_burning() -> bool:
            ally_array = Routines.Targeting.GetAllAlliesArray(Range.SafeCompass.value)
            return any(
                Routines.Checks.Agents.HasEffect(agent_id, burning_id)
                for agent_id in (ally_array or [])
            )

        if not self.build.IsSkillEquipped(breath_of_the_great_dwarf_id):
            return False
        if not (
            self.build.EvaluatePartyWideThreshold(
                breath_of_the_great_dwarf_id,
                breath_of_the_great_dwarf,
            )
            or _party_has_burning()
        ):
            return False

        return (yield from self.build.CastSkillID(
            skill_id=breath_of_the_great_dwarf_id,
            log=False,
            aftercast_delay=250,
        ))
    #endregion

    #region G
    def Great_Dwarf_Weapon(self) -> BuildCoroutine:
        great_dwarf_weapon_id: int = Skill.GetID("Great_Dwarf_Weapon")
        great_dwarf_weapon: CustomSkill = self.build.GetCustomSkill(great_dwarf_weapon_id)

        if not self.build.IsSkillEquipped(great_dwarf_weapon_id):
            return False

        target_agent_id = self.build.ResolveAllyTarget(
            great_dwarf_weapon_id,
            great_dwarf_weapon,
        )
        if not target_agent_id:
            return False

        return (yield from self.build.CastSkillIDAndRestoreTarget(
            skill_id=great_dwarf_weapon_id,
            target_agent_id=target_agent_id,
            log=False,
            aftercast_delay=250
        ))
    #endregion
    
    #region Y
    def You_Are_All_Weaklings(self) -> BuildCoroutine:
        you_are_all_weaklings_id: int = Skill.GetID("You_Are_All_Weaklings")

        if not self.build.IsSkillEquipped(you_are_all_weaklings_id):
            return False

        target_agent_id = self.build._pick_clustered_target(
            Range.Spellcast.value,
        )
        if not target_agent_id:
            return False

        return (yield from self.build.CastSkillID(
            skill_id=you_are_all_weaklings_id,
            log=False,
            aftercast_delay=250,
            target_agent_id=target_agent_id,
        ))
    #endregion

    #region E
    def Ebon_Battle_Standard_of_Wisdom(self) -> BuildCoroutine:
        ebon_battle_standard_of_wisdom_id: int = Skill.GetID("Ebon_Battle_Standard_of_Wisdom")
        player_agent_id = Player.GetAgentID()

        if not self.build.IsSkillEquipped(ebon_battle_standard_of_wisdom_id):
            return False
        if not Routines.Checks.Agents.InAggro():
            return False
        if Routines.Checks.Agents.HasEffect(player_agent_id, ebon_battle_standard_of_wisdom_id):
            return False

        ally_array = Routines.Targeting.GetAllAlliesArray(Range.Spellcast.value)
        ally_array = AgentArray.Filter.ByCondition(
            ally_array,
            lambda agent_id: Agent.IsAlive(agent_id) and Routines.Checks.Agents.IsCaster(agent_id),
        )
        if len(ally_array or []) < 2:
            return False

        return (yield from self.build.CastSkillID(
            skill_id=ebon_battle_standard_of_wisdom_id,
            log=False,
            aftercast_delay=250,
        ))
    #endregion

    #region I
    def I_Am_Unstoppable(self) -> BuildCoroutine:
        i_am_unstoppable_id: int = Skill.GetID("I_Am_Unstoppable")
        player_agent_id = Player.GetAgentID()

        if not self.build.IsSkillEquipped(i_am_unstoppable_id):
            return False
        if not Routines.Checks.Agents.InAggro():
            return False
        if Agent.GetHealth(player_agent_id) > 0.70 and not Agent.IsKnockedDown(player_agent_id):
            return False

        return (yield from self.build.CastSkillID(
            skill_id=i_am_unstoppable_id,
            log=False,
            aftercast_delay=250,
        ))
    #endregion

    #region S
    def Save_Yourselves_kurzick(self) -> BuildCoroutine:
        save_yourselves_kurzick_id: int = Skill.GetID("Save_Yourselves_kurzick")
        return (yield from self._cast_protective_party_shout(
            save_yourselves_kurzick_id,
            health_threshold=1.1,
            minimum_allies=1,
        ))

    def Save_Yourselves_luxon(self) -> BuildCoroutine:
        save_yourselves_luxon_id: int = Skill.GetID("Save_Yourselves_luxon")
        return (yield from self._cast_protective_party_shout(
            save_yourselves_luxon_id,
            health_threshold=1.1,
            minimum_allies=0,
        ))

    def Summon_Spirits_kurzick(self) -> BuildCoroutine:
        summon_spirits_kurzick_id: int = Skill.GetID("Summon_Spirits_kurzick")
        return (yield from self._summon_spirits(summon_spirits_kurzick_id))

    def Summon_Spirits_luxon(self) -> BuildCoroutine:
        summon_spirits_luxon_id: int = Skill.GetID("Summon_Spirits_luxon")
        return (yield from self._summon_spirits(summon_spirits_luxon_id))
    #endregion

    #region T
    def Theres_Nothing_to_Fear(self) -> BuildCoroutine:
        theres_nothing_to_fear_id: int = Skill.GetID("Theres_Nothing_to_Fear")
        return (yield from self._cast_protective_party_shout(
            theres_nothing_to_fear_id,
            health_threshold=1.1,
            minimum_allies=0,
        ))
    #endregion

    def _cast_protective_party_shout(
        self,
        skill_id: int,
        *,
        health_threshold: float,
        minimum_allies: int,
    ) -> BuildCoroutine:
        player_agent_id = Player.GetAgentID()

        if not self.build.IsSkillEquipped(skill_id):
            return False
        if not Routines.Checks.Agents.InAggro():
            return False
        if Routines.Checks.Agents.HasEffect(player_agent_id, skill_id):
            return False

        ally_array = Routines.Targeting.GetAllAlliesArray(Range.Earshot.value)
        ally_array = AgentArray.Filter.ByCondition(
            ally_array,
            lambda agent_id: Agent.IsAlive(agent_id) and Agent.GetHealth(agent_id) < health_threshold,
        )
        if len(ally_array or []) < minimum_allies:
            return False

        return (yield from self.build.CastSkillID(
            skill_id=skill_id,
            log=False,
            aftercast_delay=250,
        ))

    def _get_owned_core_spirits(
        self,
        range_value: float = Range.Compass.value,
        include_owner_fallback: bool = False,
    ) -> list[int]:
        core_spirits = {
            SpiritModelID.SHELTER,
            SpiritModelID.UNION,
            SpiritModelID.DISPLACEMENT,
        }
        player_agent_id = Player.GetAgentID()
        spirit_array = AgentArray.GetSpiritPetArray()
        spirit_array = AgentArray.Filter.ByDistance(spirit_array, Player.GetXY(), range_value)
        spirit_array = AgentArray.Filter.ByCondition(
            spirit_array,
            lambda agent_id: Agent.IsAlive(agent_id) and Agent.IsSpawned(agent_id),
        )

        owned_core_spirits: list[int] = []
        nearby_core_spirits: list[int] = []
        ownerless_core_spirits: list[int] = []
        for spirit_id in spirit_array:
            model_value = Agent.GetPlayerNumber(spirit_id)
            if model_value not in SpiritModelID._value2member_map_:
                continue
            if SpiritModelID(model_value) not in core_spirits:
                continue
            nearby_core_spirits.append(spirit_id)

            owner_id = Agent.GetOwnerID(spirit_id)
            if owner_id == player_agent_id:
                owned_core_spirits.append(spirit_id)
            elif owner_id == 0:
                ownerless_core_spirits.append(spirit_id)

        if owned_core_spirits:
            return owned_core_spirits
        if include_owner_fallback:
            # Return the full nearby set when ownership metadata is unreliable.
            # Returning only ownerless spirits can hide valid distant spirits.
            return nearby_core_spirits
        return owned_core_spirits

    def _summon_spirits(self, skill_id: int) -> BuildCoroutine:
        if not self.build.IsSkillEquipped(skill_id):
            self.build._debug(f"Summon Spirits skipped: skill not equipped ({skill_id})", True)
            return False

        in_aggro = Routines.Checks.Agents.InAggro()

        spirits = self._get_owned_core_spirits()
        if not spirits:
            spirits = self._get_owned_core_spirits(
                Range.Compass.value,
                include_owner_fallback=True,
            )
            if spirits:
                self.build._debug(
                    "Summon Spirits owner fallback: nearby core spirits found with non-matching owner metadata",
                    True,
                )
            else:
                spirits_safe_compass = self._get_owned_core_spirits(
                    Range.SafeCompass.value,
                    include_owner_fallback=True,
                )
                if spirits_safe_compass:
                    self.build._debug(
                        "Summon Spirits skipped: owned core spirits found, but all are outside compass range",
                        True,
                    )
                else:
                    self.build._debug("Summon Spirits skipped: no owned core spirits found", True)
                return False

        if not spirits:
            return False

        player_xy = Player.GetXY()
        spirit_distances = [
            Utils.Distance(player_xy, Agent.GetXY(spirit_id))
            for spirit_id in spirits
        ]
        if in_aggro:
            # In combat, keep spirits tight: pull them once any core spirit leaves Nearby.
            should_reposition = any(
                Range.Nearby.value < distance <= Range.Compass.value
                for distance in spirit_distances
            )
            mode_label = "aggro-nearby"
        else:
            should_reposition = any(
                Range.Spirit.value < distance <= Range.Compass.value
                for distance in spirit_distances
            )
            mode_label = "ooc-compass"

        if not should_reposition:
            nearest_distance = min(spirit_distances) if spirit_distances else 0.0
            farthest_distance = max(spirit_distances) if spirit_distances else 0.0
            self.build._debug(
                (
                    "Summon Spirits skipped: all owned core spirits within threshold "
                    f"(nearest={nearest_distance:.1f}, farthest={farthest_distance:.1f}, mode={mode_label})"
                ),
                True,
            )
            return False

        self.build._debug(
            f"Summon Spirits trigger: owned core spirit is beyond spirit range (mode={mode_label})",
            True,
        )
        precheck_failure = self.build._get_can_cast_skill_failure_reason(skill_id)
        if precheck_failure is not None:
            self.build._debug(f"Summon Spirits precheck blocked: reason={precheck_failure}", True)
            return False

        result = (yield from self.build.CastSkillID(
            skill_id=skill_id,
            log=False,
            aftercast_delay=250,
        ))
        if result:
            self.build._debug("Summon Spirits cast success", True)
        else:
            self.build._debug("Summon Spirits cast failed (CanCastSkillID or runtime cast failure)", True)
        return result
