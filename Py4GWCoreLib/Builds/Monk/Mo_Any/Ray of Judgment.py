import time

from Py4GWCoreLib import GLOBAL_CACHE
from Py4GWCoreLib import Profession
from Py4GWCoreLib import Routines
from Py4GWCoreLib.Builds.Any.HeroAI import HeroAI_Build
from Py4GWCoreLib import BuildMgr
from Py4GWCoreLib.Agent import Agent
from Py4GWCoreLib.Player import Player
from Py4GWCoreLib.Skill import Skill
from Py4GWCoreLib.Builds.Skills import HexRemovalPriority, SkillsTemplate


Ray_of_Judgment_ID = Skill.GetID("Ray_of_Judgment")
Smite_Hex_ID = Skill.GetID("Smite_Hex")
Air_of_Superiority_ID = Skill.GetID("Air_of_Superiority")
Castigation_Signet_ID = Skill.GetID("Castigation_Signet")
Arcane_Echo_ID = Skill.GetID("Arcane_Echo")
You_Move_Like_a_Dwarf_ID = Skill.GetID("You_Move_Like_a_Dwarf")
Smite_Condition_ID = Skill.GetID("Smite_Condition")
Ebon_Battle_Standard_of_Wisdom_ID = Skill.GetID("Ebon_Battle_Standard_of_Wisdom")
Glyph_of_Lesser_Energy_ID = Skill.GetID("Glyph_of_Lesser_Energy")
Smiters_Boon_ID = Skill.GetID("Smiters_Boon")
Reversal_of_Damage_ID = Skill.GetID("Reversal_of_Damage")
Technobabble_ID = Skill.GetID("Technobabble")


class Ray_of_Judgment(BuildMgr):
    def __init__(self, match_only: bool = False):
        super().__init__(
            name="Ray of Judgment",
            required_primary=Profession.Monk,
            template_code="OwAS4YIT+MuEWfAAAAAAAAwl",
            required_skills=[
                Ray_of_Judgment_ID,
                Smite_Hex_ID,
                Air_of_Superiority_ID,
                Castigation_Signet_ID,
            ],
            optional_skills=[
                Arcane_Echo_ID,
                You_Move_Like_a_Dwarf_ID,
                Smite_Condition_ID,
                Ebon_Battle_Standard_of_Wisdom_ID,
                Glyph_of_Lesser_Energy_ID,
                Smiters_Boon_ID,
                Reversal_of_Damage_ID,
                Technobabble_ID,
            ],
        )
        if match_only:
            return

        self.SetFallback("HeroAI", HeroAI_Build(standalone_fallback=True))
        self.SetSkillCastingFn(self._run_local_skill_logic)
        self.skills: SkillsTemplate = SkillsTemplate(self)

    def _run_local_skill_logic(self):
        if not Routines.Checks.Skills.CanCast():
            return False

        # Only Ray of Judgment may fire while Arcane Echo enchantment is up.
        arcane_echo_active = Routines.Checks.Agents.HasEffect(Player.GetAgentID(), Arcane_Echo_ID)

        # Refresh Air of Superiority on cooldown (approach + aggro).
        if (
            not arcane_echo_active
            and self.IsSkillEquipped(Air_of_Superiority_ID)
            and (self.IsInAggro() or self.IsCloseToAggro())
            and (yield from self.skills.Any.PvE.Air_of_Superiority())
        ):
            return True

        # Seed Arcane Echo: gated on energy > 23 AND RoJ ready (off cooldown).
        roj_slot = GLOBAL_CACHE.SkillBar.GetSlotBySkillID(Ray_of_Judgment_ID)
        roj_is_ready = roj_slot != 0 and Routines.Checks.Skills.IsSkillSlotReady(roj_slot)

        player_id = Player.GetAgentID()
        player_energy_abs = Agent.GetEnergy(player_id) * Agent.GetMaxEnergy(player_id)
        if (
            self.IsSkillEquipped(Arcane_Echo_ID)
            and roj_is_ready
            and player_energy_abs > 23
            and (yield from self.skills.Mesmer.NoAttribute.Arcane_Echo())
        ):
            return True

        if not self.IsInAggro():
            return False

        # Echo up: cast RoJ first to seed the echo slot.
        if arcane_echo_active and (yield from self.skills.Monk.SmitingPrayers.Ray_of_Judgment()):
            return True

        # HIGH-priority hex removal.
        if not arcane_echo_active and (yield from self.skills.Monk.SmitingPrayers.Smite_Hex(min_priority=HexRemovalPriority.HIGH)):
            return True

        # RoJ fallback when Arcane Echo isn't on the bar.
        if not self.IsSkillEquipped(Arcane_Echo_ID) and (yield from self.skills.Monk.SmitingPrayers.Ray_of_Judgment()):
            return True

        # Smiter's Boon: maintain self-buff.
        if not arcane_echo_active and self.IsSkillEquipped(Smiters_Boon_ID) and (yield from self.skills.Monk.SmitingPrayers.Smiters_Boon()):
            return True

        # RoJ on a different cluster than the previous cast (echo copy). Only meaningful
        # when Arcane Echo is on the bar — otherwise the fallback RoJ above already covered it.
        if self.IsSkillEquipped(Arcane_Echo_ID):
            last_roj_target_id = getattr(self, "_last_ray_of_judgment_target_id", 0)
            if (yield from self.skills.Monk.SmitingPrayers.Ray_of_Judgment(exclude_target_id=last_roj_target_id)):
                return True

        # YMLAD chain: fires when the previous cast was RoJ (within 2s, not yet chained).
        roj_cast_ts_ms = getattr(self, "_last_ray_of_judgment_cast_ts_ms", 0.0)
        ymlad_chain_ts_ms = getattr(self, "_last_ymlad_chain_ts_ms", 0.0)
        now_ms = time.monotonic() * 1000.0
        roj_chain_ready = (
            roj_cast_ts_ms > ymlad_chain_ts_ms
            and (now_ms - roj_cast_ts_ms) <= 2000.0
        )
        if (
            not arcane_echo_active
            and roj_chain_ready
            and self.IsSkillEquipped(You_Move_Like_a_Dwarf_ID)
            and (yield from self.skills.Any.NoAttribute.You_Move_Like_a_Dwarf())
        ):
            self._last_ymlad_chain_ts_ms = now_ms
            return True

        player_energy_pct = float(Agent.GetEnergy(Player.GetAgentID()))
        # MEDIUM-priority hex removal at >= 50% energy.
        if not arcane_echo_active and player_energy_pct >= 0.50 and (yield from self.skills.Monk.SmitingPrayers.Smite_Hex(min_priority=HexRemovalPriority.MEDIUM)):
            return True

        # Castigation Signet on an attacking foe.
        if not arcane_echo_active and (yield from self.skills.Monk.SmitingPrayers.Castigation_Signet()):
            return True

        # Reversal of Damage on ally with melee/enemies in touch range.
        if not arcane_echo_active and self.IsSkillEquipped(Reversal_of_Damage_ID) and (yield from self.skills.Monk.SmitingPrayers.Reversal_of_Damage()):
            return True

        # You Move Like a Dwarf: knockdown.
        if not arcane_echo_active and self.IsSkillEquipped(You_Move_Like_a_Dwarf_ID) and (yield from self.skills.Any.NoAttribute.You_Move_Like_a_Dwarf()):
            return True

        # Smite Condition: offensive cleanse — conditioned ally with most enemies in AoE.
        if not arcane_echo_active and self.IsSkillEquipped(Smite_Condition_ID) and (yield from self.skills.Monk.SmitingPrayers.Smite_Condition()):
            return True

        # Technobabble on a caster cluster.
        if not arcane_echo_active and self.IsSkillEquipped(Technobabble_ID) and (yield from self.skills.Any.PvE.Technobabble()):
            return True

        # Ebon Battle Standard of Wisdom: caster spell-power buff.
        if not arcane_echo_active and self.IsSkillEquipped(Ebon_Battle_Standard_of_Wisdom_ID) and (yield from self.skills.Any.NoAttribute.Ebon_Battle_Standard_of_Wisdom()):
            return True

        # LOW-priority hex removal at >= 70% energy.
        if not arcane_echo_active and player_energy_pct >= 0.70 and (yield from self.skills.Monk.SmitingPrayers.Smite_Hex()):
            return True

        return False
