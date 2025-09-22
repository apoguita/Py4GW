from Py4GWCoreLib import GLOBAL_CACHE
from Py4GWCoreLib import ActionQueueManager
from Py4GWCoreLib import BuildMgr
from Py4GWCoreLib import Key
from Py4GWCoreLib import Keystroke
from Py4GWCoreLib import Player
from Py4GWCoreLib import Profession
from Py4GWCoreLib import Range
from Py4GWCoreLib import Routines
from Py4GWCoreLib import Weapon
from Py4GWCoreLib.Builds.AutoCombat import AutoCombat


# =================== BUILD ========================
class DervBuildFarmStatus:
    Setup = 'setup'
    Prepare = 'prepare'
    Kill = 'kill'
    Loot = 'loot'


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
        self.criplling_victory = self.skills[4]
        self.reap_impurities = self.skills[5]
        self.vow_of_piety = self.skills[6]
        self.i_am_unstoppable = self.skills[7]

        # Build usage status
        self.status = DervBuildFarmStatus.Setup
        self.spiked = False
        self.spiking = False

    def swap_to_scythe(self):
        if GLOBAL_CACHE.Agent.GetWeaponType(Player.GetAgentID())[0] != Weapon.Scythe:
            Keystroke.PressAndRelease(Key.F1.value)
            yield

    def swap_to_shield_set(self):
        if GLOBAL_CACHE.Agent.GetWeaponType(Player.GetAgentID())[0] == Weapon.Scythe:
            Keystroke.PressAndRelease(Key.F2.value)
            yield from Routines.Yield.wait(750)

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

        if self.status == DervBuildFarmStatus.Loot or self.status == DervBuildFarmStatus.Setup:
            yield from Routines.Yield.wait(100)
            return

        player_agent_id = GLOBAL_CACHE.Player.GetAgentID()
        has_signet_of_mystic_speed = Routines.Checks.Effects.HasBuff(player_agent_id, self.signet_of_mystic_speed)
        has_pious_fury = Routines.Checks.Effects.HasBuff(player_agent_id, self.pious_fury)
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
                yield from Routines.Yield.Skills.CastSkillID(self.grenths_aura, aftercast_delay=100)
                return

            if (yield from Routines.Yield.Skills.IsSkillIDUsable(self.signet_of_mystic_speed)) and has_vow_of_silence:
                yield from Routines.Yield.Skills.CastSkillID(self.signet_of_mystic_speed, aftercast_delay=750)
                return

        if self.status == DervBuildFarmStatus.Kill:
            yield from self.swap_to_scythe()
            if (yield from Routines.Yield.Skills.IsSkillIDUsable(self.signet_of_mystic_speed)) and has_vow_of_silence:
                yield from Routines.Yield.Skills.CastSkillID(self.signet_of_mystic_speed, aftercast_delay=750)
                return

            if ((yield from Routines.Yield.Skills.IsSkillIDUsable(self.i_am_unstoppable))):
                yield from Routines.Yield.Skills.CastSkillID(self.i_am_unstoppable, aftercast_delay=100)
                return

            if (yield from Routines.Yield.Skills.IsSkillIDUsable(self.pious_fury)) and has_signet_of_mystic_speed:
                yield from Routines.Yield.Skills.CastSkillID(self.pious_fury, aftercast_delay=100)
                return

            if (
                (yield from Routines.Yield.Skills.IsSkillIDUsable(self.grenths_aura))
                and not has_grenths_aura
                and has_signet_of_mystic_speed
            ):
                yield from Routines.Yield.Skills.CastSkillID(self.grenths_aura, aftercast_delay=100)
                return

            if (
                (yield from Routines.Yield.Skills.IsSkillIDUsable(self.vow_of_silence))
                and has_grenths_aura
                and has_signet_of_mystic_speed
            ):
                yield from Routines.Yield.Skills.CastSkillID(self.grenths_aura, aftercast_delay=100)
                return

            nearest_enemy = Routines.Agents.GetNearestEnemy(Range.Nearby.value)
            if (
                has_pious_fury
                and has_grenths_aura
                and has_signet_of_mystic_speed
                and has_vow_of_silence
                and nearest_enemy
            ):
                GLOBAL_CACHE.Player.Interact(nearest_enemy, False)
                if (yield from Routines.Yield.Skills.IsSkillIDUsable(self.criplling_victory)):
                    yield from Routines.Yield.Skills.CastSkillID(self.criplling_victory, aftercast_delay=100)
                    return

                if (yield from Routines.Yield.Skills.IsSkillIDUsable(self.reap_impurities)):
                    yield from Routines.Yield.Skills.CastSkillID(self.reap_impurities, aftercast_delay=100)
                    return


# =================== BUILD END ========================
