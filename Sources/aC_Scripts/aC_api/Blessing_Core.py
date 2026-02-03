import math, time, os, tempfile
from enum import Enum, auto
from typing import Optional, Tuple, List, Dict
from Py4GWCoreLib import *
from Py4GWCoreLib import Agent, AgentArray, Player, Console, Party
from Py4GW_widget_manager import get_widget_handler
from .Blessing_dialog_helper import is_npc_dialog_visible, click_dialog_button, get_dialog_button_count
from .Verify_Blessing        import has_any_blessing

_widget_handler = get_widget_handler()

# — per-client flag file in a shared temp directory —
FLAG_DIR = os.path.join(tempfile.gettempdir(), "GuildWarsBlessFlags")
os.makedirs(FLAG_DIR, exist_ok=True)

def _flag_path() -> str:
    return os.path.join(FLAG_DIR, f"{Player.GetAgentID()}.flag")

def _write_flag():
    open(_flag_path(), "w").close()

def _remove_flag():
    try:
        os.remove(_flag_path())
    except OSError:
        pass

# how long to wait in VERIFY for the buff to register
_VERIFY_TIMEOUT = 1.0  # seconds

class BlessingNpc(Enum):
    Sunspear_Scout      = (4778, 4776)
    Wandering_Priest    = (5384, 5383)
    Vabbian_Scout       = (5632,)
    Ghostly_Scout       = (5547, 5548)
    Ghostly_Priest      = (5615,)
    Whispers_Informants = (5218, 5683)
    Forgotten_Warden    = (5002,)
    Kurzick_Priest      = (593, 912, 3426)
    Luxon_Priest        = (1947, 3641)
    Beacons_of_Droknar  = (5865,)
    Ascalonian_Refugees = (1986, 1987, 6044, 6045, 6043)
    Asuran_Krewe        = (6755, 6756, 6775, 6779)
    Norn_Hunters        = (6374, 6380)

    def __init__(self, *mids: int):
        self.model_ids = mids

# generic sequences for non-priest NPCs
DIALOG_SEQUENCES: Dict[BlessingNpc, List[int]] = {
    BlessingNpc.Sunspear_Scout:   [1],
    BlessingNpc.Wandering_Priest: [1],
    BlessingNpc.Ghostly_Scout:    [1],
    BlessingNpc.Kurzick_Priest:   [1, 2, 1, 1],
    BlessingNpc.Luxon_Priest:     [1, 2, 1, 1],
}

def get_blessing_npc() -> Tuple[Optional[BlessingNpc], Optional[int]]:
    mx, my = Player.GetXY()
    best, best_d = (None, None), float('inf')
    for npc in BlessingNpc:
        for ag in AgentArray.GetAgentArray():
            if Agent.GetModelID(ag) in npc.model_ids:
                ax, ay = Agent.GetXY(ag)
                d = math.dist((mx, my), (ax, ay))
                if d < best_d:
                    best, best_d = (npc, ag), d
    if best[1]:
        Player.ChangeTarget(best[1])
    return best

class _Mover:
    def __init__(self):
        self.agent = None
        self.dist  = 0.0
        self.done  = False

    def start(self, agent: int, dist: float):
        self.agent, self.dist, self.done = agent, dist, False

    def update(self) -> bool:
        # cancel movement if a dialog popped
        if is_npc_dialog_visible():
            self.done, self.agent = True, None
            return False
        if not self.agent or self.done:
            return False

        mx, my = Player.GetXY()
        tx, ty = Agent.GetXY(self.agent)
        if math.dist((mx, my), (tx, ty)) <= self.dist:
            Player.Interact(self.agent)
            self.done, self.agent = True, None
            return True
        Player.Move(tx, ty)
        return False

_mover = _Mover()
def move_interact_blessing_npc(agent: Optional[int], dist: float = 100.0) -> bool:
    if agent is None:
        return False
    if _mover.agent != agent or _mover.done:
        _mover.start(agent, dist)
    return _mover.update()

class _BlessState(Enum):
    IDLE        = auto()
    APPROACH    = auto()
    DIALOG_WAIT = auto()
    DIALOG_NEXT = auto()
    VERIFY      = auto()
    DONE        = auto()

class BlessingRunner:
    def __init__(self, interact_distance: float = 100.0):
        self.interact_distance = interact_distance
        self.state    = _BlessState.IDLE
        self.member: Optional[BlessingNpc] = None
        self.agent:  Optional[int]         = None

        # generic NPC state
        self.dialog_seq: List[int] = []
        self.seq_idx: int          = 0

        # special flows
        self._norn_stage = 0
        self._kl_stage   = 0

        self._wait_start   = 0.0
        self._verify_start = 0.0
        self.success       = False

    def start(self):
        _remove_flag()
        ConsoleLog("BlessingRunner", "Starting blessing sequence", Console.MessageType.Info)
        _widget_handler.disable_widget("HeroAI")

        self.member, self.agent = get_blessing_npc()
        if not self.member or not self.agent:
            ConsoleLog("BlessingRunner", "No blessing NPC found", Console.MessageType.Warning)
            self.state, self.success = _BlessState.DONE, False
            _widget_handler.enable_widget("HeroAI")
            return

        # reset all state machines
        self.state         = _BlessState.APPROACH
        self.seq_idx       = 0
        self.dialog_seq    = []
        self._norn_stage   = 0
        self._kl_stage     = 0
        self._wait_start   = 0.0
        self._verify_start = 0.0
        self.success       = False

        # prepare generic dialog list only for non-priest NPCs
        if self.member not in (BlessingNpc.Norn_Hunters,
                               BlessingNpc.Kurzick_Priest,
                               BlessingNpc.Luxon_Priest):
            self.dialog_seq = DIALOG_SEQUENCES.get(self.member, [1])

    def update(self) -> Tuple[bool, bool]:
        # 1) Norn-hunter special flow
        if self.member is BlessingNpc.Norn_Hunters:
            if self._tick_norn():
                _widget_handler.enable_widget("HeroAI")
                return True, self.success
            return False, False

        # 2) Kurzick/Luxon priest special flow
        if self.member in (BlessingNpc.Kurzick_Priest, BlessingNpc.Luxon_Priest):
            if self._tick_kurzick_luxon():
                _widget_handler.enable_widget("HeroAI")
                return True, self.success
            return False, False

        # 3) Generic FSM for all other NPCs
        if self.state == _BlessState.IDLE:
            return False, False

        # APPROACH
        if self.state == _BlessState.APPROACH:
            if move_interact_blessing_npc(self.agent, self.interact_distance):
                self.state = _BlessState.DIALOG_WAIT
                self._wait_start = time.time()
            return False, False

        # DIALOG_WAIT
        if self.state == _BlessState.DIALOG_WAIT:
            if is_npc_dialog_visible():
                self.state = _BlessState.DIALOG_NEXT
            elif time.time() - self._wait_start > 10.0:
                self.state, self.success = _BlessState.DONE, False
                _widget_handler.enable_widget("HeroAI")
                return True, False
            return False, False

        # DIALOG_NEXT
        if self.state == _BlessState.DIALOG_NEXT:
            if self.seq_idx < len(self.dialog_seq):
                click_dialog_button(self.dialog_seq[self.seq_idx])
                self.seq_idx += 1
                # wait for next dialog
                self.state = _BlessState.DIALOG_WAIT
                self._wait_start = time.time()
                return False, False
            # done → VERIFY
            self.state = _BlessState.VERIFY
            self._verify_start = time.time()
            return False, False

        # VERIFY
        if self.state == _BlessState.VERIFY:
            if has_any_blessing(Player.GetAgentID()):
                self.success = True
                _write_flag()
                _widget_handler.enable_widget("HeroAI")
                self.state = _BlessState.DONE
                return True, True
            if time.time() - self._verify_start < _VERIFY_TIMEOUT:
                return False, False
            self.success = False
            _widget_handler.enable_widget("HeroAI")
            self.state = _BlessState.DONE
            return True, False

        # DONE
        if self.state == _BlessState.DONE:
            _widget_handler.enable_widget("HeroAI")
            return True, self.success

        return False, False

    # ——— Norn-hunter logic (unchanged) ———
    def _tick_norn(self) -> bool:
        # Stage 0: approach & interact
        if self._norn_stage == 0:
            if move_interact_blessing_npc(self.agent, self.interact_distance):
                ConsoleLog("BlessingRunner", "Norn: interacted, waiting for dialog…", Console.MessageType.Debug)
                self._wait_start = time.time()
                self._norn_stage = 1
            return False

        # Stage 1: wait for challenge dialog
        if self._norn_stage == 1:
            if is_npc_dialog_visible():
                ConsoleLog("BlessingRunner", "Norn: dialog visible, clicking accept", Console.MessageType.Debug)
                click_dialog_button(1)
                self._norn_stage = 2
            elif time.time() - self._wait_start > 8:
                ConsoleLog("BlessingRunner", "Norn: dialog never showed up, aborting", Console.MessageType.Warning)
                return True
            return False

        # Stage 2: either already blessed or wait for hostility
        if self._norn_stage == 2:
            if has_any_blessing(Player.GetAgentID()):
                ConsoleLog("BlessingRunner", "Norn: already blessed, exiting", Console.MessageType.Debug)
                _write_flag()
                self.success = True
                return True
            if not self.agent:
                return False
            if Agent.GetAllegiance(self.agent) == 3:
                _widget_handler.enable_widget("HeroAI")
                self._norn_stage = 3
            return False

        # Stage 3: wait until friendly again
        if self._norn_stage == 3:
            if not self.agent:
                return False
            if Agent.GetAllegiance(self.agent) != 3:
                ConsoleLog("BlessingRunner", "Norn: back to friendly", Console.MessageType.Debug)
                _widget_handler.disable_widget("HeroAI")
                self._norn_stage = 4
            return False

        # Stage 4: final interact & blessing
        if self._norn_stage == 4:
            if move_interact_blessing_npc(self.agent, self.interact_distance):
                ConsoleLog("BlessingRunner", "Norn: final dialog click", Console.MessageType.Debug)
                click_dialog_button(1)
                self.success = has_any_blessing(Player.GetAgentID())
                if self.success:
                    _write_flag()
                return True
            return False

        return False

    # ——— Kurzick / Luxon Priest logic (refactored) ———
    def _tick_kurzick_luxon(self) -> bool:
        """
        2-button flow → [1,1]
        3-button flow → [1,2,1,1]

        Non-leaders wait 2 seconds *before* approaching/interacting.
        """
        npc_name = "Kurzick Priest" if self.member is BlessingNpc.Kurzick_Priest else "Luxon Priest"
        now = time.time()

        # Stage 0: (possible) pre-interact delay → approach & interact
        if self._kl_stage == 0:
            # on first entry, stamp the time
            if self._wait_start == 0.0:
                self._wait_start = now

            # non-leader: hold off for 2 seconds
            leader = Party.GetPartyLeaderID()
            me     = Player.GetAgentID()
            if me != leader and (now - self._wait_start) < 2.0:
                # still within our 2 s “hold” window
                return False

            # now either leader, or 2 s have passed → actually move + interact
            if move_interact_blessing_npc(self.agent, self.interact_distance):
                ConsoleLog(
                    "BlessingRunner",
                    f"{npc_name}: interacted, waiting for dialog…",
                    Console.MessageType.Debug
                )
                # reset the timer for the *next* wait (stage 1)
                self._wait_start = now
                self._kl_stage   = 1
            return False
        
            # Stage 1: initial request → click 1
        if self._kl_stage == 1:
            if is_npc_dialog_visible() and now - self._wait_start >= 0.5:
                ConsoleLog("BlessingRunner", f"{npc_name}: click 1 (initial request)", Console.MessageType.Debug)
                click_dialog_button(1)
                self._wait_start = now
                self._kl_stage   = 2
            elif now - self._wait_start > 8.0:
                ConsoleLog("BlessingRunner", f"{npc_name}: dialog never appeared, aborting", Console.MessageType.Warning)
                self.success = False
                return True
            return False

        # Stage 2: donation menu appears → decide bribe vs no-bribe
        if self._kl_stage == 2:
            if is_npc_dialog_visible() and now - self._wait_start >= 0.5:
                count = get_dialog_button_count()
                if count == 3:
                    # bribe path
                    ConsoleLog("BlessingRunner", f"{npc_name}: click 2 (high donation)", Console.MessageType.Debug)
                    click_dialog_button(2)
                    self._wait_start = now
                    self._kl_stage = 3
                else:
                    # no-bribe path: just close
                    ConsoleLog("BlessingRunner", f"{npc_name}: click 1 (no bribe)", Console.MessageType.Debug)
                    click_dialog_button(1)
                    self.success = has_any_blessing(Player.GetAgentID())
                    if self.success:
                        _write_flag()
                    return True
            elif now - self._wait_start > 8.0:
                ConsoleLog("BlessingRunner", f"{npc_name}: donation menu not found, aborting", Console.MessageType.Warning)
                self.success = False
                return True
            return False

        # Stage 3: confirm large donation → click “1”
        if self._kl_stage == 3:
            if is_npc_dialog_visible() and now - self._wait_start >= 0.5:
                ConsoleLog("BlessingRunner", f"{npc_name}: click 1 (confirm large donation)", Console.MessageType.Debug)
                click_dialog_button(1)
                self._wait_start = now
                self._kl_stage = 4
            elif now - self._wait_start > 8.0:
                ConsoleLog("BlessingRunner", f"{npc_name}: confirmation never appeared, aborting", Console.MessageType.Warning)
                self.success = False
                return True
            return False

        # Stage 4: final close → click “1” or immediate verify
        if self._kl_stage == 4:
            if is_npc_dialog_visible() and now - self._wait_start >= 0.5:
                ConsoleLog("BlessingRunner", f"{npc_name}: click 1 (final close)", Console.MessageType.Debug)
                click_dialog_button(1)
                self.success = has_any_blessing(Player.GetAgentID())
                if self.success:
                    _write_flag()
                return True
            if not is_npc_dialog_visible():
                ConsoleLog("BlessingRunner", f"{npc_name}: dialog closed, verifying blessing", Console.MessageType.Debug)
                self.success = has_any_blessing(Player.GetAgentID())
                if self.success:
                    _write_flag()
                return True
            return False

        return False

__all__ = ["_Mover", "move_interact_blessing_npc"]
