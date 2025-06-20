import Py4GW
import json
import random
import math
from datetime import datetime
from enum import IntEnum
from typing import Optional, List, Tuple
from Py4GWCoreLib import PyImGui, ImGui, Color
from Py4GWCoreLib import GLOBAL_CACHE
from Py4GWCoreLib import ThrottledTimer
from Py4GWCoreLib import Profession
from Py4GWCoreLib import Routines
from Py4GWCoreLib import IniHandler
from Py4GWCoreLib import ConsoleLog
from Py4GWCoreLib import IconsFontAwesome5
from Py4GWCoreLib import AutoInventoryHandler
from Py4GWCoreLib import ModelID
from Py4GWCoreLib import TitleID
from Py4GWCoreLib import AgentModelID
from Py4GWCoreLib import Agent
from Py4GWCoreLib import ItemArray
from Py4GWCoreLib import SharedCommandType
from Py4GWCoreLib import FSM
from Py4GWCoreLib import Range
from Py4GWCoreLib import AgentArray
from Py4GWCoreLib import LootConfig
from Py4GWCoreLib import Utils

path_points_to_leave_outpost: List[Tuple[float, float]] = [(-24380, 15074), (-26375, 16180)]
path_points_to_traverse_bjora_marches: List[Tuple[float, float]] = [
    (17810, -17649),(17516, -17270),(17166, -16813),(16862, -16324),(16472, -15934),
    (15929, -15731),(15387, -15521),(14849, -15312),(14311, -15101),(13776, -14882),
    (13249, -14642),(12729, -14386),(12235, -14086),(11748, -13776),(11274, -13450),
    (10839, -13065),(10572, -12590),(10412, -12036),(10238, -11485),(10125, -10918),
    (10029, -10348),(9909, -9778)  ,(9599, -9327)  ,(9121, -9009)  ,(8674, -8645)  ,
    (8215, -8289)  ,(7755, -7945)  ,(7339, -7542)  ,(6962, -7103)  ,(6587, -6666)  ,
    (6210, -6226)  ,(5834, -5788)  ,(5457, -5349)  ,(5081, -4911)  ,(4703, -4470)  ,
    (4379, -3990)  ,(4063, -3507)  ,(3773, -3031)  ,(3452, -2540)  ,(3117, -2070)  ,
    (2678, -1703)  ,(2115, -1593)  ,(1541, -1614)  ,(960, -1563)   ,(388, -1491)   ,
    (-187, -1419)  ,(-770, -1426)  ,(-1343, -1440) ,(-1922, -1455) ,(-2496, -1472) ,
    (-3073, -1535) ,(-3650, -1607) ,(-4214, -1712) ,(-4784, -1759) ,(-5278, -1492) ,
    (-5754, -1164) ,(-6200, -796)  ,(-6632, -419)  ,(-7192, -300)  ,(-7770, -306)  ,
    (-8352, -286)  ,(-8932, -258)  ,(-9504, -226)  ,(-10086, -201) ,(-10665, -215) ,
    (-11247, -242) ,(-11826, -262) ,(-12400, -247) ,(-12979, -216) ,(-13529, -53)  ,
    (-13944, 341)  ,(-14358, 743)  ,(-14727, 1181) ,(-15109, 1620) ,(-15539, 2010) ,
    (-15963, 2380) ,(-18048, 4223 ), (-19196, 4986),(-20000, 5595) ,(-20300, 5600)
    ]
path_points_to_npc:List[Tuple[float, float]]  = [(13367, -20771)]
path_points_to_farming_route1: List[Tuple[float, float]] = [
    (11375, -22761),
    (10925, -23466),
    (10917, -24311),
    (10280, -24620),
    (9640, -23175),
    (7815, -23200),
    (7765, -22940),
    (8213, -22829),
    (8740, -22475),
    (8880, -21384),
    (8684, -20833),
    (8982, -20576),
]


path_points_to_farming_route2: List[Tuple[float, float]] = [
    (10196, -20124), (10123, -19529),(10049, -18933), (9976, -18338), (11316, -18056),
    (10392, -17512), (10114, -16948),(10729, -16273), (10505, -14750),(10815, -14790),
    (11090, -15345), (11670, -15457),(12604, -15320), (12450, -14800),(12725, -14850),
    (12476, -16157),
]



path_points_to_killing_spot: List[Tuple[float, float]] = [
    (13070, -16911),
    (12938, -17081),
    (12790, -17201),
    (12747, -17220),
    (12703, -17239),
    (12684, -17184),
]

path_points_to_exit_jaga_moraine: List[Tuple[float, float]] = [(12289, -17700) ,(13970, -18920), (15400, -20400),(15850,-20550)]
path_points_to_return_to_jaga_moraine: List[Tuple[float, float]] = [(-20300, 5600 )]

class RunStatistics:
    class RunNode:
        def __init__(self, runid: int = 0):
            self.runID:int = runid
            self.start_time: datetime = datetime.now()
            self.end_time: Optional[datetime] = None
            self.TARGET_VAETTIR_KILLS: int = 60
            self.vaettir_kills: int = 0
            self.deaths: int = 0
            self.stuck_timeouts: int = 0
            self.failed = False
            
        def Start(self):
            self.start_time = datetime.now()

        def End(self, vaettirs_killed: int = 0, failed: bool = False, deaths: int = 0, stuck_timeouts: int = 0):
            self.end_time = datetime.now()
            self.vaettir_kills = vaettirs_killed
            self.deaths = deaths
            self.stuck_timeouts = stuck_timeouts
            self.failed = failed
            
        def GetRunDuration(self) -> float:
            """Returns the duration of the run in seconds, or None if the run has not ended."""
            if self.end_time is None:
                return (datetime.now() - self.start_time).total_seconds()
            return (self.end_time - self.start_time).total_seconds()
    
    def __init__(self):
        self.run_nodes: List[RunStatistics.RunNode] = []
        self.current_run_node: Optional[RunStatistics.RunNode] = None
        self.run_id_counter: int = 0
        
    def StartNewRun(self):
        """Starts a new run and initializes the run node."""
        self.run_id_counter += 1
        new_run_node = RunStatistics.RunNode(runid=self.run_id_counter)
        new_run_node.Start()
        self.run_nodes.append(new_run_node)
        self.current_run_node = new_run_node
        
    def EndCurrentRun(self, vaettirs_killed: int = 0, failed: bool = False, deaths: int = 0, stuck_timeouts: int = 0):
        """Ends the current run and updates the run node."""
        if self.current_run_node is not None:
            self.current_run_node.End(vaettirs_killed, failed,deaths, stuck_timeouts)
            self.current_run_node = None
            
    def GetCurrentRun(self) -> Optional["RunStatistics.RunNode"]:
        """Returns the current run node, or None if no run is in progress."""
        return self.current_run_node
    
    def _get_successful_runs(self) -> List["RunStatistics.RunNode"]:
        return [node for node in self.run_nodes if not node.failed and node.end_time is not None]

    
    def GetQuickestRun(self) -> Optional["RunStatistics.RunNode"]:
        successful = self._get_successful_runs()
        return min(successful, key=lambda node: node.GetRunDuration(), default=None)
    
    def GetLongestRun(self) -> Optional["RunStatistics.RunNode"]:
        successful = self._get_successful_runs()
        return max(successful, key=lambda node: node.GetRunDuration(), default=None)
    
    def GetAverageRunDuration(self) -> float:
        successful = self._get_successful_runs()
        if not successful:
            return 0.0
        total_duration = sum(node.GetRunDuration() for node in successful)
        if len(successful) == 0:
            return 0.0
        return total_duration / len(successful)
    
    def GetKillEffectivity(self) -> float:
        successful = self._get_successful_runs()
        if not successful:
            return 0.0
        total_kills = sum(node.vaettir_kills for node in successful)
        total_target_kills = sum(node.TARGET_VAETTIR_KILLS for node in successful)
        if total_target_kills == 0:
            return 0.0
        return (total_kills / total_target_kills) * 100.0
    
    def GetRuneffectivity(self) -> float:
        total_runs = len(self.run_nodes)
        if total_runs == 0:
            return 0.0
        successful_runs = sum(1 for node in self.run_nodes if not node.failed)
        return (successful_runs / total_runs) * 100.0
    
    def GetDeaths(self) -> int:
        return sum(node.deaths for node in self.run_nodes)

    def GetTimeouts(self) -> int:
        return sum(node.stuck_timeouts for node in self.run_nodes)
    
    def GetFailedRuns(self) -> List["RunStatistics.RunNode"]:
        return [node for node in self.run_nodes if node.failed and node.end_time is not None]

    def GetAverageKillsOnSuccess(self) -> float:
        successful = self._get_successful_runs()
        if not successful:
            return 0.0
        return sum(n.vaettir_kills for n in successful) / len(successful)
    
    def GetAverageDeathsOnSuccess(self) -> float:
        successful = self._get_successful_runs()
        if not successful:
            return 0.0
        return sum(n.deaths for n in successful) / len(successful)
    
    def GetTotalRuns(self) -> int:
        return len(self.run_nodes)
    
    def GetTotalSuccesses(self) -> int:
        return sum(1 for node in self.run_nodes if not node.failed)
    
    def GetTotalFailures(self) -> int:
        return sum(1 for node in self.run_nodes if node.failed)


#region build
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
            skill = GLOBAL_CACHE.SkillBar.GetSkillIDBySlot(i+1)
            if skill:
                skills.append(skill)

        all_valid = sorted(self.skills) == sorted(skills)

        if not all_valid:
            wait_interval = 1000
        else:
            wait_interval = 0
        yield from Routines.Yield.wait(wait_interval)
        return all_valid

    
    def EquipBuild(self):
        yield from Routines.Yield.Skills.LoadSkillbar(self.template_code,log=False)

    def ProcessSkillCasting(self):
        """Override this in child classes for casting logic."""
        raise NotImplementedError
    
    def LoadSkillBar(self):
        """
        Load the skill bar with the build's template code.
        This method can be overridden in child classes if needed.
        """
        yield from Routines.Yield.Skills.LoadSkillbar(self.template_code, log=False)
    
class ShawowFormAssassinVaettir(Build):
    def __init__(self):
        super().__init__(
            name="Shadow Form Assassin Vaettir",
            required_primary=Profession.Assassin,
            required_secondary=Profession.Mesmer,
            template_code="OwVUI2h5lPP8Id2BkAiAvpLBTAA",
            skills=[
                GLOBAL_CACHE.Skill.GetID("Deadly_Paradox"),
                GLOBAL_CACHE.Skill.GetID("Shadow_Form"),
                GLOBAL_CACHE.Skill.GetID("Shroud_of_Distress"),
                GLOBAL_CACHE.Skill.GetID("Way_of_Perfection"),
                GLOBAL_CACHE.Skill.GetID("Heart_of_Shadow"),
                GLOBAL_CACHE.Skill.GetID("Wastrels_Demise"),
                GLOBAL_CACHE.Skill.GetID("Arcane_Echo"),
                GLOBAL_CACHE.Skill.GetID("Channeling"),
            ]
        )
        

        self.deadly_paradox_slot = GLOBAL_CACHE.SkillBar.GetSlotBySkillID(GLOBAL_CACHE.Skill.GetID("Deadly_Paradox"))
        self.shadow_form_slot = GLOBAL_CACHE.SkillBar.GetSlotBySkillID(GLOBAL_CACHE.Skill.GetID("Shadow_Form"))
        self.shroud_of_distress_slot = GLOBAL_CACHE.SkillBar.GetSlotBySkillID(GLOBAL_CACHE.Skill.GetID("Shroud_of_Distress"))
        self.way_of_perfection_slot = GLOBAL_CACHE.SkillBar.GetSlotBySkillID(GLOBAL_CACHE.Skill.GetID("Way_of_Perfection"))
        self.heart_of_shadow_slot = GLOBAL_CACHE.SkillBar.GetSlotBySkillID(GLOBAL_CACHE.Skill.GetID("Heart_of_Shadow"))
        self.wastrels_demise_slot = GLOBAL_CACHE.SkillBar.GetSlotBySkillID(GLOBAL_CACHE.Skill.GetID("Wastrels_Demise"))
        self.arcane_echo_slot = GLOBAL_CACHE.SkillBar.GetSlotBySkillID(GLOBAL_CACHE.Skill.GetID("Arcane_Echo"))
        self.channeling_slot = GLOBAL_CACHE.SkillBar.GetSlotBySkillID(GLOBAL_CACHE.Skill.GetID("Channeling"))
        
        self.shadow_form = GLOBAL_CACHE.Skill.GetID("Shadow_Form")
        self.deadly_paradox = GLOBAL_CACHE.Skill.GetID("Deadly_Paradox")
        self.shroud_of_distress = GLOBAL_CACHE.Skill.GetID("Shroud_of_Distress")
        self.channeling = GLOBAL_CACHE.Skill.GetID("Channeling")
        self.way_of_perfection = GLOBAL_CACHE.Skill.GetID("Way_of_Perfection")
        self.heart_of_shadow = GLOBAL_CACHE.Skill.GetID("Heart_of_Shadow")
                
                
        self.in_killing_routine = False
        self.routine_finished = False
        self.stuck_counter = 0
        self.waypoint = (0,0)
        
    def SetKillingRoutine(self, in_killing_routine: bool):
        self.in_killing_routine = in_killing_routine
        
    def SetRoutineFinished(self, routine_finished: bool):
        self.routine_finished = routine_finished
        
    def SetStuckCounter(self, stuck_counter: int):
        self.stuck_counter = stuck_counter
        
    def DefensiveActions(self):
        player_agent_id = GLOBAL_CACHE.Player.GetAgentID()
        has_shadow_form = Routines.Checks.Effects.HasBuff(player_agent_id,self.shadow_form)
        shadow_form_buff_time_remaining = GLOBAL_CACHE.Effects.GetEffectTimeRemaining(player_agent_id,self.shadow_form) if has_shadow_form else 0
        has_deadly_paradox = Routines.Checks.Effects.HasBuff(player_agent_id, self.deadly_paradox)
        if shadow_form_buff_time_remaining <= 3500:
            if Routines.Yield.Skills.CastSkillID(self.deadly_paradox,extra_condition=(not has_deadly_paradox), log=False, aftercast_delay=100):
                ConsoleLog(self.build_name, "Casting Deadly Paradox.", Py4GW.Console.MessageType.Info, log=False)
                yield from Routines.Yield.wait(100)
                
            if Routines.Yield.Skills.CastSkillID(self.shadow_form, log=False, aftercast_delay=1750):
                ConsoleLog(self.build_name, "Casting Shadow Form.", Py4GW.Console.MessageType.Info, log=False)
                yield from Routines.Yield.wait(1750)
                
    def CastShroudOfDistress(self):
        player_agent_id = GLOBAL_CACHE.Player.GetAgentID()
        if GLOBAL_CACHE.Agent.GetHealth(player_agent_id) < 0.45:
            ConsoleLog(self.build_name, "Casting Shroud of Distress.", Py4GW.Console.MessageType.Info, log=False)
            # ** Cast Shroud of Distress **
            if Routines.Yield.Skills.CastSkillID(self.shroud_of_distress, log =False, aftercast_delay=1750):
                yield from Routines.Yield.wait(1750)
            
    def ProcessSkillCasting(self):
        def GetNotHexedEnemy():
            player_pos =  GLOBAL_CACHE.Player.GetXY()
            enemy_array = Routines.Agents.GetFilteredEnemyArray(player_pos[0],player_pos[1],Range.Spellcast.value)
            enemy_array = AgentArray.Filter.ByCondition(enemy_array, lambda agent_id:not Agent.IsHexed(agent_id))
            if len(enemy_array) == 0:
                return 0
            return enemy_array[0]
        
        def vector_angle(a: Tuple[float, float], b: Tuple[float, float]) -> float:
            """Returns the cosine similarity (dot product / magnitudes). 1 = same direction, -1 = opposite."""
            dot = a[0]*b[0] + a[1]*b[1]
            mag_a = math.hypot(*a)
            mag_b = math.hypot(*b)
            if mag_a == 0 or mag_b == 0:
                return 1  # safest fallback
            dot = a[0]*b[0] + a[1]*b[1]
            return dot / (mag_a * mag_b)
        
        while True:
            if not Routines.Checks.Map.MapValid():
                yield from Routines.Yield.wait(1000)
                continue
            
            if not GLOBAL_CACHE.Map.GetMapID() == GLOBAL_CACHE.Map.GetMapIDByName("Jaga Moraine"):
                yield from Routines.Yield.wait(1000)
                return
            
            
            if GLOBAL_CACHE.Agent.IsDead(GLOBAL_CACHE.Player.GetAgentID()):
                yield from Routines.Yield.wait(1000)
                continue
            
            if not Routines.Checks.Skills.CanCast():
                yield from Routines.Yield.wait(100)
                continue
            
            if self.routine_finished:
                return

            player_agent_id = GLOBAL_CACHE.Player.GetAgentID()
            if Routines.Checks.Agents.InDanger(Range.Spellcast):
                has_shadow_form = Routines.Checks.Effects.HasBuff(player_agent_id,self.shadow_form)
                shadow_form_buff_time_remaining = GLOBAL_CACHE.Effects.GetEffectTimeRemaining(player_agent_id,self.shadow_form) if has_shadow_form else 0
                has_deadly_paradox = Routines.Checks.Effects.HasBuff(player_agent_id, self.deadly_paradox)
                if shadow_form_buff_time_remaining <= 3500:
                    GLOBAL_CACHE._ActionQueueManager.ResetQueue("ACTION")
                    if Routines.Yield.Skills.CastSkillID(self.deadly_paradox,extra_condition=(not has_deadly_paradox), log=False, aftercast_delay=200):
                        ConsoleLog(self.build_name, "Casting Deadly Paradox.", Py4GW.Console.MessageType.Info, log=False)
                        yield from Routines.Yield.wait(200)
                    GLOBAL_CACHE._ActionQueueManager.ResetQueue("ACTION")   
                    if Routines.Yield.Skills.CastSkillID(self.shadow_form, log=False, aftercast_delay=1850):
                        ConsoleLog(self.build_name, "Casting Shadow Form.", Py4GW.Console.MessageType.Info, log=False)
                        yield from Routines.Yield.wait(1850)
                        continue

            has_shroud_of_distress = Routines.Checks.Effects.HasBuff(player_agent_id,self.shroud_of_distress)
            if not has_shroud_of_distress:
                ConsoleLog(self.build_name, "Casting Shroud of Distress.", Py4GW.Console.MessageType.Info, log=False)
                # ** Cast Shroud of Distress **
                GLOBAL_CACHE._ActionQueueManager.ResetQueue("ACTION")
                if Routines.Yield.Skills.CastSkillID(self.shroud_of_distress, log =False, aftercast_delay=1850):
                    yield from Routines.Yield.wait(1850)
                    continue
                        
            has_channeling = Routines.Checks.Effects.HasBuff(player_agent_id,self.channeling)
            if not has_channeling:
                ConsoleLog(self.build_name, "Casting Channeling.", Py4GW.Console.MessageType.Info, log=False)
                # ** Cast Channeling **
                if Routines.Yield.Skills.CastSkillID(self.channeling, log =False, aftercast_delay=1850):
                    yield from Routines.Yield.wait(1850)
                    continue
                        
            if Routines.Yield.Skills.CastSkillID(self.way_of_perfection, log=False, aftercast_delay=1000):
                ConsoleLog(self.build_name, "Casting Way of Perfection.", Py4GW.Console.MessageType.Info, log=False)
                yield from Routines.Yield.wait(1000)
                continue

            if not self.in_killing_routine:
                if GLOBAL_CACHE.Agent.GetHealth(player_agent_id) < 0.35 or self.stuck_counter > 0:
                    center_point1 = (10980, -21532)
                    center_point2 = (11461, -17282)
                    player_pos = GLOBAL_CACHE.Player.GetXY()
                    
                    distance_to_center1 = Utils.Distance(player_pos, center_point1)
                    distance_to_center2 = Utils.Distance(player_pos, center_point2)
                    goal = center_point1 if distance_to_center1 < distance_to_center2 else center_point2
                    #Compute direction to goal
                    to_goal = (goal[0] - player_pos[0], goal[1] - player_pos[1])
                    
                    best_enemy = 0
                    most_opposite_score = 1 
                    
                    enemy_array = Routines.Agents.GetFilteredEnemyArray(player_pos[0], player_pos[1], Range.Spellcast.value)
                    
                    for enemy in enemy_array:
                        if GLOBAL_CACHE.Agent.IsDead(enemy):
                            continue
                        enemy_pos = GLOBAL_CACHE.Agent.GetXY(enemy)
                        to_enemy = (enemy_pos[0] - player_pos[0], enemy_pos[1] - player_pos[1])

                        angle_score = vector_angle(to_goal, to_enemy)  # -1 is most opposite

                        if angle_score < most_opposite_score:
                            most_opposite_score = angle_score
                            best_enemy = enemy
                    if best_enemy:
                        yield from Routines.Yield.Agents.ChangeTarget(best_enemy)    
                    else:
                        yield from Routines.Yield.Agents.TargetNearestEnemy(Range.Earshot.value)

                    if Routines.Yield.Skills.CastSkillID(self.heart_of_shadow, log=False, aftercast_delay=350):
                        yield from Routines.Yield.wait(350)
                        continue
                        
            if self.in_killing_routine:
                both_ready = Routines.Checks.Skills.IsSkillSlotReady(self.wastrels_demise_slot) and Routines.Checks.Skills.IsSkillSlotReady(self.arcane_echo_slot)
                target = GetNotHexedEnemy()
                if target:
                    GLOBAL_CACHE._ActionQueueManager.ResetQueue("ACTION")
                    yield from Routines.Yield.Agents.InteractAgent(target)
                    if Routines.Yield.Skills.CastSkillSlot(self.arcane_echo_slot, extra_condition=both_ready, log=False, aftercast_delay=2850):
                        ConsoleLog(self.build_name, "Casting Arcane Echo.", Py4GW.Console.MessageType.Info, log=False)
                        yield from Routines.Yield.wait(2850)
                    else:
                        if Routines.Yield.Skills.CastSkillSlot(self.arcane_echo_slot, log=False, aftercast_delay=1000):
                            ConsoleLog(self.build_name, "Casting Echoed Wastrel.", Py4GW.Console.MessageType.Info, log=False)
                            yield from Routines.Yield.wait(1000)
                
                target = GetNotHexedEnemy()  
                if target: 
                    GLOBAL_CACHE._ActionQueueManager.ResetQueue("ACTION")
                    yield from Routines.Yield.Agents.InteractAgent(target)
                    if Routines.Yield.Skills.CastSkillSlot(self.wastrels_demise_slot, log=False, aftercast_delay=1000):
                        yield from Routines.Yield.wait(1000)

            yield from Routines.Yield.wait(100)
            
#endregion

#region Logconsole  
class LogConsole:
    class LogSeverity(IntEnum):
        INFO = 0
        WARNING = 1
        ERROR = 2
        CRITICAL = 3
        SUCCESS = 4

        def __str__(self):
            return self.name.capitalize()

        def to_color(self) -> 'Color':
            if self == self.INFO:
                return Color(255, 255, 255, 255)  # White
            elif self == self.WARNING:
                return Color(255, 255, 0, 255)    # Yellow
            elif self == self.ERROR:
                return Color(255, 0, 0, 255)      # Red
            elif self == self.CRITICAL:
                return Color(128, 0, 128, 255)    # Purple
            elif self == self.SUCCESS:
                return Color(0, 255, 0, 255)      # Green
            return Color(255, 255, 255, 255)      # Default

    class LogEntry:
        def __init__(self, message: str, extra_info: Optional[str],severity: Optional['LogConsole.LogSeverity'] = None):
            if severity is None:
                severity = LogConsole.LogSeverity.INFO
            self.message: str = message
            self.extra_info: str = extra_info if extra_info is not None else ""
            self.severity: LogConsole.LogSeverity = severity
            self.color: Color = severity.to_color()
            self.timestamp = datetime.now()

        def __str__(self):
            return f"[{self.severity}] {self.message}"

    def __init__(self,module_name="LogConsole", window_pos= (100, 100), window_size= (400, 300), is_snapped= True,  log_to_file: bool = False):
        self.messages: list[LogConsole.LogEntry] = []
        self.log_to_file: bool = log_to_file
        self.window_flags = PyImGui.WindowFlags(
            PyImGui.WindowFlags.AlwaysAutoResize
        )
        self.main_window_pos = (100, 100)  # fallback default
        self.main_window_size = (400, 300)
        
        self.window_pos = window_pos
        self.window_size = window_size
        self.is_snapped = is_snapped
        self.window_snapped_border = "Right"
        self.window_module_initialized = False
        self.window_module = ImGui.WindowModule(
            module_name=module_name,
            window_name=module_name,
            window_pos=self.window_pos,
            window_size=self.window_size,
            window_flags=self.window_flags,
            
        )
        
    def SetLogToFile(self, log_to_file: bool):
        """Set whether to log messages to a file."""
        self.log_to_file = log_to_file     
    
    def SetSnapped(self, is_snapped: bool, snapped_border: str = "Right"):
        """Set whether the console window is snapped to the main window."""
        self.is_snapped = is_snapped
        self.window_snapped_border = snapped_border
        
    def SetWindowPosition(self, pos: tuple[int, int]):
        """Set the position of the log console window."""
        self.window_pos = pos
            
    def SetWindowSize(self, size: tuple[int, int]):
        """Set the size of the log console window."""
        self.window_size = size
        
    def SetMainWindowPosition(self, pos):
        """Set the position of the main window."""
        self.main_window_pos = pos
        
    def SetMainWindowSize(self, size):
        """Set the size of the main window."""
        self.main_window_size = size

    def LogMessage(self, message: str, extra_info: Optional[str], severity: Optional['LogConsole.LogSeverity'] = None):
        """Add a new log entry to the console."""
        entry = LogConsole.LogEntry(message, extra_info, severity)
        self.messages.append(entry)

    def DrawConsole(self):
        """Draw the log console window."""
        self.window_module.initialize()
        border = self.window_snapped_border.lower()
        if border == "right":
            snapped_x = self.main_window_pos[0] + self.main_window_size[0] + 1
            snapped_y = self.main_window_pos[1]
        elif border == "left":
            snapped_x = self.main_window_pos[0] - self.main_window_size[0] - 1
            snapped_y = self.main_window_pos[1]
        elif border == "top":
            snapped_x = self.main_window_pos[0]
            snapped_y = self.main_window_pos[1] - self.window_size[1] - 1
        elif border == "bottom":
            snapped_x = self.main_window_pos[0]
            snapped_y = self.main_window_pos[1] + self.main_window_size[1] + 1
        else:
            # Fallback to right
            snapped_x = self.main_window_pos[0] + self.main_window_size[0] + 1
            snapped_y = self.main_window_pos[1]

        if self.is_snapped:
            PyImGui.set_next_window_pos(snapped_x, snapped_y)
            
        PyImGui.set_next_window_size(self.main_window_size[0] * 2, self.main_window_size[1])
            
        if self.window_module.begin():
            if PyImGui.begin_child("Log Messages", (0, 0), True, PyImGui.WindowFlags.AlwaysVerticalScrollbar):
                if PyImGui.begin_table("LogTable", 3, PyImGui.TableFlags.RowBg | PyImGui.TableFlags.ScrollY | PyImGui.TableFlags.Borders):
                    PyImGui.table_setup_column("Time", PyImGui.TableColumnFlags.WidthFixed, 75)
                    PyImGui.table_setup_column("Message", PyImGui.TableColumnFlags.WidthFixed, 150)
                    PyImGui.table_setup_column("Reason", PyImGui.TableColumnFlags.WidthStretch)
                    PyImGui.table_headers_row()
                    for message in reversed(self.messages):
                        PyImGui.table_next_row()
                        PyImGui.table_set_column_index(0)
                        PyImGui.text(f"{message.timestamp.strftime('%H:%M:%S')}")
                        
                        PyImGui.table_set_column_index(1)
                        PyImGui.push_style_color(PyImGui.ImGuiCol.Text, message.color.to_tuple_normalized())
                        PyImGui.text_wrapped(message.message)
                        PyImGui.table_set_column_index(2)
                        PyImGui.text_wrapped(message.extra_info)
                        PyImGui.pop_style_color(1)
                    PyImGui.end_table()
                PyImGui.end_child()
            self.window_module.process_window()
        self.window_module.end()

    
    
#endregion
#region YAVB

class ProgressTracker:
    def __init__(self):
        self.steps: list[tuple[str, float]] = []   # [(name, weight)]
        self.completed_weight: float = 0.0         # Total from past steps
        self.state: str = ""
        self.state_weight: float = 0.0
        self.state_percentage: float = 0.0
        self.reset()
        
    def reset(self):
        """
        Reset the progress tracker to initial state.
        """
        self.steps.clear()
        self.completed_weight = 0.0
        self.state = ""
        self.state_weight = 0.0
        self.state_percentage = 0.0

    def set_step(self, name: str, weight: float):
        """
        Start a new step with a given weight. Internally finalizes previous one.
        """
        if self.state:
            # Force complete previous step at 100%
            self.completed_weight += self.state_weight  # assume full completion
            self.state_percentage = 1.0  # just for reference
        self.steps.append((name, weight))
        self.state = name
        self.state_weight = weight
        self.state_percentage = 0.0
        
    def finalize_current_step(self):
        """
        Marks the current step as complete (100%) and adds to total progress.
        """
        if self.state:
            self.completed_weight += self.state_weight
            self.state_percentage = 1.0
            self.state = ""
            self.state_weight = 0.0

    def update_progress(self, percent: float):
        """
        Update the progress of the current step (0.0 to 1.0).
        """
        self.state_percentage = max(0.0, min(percent, 1.0))

    def get_overall_progress(self) -> float:
        """
        Return total progress: completed steps + current step's progress × weight.
        """
        return self.completed_weight + self.state_percentage * self.state_weight
    
    def get_step_name(self) -> str:
        """
        Return the name of the current step.
        """
        return self.state if self.state else "Idle"



class YAVB:
    def __init__(self):
        self.name = "YAVB"
        self.version = "1.0"
        self.author = "Apo"
        self.description = "Yet Another Vaettir Bot"
        self.icon = "YAVB\\yavb_mascot.png"
        self.tagline_file = "YAVB\\YAVB_taglines.json"
        self.ini_file = "YAVB\\YAVB.ini"
        #line randomizer
        self.prhase_throttled_timer = ThrottledTimer()
        self.current_tagline = ""
        
        #title banner
        self.banner_string = self.description + " by " + self.author + "   -   "
        self.banner_color = Color(255, 255, 0, 255)  # Yellow color
        self.banner_font_size = 1.4
        self.banner_throttled_timer = ThrottledTimer(250)
        self.banner_index = 0
        
        #build
        self.build: Optional[ShawowFormAssassinVaettir] = None
        #self.build = ShawowFormAssassinVaettir()
        self.supported_professions = {}
    
        #merchant options
        self.identification_kits_restock = 2
        self.salvage_kits_restock = 5
        self.keep_empty_inventory_slots = 2
        
        #bot options
        self.detailed_logging = False
        self.script_running = False
        self.script_paused = False
        self.state = "Idle"  # Current state of the bot
        self.state_percentage = 0.0  # Percentage of completion for the current state
        self.overall_progress = 0.0  # Overall progress of the bot
        self.progress_tracker = ProgressTracker()
        self.FSM = FSM("YAVB FSM", log_actions=False)
        self.FSM_Helpers = self._FSM_Helpers(self)
        
        #UI checks
        self.primary_profession = 0 #default to prevent crashes
        self.secondary_profession = 0 #default to prevent crashes
        self.prof_supported = False
        
        #window vars
        self.window_flags = PyImGui.WindowFlags(
            PyImGui.WindowFlags.AlwaysAutoResize | 
            PyImGui.WindowFlags.MenuBar
        )
        self.main_window_pos = (100, 100)  # fallback default
        self.main_window_size = (400, 300) # fallback default
        self.option_window_pos = (100, 100)  # fallback default
        self.option_window_size = (300, 250)  # fallback default
        self.console_pos = (100, 100)  # fallback default
        self.console_size = (400, 300)  # fallback default
        #option window
        self.option_window_visible = False
        self.option_window_snapped = True
        self.option_window_snapped_border = "Bottom"
        #Console
        self.console_visible = False
        self.console_snapped = True
        self.console_snapped_border = "Right"
        self.console_log_to_file = False
        
        self.console = LogConsole(
            module_name="YAVB Console",
            window_pos=self.main_window_pos,
            window_size=self.main_window_size,
            is_snapped=self.option_window_snapped, 
            log_to_file=False
        )
        
        #bot behavior
        self.inventory_handler = AutoInventoryHandler()
        self.use_cupcakes = False
        self.use_pumpkin_cookies = False
        self.pumpkin_cookies_restock = 4
        self.stuck_counter = 0
        self.stuck_timer = ThrottledTimer(5000)  
        self.movement_check_timer = ThrottledTimer(3000) 
        self.old_player_position = (0, 0)
        self.running_to_jaga = False
        self.in_killing_routine = False
        self.finished_routine = False
        self.in_waiting_routine = False
        self.ini_handler = IniHandler(self.ini_file)
        
        #statistics
        self.run_to_jaga_stats = RunStatistics()
        self.farming_stats = RunStatistics()
        self.current_run_node: Optional[RunStatistics.RunNode] = None
        
        
        self.load_config()
        
        # Initialize the main window module

        
        self.window_module = ImGui.WindowModule(
            module_name=self.name,
            window_name=f"{self.name} {self.version} by {self.author}",
            window_pos=self.main_window_pos,
            window_size=self.main_window_size,
            window_flags=self.window_flags,
            
        )
        
        self.option_window_module = ImGui.WindowModule(
            module_name=f"{self.name} Options",
            window_name=f"{self.name} Options",
            window_flags= PyImGui.WindowFlags(
                PyImGui.WindowFlags.AlwaysAutoResize)
            )
        
        
        self.console.SetSnapped(self.console_snapped, self.console_snapped_border)
        self.console.SetWindowPosition(self.console_pos)
        self.console.SetWindowSize(self.console_size)
        self.console.SetMainWindowPosition(self.main_window_pos)
        self.console.SetMainWindowSize(self.main_window_size)
        self.console.SetLogToFile(self.console_log_to_file)
        
        self.LONGEYES_LEDGE = GLOBAL_CACHE.Map.GetMapIDByName("Longeyes Ledge")
        self.BJORA_MARCHES = GLOBAL_CACHE.Map.GetMapIDByName("Bjora Marches")
        self.JAGA_MORAINE = GLOBAL_CACHE.Map.GetMapIDByName("Jaga Moraine")
        
        self._initialize_fsm()
        
        self.console.LogMessage("YAVB initialized", "", LogConsole.LogSeverity.SUCCESS)

    def save_config(self):
        ih = self.ini_handler

        # Main Window
        ih.write_key("MainWindow", "pos_x", self.main_window_pos[0])
        ih.write_key("MainWindow", "pos_y", self.main_window_pos[1])
        ih.write_key("MainWindow", "size_x", self.main_window_size[0])
        ih.write_key("MainWindow", "size_y", self.main_window_size[1])

        # Option Window
        ih.write_key("OptionWindow", "pos_x", self.option_window_pos[0])
        ih.write_key("OptionWindow", "pos_y", self.option_window_pos[1])
        ih.write_key("OptionWindow", "size_x", self.option_window_size[0])
        ih.write_key("OptionWindow", "size_y", self.option_window_size[1])
        ih.write_key("OptionWindow", "visible", self.option_window_visible)
        ih.write_key("OptionWindow", "snapped", self.option_window_snapped)
        ih.write_key("OptionWindow", "snapped_border", self.option_window_snapped_border)

        # Console
        ih.write_key("Console", "pos_x", self.console_pos[0])
        ih.write_key("Console", "pos_y", self.console_pos[1])
        ih.write_key("Console", "size_x", self.console_size[0])
        ih.write_key("Console", "size_y", self.console_size[1])
        ih.write_key("Console", "visible", self.console_visible)
        ih.write_key("Console", "snapped", self.console_snapped)
        ih.write_key("Console", "snapped_border", self.console_snapped_border)
        ih.write_key("Console", "log_to_file", self.console_log_to_file)
        ih.write_key("Console", "detailed_logging", self.detailed_logging)

        #Merchant
        ih.write_key("Merchant", "identification_kits_restock", self.identification_kits_restock)
        ih.write_key("Merchant", "salvage_kits_restock", self.salvage_kits_restock)
        ih.write_key("Merchant", "keep_empty_inventory_slots", self.keep_empty_inventory_slots)
        
        ih.write_key("BotConfigs", "use_cupcakes", self.use_cupcakes)
        ih.write_key("BotConfigs", "use_pumpkin_cookies", self.use_pumpkin_cookies)
        ih.write_key("BotConfigs", "pumpkin_cookies_restock", self.pumpkin_cookies_restock)



    def load_config(self):
        ih = self.ini_handler
        
        ConsoleLog("debug", "Loading configuration from INI file", log=True)

        # Main Window
        self.main_window_pos = (
            ih.read_float("MainWindow", "pos_x", self.main_window_pos[0]),
            ih.read_float("MainWindow", "pos_y", self.main_window_pos[1]),
        )
        self.main_window_size = (
            ih.read_float("MainWindow", "size_x", self.main_window_size[0]),
            ih.read_float("MainWindow", "size_y", self.main_window_size[1]),
        )

        # Option Window
        self.option_window_pos = (
            ih.read_float("OptionWindow", "pos_x", self.option_window_pos[0]),
            ih.read_float("OptionWindow", "pos_y", self.option_window_pos[1]),
        )
        self.option_window_size = (
            ih.read_float("OptionWindow", "size_x", self.option_window_size[0]),
            ih.read_float("OptionWindow", "size_y", self.option_window_size[1]),
        )
        self.option_window_visible = ih.read_bool("OptionWindow", "visible", self.option_window_visible)
        self.option_window_snapped = ih.read_bool("OptionWindow", "snapped", self.option_window_snapped)
        self.option_window_snapped_border = ih.read_key("OptionWindow", "snapped_border", self.option_window_snapped_border)

        # Console
        self.console_pos = (
            ih.read_float("Console", "pos_x", self.console_pos[0]),
            ih.read_float("Console", "pos_y", self.console_pos[1]),
        )
        self.console_size = (
            ih.read_float("Console", "size_x", self.console_size[0]),
            ih.read_float("Console", "size_y", self.console_size[1]),
        )
        self.console_visible = ih.read_bool("Console", "visible", self.console_visible)
        self.console_snapped = ih.read_bool("Console", "snapped", self.console_snapped)
        self.console_snapped_border = ih.read_key("Console", "snapped_border", self.console_snapped_border)
        self.console_log_to_file = ih.read_bool("Console", "log_to_file", self.console_log_to_file)
        self.detailed_logging = ih.read_bool("Console", "detailed_logging", self.detailed_logging)
        
        if self.detailed_logging:
            self.LogMessage("Detailed logging", "ENABLED", LogConsole.LogSeverity.INFO)
        
        #Merchant
        self.identification_kits_restock = ih.read_int("Merchant", "identification_kits_restock", self.identification_kits_restock)
        self.salvage_kits_restock = ih.read_int("Merchant", "salvage_kits_restock", self.salvage_kits_restock)
        self.keep_empty_inventory_slots = ih.read_int("Merchant", "keep_empty_inventory_slots", self.keep_empty_inventory_slots)
        
        self.supported_professions = {
                k: v for k, v in ih.list_keys("SupportedProfessions").items()
                if k.isdigit()
            }
        
        #Bot configs
        self.use_cupcakes = ih.read_bool("BotConfigs", "use_cupcakes", self.use_cupcakes)
        self.use_pumpkin_cookies = ih.read_bool("BotConfigs", "use_pumpkin_cookies", self.use_pumpkin_cookies)
        self.pumpkin_cookies_restock = ih.read_int("BotConfigs", "pumpkin_cookies_restock", self.pumpkin_cookies_restock)



       
    #region LineRandomizer
    def _randomize_throttle_timer(self):
        new_time = random.randint(30000, 90000)  # milliseconds
        self.prhase_throttled_timer.SetThrottleTime(new_time)
        self.prhase_throttled_timer.Reset()
        
    def _load_taglines(self, path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Failed to load taglines: {e}")
            return []
    
    def _get_random_tagline(self):
        with open(self.tagline_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        taglines = data.get("taglines", [])
        if not taglines:
            return "Why are you reading this? wheres the config file?."
        return random.choice(taglines)
     
    def GetTagLine(self)-> str:
        if self.prhase_throttled_timer.IsExpired() or not self.current_tagline:
            self._randomize_throttle_timer()
            self.current_tagline = self._get_random_tagline()
            return self.current_tagline
        return self.current_tagline
    
    #endregion
    #region Banner

    def GetBanner(self):
        if self.banner_throttled_timer.IsExpired():
            self.banner_index = (self.banner_index + 1) % len(self.banner_string)
            self.banner_throttled_timer.Reset()
        return self.banner_string[self.banner_index:] + self.banner_string[:self.banner_index]

    #endregion

    #region helpers
    def IsProfessionSupported(self, profession_id: int) -> bool:
        return str(profession_id) in self.supported_professions
    
    def LogMessage(self, message: str, extra_info: Optional[str] = None, severity: LogConsole.LogSeverity = LogConsole.LogSeverity.INFO):
        """Log a message to the console."""
        if not self.console:
            return
        self.console.LogMessage(message, extra_info, severity)

        match severity:
            case LogConsole.LogSeverity.INFO:
                console_severity = Py4GW.Console.MessageType.Info
            case LogConsole.LogSeverity.WARNING:
                console_severity = Py4GW.Console.MessageType.Warning
            case LogConsole.LogSeverity.ERROR:
                console_severity = Py4GW.Console.MessageType.Error
            case LogConsole.LogSeverity.CRITICAL:
                console_severity = Py4GW.Console.MessageType.Performance
            case LogConsole.LogSeverity.SUCCESS:
                console_severity = Py4GW.Console.MessageType.Success
            case _:
                console_severity = Py4GW.Console.MessageType.Info
            
        ConsoleLog(f"{self.name}", f"{message} - {extra_info}", console_severity,log= self.detailed_logging)
        
    def LogDetailedMessage(self, message: str, extra_info: Optional[str] = None, severity: LogConsole.LogSeverity = LogConsole.LogSeverity.INFO):
        if self.detailed_logging:
            """Log a detailed message to the console."""
            self.LogMessage(message, extra_info, severity)
     
    def SetCurrentStep(self, step_name: str, step_weight: float = 1.0):
        """
        Set the current step in the progress tracker.
        This will finalize the previous step and start a new one.
        """
        self.progress_tracker.set_step(step_name, step_weight)
        self.state = self.progress_tracker.get_step_name()
        self.state_percentage = 0.0
        self.overall_progress = self.progress_tracker.get_overall_progress()       

    def AdvanceProgress(self, percent: float):
        """
        Advance the progress of the current step.
        Percent should be between 0.0 and 1.0.
        """
        if percent < 0.0 or percent > 1.0:
            percent = max(0.0, min(percent, 1.0))  # Clamp to valid range
        
        self.progress_tracker.update_progress(percent)
        self.state_percentage = self.progress_tracker.state_percentage
        self.overall_progress = self.progress_tracker.get_overall_progress()

    def ResetCurrentProgress(self):
        """
        Reset the current step's progress to 0%.
        """
        self.progress_tracker.reset()
        self.state_percentage = 0.0
        self.overall_progress = self.progress_tracker.get_overall_progress()




#region OptionsWindow
    def DrawOptionsWindow(self):
        self.option_window_module.initialize()
        border = self.option_window_snapped_border.lower()
        if border == "right":
            snapped_x = self.main_window_pos[0] + self.main_window_size[0] + 1
            snapped_y = self.main_window_pos[1]
        elif border == "left":
            snapped_x = self.main_window_pos[0] - self.option_window_size[0] - 1
            snapped_y = self.main_window_pos[1]
        elif border == "top":
            snapped_x = self.main_window_pos[0]
            snapped_y = self.main_window_pos[1] - self.option_window_size[1] - 1
        elif border == "bottom":
            snapped_x = self.main_window_pos[0]
            snapped_y = self.main_window_pos[1] + self.main_window_size[1] + 1
        else:
            # Fallback to right
            snapped_x = self.main_window_pos[0] + self.main_window_size[0] + 1
            snapped_y = self.main_window_pos[1]

        if self.option_window_snapped:
            PyImGui.set_next_window_pos(snapped_x, snapped_y)
        
        if self.option_window_module.begin():
            if PyImGui.begin_child("YAVB Options Child Window", (300, 250), True, PyImGui.WindowFlags.NoFlag):
                if PyImGui.collapsing_header("Looting Options"):
                    PyImGui.text_wrapped("Looting is handled by the Looting Manager Widget, configure it there.")
                PyImGui.separator()
                if PyImGui.collapsing_header("ID & Salvage Options"):
                    PyImGui.text_wrapped("ID & Salvage is handled by AutoHandler Module of the Inventory+ Widget. Configure it there.")
                if PyImGui.collapsing_header("Merchant Options"):
                    PyImGui.text_wrapped("After inventory AutoHandler has finished, all remaining items are sent to the Merchant for id/selling.")
                    PyImGui.separator()
                    PyImGui.push_item_width(100)
                    self.identification_kits_restock = PyImGui.input_int("ID Kits to Restock", self.identification_kits_restock)
                    ImGui.show_tooltip("ID Kits to Restock")
                    self.salvage_kits_restock = PyImGui.input_int("Salvage Kits to Restock", self.salvage_kits_restock)
                    ImGui.show_tooltip("Salvage Kits to Restock")
                    self.keep_empty_inventory_slots = PyImGui.input_int("Keep Empty Inventory Slots", self.keep_empty_inventory_slots)
                    ImGui.show_tooltip("Keep Empty Inventory Slots")
                    PyImGui.pop_item_width()
                    
                if PyImGui.collapsing_header("Bot Options"):
                    self.use_cupcakes = PyImGui.checkbox("Use Cupcakes", self.use_cupcakes)
                    ImGui.show_tooltip("Withdraw 1 cupcake from inventory and use it for traversing Bjora Marches")
                    self.use_pumpkin_cookies = PyImGui.checkbox("Use Pumpkin Cookies", self.use_pumpkin_cookies)
                    ImGui.show_tooltip("Use Pumpkin Cookies for clearing Death Penalty in case of death.")
                    self.pumpkin_cookies_restock = PyImGui.input_int("Pumpkin Cookies Restock", self.pumpkin_cookies_restock)
                    ImGui.show_tooltip("Number of Pumpkin Cookies to keep in inventory.")
                
                
                PyImGui.end_child()
            
            self.option_window_module.process_window()
            self.option_window_pos = PyImGui.get_window_pos()
            self.option_window_size = PyImGui.get_window_size() 
        self.option_window_module.end()

#endregion

     
   
#region MainWindow
    def DrawMainWindow(self):
        self.window_module.initialize()
        if self.window_module.begin():
            if PyImGui.begin_menu_bar():
                # Direct clickable item on the menu bar
                if PyImGui.begin_menu("File"):
                    # Items inside the File menu
                    if PyImGui.menu_item("Save Config"):
                        self.save_config()
                        self.LogMessage("Configuration saved", "", LogConsole.LogSeverity.SUCCESS)
                    if PyImGui.menu_item("Load Config"):
                        self.load_config()
                        self.LogMessage("Configuration loaded", "", LogConsole.LogSeverity.SUCCESS)
                    PyImGui.end_menu()
                if PyImGui.begin_menu("Options"):
                    self.option_window_visible = PyImGui.checkbox("Show window", self.option_window_visible)
                    self.option_window_snapped = PyImGui.checkbox("Snapped", self.option_window_snapped)
                    if self.option_window_snapped:
                        snap_directions = ["Right", "Left", "Bottom"]
                        current_index = snap_directions.index(self.option_window_snapped_border)
                        selected_index = PyImGui.combo("Snap Direction", current_index, snap_directions)
                        self.option_window_snapped_border = snap_directions[selected_index]
                    PyImGui.end_menu()

                # Dropdown menu called "Console"
                if PyImGui.begin_menu("Console"):
                    # Items inside the Console submenu
                    self.console_visible = PyImGui.checkbox("Show Console", self.console_visible)
                    prev_value = self.console_log_to_file
                    self.console_log_to_file = PyImGui.checkbox("Log to File", self.console_log_to_file)
                    if prev_value != self.console_log_to_file:
                        self.console.SetLogToFile(self.console_log_to_file)
                    ImGui.show_tooltip("Feature WIP, not implemented yet.")
                    
                    prev_value = self.detailed_logging
                    self.detailed_logging = PyImGui.checkbox("Detailed Logging", self.detailed_logging)
                    if prev_value != self.detailed_logging:
                        self.LogDetailedMessage("Detailed logging",f"{'ENABLED' if self.detailed_logging else 'DISABLED'}.", LogConsole.LogSeverity.INFO)
                    ImGui.show_tooltip("Will output Extra Info to the YAVB Console,\nWill output Full Logging to the Py4GWConsole.")
                    
                    prev_value = self.console_snapped
                    self.console_snapped = PyImGui.checkbox("Snapped", self.console_snapped)
                    if prev_value != self.console_snapped:
                        self.console.SetSnapped(self.console_snapped, self.console_snapped_border)
                    
                    if self.console_snapped:
                        prev_value = self.console_snapped_border
                        snap_directions = ["Right", "Left", "Bottom"]
                        current_index = snap_directions.index(self.console_snapped_border)
                        selected_index = PyImGui.combo("Snap Direction", current_index, snap_directions)
                        self.console_snapped_border = snap_directions[selected_index]
                        if prev_value != self.console_snapped_border:
                            self.console.SetSnapped(self.console_snapped, self.console_snapped_border)

                    PyImGui.end_menu()

                PyImGui.end_menu_bar()
            
            
            child_width = 300
            child_height = 275
            if PyImGui.begin_child("YAVB Child Window",(child_width, child_height), True, PyImGui.WindowFlags.NoFlag):
                table_flags = PyImGui.TableFlags.RowBg | PyImGui.TableFlags.BordersOuterH
                if PyImGui.begin_table("YAVBtoptable", 2, table_flags):
                    iconwidth = 64
                    PyImGui.table_setup_column("Icon", PyImGui.TableColumnFlags.WidthFixed, iconwidth)
                    PyImGui.table_setup_column("titles", PyImGui.TableColumnFlags.WidthFixed, child_width - iconwidth)
                    PyImGui.table_next_row()
                    PyImGui.table_set_column_index(0)
                    ImGui.DrawTexture(self.icon, width=64, height=64)
                    PyImGui.table_set_column_index(1)
                    if PyImGui.begin_table("YAVB Info", 1, PyImGui.TableFlags.NoFlag):
                        PyImGui.table_next_row()
                        PyImGui.table_set_column_index(0)
                        PyImGui.text_scaled(f"{self.GetBanner()}", Color(255, 255, 0, 255).to_tuple_normalized(), 1.4)
                        PyImGui.table_next_row()
                        PyImGui.table_set_column_index(0)
                        PyImGui.text_wrapped(f"{self.GetTagLine()}")
                        PyImGui.end_table()
                    PyImGui.end_table()
                    
                    map_valid = Routines.Checks.Map.MapValid()
                    if map_valid:
                        self.primary_profession, self.secondary_profession = GLOBAL_CACHE.Agent.GetProfessionIDs(GLOBAL_CACHE.Player.GetAgentID())
                        self.prof_supported = self.IsProfessionSupported(self.primary_profession)
                    
                    
                    if not self.prof_supported:
                        if PyImGui.begin_table("YAVB maintable", 1, PyImGui.TableFlags.NoFlag):
                            PyImGui.table_next_row()
                            PyImGui.table_set_column_index(0)
                            color = Color(250, 100, 0, 255).to_tuple_normalized()

                            PyImGui.push_style_color(PyImGui.ImGuiCol.Text, color)
                            PyImGui.text_wrapped(
                                f"Your profession {Profession(self.primary_profession).name.upper()} is not currently supported by this script.\n\n"
                                "Switch to a character with one of the following supported professions:"
                            )
                            PyImGui.pop_style_color(1)
                            for prof_id in self.supported_professions.keys():
                                if not prof_id.isdigit():
                                    continue  # Skip non-integer keys

                                prof = Profession(int(prof_id))
                                PyImGui.text(f"{prof.name.upper()}")

                                
                                
                            PyImGui.end_table()
                    else:
                        if PyImGui.begin_table("YAVB maintable", 1, PyImGui.TableFlags.NoFlag):
                            PyImGui.table_next_row()
                            PyImGui.table_set_column_index(0)
                            if PyImGui.begin_tab_bar("YAVB Tabs"):
                                if PyImGui.begin_tab_item("Main"):
                                    icon = IconsFontAwesome5.ICON_CIRCLE
                                    if self.script_running and not self.script_paused:
                                        icon = IconsFontAwesome5.ICON_PAUSE_CIRCLE
                                    if self.script_running and self.script_paused:
                                        icon = IconsFontAwesome5.ICON_PLAY_CIRCLE
                                    if not self.script_running:
                                        icon = IconsFontAwesome5.ICON_PLAY_CIRCLE
                                        
                                    if PyImGui.button(icon +  "##Playbutton"):
                                        if self.script_running:
                                            if self.script_paused:
                                                self.FSM.resume()
                                                self.script_paused = False
                                                self.LogDetailedMessage("Script resumed", "", LogConsole.LogSeverity.INFO)
                                                self.state = "Running"
                                            else:
                                                self.FSM.pause()
                                                self.script_paused = True
                                                self.LogDetailedMessage("Script paused", "", LogConsole.LogSeverity.INFO) 
                                                self.state = "Paused"
                                        else:
                                            self.script_running = True
                                            self.script_paused = False
                                            
                                            self.LogDetailedMessage("Script started", "", LogConsole.LogSeverity.INFO)
                                            self.state = "Running"
                                            
                                            self.FSM.restart()
                                            
                                    PyImGui.same_line(0,-1)
                                    
                                    #change button to grey if script is not running
                                    if not self.script_running:
                                        PyImGui.push_style_color(PyImGui.ImGuiCol.Button, Color(50, 50, 50, 255).to_tuple_normalized())
                                        PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, Color(70, 70, 70, 255).to_tuple_normalized())
                                        PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonActive, Color(90, 90, 90, 255).to_tuple_normalized())
                                        PyImGui.push_style_color(PyImGui.ImGuiCol.Text, Color(70, 70, 70, 255).to_tuple_normalized())
                                        
                                    
                                    
                                    if PyImGui.button(IconsFontAwesome5.ICON_STOP_CIRCLE + "##Stopbutton"):
                                        if self.script_running:
                                            self.FSM.stop()
                                            self.script_running = False
                                            self.script_paused = False
                                            self.LogDetailedMessage("Script stopped", "", LogConsole.LogSeverity.INFO)
                                            self.state = "Idle"
                                            
                                    if not self.script_running:
                                        PyImGui.pop_style_color(4)
                                        
                                    PyImGui.same_line(0,-1)
                                    PyImGui.text(f"State: {self.state}")
                                    PyImGui.separator()
                                    PyImGui.text("Step Progress")
                                    PyImGui.push_item_width(child_width - 10)
                                    PyImGui.progress_bar(self.state_percentage, (child_width - 10), 0, f"{self.state_percentage * 100:.2f}%")
                                    PyImGui.pop_item_width()
                                    PyImGui.separator()
                                    PyImGui.text("Overall Progress")
                                    PyImGui.push_item_width(child_width - 10)
                                    PyImGui.progress_bar(self.overall_progress, (child_width - 10), 0, f"{self.overall_progress * 100:.2f}%")   
                                    PyImGui.pop_item_width()
                                                
                                    PyImGui.end_tab_item()
                                
                                if PyImGui.begin_tab_item("Statistics"):
                                    PyImGui.text("Statistics")
                                    PyImGui.separator()
                                    
                                    if self.running_to_jaga:
                                        current_run = self.run_to_jaga_stats.GetCurrentRun()
                                    else:
                                        current_run = self.farming_stats.GetCurrentRun()
                                     
                                    def format_duration(seconds: float) -> str:
                                        minutes = int(seconds // 60)
                                        secs = int(seconds % 60)
                                        millis = int((seconds - int(seconds)) * 1000)
                                        return f"{minutes:02}:{secs:02}:{millis:03}"  
                                     
                                    if not self.current_run_node:
                                        self.current_run_node = RunStatistics.RunNode()
                                        
                                    if current_run:
                                        self.current_run_node = current_run
                                        
                                    current_run = self.current_run_node 
                                    PyImGui.text(f"Run Start Time: {current_run.start_time.strftime('%H:%M:%S')}")
                                    PyImGui.text(f"Run Duration: {format_duration(current_run.GetRunDuration())}")
                                    quickest = self.farming_stats.GetQuickestRun()
                                    run_time = quickest.GetRunDuration() if quickest else 0
                                    PyImGui.text(f"Quickest Run: {format_duration(run_time)}")
                                    longest = self.farming_stats.GetLongestRun()
                                    run_time = longest.GetRunDuration() if longest else 0
                                    PyImGui.text(f"Longest Run: {format_duration(run_time)}")
                                    avg_duration = self.farming_stats.GetAverageRunDuration()
                                    PyImGui.text(f"Average Run Duration: {format_duration(avg_duration)}")
                                    PyImGui.text(f"Total Runs: {self.farming_stats.GetTotalRuns()}")
                                    PyImGui.text(f"Failed Runs: {self.farming_stats.GetTotalFailures()}")
                                    PyImGui.text(f"Run Effectivity: {self.farming_stats.GetRuneffectivity():.2f}%")
                                    PyImGui.text(f"Kill Effectivity: {self.farming_stats.GetKillEffectivity():.2f}%")
                                    PyImGui.text(f"Avg Kills on Success: {self.farming_stats.GetAverageKillsOnSuccess():.2f}")
                                        

                                    
                                    
                            PyImGui.end_table()
                        
                PyImGui.end_child()
            
            self.window_module.process_window()            
        self.window_module.end()
#endregion

#region FSM
    class _FSM_Helpers:

        def __init__(self, parent: "YAVB"):
            self._parent = parent
            
        def _init_build(self):
            self._parent.build = ShawowFormAssassinVaettir()
            
        def _stop_execution(self):
            if self._parent.script_running:
                self._parent.script_running = False
                self._parent.script_paused = False
                self._parent.in_killing_routine = False
                self._parent.finished_routine = False
                if self._parent.build is not None:
                    build = self._parent.build  # now Pylance sees it as non-Optional
                    build.SetKillingRoutine(self._parent.in_killing_routine)
                    build.SetRoutineFinished(self._parent.finished_routine)
                self._parent.LogMessage("Script stopped", "", LogConsole.LogSeverity.INFO)
                self._parent.state = "Idle"
                self._parent.FSM.reset()
                
                build = self._parent.build or ShawowFormAssassinVaettir()
                GLOBAL_CACHE.Coroutines.clear()  # Clear all coroutines
                """
                if build.ProcessSkillCasting() in GLOBAL_CACHE.Coroutines:
                    GLOBAL_CACHE.Coroutines.remove(build.ProcessSkillCasting())
                if self._parent.HandleStuckBjoraMarches() in GLOBAL_CACHE.Coroutines:
                    GLOBAL_CACHE.Coroutines.remove(self._parent.HandleStuckBjoraMarches())
                if self._parent.HandleStuckJagaMoraine() in GLOBAL_CACHE.Coroutines:
                    GLOBAL_CACHE.Coroutines.remove(self._parent.HandleStuckJagaMoraine())
                """
            yield from Routines.Yield.wait(100)
            
        def _reset_execution(self):
            if self._parent.script_running:
                self._parent.in_killing_routine = False
                self._parent.finished_routine = False
                if self._parent.build is not None:
                    build = self._parent.build  # now Pylance sees it as non-Optional
                    build.SetKillingRoutine(self._parent.in_killing_routine)
                    build.SetRoutineFinished(self._parent.finished_routine)
                self._parent.LogMessage("Script reset", "", LogConsole.LogSeverity.INFO)
                self._parent.state = "Idle"
                self._parent.FSM.restart()
                
                build = self._parent.build or ShawowFormAssassinVaettir()
                GLOBAL_CACHE.Coroutines.clear()  # Clear all coroutines
                """
                if build.ProcessSkillCasting() in GLOBAL_CACHE.Coroutines:
                    GLOBAL_CACHE.Coroutines.remove(build.ProcessSkillCasting())
                if self._parent.HandleStuckBjoraMarches() in GLOBAL_CACHE.Coroutines:
                    GLOBAL_CACHE.Coroutines.remove(self._parent.HandleStuckBjoraMarches())
                if self._parent.HandleStuckJagaMoraine() in GLOBAL_CACHE.Coroutines:
                    GLOBAL_CACHE.Coroutines.remove(self._parent.HandleStuckJagaMoraine())
                """
                    
                self._parent.farming_stats.EndCurrentRun(failed= True, deaths= 1)
                
            yield from Routines.Yield.wait(100)
            
        def _send_message(self,message:SharedCommandType, params: tuple = ()):
            account_email = GLOBAL_CACHE.Player.GetAccountEmail()
            GLOBAL_CACHE.ShMem.SendMessage(account_email,account_email, message, params)
            
        def _get_materials_to_sell(self):
            bags_to_check = GLOBAL_CACHE.ItemArray.CreateBagList(1, 2, 3, 4)
            bag_item_array = GLOBAL_CACHE.ItemArray.GetItemArray(bags_to_check)
            materials_to_sell = ItemArray.Filter.ByCondition(bag_item_array, lambda item_id: GLOBAL_CACHE.Item.Type.IsMaterial(item_id))
            return materials_to_sell
        
        def _get_number_of_id_kits_to_buy(self):
            count_of_id_kits = GLOBAL_CACHE.Inventory.GetModelCount(ModelID.Superior_Identification_Kit.value)
            if count_of_id_kits < self._parent.identification_kits_restock:
                return self._parent.identification_kits_restock - count_of_id_kits
            return 0
        
        def _get_number_of_salvage_kits_to_buy(self):
            count_of_salvage_kits = GLOBAL_CACHE.Inventory.GetModelCount(ModelID.Salvage_Kit.value)
            if count_of_salvage_kits < self._parent.salvage_kits_restock:
                return self._parent.salvage_kits_restock - count_of_salvage_kits
            return 0
        
        def _get_unidentified_items(self):
            bags_to_check = GLOBAL_CACHE.ItemArray.CreateBagList(1, 2, 3, 4)
            bag_item_array = GLOBAL_CACHE.ItemArray.GetItemArray(bags_to_check)
            unidentified_items = ItemArray.Filter.ByCondition(bag_item_array, lambda item_id: not (GLOBAL_CACHE.Item.Usage.IsIdentified(item_id)))
            white_items = ItemArray.Filter.ByCondition(bag_item_array, lambda item_id: GLOBAL_CACHE.Item.Rarity.IsWhite(item_id) and not GLOBAL_CACHE.Item.Usage.IsIdentified(item_id))
            unidentified_items = [item for item in unidentified_items if item not in white_items]  # Remove white items from unidentified items
            
            return unidentified_items if len(unidentified_items) > 0 else []
        
        def _get_items_to_salvage(self):
            bags_to_check = GLOBAL_CACHE.ItemArray.CreateBagList(1, 2, 3, 4)
            bag_item_array = GLOBAL_CACHE.ItemArray.GetItemArray(bags_to_check)
            white_items_to_salvage = ItemArray.Filter.ByCondition(bag_item_array, lambda item_id: GLOBAL_CACHE.Item.Usage.IsSalvageable(item_id) and GLOBAL_CACHE.Item.Rarity.IsWhite(item_id))
            items_to_salvage = ItemArray.Filter.ByCondition(bag_item_array, lambda item_id: GLOBAL_CACHE.Item.Usage.IsSalvageable(item_id) and GLOBAL_CACHE.Item.Usage.IsIdentified(item_id))
            items_to_salvage.extend(white_items_to_salvage)
            #remove duplicates
            items_to_salvage = list(set(items_to_salvage))
            return items_to_salvage
            
        def _inventory_handling_checks(self):
            free_slots_in_inventory = GLOBAL_CACHE.Inventory.GetFreeSlotCount()
            if free_slots_in_inventory < self._parent.keep_empty_inventory_slots:
                return True
            count_of_id_kits = GLOBAL_CACHE.Inventory.GetModelCount(ModelID.Superior_Identification_Kit.value)
            if count_of_id_kits < self._parent.identification_kits_restock:
                return True
            count_of_salvage_kits = GLOBAL_CACHE.Inventory.GetModelCount(ModelID.Salvage_Kit.value) #2992 model for salvage kit
            if count_of_salvage_kits < self._parent.salvage_kits_restock:
                return True
            
            
            materials_to_sell = self._get_materials_to_sell()
            if len(materials_to_sell) > 0:
                return True
            
            unidentified_items = self._get_unidentified_items()
            if len(unidentified_items) > 0:
                return True
            
            items_to_salvage = self._get_items_to_salvage()
            if len(items_to_salvage) > 0:
                return True
            
            return False
        
        def _movement_eval_exit_on_map_loading(self):
            if GLOBAL_CACHE.Map.IsMapLoading():
                return True
            
            if not self._parent.script_running:
                return True
            
            return False
        
        def _movement_eval_exit_on_map_loading_or_death(self):
            if GLOBAL_CACHE.Map.IsMapLoading():
                return True
            
            if not self._parent.script_running:
                return True
            
            if GLOBAL_CACHE.Agent.IsDead(GLOBAL_CACHE.Player.GetAgentID()):
                return True
            
            return False
            
        def TravelToLongeyesLedge(self):
            self._parent.SetCurrentStep("Travel to Longeyes Ledge",0.02)
            current_map = GLOBAL_CACHE.Map.GetMapID()
            if current_map != self._parent.LONGEYES_LEDGE:
                self._parent.AdvanceProgress(0.5)
                self._parent.LogMessage("Map Check", "Traveling to Longeyes Ledge", LogConsole.LogSeverity.INFO)
                if not (yield from Routines.Yield.Map.TravelToOutpost(self._parent.LONGEYES_LEDGE, log=self._parent.detailed_logging)):
                    self._parent.LogMessage("Failed to travel to Longeyes Ledge", "TIMEOUT", LogConsole.LogSeverity.ERROR)
                    yield from self._stop_execution()
            else:
                self._parent.LogDetailedMessage("Map Check", "Already at Longeyes Ledge", LogConsole.LogSeverity.INFO)
            
            
        def ActivateInventoryHandler(self):
            self._parent.SetCurrentStep("Activate Inventory+ AutoHandler", 0.02)
            if not self._parent.inventory_handler.module_active:
                self._parent.AdvanceProgress(0.5)
                self._parent.LogMessage("Inventory+ AutoHandler", "Forcing Activation", LogConsole.LogSeverity.INFO)
                self._parent.inventory_handler.module_active = True
            self._parent.LogDetailedMessage("Sleeping", "Waiting for Inventory+ AutoHandler to finish.", LogConsole.LogSeverity.INFO)   

            
        def DeactivateHeroAI(self):
            self._parent.SetCurrentStep("Deactivate Hero AI", 0.02)
            self._send_message(SharedCommandType.DisableHeroAI,(0,0,0,0))
            self._parent.LogMessage("HeroAI", "Disabled.", LogConsole.LogSeverity.INFO)
            
        def LoadSkillBar(self):
            if not self._parent.build:
                self._init_build()
            build = self._parent.build or ShawowFormAssassinVaettir()
            self._parent.SetCurrentStep("Load Skill Bar", 0.02)
            self._parent.LogMessage("Loading Skill Bar", f"{build.build_name}.", LogConsole.LogSeverity.INFO)
            yield from build.LoadSkillBar()
            self._parent.AdvanceProgress(0.33)
            if not (yield from build.ValidateSkills()):
                self._parent.AdvanceProgress(0.66)
                self._parent.LogMessage("Skillbar validation", "FAILED, Check your skillbar configuration.", LogConsole.LogSeverity.ERROR)
                yield from self._stop_execution()
            else:
                self._parent.AdvanceProgress(0.66)
                self._parent.LogDetailedMessage("Skillbar validation", "PASSED.", LogConsole.LogSeverity.SUCCESS)
                
        def InventoryHandling(self):
            #Inventory Handling
            self._parent.SetCurrentStep("Inventory Handling", 0.12)
            progress = 0.0
            for cycle in range(2):
                if self._inventory_handling_checks():
                    progress += 0.8
                    self._parent.AdvanceProgress(progress)
                    self._parent.LogMessage("Inventory Handling", "checks failed, starting Inventory handling", LogConsole.LogSeverity.INFO)
                    yield from Routines.Yield.Agents.InteractWithAgentXY(-23110, 14942)
                    progress += 0.8
                    self._parent.AdvanceProgress(progress)
                    if len(self._get_materials_to_sell()) > 0:
                        self._parent.LogMessage("Inventory Handling", f"Selling Materials to make Space", LogConsole.LogSeverity.INFO)
                        yield from Routines.Yield.Merchant.SellItems(self._get_materials_to_sell(), log=self._parent.detailed_logging)
                    else:
                        self._parent.LogDetailedMessage("Inventory Handling", "No Materials to Sell, skipping.", LogConsole.LogSeverity.INFO)
                    progress += 0.8
                    self._parent.AdvanceProgress(progress)
                    if self._get_number_of_id_kits_to_buy() > 0:
                        self._parent.LogMessage("Inventory Handling", "Restocking ID Kits", LogConsole.LogSeverity.INFO)
                        yield from Routines.Yield.Merchant.BuyIDKits(self._get_number_of_id_kits_to_buy(),log=self._parent.detailed_logging)
                    else:
                        self._parent.LogDetailedMessage("Inventory Handling", "No ID Kits to Restock, skipping.", LogConsole.LogSeverity.INFO)
                    progress += 0.8
                    self._parent.AdvanceProgress(progress)
                    if self._get_number_of_salvage_kits_to_buy() > 0:
                        self._parent.LogMessage("Inventory Handling", "Restocking Salvage Kits", LogConsole.LogSeverity.INFO)
                        yield from Routines.Yield.Merchant.BuySalvageKits(self._get_number_of_salvage_kits_to_buy(),log=self._parent.detailed_logging)
                    else:
                        self._parent.LogDetailedMessage("Inventory Handling", "No Salvage Kits to Restock, skipping.", LogConsole.LogSeverity.INFO)
                    progress += 0.8
                    self._parent.AdvanceProgress(progress)
                    if len(self._get_unidentified_items()) > 0:
                        self._parent.LogMessage("Inventory Handling", "Identifying Items", LogConsole.LogSeverity.INFO)
                        yield from Routines.Yield.Items.IdentifyItems(self._get_unidentified_items(), log=self._parent.detailed_logging)
                    else:
                        self._parent.LogDetailedMessage("Inventory Handling", "No Unidentified Items, skipping.", LogConsole.LogSeverity.INFO)
                    progress += 0.8
                    self._parent.AdvanceProgress(progress)
                    if len(self._get_items_to_salvage()) > 0:
                        self._parent.LogMessage("Inventory Handling", "Salvaging Items", LogConsole.LogSeverity.INFO)
                        yield from Routines.Yield.Items.SalvageItems(self._get_items_to_salvage(), log=self._parent.detailed_logging)
                    else:
                        self._parent.LogDetailedMessage("Inventory Handling", "No Items to Salvage, skipping.", LogConsole.LogSeverity.INFO)   
                else:
                    self._parent.LogDetailedMessage("Inventory Handling", "No Inventory Handling needed, skipping.", LogConsole.LogSeverity.SUCCESS)
                    break
                    
            
        def WitdrawBirthdayCupcake(self):
            self._parent.SetCurrentStep("Withdraw Cupcake", 0.02)
            if self._parent.use_cupcakes and GLOBAL_CACHE.Inventory.GetModelCountInStorage(ModelID.Birthday_Cupcake.value) > 0:
                self._parent.LogMessage("Cupcake Usage", "Withdraw (1) Cupcake from Inventory", LogConsole.LogSeverity.INFO)
                items_witdrawn = GLOBAL_CACHE.Inventory.WithdrawItemFromStorageByModelID(ModelID.Birthday_Cupcake.value, 1)
                self._parent.AdvanceProgress(0.5)
                if not items_witdrawn:
                    self._parent.LogDetailedMessage("Cupcake Usage", "Failed to withdraw Cupcake from Storage", LogConsole.LogSeverity.ERROR)
                yield from Routines.Yield.wait(150)
            else:
                self._parent.LogDetailedMessage("Cupcake Usage", "No Cupcakes in Storage, skipping.", LogConsole.LogSeverity.WARNING)
                
        def WitdrawPumpkinCookie(self):
            self._parent.SetCurrentStep("Withdraw Pumpkin Cookie", 0.02)
            if self._parent.use_pumpkin_cookies:
                cookies_in_inventory = GLOBAL_CACHE.Inventory.GetModelCount(ModelID.Pumpkin_Cookie.value)
                cookies_to_restock = self._parent.pumpkin_cookies_restock
                
                total_needed_cookies = cookies_to_restock - cookies_in_inventory
                if total_needed_cookies < 0:    
                    total_needed_cookies = 0
                
                if total_needed_cookies > 0:
                    self._parent.LogDetailedMessage("Pumpkin Cookie", f"Withdrawing {total_needed_cookies} Cookies from Storage", LogConsole.LogSeverity.INFO)
                    items_witdrawn = GLOBAL_CACHE.Inventory.WithdrawItemFromStorageByModelID(ModelID.Pumpkin_Cookie.value, total_needed_cookies)
                    self._parent.AdvanceProgress(0.5)
                    if not items_witdrawn:
                        self._parent.LogDetailedMessage("Pumpkin Cookie", "Failed to withdraw Pumpkin Cookies from Storage", LogConsole.LogSeverity.ERROR)
                    yield from Routines.Yield.wait(150)
                else:
                    self._parent.LogDetailedMessage("Pumpkin Cookie", "Already have enough Pumpkin Cookies in Inventory, skipping.", LogConsole.LogSeverity.INFO)
            else:
                self._parent.LogDetailedMessage("Pumpkin Cookie", "No Pumpkin Cookies in Storage, skipping.", LogConsole.LogSeverity.WARNING)

        def SetHardMode(self):
            self._parent.SetCurrentStep("Set Hard Mode", 0.02)
            if GLOBAL_CACHE.Party.IsHardModeUnlocked():
                self._parent.LogDetailedMessage("Hard Mode", "Hard Mode is unlocked, setting up for Hard Mode.", LogConsole.LogSeverity.INFO)
                if not GLOBAL_CACHE.Party.IsHardMode():
                    self._parent.LogMessage("Hard Mode", "Switching to Hard Mode.", LogConsole.LogSeverity.INFO)
                    yield from Routines.Yield.Map.SetHardMode(log=self._parent.detailed_logging)
                    self._parent.AdvanceProgress(0.5)
                else:
                    self._parent.LogMessage("Hard Mode", "Already in Hard Mode.", LogConsole.LogSeverity.INFO)
            else:
                self._parent.LogDetailedMessage("Hard Mode", "Hard Mode is not unlocked.", LogConsole.LogSeverity.INFO)
   
        def LeaveOutpost(self):
            self._parent.SetCurrentStep("Leave Outpost", 0.04)
            self._parent.LogMessage("Leaving Outpost", "Longeyes Ledge", LogConsole.LogSeverity.INFO)
            success_movement = yield from Routines.Yield.Movement.FollowPath(path_points= path_points_to_leave_outpost, 
                                                                             custom_exit_condition=lambda: self._movement_eval_exit_on_map_loading(),
                                                                             log=False,
                                                                             progress_callback=self._parent.AdvanceProgress)
            if not success_movement and not GLOBAL_CACHE.Map.IsMapLoading():
                self._parent.LogMessage("Failed to leave outpost", "TIMEOUT", LogConsole.LogSeverity.ERROR)
                yield from self._stop_execution()
                
        def WaitforBjoraMarchesMapLoad(self):
            self._parent.SetCurrentStep("Wait for Bjora Marches Map Load", 0.02)
            self._parent.LogMessage("Waiting for Map Loading", "Bjora Marches", LogConsole.LogSeverity.INFO)
            wait_of_map_load = yield from Routines.Yield.Map.WaitforMapLoad(self._parent.BJORA_MARCHES, log=self._parent.detailed_logging)
            if not wait_of_map_load:
                self._parent.LogMessage("Map Load", "Timeout Loading Bjora Marches, stopping script.", LogConsole.LogSeverity.ERROR)
                yield from self._stop_execution()
            yield from Routines.Yield.wait(1000)  # Wait a bit to ensure the mobs start moving
                
        def AddBjoraMarchesCoroutine(self):
            self._parent.finished_routine = False
            self._parent.in_killing_routine = False
            self._parent.running_to_jaga = True
            self._parent.run_to_jaga_stats.StartNewRun()
            self._parent.SetCurrentStep("Add Bjora Marches Coroutine", 0.02)
            GLOBAL_CACHE.Coroutines.append(self._parent.HandleStuckBjoraMarches())
            self._parent.LogDetailedMessage("Stuck Coroutine", "Added to Bjora Marches Coroutines.", LogConsole.LogSeverity.INFO)

        def RemoveBjoraMarchesCoroutine(self):
            self._parent.running_to_jaga = False
            self._parent.SetCurrentStep("Remove Bjora Marches Coroutine", 0.02)
            if self._parent.HandleStuckBjoraMarches() in GLOBAL_CACHE.Coroutines:
                GLOBAL_CACHE.Coroutines.remove(self._parent.HandleStuckBjoraMarches())
            self._parent.LogDetailedMessage("Stuck Coroutine", "Removed from Bjora Marches Coroutines.", LogConsole.LogSeverity.INFO)
        
        def SetNornTitle(self):
            self._parent.SetCurrentStep("Set Norn Title", 0.02)
            self._parent.LogMessage("Title", "Setting PVE Norn Title", LogConsole.LogSeverity.INFO)
            yield from Routines.Yield.Player.SetTitle(TitleID.Norn.value, log=self._parent.detailed_logging)  
            
        def UseCupcake(self):
            self._parent.SetCurrentStep("Use Cupcake", 0.02)
            if self._parent.use_cupcakes:
                self._parent.LogMessage("Cupcake Usage", "Using Cupcake for Bjora Marches Traversal", LogConsole.LogSeverity.INFO)
                self._send_message(SharedCommandType.PCon,(ModelID.Birthday_Cupcake.value, GLOBAL_CACHE.Skill.GetID("Birthday_Cupcake_skill"), 0, 0))
                
        def TraverseBjoraMarches(self):
            self._parent.SetCurrentStep("Traverse Bjora Marches", 0.62)
            self._parent.LogMessage("Traverse", "Traversing Bjora Marches", LogConsole.LogSeverity.INFO)
            success_movement = yield from Routines.Yield.Movement.FollowPath(
                        path_points= path_points_to_traverse_bjora_marches, 
                        custom_exit_condition=lambda: self._movement_eval_exit_on_map_loading_or_death(),
                        log=False,
                        timeout=600000, # 10 minutes timeout
                        progress_callback=self._parent.AdvanceProgress)   
            if not success_movement:
                yield from Routines.Yield.wait(1000)
            if not success_movement and GLOBAL_CACHE.Agent.IsDead(GLOBAL_CACHE.Player.GetAgentID()):
                self._parent.run_to_jaga_stats.EndCurrentRun(failed=True, deaths=1)
                self._parent.running_to_jaga = False
                self._parent.LogMessage("Death", "Player is dead, restarting.", LogConsole.LogSeverity.WARNING)
                yield from Routines.Yield.wait(1000)
                yield from self._reset_execution()
            
            if not success_movement and not GLOBAL_CACHE.Map.IsMapLoading():
                if GLOBAL_CACHE.Map.GetMapID() != self._parent.JAGA_MORAINE:
                    self._parent.running_to_jaga = False
                    self._parent.run_to_jaga_stats.EndCurrentRun(failed=True, stuck_timeouts=1)
                    self._parent.LogMessage("Failed to traverse Bjora Marches", "TIMEOUT", LogConsole.LogSeverity.ERROR)
                    yield from Routines.Yield.wait(1000)
                    yield from self._reset_execution()
                
        def WaitforJagaMoraineMapLoad(self):
            self._parent.LogMessage("Waiting for Map Loading", "Jaga Moraine", LogConsole.LogSeverity.INFO)
            wait_of_map_load = yield from Routines.Yield.Map.WaitforMapLoad(self._parent.JAGA_MORAINE, log=self._parent.detailed_logging)
            if not wait_of_map_load:
                self._parent.LogMessage("Map Load", "Timeout Loading Jaga Moraine, stopping script.", LogConsole.LogSeverity.ERROR)
                self._parent.run_to_jaga_stats.EndCurrentRun(failed=True, stuck_timeouts=1)
                self._parent.running_to_jaga = False
                yield from self._stop_execution()
            self._parent.finished_routine = False
            self._parent.in_killing_routine = False
            self._parent.in_waiting_routine = False
            if self._parent.build is not None:
                    build = self._parent.build  
                    build.SetKillingRoutine(self._parent.in_killing_routine)
                    build.SetRoutineFinished(self._parent.finished_routine)
            self._parent.run_to_jaga_stats.EndCurrentRun()
                    
        def AddSkillCastingCoroutine(self):
            self._parent.farming_stats.StartNewRun()
            GLOBAL_CACHE.Coroutines.append(self._parent.HandleStuckJagaMoraine())
            build = self._parent.build or ShawowFormAssassinVaettir()
            GLOBAL_CACHE.Coroutines.append(build.ProcessSkillCasting())
            self._parent.LogDetailedMessage("Skill Casting Coroutine", "Added to Coroutines.", LogConsole.LogSeverity.INFO)
            
        def RemoveSkillCastingCoroutine(self):
            build = self._parent.build or ShawowFormAssassinVaettir()
            if build.ProcessSkillCasting() in GLOBAL_CACHE.Coroutines:
                GLOBAL_CACHE.Coroutines.remove(build.ProcessSkillCasting())
            if self._parent.HandleStuckJagaMoraine() in GLOBAL_CACHE.Coroutines:
                GLOBAL_CACHE.Coroutines.remove(self._parent.HandleStuckJagaMoraine())
            self._parent.farming_stats.EndCurrentRun(vaettirs_killed=GLOBAL_CACHE.Map.GetFoesKilled())
            self._parent.LogDetailedMessage("Skill Casting Coroutine", "Removed from Coroutines.", LogConsole.LogSeverity.INFO)

        def TakeBounty(self):
            self._parent.ResetCurrentProgress()
            self._parent.SetCurrentStep("Take Bounty", 0.05)
            self._parent.LogMessage("Taking Bounty", "Jaga Moraine", LogConsole.LogSeverity.INFO)
            self._parent.AdvanceProgress(0.33)
            yield from Routines.Yield.Movement.FollowPath(path_points_to_npc, 
                                                          custom_exit_condition=lambda: self._movement_eval_exit_on_map_loading_or_death(),
                                                          timeout=20000
                                                          )
            yield from Routines.Yield.Agents.InteractWithAgentXY(13367, -20771)
            self._parent.AdvanceProgress(0.33)
            yield from Routines.Yield.Player.SendDialog("0x84")
            
        def FarmingRoute1(self):
            self._parent.SetCurrentStep("Farming Route 1", 0.25)
            self._parent.LogMessage("Farming Route", "Starting Farming Route 1", LogConsole.LogSeverity.INFO)
            movement_success = yield from Routines.Yield.Movement.FollowPath(path_points_to_farming_route1,
                                            custom_exit_condition=lambda: self._movement_eval_exit_on_map_loading_or_death(),
                                            progress_callback=self._parent.AdvanceProgress)
            if not movement_success and GLOBAL_CACHE.Agent.IsDead(GLOBAL_CACHE.Player.GetAgentID()):
                self._parent.LogMessage("Death", "Player is dead, restarting.", LogConsole.LogSeverity.WARNING)
                yield from self._reset_execution()
                
        def WaitforLeftAggroBall(self):
            self._parent.LogMessage("Waiting for Left Aggro Ball", "Waiting for enemies to ball up.", LogConsole.LogSeverity.INFO)
            self._parent.SetCurrentStep("Wait for Left Aggro Ball", 0.05)
            self._parent.in_waiting_routine = True
            for i in range(150):
                yield from Routines.Yield.wait(100)
                self._parent.AdvanceProgress((i + 1) / 150.0)
            self._parent.in_waiting_routine = False
            
            if GLOBAL_CACHE.Agent.IsDead(GLOBAL_CACHE.Player.GetAgentID()):
                self._parent.LogMessage("Death", "Player is dead, restarting.", LogConsole.LogSeverity.WARNING)
                yield from self._reset_execution()

        def WaitforRightAggroBall(self):
            self._parent.LogMessage("Waiting for Right Aggro Ball", "Waiting for enemies to ball up.", LogConsole.LogSeverity.INFO)
            self._parent.SetCurrentStep("Wait for Right Aggro Ball", 0.05)
            self._parent.in_waiting_routine = True
            for i in range(150):
                yield from Routines.Yield.wait(100)
                self._parent.AdvanceProgress((i + 1) / 150.0)
            self._parent.in_waiting_routine = False
            
            if GLOBAL_CACHE.Agent.IsDead(GLOBAL_CACHE.Player.GetAgentID()):
                self._parent.LogMessage("Death", "Player is dead, restarting.", LogConsole.LogSeverity.WARNING)
                yield from self._reset_execution()
                
        def FarmingRoute2(self):
            self._parent.SetCurrentStep("Farming Route 2", 0.25)
            self._parent.LogMessage("Farming Route", "Starting Farming Route 2", LogConsole.LogSeverity.INFO)
            movement_success = yield from Routines.Yield.Movement.FollowPath(
                        path_points_to_farming_route2,
                        custom_exit_condition=lambda: self._movement_eval_exit_on_map_loading_or_death(),
                        progress_callback=self._parent.AdvanceProgress)
            if not movement_success and GLOBAL_CACHE.Agent.IsDead(GLOBAL_CACHE.Player.GetAgentID()):
                self._parent.LogMessage("Death", "Player is dead, restarting.", LogConsole.LogSeverity.WARNING)
                yield from self._reset_execution()
                
        def FarmingRoutetoKillSpot(self):
            self._parent.SetCurrentStep("Farming Route to Kill Spot", 0.10)
            self._parent.LogMessage("Farming Route", "Starting Farming Route to Kill Spot", LogConsole.LogSeverity.INFO)
            movement_success = yield from Routines.Yield.Movement.FollowPath(
                        path_points_to_killing_spot,
                        tolerance=25,
                        custom_exit_condition=lambda: self._movement_eval_exit_on_map_loading_or_death(),
                        progress_callback=self._parent.AdvanceProgress)
            if not movement_success and GLOBAL_CACHE.Agent.IsDead(GLOBAL_CACHE.Player.GetAgentID()):
                self._parent.LogMessage("Death", "Player is dead, restarting.", LogConsole.LogSeverity.WARNING)
                yield from self._reset_execution()
                
        def KillEnemies(self):
            self._parent.LogMessage("Killing Routine", "Starting Killing Routine", LogConsole.LogSeverity.INFO)
            self._parent.in_killing_routine = True
            if self._parent.build is not None:
                    build = self._parent.build  # now Pylance sees it as non-Optional
                    build.SetKillingRoutine(self._parent.in_killing_routine)

            player_pos = GLOBAL_CACHE.Player.GetXY()
            enemy_array = Routines.Agents.GetFilteredEnemyArray(player_pos[0],player_pos[1],Range.Spellcast.value)
            while len(enemy_array) > 0: #sometimes not all enemies are killed
                if GLOBAL_CACHE.Agent.IsDead(GLOBAL_CACHE.Player.GetAgentID()):
                    self._parent.LogMessage("Death", "Player is dead, restarting.", LogConsole.LogSeverity.WARNING)
                    yield from self._reset_execution()   
                yield from Routines.Yield.wait(1000)
                enemy_array = Routines.Agents.GetFilteredEnemyArray(player_pos[0],player_pos[1],Range.Spellcast.value)
            
            self._parent.in_killing_routine = False
            self._parent.finished_routine = True
            if self._parent.build is not None:
                build = self._parent.build  # now Pylance sees it as non-Optional
                build.SetKillingRoutine(self._parent.in_killing_routine)
                build.SetRoutineFinished(self._parent.finished_routine)
            self._parent.LogMessage("Killing Routine", "Finished Killing Routine", LogConsole.LogSeverity.INFO)
            yield from Routines.Yield.wait(1000)  # Wait a bit to ensure the enemies are dead
            
 
        def LootItems(self):
            self._parent.LogMessage("Looting Items", "Starting Looting Routine", LogConsole.LogSeverity.INFO)
            self._parent.SetCurrentStep("Loot Items", 0.10)
            yield from Routines.Yield.wait(1500)  # Wait for a second before starting to loot
            filtered_agent_ids = LootConfig().GetfilteredLootArray(Range.Earshot.value)
            yield from Routines.Yield.Items.LootItems(filtered_agent_ids, 
                                                      log=self._parent.detailed_logging,
                                                      progress_callback=self._parent.AdvanceProgress)
            
        def IdentifyAndSalvageItems(self):
            self._parent.LogMessage("Identifying and Salvaging Items", "Starting Identification and Salvaging Routine", LogConsole.LogSeverity.INFO)
            self._parent.SetCurrentStep("Identify and Salvage Items", 0.10)
            yield from self._parent.inventory_handler.IDAndSalvageItems(progress_callback=self._parent.AdvanceProgress)
            
        def ExitJagaMoraine(self):
            self._parent.LogMessage("Exiting Jaga Moraine", "Resetting farm loop", LogConsole.LogSeverity.INFO)
            self._parent.SetCurrentStep("Exit Jaga Moraine", 0.05)
            self._parent.LogMessage("Exiting Jaga Moraine", "Reseting farm loop", LogConsole.LogSeverity.INFO)
            success_movement = yield from Routines.Yield.Movement.FollowPath(
                        path_points_to_exit_jaga_moraine,
                        custom_exit_condition=lambda: self._movement_eval_exit_on_map_loading(),
                        log=False,
                        progress_callback=self._parent.AdvanceProgress)
            if not success_movement:
                yield from Routines.Yield.wait(1000)
            if not success_movement and GLOBAL_CACHE.Agent.IsDead(GLOBAL_CACHE.Player.GetAgentID()):
                self._parent.LogMessage("Death", "Player is dead, restarting.", LogConsole.LogSeverity.WARNING)
                yield from Routines.Yield.wait(1000)
                yield from self._reset_execution()
            
            if not success_movement and not GLOBAL_CACHE.Map.IsMapLoading():
                if GLOBAL_CACHE.Map.GetMapID() != self._parent.BJORA_MARCHES:
                    self._parent.LogMessage("Failed to traverse Bjora Marches", "TIMEOUT", LogConsole.LogSeverity.ERROR)
                    yield from Routines.Yield.wait(1000)
                    yield from self._reset_execution()  
                    
        def WaitforBjoraMarches_returnMapLoad(self):
            self._parent.LogMessage("Waiting for Map Loading", "Bjora Marches", LogConsole.LogSeverity.INFO)
            wait_of_map_load = yield from Routines.Yield.Map.WaitforMapLoad(self._parent.BJORA_MARCHES, log=self._parent.detailed_logging)
            if not wait_of_map_load:
                self._parent.LogMessage("Map Load", "Timeout Loading Bjora Marches, stopping script.", LogConsole.LogSeverity.ERROR)
                yield from self._stop_execution()
                
        def ReturnToJagaMoraine(self):
            self._parent.LogMessage("Returning to Jaga Moraine", "Resetting farm loop", LogConsole.LogSeverity.INFO)
            success_movement = yield from Routines.Yield.Movement.FollowPath(
                        path_points_to_return_to_jaga_moraine,
                        custom_exit_condition=lambda: self._movement_eval_exit_on_map_loading(),
                        log=self._parent.detailed_logging,
                        progress_callback=self._parent.AdvanceProgress)
            if not success_movement:
                yield from Routines.Yield.wait(1000)
            if not success_movement and GLOBAL_CACHE.Agent.IsDead(GLOBAL_CACHE.Player.GetAgentID()):
                self._parent.LogMessage("Death", "Player is dead, restarting.", LogConsole.LogSeverity.WARNING)
                yield from self._reset_execution()
            
            if not success_movement and not GLOBAL_CACHE.Map.IsMapLoading():
                if GLOBAL_CACHE.Map.GetMapID() != self._parent.JAGA_MORAINE:
                    self._parent.LogMessage("Failed to return to Jaga Moraine", "TIMEOUT", LogConsole.LogSeverity.ERROR)
                    yield from Routines.Yield.wait(1000)
                    yield from self._reset_execution()
            
            self._parent.FSM.jump_to_state_by_name("Wait for Jaga Moraine Map Load")

            
            
    def _initialize_fsm(self):
        self.FSM.AddYieldRoutineStep(name = "Travel to Longeyes Ledge",coroutine_fn=self.FSM_Helpers.TravelToLongeyesLedge)
        self.FSM.AddState(name="Activate Inventory Handler",
                          execute_fn=self.FSM_Helpers.ActivateInventoryHandler,
                          run_once= True,
                          transition_delay_ms=500,
                          exit_condition=lambda: self.inventory_handler.status == "Idle")
        self.FSM.AddState(name = "Deactivate Hero AI",
                          execute_fn=self.FSM_Helpers.DeactivateHeroAI,
                          transition_delay_ms=100)
        self.FSM.AddYieldRoutineStep(name = "Load SkillBar",coroutine_fn=self.FSM_Helpers.LoadSkillBar,)
        self.FSM.AddYieldRoutineStep(name = "Inventory Handling",coroutine_fn=self.FSM_Helpers.InventoryHandling,)
        self.FSM.AddYieldRoutineStep(name = "Withdraw Cupcake",coroutine_fn=self.FSM_Helpers.WitdrawBirthdayCupcake)
        self.FSM.AddYieldRoutineStep(name = "Withdraw Pumpkin Cookie",coroutine_fn=self.FSM_Helpers.WitdrawPumpkinCookie)
        self.FSM.AddYieldRoutineStep(name = "Set Hard Mode",coroutine_fn=self.FSM_Helpers.SetHardMode)
        self.FSM.AddYieldRoutineStep(name = "Leave Outpost",coroutine_fn=self.FSM_Helpers.LeaveOutpost,)
        self.FSM.AddYieldRoutineStep(name = "Wait for Bjora Marches Map Load",coroutine_fn=self.FSM_Helpers.WaitforBjoraMarchesMapLoad)
        self.FSM.AddState(name = "Add Bjora Marches Coroutine",
                          execute_fn=self.FSM_Helpers.AddBjoraMarchesCoroutine,
                          run_once=True,
                          transition_delay_ms=100)
        self.FSM.AddYieldRoutineStep(name = "Set Norn Title",coroutine_fn=self.FSM_Helpers.SetNornTitle)
        self.FSM.AddState(name = "Use Cupcake",
                          execute_fn=self.FSM_Helpers.UseCupcake,
                          transition_delay_ms=100)
        self.FSM.AddYieldRoutineStep(name = "Traverse Bjora Marches", coroutine_fn=self.FSM_Helpers.TraverseBjoraMarches)
        self.FSM.AddYieldRoutineStep(name = "Wait for Jaga Moraine Map Load", coroutine_fn=self.FSM_Helpers.WaitforJagaMoraineMapLoad)
        self.FSM.AddState(name = "Remove Bjora Marches Coroutine",
                          execute_fn=self.FSM_Helpers.RemoveBjoraMarchesCoroutine,
                          run_once=True,
                          transition_delay_ms=100)
        self.FSM.AddState(name = "Add Skill Casting Coroutine",execute_fn=self.FSM_Helpers.AddSkillCastingCoroutine)
        self.FSM.AddYieldRoutineStep(name = "Take Bounty", coroutine_fn=self.FSM_Helpers.TakeBounty)
        self.FSM.AddYieldRoutineStep(name = "Farming Route 1", coroutine_fn=self.FSM_Helpers.FarmingRoute1)
        self.FSM.AddYieldRoutineStep(name = "Wait for lef aggro ball", coroutine_fn=self.FSM_Helpers.WaitforLeftAggroBall)
        self.FSM.AddYieldRoutineStep(name = "Farming Route 2", coroutine_fn=self.FSM_Helpers.FarmingRoute2)
        self.FSM.AddYieldRoutineStep(name = "Wait for right aggro ball", coroutine_fn=self.FSM_Helpers.WaitforRightAggroBall)
        self.FSM.AddYieldRoutineStep(name = "Farming Route to Kill Spot", coroutine_fn=self.FSM_Helpers.FarmingRoutetoKillSpot)
        self.FSM.AddYieldRoutineStep(name = "Kill Enemies", coroutine_fn=self.FSM_Helpers.KillEnemies)
        self.FSM.AddState(name = "Remove Skill Casting Coroutine",execute_fn=self.FSM_Helpers.RemoveSkillCastingCoroutine)
        self.FSM.AddYieldRoutineStep(name = "Loot Items", coroutine_fn=self.FSM_Helpers.LootItems)
        self.FSM.AddYieldRoutineStep(name = "Identify and Salvage Items", coroutine_fn=self.FSM_Helpers.IdentifyAndSalvageItems)
        self.FSM.AddYieldRoutineStep(name = "Exit Jaga Moraine", coroutine_fn=self.FSM_Helpers.ExitJagaMoraine)
        self.FSM.AddYieldRoutineStep(name = "Wait for Bjora Marches return Map Load", coroutine_fn=self.FSM_Helpers.WaitforBjoraMarches_returnMapLoad)
        self.FSM.AddYieldRoutineStep(name = "Return to Jaga Moraine", coroutine_fn=self.FSM_Helpers.ReturnToJagaMoraine)
        

#endregion
#region Stuck
    def HandleStuckBjoraMarches(self):
        while True:
            if not Routines.Checks.Map.MapValid():
                yield from Routines.Yield.wait(1000)  # Wait for map to be valid
                
            if not self.script_running:
                return
            
            if self.script_paused:
                yield from Routines.Yield.wait(1000)
                continue
                
            if GLOBAL_CACHE.Agent.IsDead(GLOBAL_CACHE.Player.GetAgentID()):
                return
            
            if self.in_waiting_routine:
                yield from Routines.Yield.wait(1000)  # Wait for waiting routine to finish
                continue
            
            if self.finished_routine:
                self.stuck_counter = 0
                
            if self.current_run_node and self.current_run_node.GetRunDuration() > 30000:
                self.LogMessage("Stuck Detection", "Current run node is taking too long, resetting.", LogConsole.LogSeverity.WARNING)
                self.stuck_counter = 0
                yield from self.FSM_Helpers._reset_execution()
                continue


            if GLOBAL_CACHE.Map.GetMapID() == self.BJORA_MARCHES:
                if self.stuck_timer.IsExpired():
                    GLOBAL_CACHE.Player.SendChatCommand("stuck")
                    self.stuck_timer.Reset()

                if self.movement_check_timer.IsExpired():
                    current_player_pos = GLOBAL_CACHE.Player.GetXY()
                    if self.old_player_position == current_player_pos:
                        self.LogMessage("Stuck Detection", "Player is stuck, sending stuck command.", LogConsole.LogSeverity.WARNING)
                        GLOBAL_CACHE.Player.SendChatCommand("stuck")
                        player_pos = GLOBAL_CACHE.Player.GetXY() #(x,y)
                        facing_direction = GLOBAL_CACHE.Agent.GetRotationAngle(GLOBAL_CACHE.Player.GetAgentID())
                        left_angle = facing_direction + math.pi / 2
                        distance = 200
                        offset_x = math.cos(left_angle) * distance
                        offset_y = math.sin(left_angle) * distance

                        sidestep_pos = (player_pos[0] + offset_x, player_pos[1] + offset_y)
                        for i in range(3):
                            GLOBAL_CACHE.Player.Move(sidestep_pos[0], sidestep_pos[1])
                        self.stuck_timer.Reset()
                    else:
                        self.old_player_position = current_player_pos
                        
                    self.movement_check_timer.Reset()
                
                build = self.build or ShawowFormAssassinVaettir()   
                yield from build.CastShroudOfDistress()
                    
                agent_array = GLOBAL_CACHE.AgentArray.GetEnemyArray()
                agent_array = AgentArray.Filter.ByCondition(agent_array, lambda agent: GLOBAL_CACHE.Agent.GetModelID(agent) in (AgentModelID.FROZEN_ELEMENTAL.value, AgentModelID.FROST_WURM.value))
                agent_array = AgentArray.Filter.ByDistance(agent_array, GLOBAL_CACHE.Player.GetXY(), Range.Spellcast.value)
                if len(agent_array) > 0:
                    yield from build.DefensiveActions()  
            else:
                return  # Exit the loop if not in Bjora Marches
                     
            yield from Routines.Yield.wait(500)
            
    def HandleStuckJagaMoraine(self):
        while True:
            if not Routines.Checks.Map.MapValid():
                yield from Routines.Yield.wait(1000)  # Wait for map to be valid
            
            if not self.script_running:
                return
            
            if self.script_paused:
                yield from Routines.Yield.wait(1000)
                continue
                
            if GLOBAL_CACHE.Agent.IsDead(GLOBAL_CACHE.Player.GetAgentID()):
                return
            
            if self.current_run_node and self.current_run_node.GetRunDuration() > 30000:
                self.LogMessage("Stuck Detection", "Current run node is taking too long, resetting.", LogConsole.LogSeverity.WARNING)
                self.stuck_counter = 0
                yield from self.FSM_Helpers._reset_execution()
                continue
              
            build = self.build or ShawowFormAssassinVaettir() 
            if self.in_waiting_routine:
                self.stuck_counter = 0
                build.SetStuckCounter(self.stuck_counter)
                self.stuck_timer.Reset()
                yield from Routines.Yield.wait(1000)
                continue
                
            if self.finished_routine:
                self.stuck_counter = 0
                build.SetStuckCounter(self.stuck_counter)
                self.stuck_timer.Reset()
                yield from Routines.Yield.wait(1000)
                continue
            
            if self.in_killing_routine:
                self.stuck_counter = 0
                build.SetStuckCounter(self.stuck_counter)
                self.stuck_timer.Reset()
                yield from Routines.Yield.wait(1000)
                continue

            if GLOBAL_CACHE.Map.GetMapID() == self.JAGA_MORAINE:
                if self.stuck_timer.IsExpired():
                    GLOBAL_CACHE.Player.SendChatCommand("stuck")
                    self.stuck_timer.Reset()
                  
                if self.movement_check_timer.IsExpired():
                    current_player_pos = GLOBAL_CACHE.Player.GetXY()
                    if self.old_player_position == current_player_pos:
                        self.LogMessage("Stuck Detection", "Player is stuck, sending stuck command.", LogConsole.LogSeverity.WARNING)
                        GLOBAL_CACHE.Player.SendChat
                        self.stuck_counter += 1
                        build.SetStuckCounter(self.stuck_counter)
                        self.stuck_timer.Reset()
                    else:
                        self.old_player_position = current_player_pos
                        self.stuck_counter = 0
                        
                    self.movement_check_timer.Reset()
                    
                if self.stuck_counter >= 10:
                    self.LogMessage("Stuck Detection", "Unrecoverable stuck detected, resetting.", LogConsole.LogSeverity.ERROR)
                    self.stuck_counter = 0
                    build.SetStuckCounter(self.stuck_counter)
                    yield from self.FSM_Helpers._reset_execution()

            else:
                return  # Exit the loop if not in Bjora Marches
                     
            yield from Routines.Yield.wait(500)

        

#endregion

_YAVB = YAVB()

def main():
    _YAVB.DrawMainWindow()
    if _YAVB.option_window_visible:
        _YAVB.DrawOptionsWindow()
    if _YAVB.console_visible:
        _YAVB.console.SetMainWindowPosition(_YAVB.main_window_pos)
        main_width, main_height = _YAVB.main_window_size
        options_width, options_height = _YAVB.option_window_size
        
        if _YAVB.option_window_snapped and _YAVB.option_window_visible:
            total_height = main_height + options_height
        else:
            total_height = main_height
        
        _YAVB.console.SetMainWindowSize((main_width, total_height))
        _YAVB.console.SetLogToFile(_YAVB.console_log_to_file)
        _YAVB.console.SetSnapped(_YAVB.console_snapped, _YAVB.console_snapped_border)
        _YAVB.console.DrawConsole()
        
    if _YAVB.FSM.finished:
        if _YAVB.script_running:
            _YAVB.script_running = False
            _YAVB.script_paused = False
            _YAVB.LogMessage("Script finished", "", LogConsole.LogSeverity.INFO)
            _YAVB.state = "Idle"
            _YAVB.FSM.stop()

            
    if _YAVB.script_running:
        _YAVB.FSM.update()
    
if __name__ == "__main__":
    main()
