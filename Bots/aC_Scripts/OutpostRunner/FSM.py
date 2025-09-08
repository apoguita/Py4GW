from Py4GWCoreLib import *
from OutpostRunner.FSMHelpers import OutpostRunnerFSMHelpers
from OutpostRunner.Build_Manager import OutpostRunnerDA
from OutpostRunner.Overwatch import OutpostRunnerOverwatch

class OutpostRunnerFSM:
    def __init__(self):
        self.fsm = FSM("OutpostRunnerFSM")
        self.helpers = OutpostRunnerFSMHelpers()
        self.skill_manager = OutpostRunnerDA()
        self.skill_coroutine = None
        self.map_chain = []  # list of RunInfo objects
        self.chain_stats = None  # ChainStatistics instance
        # Overwatch state
        self.run_active = False
        self.overwatch_coroutine = None
        self.overwatch = OutpostRunnerOverwatch(self)
        self.last_error = None

    def set_map_chain(self, map_list):
        """
        Define the chain of map scripts to run sequentially.
        Example: ["_1_Eotn_To_Gunnars", "_2_Gunnars_To_Longeyes"]
        """
        self.map_chain = map_list
        if not self.map_chain:
            ConsoleLog("OutpostRunnerFSM", "No map chain selected!")

    def build_fsm(self):
        """
        Build FSM steps dynamically based on map chain.
        Each map adds travel, wait, pathing, skill-casting phases.
        """
        if not self.map_chain:
            ConsoleLog("OutpostRunnerFSM", "Cannot build FSM — no map chain defined!")
            return

        for idx, run_info in enumerate(self.map_chain):
            self._add_map_steps(run_info, idx)

        #self.fsm.AddState("CompleteRun", self._finish_run)
        # Add a final completion state that stops Overwatch gracefully
        self.fsm.AddState("CompleteRun", self._finish_run)

    def _add_map_steps(self, run_info, idx):
        """
        FSM map steps
        """
        data = self.helpers.load_map_script(run_info.id)
        outpost_id = data["ids"]["outpost_id"]

         # Mark start
        self.fsm.AddState(f"[{idx}] MarkStarted", lambda ri=run_info: ri.mark_started())

        # 1) Teleport to outpost 
        self.fsm.AddYieldRoutineStep(f"[{idx}] TravelToOutpost",lambda oid=outpost_id: self.helpers.travel_to_outpost(oid))
        # 2) Wait for outpost map load
        self.fsm.AddYieldRoutineStep(f"[{idx}] WaitForOutpost",lambda oid=outpost_id: self.helpers.wait_for_map_load(oid))
        # 3) Exit outpost
        self.fsm.AddYieldRoutineStep(f"[{idx}] LeaveOutpostPath",lambda op=data["outpost_path"]: self.helpers.follow_path(op))
        # 4) Start build manager
        self.fsm.AddState(f"[{idx}] StartSkillCasting", self._start_skill_casting)
        # 5) Explorable segments: wait+walk each one in order
        segments = data.get("segments", [])
        for seg_i, seg in enumerate(segments):
            mid  = seg["map_id"]
            path = seg["path"]
            # 5a) Wait for this segment’s map
            self.fsm.AddYieldRoutineStep(f"[{idx}.{seg_i}] WaitMap_{mid}",lambda m=mid: self.helpers.wait_for_map_load(m))
            # 5b) Walk it
            self.fsm.AddYieldRoutineStep(f"[{idx}.{seg_i}] Walk_{mid}",lambda p=path: self.helpers.follow_path(p))
        # 6) Stop buffs at the very end
        self.fsm.AddState(f"[{idx}] StopSkillCasting", self._stop_skill_casting)
        # 7) Mark finish
        self.fsm.AddState(f"[{idx}] MarkFinished", lambda ri=run_info: ri.mark_finished())

    def _start_skill_casting(self):
        """
        Attach skill casting coroutine for OutpostRunnerDA
        so buffs (e.g. IAU, Pious Haste) are maintained during movement.
        """
        # If a skill-casting coroutine is already running, stop it first to avoid duplicates.
        if self.skill_coroutine:
            self._stop_skill_casting()
            ConsoleLog("OutpostRunnerFSM", "Stopped existing skill casting coroutine before starting a new one.")
        # Start a fresh skill-casting coroutine for the new map.
        self.skill_coroutine = self.skill_manager.ProcessSkillCasting(self.helpers)
        GLOBAL_CACHE.Coroutines.append(self.skill_coroutine)
        ConsoleLog("OutpostRunnerFSM", "Starting skill casting coroutine")

    def _stop_skill_casting(self):
        """
        Remove skill casting coroutine when leaving combat/movement.
        """
        if self.skill_coroutine:
            if self.skill_coroutine in GLOBAL_CACHE.Coroutines:
                GLOBAL_CACHE.Coroutines.remove(self.skill_coroutine)
                ConsoleLog("OutpostRunnerFSM", "Stopped skill casting coroutine.")
            self.skill_coroutine = None

    def start(self):
        """
        Start the FSM execution.
        """
        # Validate the build
        success, error_msg = self.skill_manager.ValidateBuild()
        if not success:
            ConsoleLog("OutpostRunnerFSM",f"Build validation failed: {error_msg}",Console.MessageType.Error,)
            self.last_error = error_msg
            return
        self.last_error = None  # clear any previous error

        self.helpers.cache_and_disable_all_widgets()
        self.helpers.enable_custom_widget_list()

        from OutpostRunner.StatsManager import ChainStatistics
        self.chain_stats = ChainStatistics(self.map_chain)
        self.chain_stats.start_chain()

        ConsoleLog("OutpostRunnerFSM", f"Starting OutpostRunner with {len(self.map_chain)} runs.")
        self.build_fsm()
        self.fsm.start()
        # Start Overwatch monitoring as a background coroutine
        self.run_active = True
        if not self.overwatch_coroutine:
            self.overwatch.start()  # start() already appends the coroutine internally
        else:
            ConsoleLog("OutpostRunnerFSM", "No map chain selected! Cannot start.")

    def reset(self):
        """
        HARD RESET:
        - Stop all coroutines
        - Reset skill casting
        - Reset FSM completely
        """
        ConsoleLog("OutpostRunnerFSM", "Hard resetting FSM + all coroutines...")

        # Stop overwatch
        if self.overwatch._active:
            self.overwatch.stop()
        self._stop_skill_casting()
        try:
            GLOBAL_CACHE.Coroutines.clear()
        except ValueError:
            pass
        ActionQueueManager().ResetAllQueues()

        self.helpers.restore_cached_widgets()

        # Replace FSM with a new clean instance
        self.fsm = FSM("OutpostRunnerFSM")
        # Mark inactive until restarted
        self.run_active = False
        # Reset chain statistics (clear any running stats tracking)
        self.chain_stats = None

    def soft_reset_for_retry(self):
        """
        SOFT RESET used by Overwatch (do NOT stop overwatch itself)
        - Stop skill casting
        - Clear action queues
        - Reset FSM completely
        """
        ConsoleLog("OutpostRunnerFSM", "Soft resetting FSM")
        
        # Stop skill casting
        self._stop_skill_casting()
        # Replace FSM with a new clean instance
        self.fsm = FSM("OutpostRunnerFSM")
        # Mark inactive until restarted
        self.run_active = False
    def resume_partial_chain(self):
        ConsoleLog("OutpostRunnerFSM", f"Retrying run but keeping previous stats intact")
        self.build_fsm()  # rebuild FSM states for the retry chain
        self.fsm.start()
        self.run_active = True
        # Keep overwatch running
        if not self.overwatch._active:
            self.overwatch.start()

    def _finish_run(self):
        ConsoleLog("OutpostRunnerFSM", "Run completed successfully.", Console.MessageType.Info)
        if self.chain_stats:
            self.chain_stats.finish_chain()
        self.map_chain = []
        self.overwatch.stop()
        self.helpers.restore_cached_widgets()