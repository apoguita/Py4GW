import math
from Py4GWCoreLib import ConsoleLog, Console, Overlay, Agent,Player, GLOBAL_CACHE, Profession, Routines, DXOverlay
from OutpostRunner.Build_Manager_Addon import CheckCrippleKDanger, CheckSpellcasterDanger, BodyBlockDetection
dx = DXOverlay()
ShowDXoverlay = False
FREESTYLE_MODE = False
FREESTYLE_COROUTINE = None
class Build:
    def __init__(
        self,
        name: str = "Generic Build",
        required_primary: Profession = Profession(0),
        required_secondary: Profession = Profession(0),
        template_code: str = "AAAAAAAAAAAAAAAA",
        skills: list[int] = []
    ):
        self.build_name = name
        self.required_primary: Profession = required_primary
        self.required_secondary: Profession = required_secondary
        self.template_code = template_code
        self.skills = skills

    def ValidatePrimary(self, profession: Profession) -> bool:
        return self.required_primary == profession

    def ValidateSecondary(self, profession: Profession) -> bool:
        return self.required_secondary == profession

    def ValidateSkills(self):
        skills: list[int] = []
        for i in range(8):
            skill = GLOBAL_CACHE.SkillBar.GetSkillIDBySlot(i + 1)
            if skill:
                skills.append(skill)

        all_valid = sorted(self.skills) == sorted(skills)
        yield from Routines.Yield.wait(0 if all_valid else 1000)
        return all_valid

    def EquipBuild(self):
        yield from Routines.Yield.Skills.LoadSkillbar(self.template_code, log=False)

    def LoadSkillBar(self):
        yield from Routines.Yield.Skills.LoadSkillbar(self.template_code, log=False)

    def ProcessSkillCasting2(self):
        raise NotImplementedError
    
    def ValidateBuild(self):
        """
        Validates profession + skillbar for this build.
        Returns (success: bool, error_msg: str)
        """
        return True, ""
    def refresh_current_skills(self):
        """Re-read the current skillbar and update the build_obj.skills"""
        skills = []
        for i in range(8):
            sid = GLOBAL_CACHE.SkillBar.GetSkillIDBySlot(i + 1)
            if sid:
                skills.append(sid)
        self.skills = skills
        ConsoleLog("Build_Manager", f"Refreshed build skills → {skills}", Console.MessageType.Info)

class OutpostRunnerDA(Build):
    def __init__(self):
        super().__init__(
            name="D/A Outpost Runner",
            required_primary=Profession.Dervish,
            required_secondary=Profession.Assassin,
            template_code="Ogej4NfMLTjbHY3l0k6M4OHQ8IA"
        )

        self.debug_logs = True

        # Skill IDs
        self.zealous_renewal = GLOBAL_CACHE.Skill.GetID("Zealous_Renewal")
        self.pious_haste = GLOBAL_CACHE.Skill.GetID("Pious_Haste")
        self.dwarven_stability = GLOBAL_CACHE.Skill.GetID("Dwarven_Stability")
        self.i_am_unstoppable = GLOBAL_CACHE.Skill.GetID("I_Am_Unstoppable")
        self.shadow_form = GLOBAL_CACHE.Skill.GetID("Shadow_Form")
        self.deaths_charge = GLOBAL_CACHE.Skill.GetID("Deaths_Charge")
        self.shroud_of_distress = GLOBAL_CACHE.Skill.GetID("Shroud_of_Distress")
        self.deadly_paradox = GLOBAL_CACHE.Skill.GetID("Deadly_Paradox")

        self.skills = [
            self.deadly_paradox,
            self.shadow_form,
            self.deaths_charge,
            self.shroud_of_distress,
            self.i_am_unstoppable,
            self.pious_haste,
            self.dwarven_stability,
            self.zealous_renewal
        ]


    def DeathsChargeToBestEnemie(self, fsm_helpers):
        def angle_between_player_and_enemy(facing_vec, enemy_vec):
            """
            Returns absolute angle (0..180°) between player's facing vector
            and the vector from player -> enemy.
            """
            fx, fy = facing_vec
            ex, ey = enemy_vec
            dot = fx * ex + fy * ey            
            det = fx * ey - fy * ex            
            angle_rad = math.atan2(det, dot)
            angle_deg = abs(math.degrees(angle_rad))

            return angle_deg
        SPELLCAST_RANGE = 1248.0
        px, py = Player.GetXY()
        pz = Overlay().FindZ(px, py)
        heading = Agent.GetRotationAngle(Player.GetAgentID())
        facing_vec = (math.cos(heading), math.sin(heading))

        enemy_array = Routines.Agents.GetFilteredEnemyArray(px, py, max_distance=SPELLCAST_RANGE)

        best_15deg = None
        best_15deg_dist = -1
        best_30deg = None
        best_30deg_dist = -1

        for enemy in enemy_array:
            if Agent.IsDead(enemy):
                continue

            ex, ey = Agent.GetXY(enemy)
            enemy_vec = (ex - px, ey - py)
            dist = math.hypot(enemy_vec[0], enemy_vec[1])
            angle = angle_between_player_and_enemy(facing_vec, enemy_vec)

            if angle <= 15.0:
                if dist > best_15deg_dist:
                    best_15deg_dist = dist
                    best_15deg = enemy
            elif angle <= 60.0:
                if dist > best_30deg_dist:
                    best_30deg_dist = dist
                    best_30deg = enemy

        best_target = best_15deg if best_15deg else best_30deg

        if not best_target:
            ConsoleLog("Teleport", "No valid target in 15° or 30° cone → skip", Console.MessageType.Debug)
            return

        ex, ey = Agent.GetXY(best_target)
        ez = Overlay().FindZ(ex, ey)
        target_dist = math.hypot(ex - px, ey - py)
        ConsoleLog(
            "Teleport",
            f"Chosen enemy at ({ex:.1f}, {ey:.1f}) | Cone: {'15°' if best_target == best_15deg else '30°'} | Distance={target_dist:.1f}",
            Console.MessageType.Debug
        )

        if ShowDXoverlay:
            overlay = Overlay()
            overlay.BeginDraw()
            overlay.DrawLine3D(px, py, pz, ex, ey, ez, 0xFFFFFF00, 3.0)  # thick yellow/white line
            overlay.EndDraw()

        yield from Routines.Yield.Agents.ChangeTarget(best_target)
        if (yield from Routines.Yield.Skills.CastSkillID(self.deaths_charge, aftercast_delay=1000)):
            yield from Routines.Yield.wait(1000)

    @staticmethod
    def CanUsePiousHaste(self):
        player_id = Player.GetAgentID()
        if Routines.Checks.Effects.HasBuff(player_id, self.pious_haste) or not Routines.Checks.Skills.IsSkillIDReady(self.pious_haste):
            return False

        #dont cast pious if we're about to cast shadow form
        if Routines.Checks.Effects.HasBuff(player_id, self.shadow_form) and GLOBAL_CACHE.Effects.GetEffectTimeRemaining(player_id, self.shadow_form) <= 3000:
            return False

        #castable if we already have zealous renewal
        if Routines.Checks.Effects.HasBuff(player_id, self.zealous_renewal):
            return True

        #cast if we have enough energy
        if Routines.Checks.Skills.IsSkillIDReady(self.zealous_renewal):
            max_energy = Agent.GetMaxEnergy(player_id)
            return Agent.GetEnergy(player_id) * max_energy > 10

        return False

    def ProcessSkillCasting(self, fsm_helpers):
        while True:
            if not Routines.Checks.Map.MapValid():
                yield from Routines.Yield.wait(1000)
                continue
            
            if Agent.IsDead(Player.GetAgentID()):
                yield from Routines.Yield.wait(1000)
                continue
            
            if not Routines.Checks.Skills.CanCast():
                yield from Routines.Yield.wait(100)
                continue
            
            player_id = Player.GetAgentID()
            # === BUFF STATE ===
            has_shadow_form = Routines.Checks.Effects.HasBuff(player_id, self.shadow_form)
            shadow_time = GLOBAL_CACHE.Effects.GetEffectTimeRemaining(player_id, self.shadow_form) if has_shadow_form else 0
            has_deadly_paradox = Routines.Checks.Effects.HasBuff(player_id, self.deadly_paradox)
            has_shroud = Routines.Checks.Effects.HasBuff(player_id, self.shroud_of_distress)
            has_dwarven = Routines.Checks.Effects.HasBuff(player_id, self.dwarven_stability)
            has_iau = Routines.Checks.Effects.HasBuff(player_id, self.i_am_unstoppable)
            hp = Agent.GetHealth(player_id)
            
            current_target = Player.GetTargetID()
            if current_target != player_id:
                Player.ChangeTarget(player_id)
                yield from Routines.Yield.wait(250)

            # === 1. SHADOW FORM + PARADOX MAINTENANCE ===

            if not has_shadow_form and shadow_time <= 3500:
                if CheckSpellcasterDanger(custom_distance=2000):
                    # Force combo in one go
                    aftercast = 200
                    GLOBAL_CACHE._ActionQueueManager.ResetQueue("ACTION")
                    if (yield from Routines.Yield.Skills.CastSkillID(self.deadly_paradox, aftercast_delay=aftercast)):
                        yield from Routines.Yield.wait(aftercast)

                    # Immediately follow with Shadow Form
                    aftercast = 1950
                    GLOBAL_CACHE._ActionQueueManager.ResetQueue("ACTION")
                    if (yield from Routines.Yield.Skills.CastSkillID(self.shadow_form, aftercast_delay=aftercast)):
                        yield from Routines.Yield.wait(aftercast)
                        continue  


            # === 2. LOW-HP EMERGENCY SHROUD ===
            
            if hp < 0.60 and not has_shroud:
                aftercast = 1950 #SF cast 1000 + 750aftercast + assuming 200ms for something else
                GLOBAL_CACHE._ActionQueueManager.ResetQueue("ACTION")
                if (yield from Routines.Yield.Skills.CastSkillID(self.shroud_of_distress, aftercast_delay=aftercast)):
                    yield from Routines.Yield.wait(aftercast)
                    continue #nothing else to do this loop

            # === 4. MAINTAIN RUNNING STANCES ===
            if not has_dwarven and Routines.Checks.Skills.IsSkillIDReady(self.dwarven_stability):
                aftercast = 350 #1/4 sec + 100ms for something else
                if (yield from Routines.Yield.Skills.CastSkillID(self.dwarven_stability, aftercast_delay=aftercast)):
                    yield from Routines.Yield.wait(aftercast)
                    continue #nothing else to do this loop

            if self.CanUsePiousHaste(self):
                # Zealous Renewal → Pious Haste combo
                aftercast = 200 #it's instant but we need time
                if (yield from Routines.Yield.Skills.CastSkillID(self.zealous_renewal, aftercast_delay=aftercast)):
                    yield from Routines.Yield.wait(aftercast)
                # Immediately follow with Pious Haste
                aftercast = 200 #it's instant but we need time
                if (yield from Routines.Yield.Skills.CastSkillID(self.pious_haste, aftercast_delay=aftercast)):
                    yield from Routines.Yield.wait(aftercast)
                    continue

            # === 5. SMART ANTI CRIPPLE AND KD ===
            if not has_iau:
                player_id = Player.GetAgentID()
                player_pos = Player.GetXY()
                px, py = player_pos[0], player_pos[1]
                if Agent.IsCrippled(player_id) or CheckCrippleKDanger(px, py):
                    aftercast = 200
                    if (yield from Routines.Yield.Skills.CastSkillID(self.i_am_unstoppable, aftercast_delay=aftercast)):
                        yield from Routines.Yield.wait(aftercast)
                        continue

            # === 6. SMART ANTI Bodyblock ===
            if not FREESTYLE_MODE:  
                if BodyBlockDetection(seconds=1.0):
                    yield from self.DeathsChargeToBestEnemie(fsm_helpers)

            # === IDLE WAIT ===
            yield from Routines.Yield.wait(150)
