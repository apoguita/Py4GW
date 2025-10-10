from Py4GWCoreLib import GLOBAL_CACHE
from Py4GWCoreLib import Routines
from Py4GWCoreLib import BuildMgr
from Py4GWCoreLib.Builds import AutoCombat

from Py4GWCoreLib import ActionQueueManager
from Py4GWCoreLib import Keystroke
from Py4GWCoreLib import Key

from Py4GWCoreLib import Range
from Py4GWCoreLib import ThrottledTimer
from Py4GWCoreLib import Profession
from Py4GWCoreLib import Agent


DUNGEON_MODEL_IDS = {
    6493: "Stone Summit Dominator",  # 6
    6495: "Stone Summit Contaminator",  # 4
    6496: "Stone Summit Blasphemer",
    6497: "Stone Summit Warder",  # 5
    6498: "Stone Summit Priest",  # 3
    6499: "Stone Summit Defender",  # 1
    6500: "Stone Summit Cleaver",
    6502: "Stone Summit Pounder",
    6503: "Stone Summit Demolisher",
    6504: "Stone Summit Marksman",
    6505: "Stone Summit Distracter",
    6506: "Stone Summit Zealot",
    6507: "Stone Summit Summoner",  # 6
    6512: "Modniir Priest",  # 2
    6514: "Modniir Berserker",
    6515: "Modniir Hunter",
    6798: "Wretched Wolf",
}


class BuildStatus:
    Kill = 'kill'
    Wait = 'wait'


class AssassinShadowTheftDaggerSpammer(BuildMgr):
    def __init__(self):
        super().__init__(
            name="Assassin Shadow Theft Dagger Spammer",
            required_primary=Profession.Assassin,
            required_secondary=Profession.Warrior,  # change if needed
            template_code="OwFjUNd8ITPPOMMMHMvl0k6Pk1A",
            skills=[
                GLOBAL_CACHE.Skill.GetID("Exhausting_Assault"),
                GLOBAL_CACHE.Skill.GetID("Jagged_Strike"),
                GLOBAL_CACHE.Skill.GetID("Fox_Fangs"),
                GLOBAL_CACHE.Skill.GetID("Death_Blossom"),
                GLOBAL_CACHE.Skill.GetID("Asuran_Scan"),
                GLOBAL_CACHE.Skill.GetID("I_Am_Unstoppable"),
                GLOBAL_CACHE.Skill.GetID("Critical_Eye"),
                GLOBAL_CACHE.Skill.GetID("Shadow_Theft"),
            ],
        )
        self.auto_combat_handler = AutoCombat()

        # === Skill References ===
        (
            self.exhausting_assault,
            self.jagged_strike,
            self.fox_fangs,
            self.death_blossom,
            self.asuran_scan,
            self.i_am_unstoppable,
            self.critical_eye,
            self.shadow_theft,
        ) = self.skills

        self.blind = GLOBAL_CACHE.Skill.GetID("Blind")

        self.status = BuildStatus.Wait
        self.priority_target = None

        self.last_asuran_scan_target = None
        self.last_asuran_scan_time = 0
        self.asuran_scan_throttle = ThrottledTimer(10000)  # 10 seconds
        self.last_asuran_scan_target_id = None  # Track which target we last cast on

    def call_a_priority_target(self, range_limit=Range.Spellcast.value):
        """
        Scans nearby enemies and locks onto the nearest valid target within range_limit.
        Returns True if a target was successfully locked, else False.
        """
        player_x, player_y = GLOBAL_CACHE.Player.GetXY()
        enemies_left = Routines.Agents.GetFilteredEnemyArray(player_x, player_y, range_limit)
        if enemies_left:
            yield from Routines.Yield.Keybinds.TargetNearestEnemy()
            target_id = GLOBAL_CACHE.Player.GetTargetID()
            yield from Routines.Yield.Keybinds.Interact()
            ActionQueueManager().AddAction("ACTION", Keystroke.PressAndReleaseCombo, [Key.Ctrl.value, Key.Space.value])
            self.priority_target = target_id
            return
        else:
            if Routines.Checks.Agents.InDanger(Range.Spellcast):
                yield from Routines.Yield.Keybinds.TargetNearestEnemy()
                target_id = GLOBAL_CACHE.Player.GetTargetID()
                yield from Routines.Yield.Keybinds.Interact()
                ActionQueueManager().AddAction(
                    "ACTION", Keystroke.PressAndReleaseCombo, [Key.Ctrl.value, Key.Space.value]
                )
                self.priority_target = target_id
                return
            self.priority_target = None
        return

    def update_priority_target_if_needed(self):
        """
        Checks if the current target is still valid; if dead or out of range, reacquire one.
        """
        if not self.priority_target:
            yield from self.call_a_priority_target()
            return

        yield from Routines.Yield.Keybinds.TargetPriorityTarget()
        target_id = GLOBAL_CACHE.Player.GetTargetID()
        if target_id != self.priority_target:
            self.priority_target = None
            yield from self.call_a_priority_target()
            return

        agent = GLOBAL_CACHE.Agent.GetAgentByID(self.priority_target)
        if not agent or GLOBAL_CACHE.Agent.IsDead(self.priority_target):
            self.priority_target = None
            yield from self.call_a_priority_target()
            return

    def find_shadow_theft_target(self):
        """
        Specifically for Shadow Theft — find a new target within half Earshot range,
        prioritizing enemies based on model ID importance, then proximity.
        """

        # === Define target priority ranking (lower number = higher priority) ===
        priority_order = {
            6499: 1,  # Stone Summit Defender
            6512: 2,  # Modniir Priest
            6498: 3,  # Stone Summit Priest
            6495: 4,  # Stone Summit Contaminator
            6497: 5,  # Stone Summit Warder
            6507: 6,  # Stone Summit Summoner
            6493: 7,  # Stone Summit Dominator
        }

        player_x, player_y = GLOBAL_CACHE.Player.GetXY()
        enemy_agent_ids = Routines.Agents.GetFilteredEnemyArray(player_x, player_y, Range.Earshot.value * 0.5)

        best_agent_id = None
        best_priority = float("inf")
        best_dist_sq = float("inf")

        for agent_id in enemy_agent_ids:
            agent = GLOBAL_CACHE.Agent.GetAgentByID(agent_id)
            model_id = GLOBAL_CACHE.Agent.GetModelID(agent.id)
            dx, dy = agent.x - player_x, agent.y - player_y
            dist_sq = dx * dx + dy * dy

            # Determine priority rank (default = 999 if not special)
            rank = priority_order.get(model_id, 999)

            # Prefer higher-priority targets, then nearer distance as tiebreaker
            if rank < best_priority or (rank == best_priority and dist_sq < best_dist_sq):
                best_priority = rank
                best_dist_sq = dist_sq
                best_agent_id = agent_id

        # === Lock and engage the chosen target ===
        if best_agent_id:
            self.priority_target = best_agent_id
            GLOBAL_CACHE.Player.ChangeTarget(best_agent_id)
            GLOBAL_CACHE.Player.Interact(best_agent_id, True)
            ActionQueueManager().AddAction("ACTION", Keystroke.PressAndReleaseCombo, [Key.Ctrl.value, Key.Space.value])
            yield from Routines.Yield.Keybinds.TargetPriorityTarget()
            return
        else:
            yield from Routines.Yield.Keybinds.TargetNearestEnemy()
            target_id = GLOBAL_CACHE.Player.GetTargetID()
            yield from Routines.Yield.Keybinds.Interact()
            ActionQueueManager().AddAction("ACTION", Keystroke.PressAndReleaseCombo, [Key.Ctrl.value, Key.Space.value])
            self.priority_target = target_id
            return

    def ProcessSkillCasting(self):
        if not (
            Routines.Checks.Map.IsExplorable()
            and Routines.Checks.Player.CanAct()
            and Routines.Checks.Map.IsExplorable()
            and Routines.Checks.Skills.CanCast()
        ):
            ActionQueueManager().ResetAllQueues()
            yield from Routines.Yield.wait(25)
            return

        if self.status == BuildStatus.Wait:
            yield from Routines.Yield.wait(100)
            self.priority_target = None
            return

        player_agent_id = GLOBAL_CACHE.Player.GetAgentID()
        has_critical_eye = Routines.Checks.Effects.HasBuff(player_agent_id, self.critical_eye)
        has_i_am_unstoppable = Routines.Checks.Effects.HasBuff(player_agent_id, self.i_am_unstoppable)
        has_shadow_theft = Routines.Checks.Effects.HasBuff(player_agent_id, self.shadow_theft)

        if self.status == BuildStatus.Kill:
            # Ensure we have a valid target locked
            yield from self.update_priority_target_if_needed()

            if not self.priority_target:
                # Couldn’t find any enemies nearby, wait and retry
                yield from Routines.Yield.wait(25)
                return

            yield from Routines.Yield.Keybinds.TargetPriorityTarget()
            nearest_enemy_agent_id = GLOBAL_CACHE.Player.GetTargetID()
            nearest_enemy_agent = Agent.GetAgentByID(nearest_enemy_agent_id)
            player_x, player_y = GLOBAL_CACHE.Player.GetXY()
            enemy_x, enemy_y = nearest_enemy_agent.x, nearest_enemy_agent.y

            # --- Compute squared distance between player and enemy ---
            dx = enemy_x - player_x
            dy = enemy_y - player_y
            dist_sq = dx * dx + dy * dy

            yield from Routines.Yield.Keybinds.Interact()

            # === Handle Asuran Scan with per-target throttle + hex check ===
            if (yield from Routines.Yield.Skills.IsSkillIDUsable(self.asuran_scan)) and nearest_enemy_agent_id:
                if (
                    self.asuran_scan_throttle.IsExpired()
                    or not GLOBAL_CACHE.Agent.IsHexed(nearest_enemy_agent_id)
                    or self.last_asuran_scan_target_id != nearest_enemy_agent_id
                ):
                    asura_scan_slot = GLOBAL_CACHE.SkillBar.GetSlotBySkillID(self.asuran_scan)
                    yield from Routines.Yield.Keybinds.UseSkill(asura_scan_slot)
                    yield from Routines.Yield.wait(250)

                    # Reset throttle after casting
                    self.asuran_scan_throttle.Reset()
                    self.last_asuran_scan_target_id = nearest_enemy_agent_id

            if (
                nearest_enemy_agent_id
                and (yield from Routines.Yield.Skills.IsSkillIDUsable(self.shadow_theft))
                and not has_shadow_theft
                or (yield from Routines.Yield.Skills.IsSkillIDUsable(self.shadow_theft))
                and dist_sq <= Range.Area.value**2
            ):
                # Acquire new target specifically for Shadow Theft
                yield from self.find_shadow_theft_target()

                if self.priority_target:
                    nearest_enemy_agent_id = self.priority_target
                    nearest_enemy_agent = Agent.GetAgentByID(nearest_enemy_agent_id)

                    if nearest_enemy_agent and nearest_enemy_agent.is_living and nearest_enemy_agent.living_agent:
                        shadow_theft_slot = GLOBAL_CACHE.SkillBar.GetSlotBySkillID(self.shadow_theft)
                        yield from Routines.Yield.Keybinds.UseSkill(shadow_theft_slot)
                        yield from Routines.Yield.wait(350)

            if (yield from Routines.Yield.Skills.IsSkillIDUsable(self.critical_eye)) and not has_critical_eye:
                critical_eye_slot = GLOBAL_CACHE.SkillBar.GetSlotBySkillID(self.critical_eye)
                yield from Routines.Yield.Keybinds.UseSkill(critical_eye_slot)

            if (yield from Routines.Yield.Skills.IsSkillIDUsable(self.i_am_unstoppable)) and not has_i_am_unstoppable:
                i_am_unstoppable_slot = GLOBAL_CACHE.SkillBar.GetSlotBySkillID(self.i_am_unstoppable)
                yield from Routines.Yield.Keybinds.UseSkill(i_am_unstoppable_slot)

            # --- Only proceed if within adjacent range ---
            if dist_sq <= Range.Adjacent.value**2:
                player_current_energy = GLOBAL_CACHE.Agent.GetEnergy(player_agent_id) * GLOBAL_CACHE.Agent.GetMaxEnergy(
                    player_agent_id
                )
                if (
                    yield from Routines.Yield.Skills.IsSkillIDUsable(self.exhausting_assault)
                ) and player_current_energy >= 10:
                    nearest_enemy_agent = GLOBAL_CACHE.Agent.GetAgentByID(nearest_enemy_agent_id)
                    if not nearest_enemy_agent:
                        return  # no valid target

                    MAX_RANGE_SQ = Range.Adjacent.value**2

                    # --- Wait for Jagged Strike to become usable ---
                    while not (yield from Routines.Yield.Skills.IsSkillIDUsable(self.jagged_strike)):
                        yield from Routines.Yield.wait(50)

                    # --- Confirm target is still in range before chaining ---
                    player_x, player_y = GLOBAL_CACHE.Player.GetXY()
                    dx, dy = nearest_enemy_agent.x - player_x, nearest_enemy_agent.y - player_y
                    if dx * dx + dy * dy > MAX_RANGE_SQ:
                        yield from Routines.Yield.Keybinds.Interact()
                        return

                    # --- Queue chain execution ---
                    jagged_slot = GLOBAL_CACHE.SkillBar.GetSlotBySkillID(self.jagged_strike)
                    exhausting_slot = GLOBAL_CACHE.SkillBar.GetSlotBySkillID(self.exhausting_assault)

                    # Interact and prepare to cast
                    yield from Routines.Yield.Keybinds.Interact()

                    # --- Cast Jagged Strike first ---
                    yield from Routines.Yield.Keybinds.TargetPriorityTarget()
                    yield from Routines.Yield.Keybinds.UseSkill(jagged_slot)
                    yield from Routines.Yield.wait(200)

                    # --- Cast Exhausting Assault right after ---
                    if (yield from Routines.Yield.Skills.IsSkillIDUsable(self.exhausting_assault)):
                        if GLOBAL_CACHE.Agent.IsDead(nearest_enemy_agent_id):
                            return
                        yield from Routines.Yield.Keybinds.UseSkill(exhausting_slot)
                        yield from Routines.Yield.wait(250)

                if (
                    yield from Routines.Yield.Skills.IsSkillIDUsable(self.death_blossom)
                ) and player_current_energy >= 12:
                    jagged = self.jagged_strike
                    fox_fangs = self.fox_fangs
                    death_blossom = self.death_blossom

                    # === Check distance first ===
                    player_x, player_y = GLOBAL_CACHE.Player.GetXY()
                    target_x, target_y = GLOBAL_CACHE.Agent.GetXY(nearest_enemy_agent_id)
                    dist_sq = (player_x - target_x) ** 2 + (player_y - target_y) ** 2
                    if dist_sq > Range.Adjacent.value**2:
                        yield from Routines.Yield.Keybinds.Interact()
                        return  # Too far, skip chain

                    # === Execute chain sequence ===
                    yield from Routines.Yield.Keybinds.Interact()

                    # Jagged Strike
                    skill_slot = GLOBAL_CACHE.SkillBar.GetSlotBySkillID(jagged)
                    yield from Routines.Yield.Keybinds.TargetPriorityTarget()
                    yield from Routines.Yield.Keybinds.UseSkill(skill_slot)
                    yield from Routines.Yield.wait(200)  # small follow-up delay

                    # Fox Fangs
                    if (yield from Routines.Yield.Skills.IsSkillIDUsable(fox_fangs)):
                        if GLOBAL_CACHE.Agent.IsDead(nearest_enemy_agent_id):
                            return

                        skill_slot = GLOBAL_CACHE.SkillBar.GetSlotBySkillID(fox_fangs)
                        yield from Routines.Yield.Keybinds.UseSkill(skill_slot)
                        yield from Routines.Yield.wait(200)  # roughly same cast rhythm

                        # Death Blossom
                        if (yield from Routines.Yield.Skills.IsSkillIDUsable(death_blossom)):
                            if GLOBAL_CACHE.Agent.IsDead(nearest_enemy_agent_id):
                                return

                            skill_slot = GLOBAL_CACHE.SkillBar.GetSlotBySkillID(death_blossom)
                            yield from Routines.Yield.Keybinds.UseSkill(skill_slot)
                            yield from Routines.Yield.wait(250)  # DB has longer aftercast

                if (yield from Routines.Yield.Skills.IsSkillIDUsable(self.fox_fangs)) and player_current_energy >= 10:
                    jagged = self.jagged_strike
                    fox_fangs = self.fox_fangs

                    # === Check distance first ===
                    player_x, player_y = GLOBAL_CACHE.Player.GetXY()
                    target_x, target_y = GLOBAL_CACHE.Agent.GetXY(nearest_enemy_agent_id)
                    dist_sq = (player_x - target_x) ** 2 + (player_y - target_y) ** 2
                    if dist_sq > Range.Adjacent.value**2:
                        yield from Routines.Yield.Keybinds.Interact()
                        return  # Too far, skip chain

                    # === Execute chain sequence ===
                    yield from Routines.Yield.Keybinds.Interact()

                    # Jagged Strike
                    skill_slot = GLOBAL_CACHE.SkillBar.GetSlotBySkillID(jagged)
                    yield from Routines.Yield.Keybinds.TargetPriorityTarget()
                    yield from Routines.Yield.Keybinds.UseSkill(skill_slot)
                    yield from Routines.Yield.wait(200)  # small follow-up delay

                    # Fox Fangs
                    if (yield from Routines.Yield.Skills.IsSkillIDUsable(fox_fangs)):
                        if GLOBAL_CACHE.Agent.IsDead(nearest_enemy_agent_id):
                            return

                        skill_slot = GLOBAL_CACHE.SkillBar.GetSlotBySkillID(fox_fangs)
                        yield from Routines.Yield.Keybinds.UseSkill(skill_slot)
                        yield from Routines.Yield.wait(200)  # roughly same cast rhythm
            return
