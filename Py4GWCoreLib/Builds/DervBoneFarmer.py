from Py4GWCoreLib import GLOBAL_CACHE
from Py4GWCoreLib import ActionQueueManager
from Py4GWCoreLib import BuildMgr
from Py4GWCoreLib import Key
from Py4GWCoreLib import Keystroke
from Py4GWCoreLib import Player
from Py4GWCoreLib import Profession
from Py4GWCoreLib import Range
from Py4GWCoreLib import Routines
from Py4GWCoreLib import Skill
from Py4GWCoreLib import Weapon
from Py4GWCoreLib.Builds.AutoCombat import AutoCombat


# =================== BUILD ========================
class DervBuildFarmStatus:
    Setup = 'setup'
    Prepare = 'prepare'
    Kill = 'kill'
    Loot = 'loot'
    Wait = 'wait'


class DervBoneFarmer(BuildMgr):
    def __init__(self):
        super().__init__(
            name="Derv Feather Farmer",
            required_primary=Profession.Dervish,
            required_secondary=Profession.Assassin,
            template_code='OgCjkqqLrSYiihdftXjhOXhX0kA',
            skills=[
                GLOBAL_CACHE.Skill.GetID("Signet_of_Mystic_Speed"),
                GLOBAL_CACHE.Skill.GetID("Pious_Fury"),
                GLOBAL_CACHE.Skill.GetID("Grenths_Aura"),
                GLOBAL_CACHE.Skill.GetID("Vow_of_Silence"),
                GLOBAL_CACHE.Skill.GetID("Crippling_Victory"),
                GLOBAL_CACHE.Skill.GetID("Reap_Impurities"),
                GLOBAL_CACHE.Skill.GetID("Vow_of_Piety"),
                GLOBAL_CACHE.Skill.GetID("I_Am_Unstoppable"),
            ],
        )

        self.auto_combat_handler: BuildMgr = AutoCombat()
        # assign extra skill attributes from the already populated self.skills
        self.signet_of_mystic_speed = self.skills[0]
        self.pious_fury = self.skills[1]
        self.grenths_aura = self.skills[2]
        self.vow_of_silence = self.skills[3]
        self.crippling_victory = self.skills[4]
        self.reap_impurities = self.skills[5]
        self.vow_of_piety = self.skills[6]
        self.i_am_unstoppable = self.skills[7]

        self.crippling_victory_slot = 5
        self.reap_impurities_slot = 6

        # Build usage status
        self.status = DervBuildFarmStatus.Wait
        self.attacking = False

    def swap_to_scythe(self):
        if GLOBAL_CACHE.Agent.GetWeaponType(Player.GetAgentID())[0] != Weapon.Scythe:
            Keystroke.PressAndRelease(Key.F1.value)
            yield

    def swap_to_shield_set(self):
        if GLOBAL_CACHE.Agent.GetWeaponType(Player.GetAgentID())[0] == Weapon.Scythe:
            Keystroke.PressAndRelease(Key.F2.value)
            yield from Routines.Yield.wait(750)

    def has_enough_adrenaline(self, skill_slot):
        skill_id = GLOBAL_CACHE.SkillBar.GetSkillIDBySlot(skill_slot)

        return GLOBAL_CACHE.SkillBar.GetSkillData(skill_slot).adrenaline_a >= Skill.Data.GetAdrenaline(skill_id)

    def ProcessSkillCasting(self):
        if not (
            Routines.Checks.Map.IsExplorable()
            and Routines.Checks.Player.CanAct()
            and Routines.Checks.Map.IsExplorable()
            and Routines.Checks.Skills.CanCast()
        ):
            ActionQueueManager().ResetAllQueues()
            yield from Routines.Yield.wait(1000)
            return

        if (
            self.status == DervBuildFarmStatus.Loot
            or self.status == DervBuildFarmStatus.Setup
            or self.status == DervBuildFarmStatus.Wait
        ):
            yield from self.swap_to_shield_set()
            yield from Routines.Yield.wait(100)
            return

        player_agent_id = GLOBAL_CACHE.Player.GetAgentID()
        has_signet_of_mystic_speed = Routines.Checks.Effects.HasBuff(player_agent_id, self.signet_of_mystic_speed)
        has_grenths_aura = Routines.Checks.Effects.HasBuff(player_agent_id, self.grenths_aura)
        has_vow_of_silence = Routines.Checks.Effects.HasBuff(player_agent_id, self.vow_of_silence)
        has_vow_of_piety = Routines.Checks.Effects.HasBuff(player_agent_id, self.vow_of_piety)

        if self.status == DervBuildFarmStatus.Prepare:
            if (yield from Routines.Yield.Skills.IsSkillIDUsable(self.vow_of_piety)) and not has_vow_of_piety:
                yield from Routines.Yield.Skills.CastSkillID(self.vow_of_piety, aftercast_delay=750)
                return

            if (yield from Routines.Yield.Skills.IsSkillIDUsable(self.grenths_aura)) and not has_grenths_aura:
                yield from Routines.Yield.Skills.CastSkillID(self.grenths_aura, aftercast_delay=100)
                return

            if (
                (yield from Routines.Yield.Skills.IsSkillIDUsable(self.vow_of_silence))
                and has_grenths_aura
                and has_vow_of_piety
            ):
                yield from Routines.Yield.Skills.CastSkillID(self.vow_of_silence, aftercast_delay=100)
                return

        if self.status == DervBuildFarmStatus.Kill:
            if (
                (yield from Routines.Yield.Skills.IsSkillIDUsable(self.signet_of_mystic_speed))
                and has_vow_of_silence
                and not has_signet_of_mystic_speed
            ):
                yield from Routines.Yield.Skills.CastSkillID(self.signet_of_mystic_speed, aftercast_delay=250)
                return

            if (yield from Routines.Yield.Skills.IsSkillIDUsable(self.i_am_unstoppable)):
                yield from Routines.Yield.Skills.CastSkillID(self.i_am_unstoppable, aftercast_delay=100)
                return

            if (
                yield from Routines.Yield.Skills.IsSkillIDUsable(self.grenths_aura)
                and Routines.Yield.Skills.IsSkillIDUsable(self.vow_of_silence)
            ) and has_signet_of_mystic_speed:
                yield from Routines.Yield.Skills.CastSkillID(self.pious_fury, aftercast_delay=50)
                yield from Routines.Yield.Skills.CastSkillID(self.grenths_aura, aftercast_delay=50)
                yield from Routines.Yield.Skills.CastSkillID(self.vow_of_silence, aftercast_delay=50)
                return

            nearest_enemy = Routines.Agents.GetNearestEnemy(Range.Nearby.value)
            vos_buff_time_remaining = (
                GLOBAL_CACHE.Effects.GetEffectTimeRemaining(GLOBAL_CACHE.Player.GetAgentID(), self.vow_of_silence)
                if has_vow_of_silence
                else 0
            )
            if nearest_enemy and vos_buff_time_remaining > 2000:
                yield from self.swap_to_scythe()
                GLOBAL_CACHE.Player.Interact(nearest_enemy, False)
                if self.has_enough_adrenaline(self.crippling_victory_slot):
                    yield from Routines.Yield.Skills.CastSkillID(self.crippling_victory, aftercast_delay=100)
                    return

                if self.has_enough_adrenaline(self.reap_impurities_slot):
                    yield from Routines.Yield.Skills.CastSkillID(self.reap_impurities, aftercast_delay=100)
                    return


# =================== BUILD END ========================
