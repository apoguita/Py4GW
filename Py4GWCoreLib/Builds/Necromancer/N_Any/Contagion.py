from Py4GWCoreLib import AgentArray, BuildMgr, GLOBAL_CACHE, Profession, Range, Routines, Utils
from Py4GWCoreLib.Agent import Agent
from Py4GWCoreLib.Player import Player
from Py4GWCoreLib.Builds.Any.HeroAI import HeroAI_Build
from Py4GWCoreLib.Skill import Skill
from Py4GWCoreLib.Builds.Skills import SkillsTemplate

# Real condition skill ids — the values conditions register under as effects /
# shared-memory buffs (distinct from the Ailment display enum). Used to count
# every distinct condition on an agent, including those (Burning, Blind, Dazed,
# Weakness, Disease, Cracked Armor) the agent effects bitfield cannot expose.
CONDITION_SKILL_IDS = {
    "bleeding": Skill.GetID("Bleeding"),
    "burning": Skill.GetID("Burning"),
    "poison": Skill.GetID("Poison"),
    "disease": Skill.GetID("Disease"),
    "blind": Skill.GetID("Blind"),
    "dazed": Skill.GetID("Dazed"),
    "crippled": Skill.GetID("Crippled"),
    "deep_wound": Skill.GetID("Deep_Wound"),
    "weakness": Skill.GetID("Weakness"),
    "cracked_armor": Skill.GetID("Cracked_Armor"),
}

# Required
CONTAGION_ID = Skill.GetID("Contagion")
FOUL_FEAST_ID = Skill.GetID("Foul_Feast")
MASOCHISM_ID = Skill.GetID("Masochism")
DARK_AURA_ID = Skill.GetID("Dark_Aura")

# Optional
BURNING_SPEED_ID = Skill.GetID("Burning_Speed")
POISONED_HEART_ID = Skill.GetID("Poisoned_Heart")
EBON_ESCAPE_ID = Skill.GetID("Ebon_Escape")
I_AM_UNSTOPPABLE_ID = Skill.GetID("I_Am_Unstoppable")
SHADOW_SANCTUARY_KURZICK_ID = Skill.GetID("Shadow_Sanctuary_kurzick")
SHADOW_SANCTUARY_LUXON_ID = Skill.GetID("Shadow_Sanctuary_luxon")
SIGNET_OF_AGONY_ID = Skill.GetID("Signet_of_Agony")
DEATHS_CHARGE_ID = Skill.GetID("Deaths_Charge")


class Contagion(BuildMgr):
    def __init__(self, match_only: bool = False):
        super().__init__(
            name="Contagion",
            required_primary=Profession.Necromancer,
            required_secondary=Profession(0),  # Any
            template_code="OAZDUsx6QJgbhMV3MIN0l0k0BA",
            required_skills=[
                CONTAGION_ID,
                FOUL_FEAST_ID,
                MASOCHISM_ID,
                DARK_AURA_ID,
            ],
            optional_skills=[
                BURNING_SPEED_ID,
                POISONED_HEART_ID,
                EBON_ESCAPE_ID,
                I_AM_UNSTOPPABLE_ID,
                SHADOW_SANCTUARY_KURZICK_ID,
                SHADOW_SANCTUARY_LUXON_ID,
                SIGNET_OF_AGONY_ID,
                DEATHS_CHARGE_ID,
            ],
        )
        if match_only:
            return

        self.SetFallback("HeroAI", HeroAI_Build(standalone_fallback=True))
        self.SetSkillCastingFn(self._run_local_skill_logic)
        self.skills: SkillsTemplate = SkillsTemplate(self)

        # One-shot guard so the melee-weapon hint is logged only once per load.
        self._melee_hint_logged = False

    def LoadSkillBar(self):
        # Load the template bar first, then log the melee-weapon hint once.
        yield from super().LoadSkillBar()

        if not self._melee_hint_logged:
            from Py4GWCoreLib import ConsoleLog, Console

            ConsoleLog(
                "Contagion",
                "This build works best with a melee weapon equipped.",
                Console.MessageType.Info,
            )
            self._melee_hint_logged = True

    def _run_local_skill_logic(self):
        if not Routines.Checks.Skills.CanCast():
            return False

        # Top priority: Ebon Escape as an emergency bail when the player's own
        # health or the target ally's health drops below 40%.
        if (yield from self._ebon_escape_emergency()):
            return True

        # Masochism first so it is up before Contagion (energy regen + the
        # condition Contagion mirrors). Maintained in and out of combat
        # (local logic, no aggro gate).
        if (yield from self._masochism()):
            return True

        # Dark Aura: local build logic, priority directly behind Masochism.
        # Applied just before combat (close to aggro).
        if (yield from self._dark_aura()):
            return True

        # Maintain Contagion (elite) at all times, in and out of combat. The
        # helper defers to Masochism while near aggro but keeps the enchant up
        # out of combat.
        if (yield from self.skills.Necromancer.DeathMagic.Contagion()):
            return True

        # Offensive damage/condition skills prioritised ahead of Foul Feast,
        # each gated on a foe within "nearby" (umstehend) range inside its
        # helper.
        if self.IsSkillEquipped(BURNING_SPEED_ID) and (
            yield from self.skills.Elementalist.FireMagic.Burning_Speed()
        ):
            return True

        if self.IsSkillEquipped(POISONED_HEART_ID) and (
            yield from self.skills.Necromancer.Curses.Poisoned_Heart()
        ):
            return True

        if self.IsSkillEquipped(SIGNET_OF_AGONY_ID) and (
            yield from self.skills.Necromancer.BloodMagic.Signet_of_Agony()
        ):
            return True

        # Foul Feast: local build logic. Cleanse the ally (never self) carrying
        # the most distinct conditions, gated on an enemy being nearby.
        if (yield from self._foul_feast()):
            return True

        # I Am Unstoppable: maintained whenever in combat (local build logic).
        if (yield from self._i_am_unstoppable()):
            return True

        # Ebon Escape (offensive): shadow step to the ally standing among the
        # most enemies (local build logic). Emergency low-health case is handled
        # at the top of the rotation.
        if (yield from self._ebon_escape_cluster()):
            return True

        # Death's Charge: gap-close onto the most clustered foe (> 500 away,
        # within spellcast). Run before the nearby-gated block so the step
        # brings those skills into range.
        if self.IsSkillEquipped(DEATHS_CHARGE_ID) and (
            yield from self.skills.Assassin.ShadowArts.Deaths_Charge()
        ):
            return True

        # Shadow Sanctuary: self-enchant defensive, gated on a foe within
        # "nearby" range inside its helper.
        if (
            self.IsSkillEquipped(SHADOW_SANCTUARY_KURZICK_ID)
            or self.IsSkillEquipped(SHADOW_SANCTUARY_LUXON_ID)
        ) and (
            yield from self.skills.Assassin.ShadowArts.Shadow_Sanctuary()
        ):
            return True

        # Lowest priority: auto-attack, preferring the most clustered enemy.
        # Throttled by weapon aftercast, so it only returns True on a re-issue
        # tick and otherwise lets the HeroAI fallback handle unbound skills.
        if (yield from self.AutoAttack(target_type="EnemyClustered")):
            return True

        return False

    def _ebon_escape_target(self):
        """Ally (never self) in spellcast range standing among the most enemies.

        Returns ``(ally_id, enemy_count)``; ``(0, -1)`` when no ally qualifies.
        Enemies around the ally are counted directly within "nearby" range.
        """
        player_pos = Player.GetXY()
        allies = Routines.Agents.GetFilteredAllyArray(
            player_pos[0],
            player_pos[1],
            Range.Spellcast.value,
            other_ally=True,
        )

        target_agent_id = 0
        best_enemy_count = -1
        for ally_id in allies:
            ally_x, ally_y = Agent.GetXY(ally_id)
            enemies = Routines.Agents.GetFilteredEnemyArray(ally_x, ally_y, Range.Nearby.value)
            enemies = AgentArray.Filter.ByCondition(enemies, lambda eid: Agent.IsAlive(eid))
            enemy_count = len(enemies or [])
            if enemy_count > best_enemy_count:
                best_enemy_count = enemy_count
                target_agent_id = ally_id

        return target_agent_id, best_enemy_count

    def _ebon_escape_emergency(self):
        """Ebon Escape emergency bail: own or target-ally health below 40%."""
        if not self.IsSkillEquipped(EBON_ESCAPE_ID):
            return False

        target_agent_id, _ = self._ebon_escape_target()
        if not target_agent_id:
            return False

        own_low = Agent.GetHealth(Player.GetAgentID()) < 0.40
        ally_low = Agent.GetHealth(target_agent_id) < 0.40
        if not (own_low or ally_low):
            return False

        return (yield from self.CastSkillIDAndRestoreTarget(
            skill_id=EBON_ESCAPE_ID,
            target_agent_id=target_agent_id,
            log=False,
            aftercast_delay=250,
        ))

    def _ebon_escape_cluster(self):
        """Ebon Escape onto the ally standing among the most enemies."""
        if not self.IsSkillEquipped(EBON_ESCAPE_ID):
            return False

        target_agent_id, best_enemy_count = self._ebon_escape_target()
        if not target_agent_id or best_enemy_count <= 0:
            return False

        return (yield from self.CastSkillIDAndRestoreTarget(
            skill_id=EBON_ESCAPE_ID,
            target_agent_id=target_agent_id,
            log=False,
            aftercast_delay=250,
        ))

    def _i_am_unstoppable(self):
        """Maintain I Am Unstoppable for the whole time the player is in combat.

        Cast whenever in aggro and the buff is not already active; the skill's
        own recharge prevents spam.
        """
        if not self.IsSkillEquipped(I_AM_UNSTOPPABLE_ID):
            return False
        if not self.IsInAggro():
            return False
        if Routines.Checks.Agents.HasEffect(Player.GetAgentID(), I_AM_UNSTOPPABLE_ID):
            return False

        return (yield from self.CastSkillID(
            skill_id=I_AM_UNSTOPPABLE_ID,
            log=False,
            aftercast_delay=250,
        ))

    def _masochism(self, assume_active_ms: int = 25000):
        """Maintain Masochism on the caster at all times, in and out of combat.

        Local build logic with no aggro gate (unlike the shared helper), so the
        energy regen is kept up before pulls and between fights. Refreshes inside
        the last 2 seconds and uses a short assume-active window to avoid
        recasting before the effect registers.
        """
        if not self.IsSkillEquipped(MASOCHISM_ID):
            return False

        player_agent_id = Player.GetAgentID()
        now_ms = int(Utils.GetBaseTimestamp())
        assumed_effects = getattr(self, "_self_effect_assumed_until", {})

        if int(assumed_effects.get(MASOCHISM_ID, 0) or 0) > now_ms:
            return False

        if Routines.Checks.Agents.HasEffect(player_agent_id, MASOCHISM_ID):
            remaining_ms = int(GLOBAL_CACHE.Effects.GetEffectTimeRemaining(
                player_agent_id, MASOCHISM_ID,
            ) or 0)
            if remaining_ms > 2000:
                assumed_effects.pop(MASOCHISM_ID, None)
                return False

        cast_result = yield from self.CastSkillID(
            skill_id=MASOCHISM_ID,
            log=False,
            aftercast_delay=250,
        )
        if cast_result:
            assumed_effects[MASOCHISM_ID] = now_ms + max(0, int(assume_active_ms))
            setattr(self, "_self_effect_assumed_until", assumed_effects)
            return True

        return False

    def _dark_aura(self):
        """Dark Aura with build-specific targeting.

        Cast just before / during combat (close to aggro). Prefers the caster
        when Dark Aura is not already up on the player. Once the player already
        has it, Dark Aura may only be cast on an ally that carries Masochism but
        not Dark Aura; otherwise it holds.
        """
        if not self.IsSkillEquipped(DARK_AURA_ID):
            return False
        if not (self.IsInAggro() or self.IsCloseToAggro()):
            return False

        player_agent_id = Player.GetAgentID()
        target_agent_id = 0

        if not Routines.Checks.Agents.HasEffect(player_agent_id, DARK_AURA_ID):
            # Preferred case: put Dark Aura on the caster first.
            target_agent_id = player_agent_id
        else:
            # Self already enchanted: only an ally with Masochism and without
            # Dark Aura qualifies.
            player_pos = Player.GetXY()
            allies = Routines.Agents.GetFilteredAllyArray(
                player_pos[0],
                player_pos[1],
                Range.Spellcast.value,
                other_ally=True,
            )
            for ally_id in allies:
                if (
                    Routines.Checks.Agents.HasEffect(ally_id, MASOCHISM_ID)
                    and not Routines.Checks.Agents.HasEffect(ally_id, DARK_AURA_ID)
                ):
                    target_agent_id = ally_id
                    break

        if not target_agent_id:
            return False

        return (yield from self.CastSkillIDAndRestoreTarget(
            skill_id=DARK_AURA_ID,
            target_agent_id=target_agent_id,
            log=False,
            aftercast_delay=250,
        ))

    def _count_distinct_conditions(self, agent_id: int) -> int:
        """Number of distinct conditions on the agent.

        Conditions are detected via Routines.Checks.Agents.HasEffect, which
        reads party members' conditions from shared memory (each account
        publishes its own full condition set as buffs) and falls back to the
        local effect cache. The four bitfield-exposed conditions (Bleeding,
        Crippled, Deep Wound, Poison) are also checked directly so they still
        register when shared-memory data is unavailable. Detections are deduped
        by condition name; the generic "is conditioned" flag provides a floor of
        1 for anything left unattributed.
        """
        detected: set[str] = set()

        for name, has_flag in (
            ("bleeding", Agent.IsBleeding),
            ("crippled", Agent.IsCrippled),
            ("deep_wound", Agent.IsDeepWounded),
            ("poison", Agent.IsPoisoned),
        ):
            if has_flag(agent_id):
                detected.add(name)

        for name, condition_id in CONDITION_SKILL_IDS.items():
            if (
                condition_id
                and name not in detected
                and Routines.Checks.Agents.HasEffect(agent_id, condition_id)
            ):
                detected.add(name)

        count = len(detected)
        if count == 0 and Agent.IsConditioned(agent_id):
            count = 1
        return count

    def _foul_feast(self):
        """Foul Feast on the most-conditioned ally, lowest-HP first on ties.

        Only fires while a live enemy stands within "nearby" range of the
        player, and never targets the caster (allies only). Among allies in
        spellcast range, the one carrying the most distinct (detectable)
        conditions is chosen; ties are broken toward the lowest health so the
        most endangered conditioned ally is cleansed. Holds if no ally has any
        condition.
        """
        if not self.IsSkillEquipped(FOUL_FEAST_ID):
            return False

        player_pos = Player.GetXY()

        # Gate: require a live enemy within "nearby" (umstehend) range.
        enemy_array = AgentArray.GetEnemyArray()
        enemy_array = AgentArray.Filter.ByDistance(enemy_array, player_pos, Range.Nearby.value)
        enemy_array = AgentArray.Filter.ByCondition(enemy_array, lambda aid: Agent.IsAlive(aid))
        if not enemy_array:
            return False

        # Pick the conditioned ally (excluding self) by most conditions, then
        # lowest health. The sort key is maximised: higher count wins, and for
        # equal counts the more negative -health (i.e. lower health) wins.
        allies = Routines.Agents.GetFilteredAllyArray(
            player_pos[0],
            player_pos[1],
            Range.Spellcast.value,
            other_ally=True,
        )
        target_agent_id = 0
        best_key = None
        for ally_id in allies:
            condition_count = self._count_distinct_conditions(ally_id)
            if condition_count <= 0:
                continue
            key = (condition_count, -Agent.GetHealth(ally_id))
            if best_key is None or key > best_key:
                best_key = key
                target_agent_id = ally_id

        if not target_agent_id:
            return False

        return (yield from self.CastSkillIDAndRestoreTarget(
            skill_id=FOUL_FEAST_ID,
            target_agent_id=target_agent_id,
            log=False,
            aftercast_delay=250,
        ))
