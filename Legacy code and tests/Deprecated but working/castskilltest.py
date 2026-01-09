import Py4GW
import math
from typing import Tuple
from Py4GWCoreLib import Profession
from Py4GWCoreLib import GLOBAL_CACHE
from Py4GWCoreLib import Routines
from Py4GWCoreLib import ConsoleLog
from Py4GWCoreLib import AgentArray
from Py4GWCoreLib import Agent
from Py4GWCoreLib import Range
from Py4GWCoreLib import Utils
from Py4GWCoreLib import *



class OutpostRunnerDA:
    def __init__(self):
        self.name = "Dervish/Assassin Outpost Runner"
        self.required_primary = Profession.Dervish
        self.required_secondary = Profession.Assassin
        self.template_code = "Ogej4NfMLTIQ0k6MHYjb3l4OHQA"

        # Store skill IDs and slots for quick access
        self.zealous_renewal     = GLOBAL_CACHE.Skill.GetID("Zealous_Renewal")
        self.pious_haste         = GLOBAL_CACHE.Skill.GetID("Pious_Haste")
        self.dwarven_stability   = GLOBAL_CACHE.Skill.GetID("Dwarven_Stability")
        self.i_am_unstoppable    = GLOBAL_CACHE.Skill.GetID("I_Am_Unstoppable")
        self.shadow_form         = GLOBAL_CACHE.Skill.GetID("Shadow_Form")
        self.heart_of_shadow     = GLOBAL_CACHE.Skill.GetID("Heart_of_Shadow")
        self.shroud_of_distress  = GLOBAL_CACHE.Skill.GetID("Shroud_of_Distress")
        self.deaths_charge       = GLOBAL_CACHE.Skill.GetID("Deaths_Charge")

        self.zealous_slot        = GLOBAL_CACHE.SkillBar.GetSlotBySkillID(self.zealous_renewal)
        self.pious_slot          = GLOBAL_CACHE.SkillBar.GetSlotBySkillID(self.pious_haste)
        self.dwarven_slot        = GLOBAL_CACHE.SkillBar.GetSlotBySkillID(self.dwarven_stability)
        self.iau_slot            = GLOBAL_CACHE.SkillBar.GetSlotBySkillID(self.i_am_unstoppable)
        self.shadow_form_slot    = GLOBAL_CACHE.SkillBar.GetSlotBySkillID(self.shadow_form)
        self.heart_slot          = GLOBAL_CACHE.SkillBar.GetSlotBySkillID(self.heart_of_shadow)
        self.shroud_slot         = GLOBAL_CACHE.SkillBar.GetSlotBySkillID(self.shroud_of_distress)
        self.deaths_charge_slot  = GLOBAL_CACHE.SkillBar.GetSlotBySkillID(self.deaths_charge)

    def ProcessSkillCasting(self):
        # Helper: compute cosine similarity between two vectors (for angle calculations)
        def vector_cos(v1, v2):
            dot = v1[0]*v2[0] + v1[1]*v2[1]
            mag1 = (v1[0]**2 + v1[1]**2) ** 0.5
            mag2 = (v2[0]**2 + v2[1]**2) ** 0.5
            if mag1 == 0 or mag2 == 0:
                return 1  # default if no direction
            return dot / (mag1 * mag2)

        while True:
            # Basic sanity checks: valid map, not loading, player alive, etc.
            if not Routines.Checks.Map.MapValid():
                yield from Routines.Yield.wait(1000)
                continue
            if Agent.IsDead(GLOBAL_CACHE.Player.GetAgentID()):
                yield from Routines.Yield.wait(1000)
                continue
            if not Routines.Checks.Skills.CanCast():
                # If player is casting, knocked down, etc., wait briefly
                yield from Routines.Yield.wait(100)
                continue

            player_id = GLOBAL_CACHE.Player.GetAgentID()
            player_pos = GLOBAL_CACHE.Player.GetXY()
            px, py = player_pos[0], player_pos[1]
            # Unit vector for player's facing direction (to evaluate front/back for targeting)
            facing_angle = Agent.GetRotationAngle(player_id)
            facing_vector = (math.cos(facing_angle), math.sin(facing_angle))

            # **1. Anti-Cripple:** Use "I Am Unstoppable!" immediately if crippled
            if Routines.Checks.Effects.HasBuff(player_id, self.i_am_unstoppable) is False:
                # Check if player has "Crippled" condition (implementation dependent)
                if  Agent.IsCrippled(player_id):
                    ConsoleLog(self.name, "Crippled! Using 'I Am Unstoppable!'", 
                               Py4GW.Console.MessageType.Info, log=False)
                    if Routines.Yield.Skills.CastSkillID(self.i_am_unstoppable, log=False, aftercast_delay=100):
                        yield from Routines.Yield.wait(100)
                        continue

            # **2. Preemptive Shadow Form:** Cast before hitting caster mobs (~1500 range)
            has_sf = Routines.Checks.Effects.HasBuff(player_id, self.shadow_form)
            if not has_sf and Routines.Checks.Skills.IsSkillSlotReady(self.shadow_form_slot):
                # Scan for any hostile spellcaster within ~1500 units
                enemies_near = Routines.Agents.GetFilteredEnemyArray(px, py, 1500.0)
                caster_found = False
                for eid in enemies_near:
                    if Agent.IsAlive(eid) and not Agent.IsMartial(eid):
                        # Found an enemy that is likely a caster (not a martial attacker)
                        caster_found = True
                        break
                if caster_found:
                    ConsoleLog(self.name, "Approaching casters: activating Shadow Form.", 
                               Py4GW.Console.MessageType.Info, log=False)
                    if Routines.Yield.Skills.CastSkillID(self.shadow_form, log=False, aftercast_delay=1750):
                        yield from Routines.Yield.wait(1750)
                        continue

            # **3. Emergency Defense:** Shroud of Distress if HP < 60% and not already active
            if Agent.GetHealth(player_id) < 0.60:
                has_shroud = Routines.Checks.Effects.HasBuff(player_id, self.shroud_of_distress)
                if not has_shroud and Routines.Checks.Skills.IsSkillSlotReady(self.shroud_slot):
                    ConsoleLog(self.name, "Health low! Casting Shroud of Distress.", 
                               Py4GW.Console.MessageType.Info, log=False)
                    if Routines.Yield.Skills.CastSkillID(self.shroud_of_distress, log=False, aftercast_delay=1750):
                        yield from Routines.Yield.wait(1750)
                        continue

            # **4. Maintain Stances:** Keep Pious Haste (speed) and Dwarven Stability up
            # Always cast Zealous Renewal immediately before Pious Haste for +50% IMS:contentReference[oaicite:9]{index=9}.
            has_pious   = Routines.Checks.Effects.HasBuff(player_id, self.pious_haste)
            has_dwarven = Routines.Checks.Effects.HasBuff(player_id, self.dwarven_stability)
            if not has_pious:
                ConsoleLog(self.name, "Maintaining speed: refreshing Pious Haste (with Zealous Renewal).", 
                           Py4GW.Console.MessageType.Info, log=False)
                # Cast Dwarven Stability first if it's down, to extend stance duration
                if not has_dwarven and Routines.Checks.Skills.IsSkillSlotReady(self.dwarven_slot):
                    Routines.Yield.Skills.CastSkillID(self.dwarven_stability, log=False, aftercast_delay=250)
                    yield from Routines.Yield.wait(250)
                # Cast Zealous Renewal right before Pious Haste for energy gain and 50% speed
                if Routines.Checks.Skills.IsSkillSlotReady(self.zealous_slot):
                    Routines.Yield.Skills.CastSkillID(self.zealous_renewal, log=False, aftercast_delay=250)
                    yield from Routines.Yield.wait(250)
                # Now activate Pious Haste (stance)
                if Routines.Yield.Skills.CastSkillID(self.pious_haste, log=False, aftercast_delay=1000):
                    ConsoleLog(self.name, "Activated Pious Haste (25%–50% speed buff).", 
                               Py4GW.Console.MessageType.Info, log=False)
                    yield from Routines.Yield.wait(1000)
                continue  # restart loop after updating speed buffs
            if not has_dwarven:
                # Dwarven Stability fell off (recast to maintain stance extension and KD immunity)
                if Routines.Yield.Skills.CastSkillID(self.dwarven_stability, log=False, aftercast_delay=250):
                    ConsoleLog(self.name, "Recasting Dwarven Stability (extending stances).", 
                               Py4GW.Console.MessageType.Info, log=False)
                    yield from Routines.Yield.wait(250)
                    continue

            # **5. Escape when Surrounded:** use Death's Charge on a front-most far enemy
            # Determine if we are “surrounded” – e.g. multiple foes very close by
            close_enemies = Routines.Agents.GetFilteredEnemyArray(px, py, 300.0)  # within ~300 units
            # Count alive hostiles in close proximity
            close_count = 0
            for eid in close_enemies:
                if Agent.IsAlive(eid) and GLOBAL_CACHE.Player.GetAgentID() != eid:
                    # Only count distinct living enemies
                    close_count += 1
                    if close_count >= 3:
                        break
            if close_count >= 3 and Routines.Checks.Skills.IsSkillSlotReady(self.deaths_charge_slot):
                # Find the furthest enemy *ahead* of player (in front hemisphere)
                target_enemy = None
                max_distance = 0.0
                enemies_in_area = Routines.Agents.GetFilteredEnemyArray(px, py, 1500.0)
                for eid in enemies_in_area:
                    if not Agent.IsAlive(eid):
                        continue
                    ex, ey = Agent.GetXY(eid)
                    to_enemy_vec = (ex - px, ey - py)
                    # Check if enemy is generally in front (cosine > 0 means < 90° ahead)
                    if vector_cos(facing_vector, to_enemy_vec) > 0:
                        dist = Utils.Distance(player_pos, (ex, ey))
                        if dist > max_distance:
                            max_distance = dist
                            target_enemy = eid
                if target_enemy:
                    GLOBAL_CACHE._ActionQueueManager.ResetQueue("ACTION")  # stop other actions
                    yield from Routines.Yield.Agents.ChangeTarget(target_enemy)
                    ConsoleLog(self.name, "Surrounded! Shadow stepping to furthest front enemy (Death's Charge).", 
                               Py4GW.Console.MessageType.Info, log=False)
                    if Routines.Yield.Skills.CastSkillID(self.deaths_charge, log=False, aftercast_delay=1000):
                        yield from Routines.Yield.wait(1000)
                        # After teleporting, drop target to avoid fighting
                        GLOBAL_CACHE.Player.ChangeTarget(0)
                        continue

            # **6. Shadow Step for Distance (Heart of Shadow):** use on rear enemy for forward escape
            if Routines.Checks.Skills.IsSkillSlotReady(self.heart_slot):
                # Find an enemy directly behind the player to maximize forward teleport
                target_enemy = None
                most_behind_val = 1.0  # looking for lowest cosine (most behind, approaching -1)
                enemies_around = Routines.Agents.GetFilteredEnemyArray(px, py, 1000.0)
                for eid in enemies_around:
                    if not Agent.IsAlive(eid):
                        continue
                    ex, ey = Agent.GetXY(eid)
                    to_enemy_vec = (ex - px, ey - py)
                    cos_angle = vector_cos(facing_vector, to_enemy_vec)
                    if cos_angle < most_behind_val:
                        most_behind_val = cos_angle
                        target_enemy = eid
                if target_enemy:
                    GLOBAL_CACHE._ActionQueueManager.ResetQueue("ACTION")
                    yield from Routines.Yield.Agents.ChangeTarget(target_enemy)
                    ConsoleLog(self.name, "Using Heart of Shadow on rear target to leap forward.", 
                               Py4GW.Console.MessageType.Info, log=False)
                    if Routines.Yield.Skills.CastSkillID(self.heart_of_shadow, log=False, aftercast_delay=500):
                        yield from Routines.Yield.wait(500)
                        GLOBAL_CACHE.Player.ChangeTarget(0)
                        # (Heart of Shadow heals as well, providing sustain during the run)
                        continue
                

            # Short idle wait before next loop iteration
            yield from Routines.Yield.wait(100)
