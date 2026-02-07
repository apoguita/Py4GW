# OutpostRunner_Overwatch.py

from Py4GWCoreLib import *
from Sources.aC_Scripts.OutpostRunner import map_loader
import time


class OutpostRunnerOverwatch:
    """
    Overwatch monitor for OutpostRunner.
    Runs as a coroutine to detect death/stuck conditions
    and triggers a resign/reset sequence.
    """

    def __init__(self, fsm_runner):
        """
        fsm_runner: instance of OutpostRunnerFSM
        """
        self.runner = fsm_runner
        self._coroutine = None
        self._active = False
        self._stuck_threshold = 45  # seconds of no movement before considered stuck

    def start(self):
        """Start overwatch coroutine"""
        if self._coroutine is None:
            self._active = True
            self._coroutine = self._loop()
            GLOBAL_CACHE.Coroutines.append(self._coroutine)
            ConsoleLog("Overwatch", f"Overwatch started - i'll handle if we die or get stuck. all my messages are yellow text", Console.MessageType.Warning)

    def stop(self):
        """Stop overwatch coroutine"""
        self._active = False
        if self._coroutine and self._coroutine in GLOBAL_CACHE.Coroutines:
            GLOBAL_CACHE.Coroutines.remove(self._coroutine)
        self._coroutine = None
        ConsoleLog("Overwatch", f"Overwatch stopped.", Console.MessageType.Warning)

    def _loop(self):
        """Coroutine that yields and monitors player state"""
        
        prev_pos = Player.GetXY() or (0.0, 0.0)
        last_move_time = time.time()

        def _generator():
            nonlocal prev_pos, last_move_time 

            while True:
                # Stop if overwatch is no longer active
                if not self._active:
                    return  # Exit the coroutine cleanly

                # Skip checks during loading/zoning to avoid false stuck detection
                if not Routines.Checks.Map.MapValid():
                    yield from Routines.Yield.wait(1000)
                    # After zoning, reinitialize movement tracking
                    new_pos = Player.GetXY()
                    if new_pos:
                        prev_pos = new_pos
                    last_move_time = time.time()
                    continue

                # --- Death detection ---
                if Agent.IsDead(Player.GetAgentID()):
                    ConsoleLog("Overwatch", f"Overwatch: Player died - resetting run.", Console.MessageType.Warning)
                    yield from self._trigger_resign_and_restart()
                    continue

                # --- Stuck detection ---
                current_pos = Player.GetXY() or prev_pos
                if current_pos == prev_pos:
                    if time.time() - last_move_time > self._stuck_threshold:
                        ConsoleLog("Overwatch", f"Overwatch: Player stuck >{self._stuck_threshold}s - resetting run.", Console.MessageType.Warning)
                        yield from self._trigger_resign_and_restart()
                        continue
                else:
                    # Player moved → reset timer
                    prev_pos = current_pos
                    last_move_time = time.time()

                # Sleep 1 second between checks
                yield from Routines.Yield.wait(1000)

        return _generator()

    def _trigger_resign_and_restart(self):
        # Mark current run failed
        current_run = next((r for r in self.runner.map_chain if r.started and not r.finished), None)
        if current_run:
            current_run.failures += 1

        # Stop FSM + buffs
        self.runner.soft_reset_for_retry()

        # Broadcast resign for multi-box team
        accounts = GLOBAL_CACHE.ShMem.GetAllAccountData()
        sender_email = Player.GetAccountEmail()
        for account in accounts:
            ConsoleLog("Messaging", "Resigning account: " + account.AccountEmail)
            GLOBAL_CACHE.ShMem.SendMessage(sender_email, account.AccountEmail, SharedCommandType.Resign, (0,0,0,0))

        # Find unfinished runs
        if current_run:
            # Ensure region/run_name are present (parse from ID if missing)
            region = getattr(current_run, 'region', None)
            run_name = getattr(current_run, 'run_name', None)
            if not region or not run_name:
                if "__" in current_run.id:
                    region, run_name = current_run.id.split("__", 1)
                    current_run.region = region
                    current_run.run_name = run_name

            # Load map data
            data = map_loader.load_map_data(current_run.region, current_run.run_name)
            outpost_id = data["ids"]["outpost_id"]
            yield from Routines.Yield.wait(3000)  # small delay to let transition settle

            # === STEP 1: Wait for resign conditions before returning to outpost ===
            timeout = 20
            start_time = time.time()

            while time.time() - start_time < timeout:
                is_map_ready = Map.IsMapReady()
                is_party_loaded = GLOBAL_CACHE.Party.IsPartyLoaded()
                is_explorable = Map.IsExplorable()
                is_party_defeated = GLOBAL_CACHE.Party.IsPartyDefeated()

                if is_map_ready and is_party_loaded and is_explorable and is_party_defeated:
                    ConsoleLog("Overwatch", f"Party resigned. Returning to outpost {outpost_id} restarting run={current_run.run_name}", Console.MessageType.Warning)
                    GLOBAL_CACHE.Party.ReturnToOutpost()
                    break

                yield from Routines.Yield.wait(500)
            else:
                ConsoleLog("Overwatch", f"Something failed, i am not able to recover - stopping bot.", Console.MessageType.Error)
                #self.runner.reset()
                return

            # === STEP 2: Wait for return to outpost and restart fsm ===
            timeout = 20
            start_time = time.time()

            while time.time() - start_time < timeout:
                if Routines.Checks.Map.MapValid() and Map.IsOutpost():
                    ConsoleLog("Overwatch", f"Restarting run: {current_run.display}", Console.MessageType.Warning)
                    remaining_runs = [r for r in self.runner.map_chain if not r.finished]
                    retry_chain = [current_run] + [r for r in remaining_runs if r != current_run]
                    self.runner.set_map_chain(retry_chain)
                    self.runner.resume_partial_chain()
                    break

                yield from Routines.Yield.wait(500)
            else:
                ConsoleLog("Overwatch", f"Failed to load outpost within 5s after returning. Cannot retry run.", Console.MessageType.Error)
                return