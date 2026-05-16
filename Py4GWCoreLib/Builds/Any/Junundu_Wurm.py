"""
Junundu Wurm combat build for HeroAI.

Matched when the player's skill bar contains the three core Junundu skill IDs.
Handles the full skill rotation inside a Junundu Wurm (The Sulfurous Wastes).

Skill layout (slots 1–7; slot 8 = Leave Junundu is blocked externally):
  Slot 1 – Junundu Strike  (1439) – basic melee attack
  Slot 2 – Junundu Smash   (1440) – PBAoE melee
  Slot 3 – Junundu Bite    (1862) – melee AoE on target
  Slot 4 – Junundu Siege   (1441) – long-range AoE spike
  Slot 5 – Junundu Tunnel  (1442) – speed boost (self)
  Slot 6 – Junundu Feast   (1438) – self heal + condition removal (unused)
  Slot 7 – Junundu Wail    (1865) – PBAoE blind + armor buff
"""
import Py4GW
from Py4GWCoreLib import Agent, AgentArray, BuildMgr, GLOBAL_CACHE, Player, Profession, Routines, ThrottledTimer
from Py4GWCoreLib.enums_src.GameData_enums import Range

_LOG = "JununduWurm"
_combat_log_timer = ThrottledTimer(2000)

_STRIKE_ID = 1439
_SMASH_ID  = 1440
_BITE_ID   = 1862
_SIEGE_ID  = 1441
_TUNNEL_ID = 1442
_FEAST_ID  = 1438
_WAIL_ID   = 1865
_LEAVE_ID  = 1443  # Leave Junundu — only present on slot 8 when inside a wurm

_NEARBY_SQ  = Range.Nearby.value  ** 2
_EARSHOT_SQ = Range.Earshot.value ** 2


def _siege_target(player_id: int) -> int:
    """Return an earshot enemy that is outside Nearby range (valid Siege target), or 0."""
    px, py = Agent.GetXY(player_id)
    for enemy_id in AgentArray.GetEnemyArray():
        if not Agent.IsAlive(enemy_id):
            continue
        ex, ey = Agent.GetXY(enemy_id)
        dx, dy = ex - px, ey - py
        dist_sq = dx * dx + dy * dy
        if _NEARBY_SQ < dist_sq <= _EARSHOT_SQ:
            return enemy_id
    return 0


def _has_dead_hero_nearby(player_id: int) -> bool:
    """Return True if any hero is dead within Nearby range."""
    px, py = Agent.GetXY(player_id)
    hero_count = GLOBAL_CACHE.Party.GetHeroCount()
    for pos in range(1, hero_count + 1):
        hid = GLOBAL_CACHE.Party.Heroes.GetHeroAgentIDByPartyPosition(pos)
        if hid <= 0 or Agent.IsAlive(hid):
            continue
        hx, hy = Agent.GetXY(hid)
        dx, dy = hx - px, hy - py
        if dx * dx + dy * dy <= _NEARBY_SQ:
            return True
    return False


class JununduWurm(BuildMgr):
    """HeroAI build that drives the Junundu Wurm skill rotation."""

    def __init__(self, match_only: bool = False, **kwargs):
        super().__init__(
            name="Junundu Wurm",
            required_primary=Profession(0),
            required_secondary=Profession(0),
            template_code="",
            required_skills=[_STRIKE_ID, _SIEGE_ID, _TUNNEL_ID],
            optional_skills=[_SMASH_ID, _BITE_ID, _FEAST_ID, _WAIL_ID],
        )
        if match_only:
            return
        Py4GW.Console.Log(_LOG, "JununduWurm build matched and active.", Py4GW.Console.MessageType.Success)

    def ScoreMatch(self, current_primary=None, current_secondary=None, current_skills=None) -> int:
        # Skill 1443 (Leave Junundu) only appears on slot 8 when inside a wurm.
        # Refuse selection entirely when outside so HeroAI keeps the player's real build.
        if current_skills is None:
            current_skills = self._get_current_skills()
        if _LEAVE_ID not in current_skills:
            return -1
        return super().ScoreMatch(current_primary, current_secondary, current_skills)

    def ProcessSkillCasting(self):
        player_id = Player.GetAgentID()

        # Locate nearest enemy in earshot
        target_id = Routines.Agents.GetNearestEnemy(Range.Earshot.value)

        if _combat_log_timer.IsExpired():
            _combat_log_timer.Reset()
            hp = Agent.GetHealth(player_id)
            enemy_count = sum(1 for e in AgentArray.GetEnemyArray() if Agent.IsAlive(e))
            px, py = Agent.GetXY(player_id)
            Py4GW.Console.Log(_LOG,
                f"Combat | pos=({px:.0f},{py:.0f}) hp={hp:.0%} "
                f"target={target_id} earshot_enemies={enemy_count}",
                Py4GW.Console.MessageType.Info)

        if not target_id:
            # No enemies: Wail if below 60% health, otherwise keep Tunnel uptime.
            hp = Agent.GetHealth(player_id)
            if hp < 0.6 and (yield from self.CastSkillSlot(7, aftercast_delay=500)):  # Wail
                return
            yield from self.CastSkillSlot(5, aftercast_delay=300)  # Tunnel
            return

        # Lock melee target synchronously — Player.ChangeTarget has no yield overhead.
        if Player.GetTargetID() != target_id:
            Player.ChangeTarget(target_id)

        hp = Agent.GetHealth(player_id)

        # Wail — dead teammate nearby; use as revive-window armor buff
        if _has_dead_hero_nearby(player_id) and (yield from self.CastSkillSlot(7, aftercast_delay=500)):  # Wail
            return

        # Siege — priority AoE spike; fire at first earshot enemy outside Nearby range.
        # target_agent_id bypasses the displayed target, so no target swap is needed.
        siege_id = _siege_target(player_id)
        if siege_id and (yield from self.CastSkillSlot(4, aftercast_delay=500, target_agent_id=siege_id)):  # Siege
            return

        # Smash — PBAoE melee; hits all enemies in melee range
        if (yield from self.CastSkillSlot(2, aftercast_delay=300)):  # Smash
            return

        # Bite — melee AoE on current target
        if (yield from self.CastSkillSlot(3, aftercast_delay=300)):  # Bite
            return

        # Tunnel — speed boost; harmless mid-combat
        if (yield from self.CastSkillSlot(5, aftercast_delay=300)):  # Tunnel
            return

        # Strike — basic attack fill when everything else is recharging
        yield from self.CastSkillSlot(1, aftercast_delay=300)  # Strike

    def ProcessOOC(self):
        """OOC: no-op — hero Tunnel removed for debugging; player speed handled by _speed_team() in the bot."""
        if False:
            yield
