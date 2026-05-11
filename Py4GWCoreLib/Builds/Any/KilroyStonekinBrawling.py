from Py4GWCoreLib import Agent
from Py4GWCoreLib import BuildMgr
from Py4GWCoreLib import GLOBAL_CACHE
from Py4GWCoreLib import Map
from Py4GWCoreLib import Player
from Py4GWCoreLib import Range
from Py4GWCoreLib import Routines
from Py4GWCoreLib.Builds.Any.HeroAI import HeroAI_Build


PUNCHOUT_MAP_IDS = {702, 703, 726}


def _skill_id(*names: str) -> int:
    for name in names:
        skill_id = int(GLOBAL_CACHE.Skill.GetID(name) or 0)
        if skill_id:
            return skill_id
    return 0


class KilroyStonekinBrawling(BuildMgr):
    def __init__(self, match_only: bool = False):
        brawling_jab = _skill_id("Brawling_Jab")
        brawling_uppercut = _skill_id("Brawling_Uppercut")
        brawling_block = _skill_id("Brawling_Block")
        brawling_straight_right = _skill_id("Brawling_Straight_Right")
        brawling_hook = _skill_id("Brawling_Hook")
        brawling_headbutt = _skill_id("Brawling_Headbutt_Brawling_skill", "Brawling_Headbutt")
        brawling_combo_punch = _skill_id("Brawling_Combo_Punch")

        super().__init__(
            name="Kilroy Stonekin Brawling",
            template_code="BRAWLING",
            required_skills=[
                brawling_jab,
                brawling_uppercut,
            ],
            optional_skills=[
                brawling_block,
                brawling_straight_right,
                brawling_hook,
                brawling_headbutt,
                brawling_combo_punch,
            ],
        )
        self.minimum_required_match = 1
        if match_only:
            return

        self.SetFallback("HeroAI", HeroAI_Build(standalone_fallback=True))
        self.brawling_jab = brawling_jab
        self.brawling_uppercut = brawling_uppercut
        self.brawling_block = brawling_block
        self.brawling_straight_right = brawling_straight_right
        self.brawling_hook = brawling_hook
        self.brawling_headbutt = brawling_headbutt
        self.brawling_combo_punch = brawling_combo_punch

    def ScoreMatch(self, current_primary=None, current_secondary=None, current_skills: list[int] | None = None) -> int:
        score = super().ScoreMatch(current_primary, current_secondary, current_skills)
        if score < 0:
            return score

        try:
            if int(Map.GetMapID()) in PUNCHOUT_MAP_IDS:
                score += 20
        except Exception:
            pass

        return score

    def _get_brawling_target(self, prefer_casting: bool = False) -> int:
        target_id = int(Player.GetTargetID() or 0)
        player_x, player_y = Player.GetXY()
        adjacent_enemies = Routines.Agents.GetFilteredEnemyArray(player_x, player_y, Range.Adjacent.value)
        if target_id in adjacent_enemies and Agent.IsValid(target_id) and not Agent.IsDead(target_id):
            return target_id

        if prefer_casting:
            target_id = Routines.Targeting.GetEnemyCasting(Range.Adjacent.value)
            if target_id:
                return target_id

        target_id = Routines.Targeting.GetEnemyAttacking(Range.Adjacent.value)
        if target_id:
            return target_id

        target_id = Routines.Targeting.GetEnemyInjured(Range.Adjacent.value)
        if target_id:
            return target_id

        return int(Routines.Agents.GetNearestEnemy(Range.Adjacent.value) or 0)

    def _cast_if_ready(self, skill_id: int, target_id: int = 0, aftercast_delay: int = 0):
        if not skill_id:
            return False
        return (
            yield from self.CastSkillID(
                skill_id,
                target_agent_id=target_id,
                aftercast_delay=aftercast_delay,
            )
        )

    def _cast_on_current_target(self, skill_id: int, target_id: int):
        if not skill_id or not target_id:
            return False
        if Player.GetTargetID() != target_id:
            Player.ChangeTarget(target_id)
            yield
        return (yield from self.CastSkillID(skill_id))

    def ProcessSkillCasting(self):
        self.ResetTickState()

        player_id = Player.GetAgentID()
        if not Agent.IsValid(player_id) or Agent.IsDead(player_id):
            self.SetTickFailure()
            yield
            return

        if not (
            Routines.Checks.Map.IsExplorable()
            and Routines.Checks.Player.CanAct()
            and Routines.Checks.Skills.CanCast()
        ):
            self.SetTickFailure()
            yield
            return

        yield from self._cast_if_ready(self.brawling_block)

        target_id = self._get_brawling_target()
        if not target_id:
            fallback = self.current_fallback_handler
            if fallback is not None:
                yield from fallback.ProcessSkillCasting()
                self.tick_state = fallback.tick_state
                return

            self.SetTickFailure()
            yield
            return

        if (yield from self._cast_if_ready(self.brawling_headbutt, target_id)):
            return
        if (yield from self._cast_if_ready(self.brawling_uppercut, target_id)):
            return
        if (yield from self._cast_if_ready(self.brawling_combo_punch, target_id)):
            return
        if (yield from self._cast_if_ready(self.brawling_hook, target_id)):
            return
        if (yield from self._cast_on_current_target(self.brawling_straight_right, target_id)):
            return
        if (yield from self._cast_if_ready(self.brawling_jab, target_id)):
            return


        fallback = self.current_fallback_handler
        if fallback is not None:
            yield from fallback.ProcessSkillCasting()
            self.tick_state = fallback.tick_state
            return

        self.SetTickFailure()
        yield
