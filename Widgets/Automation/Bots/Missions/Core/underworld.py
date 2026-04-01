
# ╔══════════════════════════════════════════════════════════════════════════════
# ║  File    : underworld.py
# ║  Purpose : Fully automated Guild Wars Underworld bot.
# ║            Drives all quest sections from Chamber through Dhuum,
# ║            handles entering  and exiting, inventory refill, conset
# ║            management, and multibox party coordination.
# ║            Combat-system integration (CB vs. HeroAI) is swapped via
# ║            the adapter pattern — quest-section code never touches
# ║            the combat system directly.
# ╚══════════════════════════════════════════════════════════════════════════════

# Force a fresh reimport of adapter modules on every script (re)load so that
# edits to adapter files are picked up without restarting the entire Py4GW process.
import sys as _sys
for _mod_key in [k for k in _sys.modules if "sch0l0ka.adapter" in k]:
    del _sys.modules[_mod_key]
del _sys

from Py4GWCoreLib import Botting, Routines, Agent, AgentArray, Player, Utils, AutoPathing, GLOBAL_CACHE, ConsoleLog, Map, Pathing, FlagPreference, Party, IniHandler, Overlay, Item, ItemArray
from Py4GWCoreLib.enums_src.Model_enums import ModelID
from Py4GWCoreLib.enums_src.Map_enums import name_to_map_id
import os
import time
from typing import Any, Generator
from Py4GWCoreLib.enums_src.Multiboxing_enums import SharedCommandType
from Sources.oazix.CustomBehaviors.primitives.behavior_state import BehaviorState
from pathlib import Path
import PyImGui
import Py4GW

# ╔══════════════════════════════════════════════════════════════════
# ║                     POSSIBLE IMPROVEMENTS                        
# ╠══════════════════════════════════════════════════════════════════
# ║                                                                  
# ║  [ ] Better antistuck at Unwanted Guests                                                         
# ║  [X] Kill the Chained Souls when we wait till the quest is done                                                        
# ║  [X] Blacklist Dreamrider to improve Plains speed                                                         
# ║  [X] add Inventory Management                                                          
# ║  [X] unequip armor at dhuum to sacrifice selected heroes  
# ║  [ ] add Heroai 
# ║  [ ] Take the Dhuum quest earlier   
# ║  [ ] Make pits quest saver and fix 3d navigation                                       
# ║                                                                  
# ╚══════════════════════════════════════════════════════════════════



# Model ID 3078 = Dhuum ghost buff NPC (informational reference)
MODULE_NAME = "Underworld"
MODULE_ICON = "Textures/Module_Icons/Underworld.png"

# Override the help window
BOT_NAME = "Underworld"
_ini_file = os.path.join(Py4GW.Console.get_projects_path(), "Widgets", "Config", "UnderworldBot.ini")
_ini = IniHandler(_ini_file)
bot = Botting(BOT_NAME, config_draw_path=True, upkeep_auto_inventory_management_active=True)
bot.Templates.Aggressive()
# Override the help window
bot.UI.override_draw_help(lambda: _draw_help())
bot.UI.override_draw_config(lambda: _draw_settings())  # Disable default config window
MAIN_LOOP_HEADER_NAME = ""
_entered_dungeon: bool = False      # set True once map 72 is loaded; watchdog uses this
_dhuum_fight_active: bool = False   # set True from start of Dhuum fight to chest spawn
_run_start_uptime_ms: int = 0       # Map.GetInstanceUptime() value (ms) when the dungeon was entered
_king_frozenwind_model_id: int = 2403
_SKELETON_OF_DHUUM_MODEL_ID: int = 2392
_DRAW_BLOCKED_AREAS_3D = True
_BLOCKED_AREA_SEGMENTS = 48
_BLOCKED_AREA_THICKNESS = 2.5
_BLOCKED_AREA_COLOR = Utils.RGBToColor(255, 40, 40, 170)
_BLOCKED_AREA_RADIUS = 200.0
_blacklist_draw_points: list[tuple[float, float]] = []  # legacy, kept for compatibility
_active_move_path_3d: list[tuple[float, float, float]] = []  # current move path drawn every frame
_pending_wipe_recovery: bool = False   # set by coroutine; consumed by main() before bot.Update()
_pending_wipe_reason:   str  = ""      # human-readable label logged when the restart fires

# ── Quest section completion tracking ────────────────────────────────────────
_QUEST_ORDER: list[str] = [
    "Clear the Chamber",
    "Pass the Mountains",
    "Restore Mountains",
    "Deamon Assassin",
    "Restore Planes",
    "The Four Horsemen",
    "Restore Pools",
    "Terrorweb Queen",
    "Restore Pit",
    "Imprisoned Spirits",
    "Restore Vale",
    "Wrathfull Spirits",
    "Unwanted Guests",
    "Restore Wastes",
    "Servants of Grenth",
    "Dhuum",
]
_quest_completion_times: dict[str, int] = {}   # quest_name → GetInstanceUptime() ms at completion

UW_MAP_ID = 72
UW_SCROLL_MODEL_ID = int(ModelID.Passage_Scroll_Uw.value)  # 3746
UW_ENTRYPOINTS: dict[str, tuple[str, int]] = {
    "embark_beach":       ("Embark Beach",       int(name_to_map_id["Embark Beach"])),
    "temple_of_the_ages": ("Temple of the Ages", int(name_to_map_id["Temple of the Ages"])),
    "chantry_of_secrets": ("Chantry of Secrets", int(name_to_map_id["Chantry of Secrets"])),
    "zin_ku_corridor":    ("Zin Ku Corridor",     int(name_to_map_id["Zin Ku Corridor"])),
}
DEFAULT_UW_ENTRYPOINT_KEY = "embark_beach"

# ── Combat adapter (Strategy Pattern) ────────────────────────────────────────
# _get_adapter() returns the right singleton based on BotSettings.BotMode.
# CB mode (default): UWCBAdapter — uses CustomBehaviors shared-memory flags.
# HeroAI mode:       UWHeroAIAdapter — drives native GW flags + HeroAI options.
_cb_adapter_instance = None
_heroai_adapter_instance = None


def _get_adapter():
    global _cb_adapter_instance, _heroai_adapter_instance
    if BotSettings.BotMode == "heroai":
        if _heroai_adapter_instance is None:
            from Sources.sch0l0ka.adapter.uw_heroai_adapter import UWHeroAIAdapter
            _heroai_adapter_instance = UWHeroAIAdapter(BOT_NAME)
        return _heroai_adapter_instance
    if _cb_adapter_instance is None:
        from Sources.sch0l0ka.adapter.uw_cb_adapter import UWCBAdapter
        _cb_adapter_instance = UWCBAdapter(BOT_NAME)
    return _cb_adapter_instance


def _mark_entered_dungeon() -> None:
    global _entered_dungeon, _run_start_uptime_ms
    _entered_dungeon = True
    _run_start_uptime_ms = Map.GetInstanceUptime()


def _set_dhuum_fight_active(value: bool) -> None:
    global _dhuum_fight_active
    _dhuum_fight_active = value


def _record_quest_done(name: str) -> None:
    """Record the completion time (instance uptime ms) for a quest section."""
    if name not in _quest_completion_times:
        _quest_completion_times[name] = Map.GetInstanceUptime()


class InventorySettings:
    """Settings for between-run inventory management."""
    RefillEnabled:          bool = bool(_ini.read_bool(BOT_NAME, "inv_refill_enabled",      True))
    RestockKits:            bool = bool(_ini.read_bool(BOT_NAME, "inv_restock_kits",         True))
    RestockCons:            bool = bool(_ini.read_bool(BOT_NAME, "inv_restock_cons",         True))
    DepositMaterials:       bool = bool(_ini.read_bool(BOT_NAME, "inv_deposit_mats",         True))
    SellNonConsMaterials:   bool = bool(_ini.read_bool(BOT_NAME, "inv_sell_non_cons_mats",   False))
    SellAllCommonMaterials: bool = bool(_ini.read_bool(BOT_NAME, "inv_sell_all_common_mats", False))
    BuyEctoplasm:           bool = bool(_ini.read_bool(BOT_NAME, "inv_buy_ecto",             False))
    InventoryLocation:      str  = str(_ini.read_key(BOT_NAME,  "inv_location",             "guild_hall") or "guild_hall")

    @classmethod
    def save(cls) -> None:
        _ini.write_key(BOT_NAME, "inv_refill_enabled",      str(cls.RefillEnabled))
        _ini.write_key(BOT_NAME, "inv_restock_kits",        str(cls.RestockKits))
        _ini.write_key(BOT_NAME, "inv_restock_cons",        str(cls.RestockCons))
        _ini.write_key(BOT_NAME, "inv_deposit_mats",        str(cls.DepositMaterials))
        _ini.write_key(BOT_NAME, "inv_sell_non_cons_mats",  str(cls.SellNonConsMaterials))
        _ini.write_key(BOT_NAME, "inv_sell_all_common_mats",str(cls.SellAllCommonMaterials))
        _ini.write_key(BOT_NAME, "inv_buy_ecto",            str(cls.BuyEctoplasm))
        _ini.write_key(BOT_NAME, "inv_location",            str(cls.InventoryLocation))


class DhuumSettings:
    """Which multibox accounts are designated as sacrifice targets in the Dhuum fight."""
    _raw: str = _ini.read_key(BOT_NAME, "dhuum_sacrifice_emails", "")
    SacrificeEmails: set[str] = set(e.strip() for e in _raw.split(";") if e.strip())

    @classmethod
    def save(cls) -> None:
        _ini.write_key(BOT_NAME, "dhuum_sacrifice_emails", ";".join(sorted(cls.SacrificeEmails)))

    @classmethod
    def is_sacrifice(cls, email: str) -> bool:
        return email in cls.SacrificeEmails

    @classmethod
    def set_sacrifice(cls, email: str, value: bool) -> None:
        if value:
            cls.SacrificeEmails.add(email)
        else:
            cls.SacrificeEmails.discard(email)
        cls.save()


class ImprisonedSpiritsSettings:
    """Team assignments for the Imprisoned Spirits quest (left vs. right side)."""
    _raw_left:  str = _ini.read_key(BOT_NAME, "imprisoned_left_emails",  "") or ""
    _raw_right: str = _ini.read_key(BOT_NAME, "imprisoned_right_emails", "") or ""
    LeftTeamEmails:  list[str] = [e.strip() for e in _raw_left.split(";")  if e.strip()]
    RightTeamEmails: list[str] = [e.strip() for e in _raw_right.split(";") if e.strip()]

    @classmethod
    def save(cls) -> None:
        _ini.write_key(BOT_NAME, "imprisoned_left_emails",  ";".join(cls.LeftTeamEmails))
        _ini.write_key(BOT_NAME, "imprisoned_right_emails", ";".join(cls.RightTeamEmails))

    @classmethod
    def get_team(cls, email: str) -> str:
        """Returns 'left' or 'right'. Defaults to 'right' if unassigned."""
        if email in cls.LeftTeamEmails:
            return "left"
        return "right"

    @classmethod
    def set_team(cls, email: str, team: str) -> None:
        cls.LeftTeamEmails  = [e for e in cls.LeftTeamEmails  if e != email]
        cls.RightTeamEmails = [e for e in cls.RightTeamEmails if e != email]
        if team == "left":
            cls.LeftTeamEmails.append(email)
        else:
            cls.RightTeamEmails.append(email)
        cls.save()

    @classmethod
    def apply_defaults_if_empty(cls, accounts: list) -> None:
        """If no assignments saved yet, put first 3 on left, rest on right."""
        if cls.LeftTeamEmails or cls.RightTeamEmails:
            return
        emails = [str(a.AccountEmail) for a in accounts]
        cls.LeftTeamEmails  = emails[:3]
        cls.RightTeamEmails = emails[3:]
        cls.save()


class BotSettings:
    Repeat:    bool = bool(_ini.read_bool(BOT_NAME, "quest_repeat",    False))
    UseCons:   bool = bool(_ini.read_bool(BOT_NAME, "quest_use_cons",  True))
    HardMode:  bool = bool(_ini.read_bool(BOT_NAME, "quest_hardmode",  False))
    BotMode:   str  = str(_ini.read_key(BOT_NAME,  "quest_bot_mode",  "custom_behavior") or "custom_behavior")

    @classmethod
    def save(cls) -> None:
        _ini.write_key(BOT_NAME, "quest_repeat",    str(cls.Repeat))
        _ini.write_key(BOT_NAME, "quest_use_cons",  str(cls.UseCons))
        _ini.write_key(BOT_NAME, "quest_hardmode",  str(cls.HardMode))
        _ini.write_key(BOT_NAME, "quest_bot_mode",  str(cls.BotMode))


class EnterSettings:
    """Settings for how the bot travels to and enters the Underworld."""
    EntryPoint: str = str(_ini.read_key(BOT_NAME, "enter_entrypoint", DEFAULT_UW_ENTRYPOINT_KEY) or DEFAULT_UW_ENTRYPOINT_KEY)

    @classmethod
    def save(cls) -> None:
        _ini.write_key(BOT_NAME, "enter_entrypoint", str(cls.EntryPoint))


# ── Thin-wrapper toggle functions ────────────────────────────────────────────
# Each delegates to the active adapter so quest-section code needs no changes.

def _toggle_wait_if_aggro(enabled: bool) -> None:
    _get_adapter().toggle_wait_if_aggro(enabled)

def _toggle_wait_for_party(enabled: bool) -> None:
    _get_adapter().toggle_wait_for_party(enabled)

def _toggle_move_to_party_member_if_dead(enabled: bool) -> None:
    _get_adapter().toggle_move_to_party_member_if_dead(enabled)

def _enqueue_section(bot_instance: Botting, attr_name: str, label: str, section_fn):
    bot_instance.States.AddHeader(label)
    bot_instance.States.AddCustomState(
        lambda l=label: _get_adapter().reactivate_for_step(bot_instance, l),
        f"[Setup] {label}",
    )
    section_fn(bot_instance)

def _add_header_with_name(bot_instance: Botting, step_name: str) -> str:
    header_name = f"[H]{step_name}_{bot_instance.config.get_counter('HEADER_COUNTER')}"
    bot_instance.config.FSM.AddYieldRoutineStep(
        name=header_name,
        coroutine_fn=lambda: Routines.Yield.wait(100),
    )
    return header_name

def _restart_main_loop(bot_instance: Botting, reason: str) -> None:
    global _entered_dungeon, _dhuum_fight_active
    _entered_dungeon = False
    _dhuum_fight_active = False
    _quest_completion_times.clear()
    target = MAIN_LOOP_HEADER_NAME
    fsm = bot_instance.config.FSM
    fsm.pause()
    fsm.finished = False  # clear finished flag in case the FSM had reached its last state
    try:
        if target:
            fsm.jump_to_state_by_name(target)
            ConsoleLog(BOT_NAME, f"[WIPE] {reason} – restarting at {target}.", Py4GW.Console.MessageType.Info)
        else:
            ConsoleLog(BOT_NAME, "[WIPE] MAIN_LOOP header missing, restarting from first state.", Py4GW.Console.MessageType.Warning)
            fsm.jump_to_state_by_step_number(0)
    except (ValueError, IndexError):
        # ValueError  – state name not found; IndexError – states list empty
        ConsoleLog(BOT_NAME, f"[WIPE] Header '{target}' not found, restarting from first state.", Py4GW.Console.MessageType.Error)
        try:
            fsm.jump_to_state_by_step_number(0)
        except (ValueError, IndexError):
            ConsoleLog(BOT_NAME, "[WIPE] FSM has no states – cannot restart.", Py4GW.Console.MessageType.Error)
    finally:
        fsm.resume()


def _request_wipe_restart(reason: str) -> None:
    """Request a wipe-recovery restart from inside a managed coroutine.

    Keeps the FSM paused and sets a flag that main() will consume BEFORE
    the next bot.Update() call — guaranteeing the resume never happens from
    inside FSM.update()'s managed-coroutines loop (which would allow
    execute() to run with a potentially stale or None current_state).
    """
    global _pending_wipe_recovery, _pending_wipe_reason
    _pending_wipe_recovery = True
    _pending_wipe_reason   = reason


def _ensure_minimum_gold(bot_instance: Botting, minimum_gold: int = 1000, withdraw_amount: int = 10000) -> None:
    def _check_and_restock():
        gold_on_char = GLOBAL_CACHE.Inventory.GetGoldOnCharacter()
        if gold_on_char >= minimum_gold:
            return

        gold_in_storage = GLOBAL_CACHE.Inventory.GetGoldInStorage()
        amount_to_withdraw = min(withdraw_amount, gold_in_storage)

        if amount_to_withdraw <= 0:
            ConsoleLog(BOT_NAME, "[GOLD] Storage empty – cannot restock gold.", Py4GW.Console.MessageType.Warning)
            return

        ConsoleLog(
            BOT_NAME,
            f"[GOLD] Inventory only has {gold_on_char}g. Withdrawing {amount_to_withdraw}g from storage.",
            Py4GW.Console.MessageType.Info,
        )
        GLOBAL_CACHE.Inventory.WithdrawGold(amount_to_withdraw)

    bot_instance.States.AddCustomState(_check_and_restock, "Ensure Minimum Gold")
    bot_instance.Wait.ForTime(1000)


def _flag_both(party_pos: int, flag_index: int, x, y) -> None:
    _get_adapter().set_flag(flag_index, x, y)


def _enqueue_spread_flags(bot_instance: Botting, flag_points: list[tuple[int, int]]) -> None:
    """Clear flags, auto-assign emails, then set adapter flags for each position.
    Only heroes are flagged (player/party leader is excluded automatically)."""
    bot_instance.States.AddCustomState(
        lambda: _get_adapter().clear_flags(),
        "Clear Flags",
    )
    bot_instance.States.AddCustomState(
        lambda: _get_adapter().auto_assign_flag_emails(),
        "Assign Flag Emails",
    )
    for idx, (flag_x, flag_y) in enumerate(flag_points):
        bot_instance.States.AddCustomState(
            lambda i=idx, x=flag_x, y=flag_y: _get_adapter().set_flag(i, x, y),
            f"Set Flag {idx}",
        )


def _enqueue_imprisoned_spirits_flags(bot_instance: Botting) -> None:
    """Clear flags, then assign left/right team accounts to their respective flag positions.
    The player's own account is excluded (it navigates via the bot FSM directly).
    Left accounts → LEFT_POINTS sequentially; right accounts → RIGHT_POINTS sequentially."""
    LEFT_POINTS  = [(13849, 6602), (13876, 6752), (13985, 6840), (13598, 6779)]
    RIGHT_POINTS = [(12871, 2512), (12640, 2485), (12402, 2472), (12137, 2444), (12150, 2139)]

    def _set_team_flags() -> None:
        _get_adapter().clear_flags()
        my_email     = Player.GetAccountEmail()
        left_emails  = ImprisonedSpiritsSettings.LeftTeamEmails
        right_emails = ImprisonedSpiritsSettings.RightTeamEmails

        cb_idx = 0

        left_pt = 0
        for email in left_emails:
            if email == my_email:
                continue
            if left_pt >= len(LEFT_POINTS):
                break
            x, y = LEFT_POINTS[left_pt]
            _get_adapter().set_flag_for_email(email, cb_idx, x, y)
            ConsoleLog(BOT_NAME, f"[Imprisoned] Left  [{cb_idx}] {email} \u2192 ({x},{y})", Py4GW.Console.MessageType.Info)
            cb_idx  += 1
            left_pt += 1

        right_pt = 0
        for email in right_emails:
            if email == my_email:
                continue
            if right_pt >= len(RIGHT_POINTS):
                break
            x, y = RIGHT_POINTS[right_pt]
            _get_adapter().set_flag_for_email(email, cb_idx, x, y)
            ConsoleLog(BOT_NAME, f"[Imprisoned] Right [{cb_idx}] {email} \u2192 ({x},{y})", Py4GW.Console.MessageType.Info)
            cb_idx   += 1
            right_pt += 1

        ConsoleLog(BOT_NAME, f"[Imprisoned] Flagged {cb_idx} account(s) total.", Py4GW.Console.MessageType.Info)

    bot_instance.States.AddCustomState(_set_team_flags, "Set Imprisoned Spirits Team Flags")


def WaitTillQuestDone(bot_instance: Botting) -> None:
    from Py4GWCoreLib.Quest import Quest
    bot_instance.Wait.UntilCondition(
        lambda: (Quest.GetActiveQuest() > 0) and Quest.IsQuestCompleted(Quest.GetActiveQuest())
    )


def _coro_hold_horsemen_position() -> Generator[Any, Any, None]:
    """Move the player back to the Four Horsemen wait position every 5 s.
    Runs once as a YieldRoutineStep; exits as soon as the quest is completed.
    """
    from Py4GWCoreLib.Quest import Quest
    _HOLD_X, _HOLD_Y = 11510.0, -18234.0
    _INTERVAL_MS = 5000
    while True:
        if (Quest.GetActiveQuest() > 0) and Quest.IsQuestCompleted(Quest.GetActiveQuest()):
            return
        Player.Move(_HOLD_X, _HOLD_Y)
        yield from Routines.Yield.wait(_INTERVAL_MS)


def _move_with_unstuck(
    bot_instance: Botting,
    target_x: float,
    target_y: float,
    step_name: str = "",
    stuck_check_ms: int = 1000,
    stuck_threshold: float = 50.0,
    backup_ms: int = 800,
    max_retries: int = 5,
    timeout: int = 60_000,
    recalc_interval_ms: int = 500,
) -> None:
    """Move to (target_x, target_y) with continuous path recalculation every recalc_interval_ms.

    Every interval the path is rebuilt from the current player position, hard-avoiding
    all navmesh nodes within 150 units of any blacklisted alive enemy.
    If no avoiding path exists (narrow corridor), falls back to a direct navmesh path.
    The active path is stored in _active_move_path_3d and drawn as cyan 3D lines every frame.
    Stuck detection: if progress toward the target is less than stuck_threshold per interval
    for max_retries consecutive intervals → /stuck + walk backwards.
    """
    import math
    _AVOID_RADIUS = 150.0

    def _coro():
        global _active_move_path_3d
        import heapq as _heapq
        from Py4GWCoreLib.Pathing import AutoPathing, AStar, AStarNode, densify_path2d
        from Py4GWCoreLib.EnemyBlacklist import EnemyBlacklist

        tolerance = 150.0
        tx, ty = target_x, target_y
        stuck_counter = 0

        class _AStarAvoid(AStar):
            """A* that hard-blocks any node within _AVOID_RADIUS of a blacklisted enemy."""
            def __init__(self, navmesh, avoid_pts):
                super().__init__(navmesh)
                self._avoid = avoid_pts

            def _blocked(self, node_id: int) -> bool:
                if not self._avoid:
                    return False
                nx, ny = self.navmesh.get_position(node_id)
                return any(math.hypot(nx - ax, ny - ay) < _AVOID_RADIUS for ax, ay in self._avoid)

            def search(self, start_pos, goal_pos):
                s_id = self.navmesh.find_trapezoid_id_by_coord(start_pos)
                g_id = self.navmesh.find_trapezoid_id_by_coord(goal_pos)
                if s_id is None or g_id is None:
                    return False
                ol: list = []
                _heapq.heappush(ol, AStarNode(s_id, 0, self.heuristic(s_id, g_id)))
                came: dict = {}
                cost: dict = {s_id: 0}
                while ol:
                    cur = _heapq.heappop(ol)
                    if cur.id == g_id:
                        self._reconstruct(came, g_id)
                        self.path.insert(0, start_pos)
                        self.path.append(goal_pos)
                        return True
                    for nb in self.navmesh.get_neighbors(cur.id):
                        if nb != g_id and self._blocked(nb):
                            continue
                        nc = cost[cur.id] + self.heuristic(cur.id, nb)
                        if nb not in cost or nc < cost[nb]:
                            cost[nb] = nc
                            _heapq.heappush(ol, AStarNode(nb, nc, nc + self.heuristic(nb, g_id), cur.id))
                            came[nb] = cur.id
                return False

        def _escape_point(px, py, avoid_pts) -> tuple[float, float] | None:
            """Return the closest point that lies outside all avoid zones, or None if already clear."""
            best_dist = float("inf")
            best_pt: tuple[float, float] | None = None
            for ax, ay in avoid_pts:
                d = math.hypot(px - ax, py - ay)
                if d < _AVOID_RADIUS:
                    # Step directly away from this enemy just past the radius
                    if d < 1.0:
                        dx, dy = 1.0, 0.0
                    else:
                        dx, dy = (px - ax) / d, (py - ay) / d
                    ex = ax + dx * (_AVOID_RADIUS + 20.0)
                    ey = ay + dy * (_AVOID_RADIUS + 20.0)
                    escape_d = math.hypot(ex - px, ey - py)
                    if escape_d < best_dist:
                        best_dist = escape_d
                        best_pt = (ex, ey)
            return best_pt

        def _build_path(px, py, avoid_pts):
            """Return (move_path, vis_path). move_path is densified for FollowPath,
            vis_path is smoothed only (fewer points) for 3D drawing.
            If the player is currently inside an avoid zone, a short escape segment
            is prepended so the route leaves the zone first."""
            navmesh = AutoPathing().get_navmesh()
            if navmesh is None:
                return [(tx, ty)], [(tx, ty)]

            # If already inside a blocked zone, prepend an escape step.
            escape = _escape_point(px, py, avoid_pts) if avoid_pts else None
            start = escape if escape else (px, py)

            for pts in (avoid_pts, []):
                ast = _AStarAvoid(navmesh, pts)
                if ast.search(start, (tx, ty)):
                    raw = ast.get_path()
                    try:
                        smoothed = navmesh.smooth_path_by_los(raw, margin=100, step_dist=200.0) or raw
                    except Exception:
                        smoothed = raw
                    if escape:
                        smoothed = [escape] + smoothed
                    return densify_path2d(smoothed), smoothed
                if not avoid_pts:
                    break  # already tried bare pass

            return [(tx, ty)], [(tx, ty)]

        while True:
            px, py = Player.GetXY()
            if math.hypot(tx - px, ty - py) <= tolerance:
                _active_move_path_3d = []
                return

            bl = EnemyBlacklist()
            avoid_pts = [
                Agent.GetXY(eid)
                for eid in AgentArray.GetEnemyArray()
                if bl.is_blacklisted(eid) and Agent.IsAlive(eid)
            ]

            # Only recalculate frequently when a blacklisted enemy is within 500 units.
            enemy_nearby = any(
                math.hypot(px - ax, py - ay) <= 500.0
                for ax, ay in avoid_pts
            )
            follow_timeout = recalc_interval_ms if enemy_nearby else 0  # 0 = no timeout, run to end

            move_path, vis_path = _build_path(px, py, avoid_pts if enemy_nearby else [])

            try:
                _ov = Overlay()
                _active_move_path_3d = [(x, y, _ov.FindZ(x, y, 0)) for x, y in vis_path]
            except Exception:
                _active_move_path_3d = []

            reached = yield from Routines.Yield.Movement.FollowPath(
                path_points=move_path,
                tolerance=tolerance,
                timeout=follow_timeout,
            )
            if reached:
                _active_move_path_3d = []
                return

            npx, npy = Player.GetXY()
            progress = math.hypot(tx - px, ty - py) - math.hypot(tx - npx, ty - npy)

            if progress < stuck_threshold:
                stuck_counter += 1
                if stuck_counter >= max_retries:
                    ConsoleLog(
                        BOT_NAME,
                        f"[Move] Stuck at ({px:.0f},{py:.0f}) → ({tx:.0f},{ty:.0f}). Recovering.",
                        Py4GW.Console.MessageType.Warning,
                    )
                    Player.SendChatCommand("stuck")
                    yield from Routines.Yield.wait(1000)
                    yield from Routines.Yield.Movement.WalkBackwards(backup_ms)
                    yield from Routines.Yield.wait(300)
                    stuck_counter = 0
            else:
                stuck_counter = 0

    label = step_name or f"MoveUnstuck_{target_x:.0f}_{target_y:.0f}"
    bot_instance.config.FSM.AddYieldRoutineStep(name=label, coroutine_fn=_coro)


def FocusKeeperOfSouls(bot_instance: Botting):
    KeeperOfSoulsModelID = 2373
    def _focus_logic():
        enemies = [e for e in AgentArray.GetEnemyArray() if Agent.IsAlive(e) and Agent.GetModelID(e) == KeeperOfSoulsModelID]
        
        if not enemies:
            return
        
        player_pos = Player.GetXY()
        closest_enemy = min(enemies, key=lambda e: ((player_pos[0] - Agent.GetXYZ(e)[0])**2 + (player_pos[1] - Agent.GetXYZ(e)[1])**2)**0.5)
        if Agent.IsValid(closest_enemy):
            _get_adapter().set_custom_target(closest_enemy)

    bot_instance.States.AddCustomState(_focus_logic, "Focus Keeper of Souls")


def _coro_draw_blocked_areas_3d(bot_instance: Botting):
    """No-op placeholder — drawing is handled entirely by _draw_blocked_areas_overlay() in main()."""
    while True:
        yield from Routines.Yield.wait(500)


def _draw_blocked_areas_overlay() -> None:
    """Query blacklisted enemy positions and draw circles every frame. Called from main()."""
    if not _DRAW_BLOCKED_AREAS_3D:
        return
    if Map.GetMapID() != UW_MAP_ID:
        return
    try:
        from Py4GWCoreLib.EnemyBlacklist import EnemyBlacklist
        _bl = EnemyBlacklist()
        avoid_points = [
            Agent.GetXY(_eid)
            for _eid in AgentArray.GetEnemyArray()
            if _bl.is_blacklisted(_eid) and Agent.IsAlive(_eid)
        ]
        if not avoid_points:
            return
        _overlay = Overlay()
        _overlay.BeginDraw()
        for _ax, _ay in avoid_points:
            _az = _overlay.FindZ(_ax, _ay, 0)
            _overlay.DrawPoly3D(
                _ax,
                _ay,
                _az,
                radius=_BLOCKED_AREA_RADIUS,
                color=_BLOCKED_AREA_COLOR,
                numsegments=_BLOCKED_AREA_SEGMENTS,
                thickness=_BLOCKED_AREA_THICKNESS,
            )
        _overlay.EndDraw()
    except Exception:
        pass


def _draw_active_path_overlay() -> None:
    """Draw the current move path as cyan 3D lines every frame. Called from main()."""
    path = _active_move_path_3d
    if not path or len(path) < 2:
        return
    if Map.GetMapID() != UW_MAP_ID:
        return
    try:
        _color = Utils.RGBToColor(0, 220, 255, 220)
        _overlay = Overlay()
        _overlay.BeginDraw()
        for i in range(1, len(path)):
            x1, y1, z1 = path[i - 1]
            x2, y2, z2 = path[i]
            _overlay.DrawLine3D(x1, y1, z1, x2, y2, z2, _color, 3.0)
        _overlay.EndDraw()
    except Exception:
        pass


def _coro_skeleton_dhuum_watchdog(bot: Botting):
    """Continuously target the nearest alive Skeleton of Dhuum within spell range
    while pause_on_danger is active."""
    from Py4GWCoreLib.enums import Range
    while True:
        yield from Routines.Yield.wait(250)

        if not bot.config.fsm_running:
            continue
        if not _entered_dungeon:
            continue
        if Map.GetMapID() != UW_MAP_ID:
            continue
        if not bot.config.pause_on_danger_fn():
            continue

        player_pos = Player.GetXY()
        skeletons = [
            e for e in AgentArray.GetEnemyArray()
            if Agent.IsAlive(e)
            and int(Agent.GetModelID(e)) == _SKELETON_OF_DHUUM_MODEL_ID
            and Utils.Distance(player_pos, Agent.GetXY(e)) <= Range.Spellcast.value
        ]
        if not skeletons:
            continue

        nearest = min(skeletons, key=lambda e: Utils.Distance(player_pos, Agent.GetXY(e)))
        # Re-check validity: the agent may have died between loop and ChangeTarget call.
        if Agent.IsValid(nearest):
            _get_adapter().set_custom_target(nearest)


def _coro_dhuum_spirit_form_watchdog(bot: Botting):
    """Monitor all ShMem party members during the Dhuum fight for the Spirit Form buff
    (skill ID 3134 — Spirit_Form_disguise).  As soon as an account gains the buff,
    its flag is repositioned to the ghost position AND a PixelStack command is sent
    so the ghost account immediately walks there."""
    _SPIRIT_FORM_SKILL_ID = 3134
    _SPIRIT_FLAG_X = -13922.0
    _SPIRIT_FLAG_Y = 17153.0
    _already_flagged: set[str] = set()

    while True:
        yield from Routines.Yield.wait(500)

        if not bot.config.fsm_running:
            continue
        if not _dhuum_fight_active:
            # Reset tracker when outside the fight so the next run starts clean.
            _already_flagged.clear()
            continue

        current_map_id = Map.GetMapID()
        if current_map_id != UW_MAP_ID:
            continue

        my_email = Player.GetAccountEmail()

        for account in GLOBAL_CACHE.ShMem.GetAllAccountData() or []:
            if not getattr(account, "IsSlotActive", True):
                continue
            email = str(getattr(account, "AccountEmail", "") or "").strip()
            if not email or email in _already_flagged:
                continue
            # Only process accounts in the same map instance.
            if getattr(account.AgentData.Map, "MapID", 0) != current_map_id:
                continue

            # Check the buff array for Spirit Form (buff ID 3134).
            has_spirit_form = any(
                b.SkillId == _SPIRIT_FORM_SKILL_ID
                for b in account.AgentData.Buffs.Buffs
                if b.SkillId != 0
            )
            if not has_spirit_form:
                continue

            _already_flagged.add(email)
            ConsoleLog(
                BOT_NAME,
                f"[Dhuum] {email} gained Spirit Form — repositioning flag and sending to ghost position.",
                Py4GW.Console.MessageType.Info,
            )
            # Update the flag so CB/HeroAI keeps the ghost at the target position.
            _get_adapter().update_flag_position_for_email(email, _SPIRIT_FLAG_X, _SPIRIT_FLAG_Y)
            # Send a direct PixelStack command so the ghost walks there immediately,
            # bypassing any flag-polling delay on the receiving account.
            GLOBAL_CACHE.ShMem.SendMessage(
                sender_email=my_email,
                receiver_email=email,
                command=SharedCommandType.PixelStack,
                params=(_SPIRIT_FLAG_X, _SPIRIT_FLAG_Y, 0.0, 0.0),
            )


def bot_routine(bot: Botting):
    global MAIN_LOOP_HEADER_NAME, _run_start_uptime_ms

    # Set a fallback start time so Duration is never 00:00:00 if _mark_entered_dungeon
    # was not reached (e.g. bot started directly at a later section).
    if _run_start_uptime_ms == 0:
        _run_start_uptime_ms = Map.GetInstanceUptime()

    # ── One-time adapter and coroutine setup ──────────────────────────────────
    bot.Events.OnPartyWipeCallback(lambda: OnPartyWipe(bot))
    _get_adapter().set_blessing_enabled(True)
    _get_adapter().setup(bot)

    # Managed coroutines run on every FSM frame.  They must be registered before
    # the quest states so they are active from the very first step onwards.
    bot.config.FSM.AddManagedCoroutine("UW_DrawBlockedAreas3D", lambda: _coro_draw_blocked_areas_3d(bot))
    bot.config.FSM.AddManagedCoroutine("UW_SkeletonDhuumWatchdog", lambda: _coro_skeleton_dhuum_watchdog(bot))
    bot.config.FSM.AddManagedCoroutine("UW_DhuumSpiritFormWatchdog", lambda: _coro_dhuum_spirit_form_watchdog(bot))

    # Broadcast widget-policy states: disable/enable CB or HeroAI on all accounts.
    _get_adapter().configure_startup_states(bot)
    bot.Templates.Aggressive()

    # ── Quest-section state chain ─────────────────────────────────────────────
    # MAIN_LOOP_HEADER_NAME is the FSM jump target used by the wipe handler so
    # a restart skips the one-time setup above and jumps straight to this point.
    MAIN_LOOP_HEADER_NAME = _add_header_with_name(bot, "MAIN_LOOP")

    Enter_UW(bot)
    Clear_the_Chamber(bot)
    _enqueue_section(bot, "PassTheMountains", "Pass the Mountains", Pass_The_Mountains)
    _enqueue_section(bot, "RestoreMountains", "Restore Mountains", Restore_Mountains)
    _enqueue_section(bot, "DeamonAssassin", "Deamon Assassin", Deamon_Assassin)
    _enqueue_section(bot, "RestorePlanes", "Restore Planes", Restore_Planes)
    _enqueue_section(bot, "TheFourHorsemen", "The Four Horsemen", The_Four_Horsemen)
    _enqueue_section(bot, "RestorePools", "Restore Pools", Restore_Pools)
    _enqueue_section(bot, "TerrorwebQueen", "Terrorweb Queen", Terrorweb_Queen)
    _enqueue_section(bot, "RestorePit", "Restore Pit", Restore_Pit)
    _enqueue_section(bot, "ImprisonedSpirits", "Imprisoned Spirits", Imprisoned_Spirits)
    _enqueue_section(bot, "RestoreVale", "Restore Vale", Restore_Vale)
    _enqueue_section(bot, "WrathfullSpirits", "Wrathfull Spirits", Wrathfull_Spirits)
    #_enqueue_section(bot, "EscortOfSouls", "Escort of Souls", Escort_of_Souls)
    _enqueue_section(bot, "UnwantedGuests", "Unwanted Guests", Unwanted_Guests)
    _enqueue_section(bot, "RestoreWastes", "Restore Wastes", Restore_Wastes)
    _enqueue_section(bot, "ServantsOfGrenth", "Servants of Grenth", Servants_of_Grenth)
    
    _enqueue_section(bot, "Dhuum", "Dhuum", Dhuum)
    _enqueue_section(bot, "Repeat", "Repeat the whole thing", ResignAndRepeat)
    bot.States.AddHeader("END")




def Enter_UW(bot_instance: Botting):
    from Sources.modular_bot.recipes.step_context import StepContext
    from Sources.modular_bot.recipes.actions_movement import handle_random_travel, handle_wait_map_change, handle_leave_party
    from Sources.modular_bot.recipes.actions_party import handle_summon_all_accounts, handle_invite_all_accounts, handle_set_hard_mode
    from Sources.modular_bot.recipes.actions_interaction import handle_use_item

    def _make_ctx(step: dict) -> StepContext:
        return StepContext(
            bot=bot_instance,
            step=step,
            step_idx=0,
            recipe_name="UW_Enter",
            step_type=step.get("type", ""),
            step_display=step.get("name", ""),
        )

    bot_instance.States.AddHeader("Enter Underworld")

    # ── Inventory refill at GH / configured outpost ───────────────────
    bot_instance.Multibox.KickAllAccounts()
    _do_inventory_refill(bot_instance)
    _ensure_minimum_gold(bot_instance)

    if BotSettings.UseCons:
        # Withdraw consets (Essence, Grail, Armor) per account from Xunlai chest
        bot_instance.Multibox.RestockConset(10)

    # ── Leave any existing party (multibox-aware) ─────────────────────
    handle_leave_party(_make_ctx({"type": "leave_party", "name": "Leave Party", "multibox": True}))

    # ── Travel to the selected entrypoint ────────────────────────────
    entrypoint_name, entrypoint_map_id = UW_ENTRYPOINTS.get(
        EnterSettings.EntryPoint, UW_ENTRYPOINTS[DEFAULT_UW_ENTRYPOINT_KEY]
    )
    handle_random_travel(_make_ctx({
        "type": "random_travel",
        "name": f"Travel to {entrypoint_name}",
        "target_map_id": entrypoint_map_id,
    }))

    # ── Form party ───────────────────────────────────────────────────
    handle_summon_all_accounts(_make_ctx({"type": "summon_all_accounts", "name": "Summon Alts", "ms": 5000}))

    # Wait until every account has loaded into the entrypoint map (up to 90 s).
    _expected_map = entrypoint_map_id
    bot_instance.Wait.UntilCondition(
        lambda: all(int(acc.AgentData.Map.MapID) == _expected_map for acc in GLOBAL_CACHE.ShMem.GetAllAccountData()),
        duration=20000,
    )

    handle_invite_all_accounts(_make_ctx({"type": "invite_all_accounts", "name": "Invite Alts"}))

    # ── Apply hard mode before using scroll ──────────────────────────
    handle_set_hard_mode(_make_ctx({"type": "set_hard_mode", "name": "Set Hard Mode", "enabled": BotSettings.HardMode}))

    # ── Use UW scroll (model 3746) ───────────────────────────────────
    handle_use_item(_make_ctx({"type": "use_item", "name": "Use UW Scroll", "model_id": UW_SCROLL_MODEL_ID}))

    # ── Wait until inside the Underworld ────────────────────────────
    handle_wait_map_change(_make_ctx({"type": "wait_map_change", "name": "Wait For UW", "target_map_id": UW_MAP_ID}))

    bot_instance.States.AddCustomState(_mark_entered_dungeon, "Mark entered dungeon")
    bot_instance.Properties.ApplyNow("pause_on_danger", "active", True)

    


def enable_default_party_behavior(bot_instance: Botting):
    """
    Enable the baseline party behavior toggles used across Underworld missions.
    """
    bot_instance.States.AddCustomState(lambda: _toggle_wait_for_party(True), "Enable WaitIfPartyMemberTooFar")
    bot_instance.States.AddCustomState(lambda: _toggle_wait_if_aggro(True), "Enable WaitIfInAggro")
    bot_instance.States.AddCustomState(lambda: _get_adapter().set_following_enabled(True), "Enable Follow")
    bot_instance.States.AddCustomState(lambda: _get_adapter().set_combat_enabled(True), "Enable Combat")
    bot_instance.States.AddCustomState(lambda: _get_adapter().set_looting_enabled(True), "Enable Looting")


def Clear_the_Chamber(bot_instance: Botting):
    bot_instance.States.AddHeader("Clear the Chamber")
    bot_instance.States.AddCustomState(
        lambda: _get_adapter().reactivate_for_step(bot_instance, "Clear the Chamber"),
        "[Setup] Clear the Chamber",
    )
    bot_instance.States.AddCustomState(lambda: _get_adapter().set_party_leader(Player.GetAccountEmail()), "Set Party Leader")    
    # Configure the enemy blacklist for this quest section.
    bot_instance.States.AddCustomState(
        lambda: __import__("Py4GWCoreLib.EnemyBlacklist", fromlist=["EnemyBlacklist"]).EnemyBlacklist().add_name("obsidian guardian"),
        "Blacklist Obsidian Guardian",
    )
    bot_instance.States.AddCustomState(
        lambda: __import__("Py4GWCoreLib.EnemyBlacklist", fromlist=["EnemyBlacklist"]).EnemyBlacklist().add_name("vengeful aatxe"),
        "Blacklist Vengeful Aatxe",
    )
    bot_instance.States.AddCustomState(
        lambda: __import__("Py4GWCoreLib.EnemyBlacklist", fromlist=["EnemyBlacklist"]).EnemyBlacklist().add_name("chained soul"),
        "Blacklist Chained Soul",
    )
    bot_instance.States.AddCustomState(
        lambda: __import__("Py4GWCoreLib.EnemyBlacklist", fromlist=["EnemyBlacklist"]).EnemyBlacklist().remove_name("wastfull spirit"),
        "Unblacklist Wastfull Spirit",
    )
    bot_instance.States.AddCustomState(
        lambda: __import__("Py4GWCoreLib.EnemyBlacklist", fromlist=["EnemyBlacklist"]).EnemyBlacklist().remove_name("obsidian behemoth"),
        "Unblacklist Obsidian Behemoth",
    )
    bot_instance.States.AddCustomState(
        lambda: __import__("Py4GWCoreLib.EnemyBlacklist", fromlist=["EnemyBlacklist"]).EnemyBlacklist().remove_name("banished dream rider"),
        "Unblacklist Banished Dream Rider",
    )
    enable_default_party_behavior(bot_instance)
    bot_instance.States.AddCustomState(lambda: _get_adapter().set_combat_enabled(False), "Disable Combat")
    bot_instance.Move.XYAndInteractNPC(295, 7221, "go to NPC")
    bot_instance.Dialogs.AtXY(295, 7221, 0x806501, "take quest")
    bot_instance.Multibox.SendDialogToTarget(0x806501)
    bot_instance.States.AddCustomState(lambda: _get_adapter().set_combat_enabled(True), "Enable Combat")
    bot_instance.Move.XY(769, 6564, "Prepare to clear the chamber")
    bot_instance.States.AddCustomState(lambda: _get_adapter().set_forced_state(BehaviorState.CLOSE_TO_AGGRO),"Force Close_to_Aggro",)
    bot_instance.Wait.ForTime(5000)
    bot_instance.Multibox.UsePcons()
    #bot_instance.Items.UseSummoningStone()

    if BotSettings.UseCons:
        # Enable auto-renewal: Properties system re-pops each conset when it expires
        bot_instance.Properties.ApplyNow("armor_of_salvation", "active", True)
        bot_instance.Properties.ApplyNow("essence_of_celerity", "active", True)
        bot_instance.Properties.ApplyNow("grail_of_might", "active", True)
        # Immediately use conset on dungeon entry
        #bot_instance.Items.UseConset()

    bot_instance.States.AddCustomState(lambda: _get_adapter().set_forced_state(None),"Release Close_to_Aggro",)

    bot_instance.States.AddCustomState(lambda: _toggle_wait_if_aggro(True), "Enable WaitIfInAggro")
    bot_instance.States.AddCustomState(lambda: _toggle_wait_for_party(True), "Enable WaitIfPartyMemberTooFar")
    bot_instance.States.AddCustomState(lambda: _toggle_move_to_party_member_if_dead(True), "Enable MoveToPartyMemberIfDead")

    bot_instance.Move.XY(-1505, 6352, "Left")
    bot_instance.Move.XY(-755, 8982, "Mid")
    bot_instance.Move.XY(1259, 10214, "Right")
    bot_instance.Move.XY(-3729, 13414, "Right")
    bot_instance.Move.XY(-5855, 11202, "Clear the Room")
    bot_instance.Wait.ForTime(3000)
    
    bot_instance.Move.XYAndInteractNPC(-5806, 12831, "go to NPC")
    #bot_instance.Dialogs.AtXY(-5806, 12831, 0x806507, "take quest")
    bot_instance.Multibox.SendDialogToTarget(0x806507)
    bot_instance.Dialogs.AtXY(-5806, 12831, 0x806D01, "take quest")
    bot_instance.Multibox.SendDialogToTarget(0x806D01)
    bot_instance.Wait.ForTime(3000)
    bot_instance.States.AddCustomState(lambda: _record_quest_done("Clear the Chamber"), "Record Clear the Chamber done")

def Pass_The_Mountains(bot_instance: Botting):
    bot_instance.States.AddCustomState(lambda: _toggle_wait_if_aggro(True), "Enable WaitIfInAggro")
    bot_instance.States.AddCustomState(lambda: _toggle_wait_for_party(True), "Enable WaitIfPartyMemberTooFar")
    bot_instance.States.AddCustomState(lambda: _toggle_move_to_party_member_if_dead(True), "Enable MoveToPartyMemberIfDead")
    bot_instance.Move.XY(-2740, 10133, "Pass the Mountains 0")
    bot_instance.Move.XY(-728,  8910,  "Pass the Mountains 1")
    bot_instance.Move.XY(-1807, 5883,  "Pass the Mountains 2")
    bot_instance.Move.XY(-3486, 1176,  "Pass the Mountains 3")
    bot_instance.Move.XY(536,   1321,  "Pass the Mountains 4")
    bot_instance.Move.XY(3418,  2213,  "Pass the Mountains 5")
    bot_instance.Move.XY(4911,  1425,  "Pass the Mountains 6")
    bot_instance.Move.XY(7938,  616,   "Pass the Mountains 7")
    bot_instance.Move.XY(8001,  -2390, "Pass the Mountains 8")
    bot_instance.Move.XY(8705,  -5293, "Pass the Mountains 9")
    bot_instance.Move.XY(6528,  -7283, "Pass the Mountains 10")
    bot_instance.States.AddCustomState(lambda: _record_quest_done("Pass the Mountains"), "Record Pass the Mountains done")
    
    

def Restore_Mountains(bot_instance: Botting):
    bot_instance.States.AddCustomState(lambda: _toggle_wait_if_aggro(True), "Enable WaitIfInAggro")
    bot_instance.States.AddCustomState(lambda: _toggle_wait_for_party(True), "Enable WaitIfPartyMemberTooFar")
    bot_instance.States.AddCustomState(lambda: _toggle_move_to_party_member_if_dead(True), "Enable MoveToPartyMemberIfDead")
    bot_instance.Move.XY(4455,  -7967, "Restore the Mountains 1")
    bot_instance.Move.XY(2008,  -10290, "Restore the Mountains 2")
    bot_instance.Move.XY(-542,  -9046, "Restore the Mountains 3")
    bot_instance.Move.XY(-2408, -7698, "Restore the Mountains 4")
    bot_instance.Move.XY(-4233, -5583, "Restore the Mountains 5")
    bot_instance.Move.XY(-6140, -5230, "Restore the Mountains 6")
    bot_instance.Move.XY(-7923, -4567, "Restore the Mountains 7")
    bot_instance.Wait.ForTime(5000)
    bot_instance.States.AddCustomState(lambda: _record_quest_done("Restore Mountains"), "Record Restore Mountains done")

def Deamon_Assassin(bot_instance: Botting):
    bot_instance.States.AddCustomState(lambda: _toggle_wait_if_aggro(True), "Enable WaitIfInAggro")
    bot_instance.States.AddCustomState(lambda: _toggle_wait_for_party(True), "Enable WaitIfPartyMemberTooFar")
    bot_instance.States.AddCustomState(lambda: _toggle_move_to_party_member_if_dead(True), "Enable MoveToPartyMemberIfDead")
    bot_instance.Move.XYAndInteractNPC(-8250, -5171, "go to NPC")
    bot_instance.Dialogs.AtXY(-8250, -5171, 0x806801, "take quest")
    #bot_instance.Dialogs.WithEncName("Reaper of the Twin Serpent Mountains",0x806801, "Take Deamon Assassin")
    bot_instance.Move.XY(-3645, -5820, "Deamon Assassin 1")
    WaitTillQuestDone(bot_instance)
    bot_instance.States.AddCustomState(lambda: _record_quest_done("Deamon Assassin"), "Record Deamon Assassin done")

def Restore_Planes(bot_instance: Botting):
    bot_instance.States.AddCustomState(lambda: _toggle_wait_if_aggro(True), "Enable WaitIfInAggro")
    bot_instance.States.AddCustomState(lambda: _toggle_wait_for_party(True), "Enable WaitIfPartyMemberTooFar")
    bot_instance.States.AddCustomState(lambda: _toggle_move_to_party_member_if_dead(True), "Enable MoveToPartyMemberIfDead")
    '''
    Wait_for_Spawns(bot_instance,10371, -10510)
    Wait_for_Spawns(bot_instance,12795, -8811)
    Wait_for_Spawns(bot_instance,11180, -13780)
    Wait_for_Spawns(bot_instance,13740, -15087)
    bot_instance.Move.XY(11546, -13787, "Restore Planes 1")
    bot_instance.Move.XY(8530, -11585, "Restore Planes 2")
    Wait_for_Spawns(bot_instance,8533, -13394)
    Wait_for_Spawns(bot_instance,8579, -20627)
    Wait_for_Spawns(bot_instance,11218, -17404)
    '''
    bot_instance.States.AddCustomState(
        lambda: __import__("Py4GWCoreLib.EnemyBlacklist", fromlist=["EnemyBlacklist"]).EnemyBlacklist().add_name("banished dream rider"),
        "Blacklist Banished Dream Rider",
    )
    
    bot_instance.Move.XY(13837, -14736, "Restore Planes 1 left Rider")
    bot_instance.States.AddCustomState(
        lambda: __import__("Py4GWCoreLib.EnemyBlacklist", fromlist=["EnemyBlacklist"]).EnemyBlacklist().remove_name("banished dream rider"),
        "Unblacklist Banished Dream Rider",
    )
    
    Wait_for_Spawns(bot_instance,13790, -15568)
    Wait_for_Spawns(bot_instance,11287, -17921)
    bot_instance.States.AddCustomState(lambda: _record_quest_done("Restore Planes"), "Record Restore Planes done")


def The_Four_Horsemen(bot_instance: Botting):
    bot_instance.States.AddCustomState(lambda: _toggle_wait_if_aggro(True), "Enable WaitIfInAggro")
    bot_instance.States.AddCustomState(lambda: _toggle_wait_for_party(True), "Enable WaitIfPartyMemberTooFar")
    bot_instance.States.AddCustomState(lambda: _toggle_move_to_party_member_if_dead(True), "Enable MoveToPartyMemberIfDead")
    bot_instance.Move.XY(13473, -12091, "The Four Horseman 1")
    bot_instance.Wait.ForTime(10000)
    THE_FOUR_HORSEMEN_FLAG_POINTS = [
        (13432, -12100),
        (13246, -12440),
        (13072, -12188),
        (13216, -11841),
        (13639, -11866),
        (13745, -12151),
        (13520, -12436),
    ]
    #_enqueue_spread_flags(bot_instance, THE_FOUR_HORSEMEN_FLAG_POINTS)
    bot_instance.States.AddCustomState(lambda: _get_adapter().set_following_enabled(False), "Disable Following")
    bot_instance.States.AddCustomState(lambda: _get_adapter().set_looting_enabled(False), "Disable Looting")
    bot_instance.States.AddCustomState(lambda: _toggle_wait_for_party(False), "Disable WaitIfPartyMemberTooFar")
    bot_instance.States.AddCustomState(lambda: _get_adapter().set_forced_state(BehaviorState.CLOSE_TO_AGGRO),"Force Close_to_Aggro",)
    bot_instance.Move.XYAndInteractNPC(11371, -17990, "go to NPC")
    bot_instance.Dialogs.AtXY(-8250, -5171, 0x806A01, "take quest")  
    bot_instance.States.AddCustomState(lambda: _get_adapter().set_forced_state(None),"Release Close_to_Aggro",)

    bot_instance.Wait.ForTime(32000)

    bot_instance.Move.XYAndInteractNPC(11371, -17990, "TP to Chamber")
    #bot_instance.Dialogs.AtXY(11371, -17990, 0x7F, "take quest")
    #bot_instance.Dialogs.AtXY(11371, -17990, 0x86, "take quest") 
    bot_instance.Dialogs.AtXY(11371, -17990, 0x8D, "take quest") 
    bot_instance.States.AddCustomState(
        lambda: _get_adapter().clear_flags(),
        "Clear Flags",
    )

    #bot_instance.Wait.ForTime(1000)
    bot_instance.States.AddCustomState(lambda: _get_adapter().set_following_enabled(True), "Enable Following")
    bot_instance.Move.XYAndInteractNPC(-5782, 12819, "TP back to Chaos")
    #bot_instance.Dialogs.AtXY(11371, -17990, 0x7F, "take quest")
    #bot_instance.Dialogs.AtXY(11371, -17990, 0x84, "take quest") 
    bot_instance.Dialogs.AtXY(11371, -17990, 0x8B, "take quest") 
    bot_instance.Wait.ForTime(1000)
    bot_instance.States.AddCustomState(lambda: _get_adapter().set_following_enabled(True), "Enable Following")
    THE_FOUR_HORSEMEN_FLAG_POINTS_2 = [
        (11510, -18234),
        (11510, -18234),
        (11510, -18234),
        (11510, -18234),
        (11510, -18234),
        (11510, -18234),
        (11510, -18234),
    ]
    _enqueue_spread_flags(bot_instance, THE_FOUR_HORSEMEN_FLAG_POINTS_2)
    bot_instance.Party.UnflagAllHeroes()
    bot_instance.States.AddCustomState(
        lambda: bot_instance.Properties.ApplyNow("pause_on_danger", "active", False),
        "Disable PauseOnDanger for Horsemen wait",
    )
    bot_instance.config.FSM.AddYieldRoutineStep(
        name="Hold position at Horsemen",
        coroutine_fn=_coro_hold_horsemen_position,
    )
    WaitTillQuestDone(bot_instance)
    bot_instance.States.AddCustomState(
        lambda: bot_instance.Properties.ApplyNow("pause_on_danger", "active", True),
        "Re-enable PauseOnDanger after Horsemen",
    )
    bot_instance.States.AddCustomState(
        lambda: _get_adapter().clear_flags(),
        "Clear Flags",
    )
    bot_instance.Wait.ForTime(10000)
    bot_instance.Move.XYAndInteractNPC(11371, -17990, "go to NPC")
    bot_instance.Dialogs.AtXY(-8250, -5171, 0x806A07, "take quest")  
    bot_instance.States.AddCustomState(lambda: _get_adapter().set_following_enabled(True), "Enable Follow")
    bot_instance.States.AddCustomState(lambda: _toggle_wait_for_party(True), "Enable WaitIfPartyMemberTooFar")
    bot_instance.States.AddCustomState(lambda: _get_adapter().set_looting_enabled(True), "Enable Looting")
    bot_instance.States.AddCustomState(lambda: _record_quest_done("The Four Horsemen"), "Record The Four Horsemen done")

def Restore_Pools(bot_instance: Botting):
    bot_instance.States.AddCustomState(lambda: _toggle_wait_if_aggro(True), "Enable WaitIfInAggro")
    bot_instance.States.AddCustomState(lambda: _toggle_wait_for_party(True), "Enable WaitIfPartyMemberTooFar")
    bot_instance.States.AddCustomState(lambda: _toggle_move_to_party_member_if_dead(True), "Enable MoveToPartyMemberIfDead")
    '''
    Wait_for_Spawns(bot_instance,4647, -16833)
    Wait_for_Spawns(bot_instance,2098, -15543)
    '''
    bot_instance.States.AddCustomState(
        lambda: __import__("Py4GWCoreLib.EnemyBlacklist", fromlist=["EnemyBlacklist"]).EnemyBlacklist().add_name("banished dream rider"),
        "Blacklist Banished Dream Rider",
    )
    bot_instance.Move.XY(6869, -17771, "Restore Pools 1")
    bot_instance.Move.XY(2867, -19746, "Restore Pools 1")
    bot_instance.Move.XY(1753, -14703, "Restore Pools 1")
    bot_instance.Move.XY(-12703, -10990, "Restore Pools 1")
    bot_instance.Move.XY(-11849, -11986, "Restore Pools 2")
    bot_instance.Move.XY(-5974, -19739, "Restore Pools 3")
    bot_instance.Move.XY(-7217, -19394, "Restore Pools 4")
    bot_instance.Move.XY(-5688, -19471, "Restore Pools 4")
    bot_instance.States.AddCustomState(lambda: _record_quest_done("Restore Pools"), "Record Restore Pools done")

def Terrorweb_Queen(bot_instance: Botting):
    bot_instance.States.AddCustomState(lambda: _toggle_wait_if_aggro(True), "Enable WaitIfInAggro")
    bot_instance.States.AddCustomState(lambda: _toggle_wait_for_party(True), "Enable WaitIfPartyMemberTooFar")
    bot_instance.States.AddCustomState(lambda: _toggle_move_to_party_member_if_dead(True), "Enable MoveToPartyMemberIfDead")
    bot_instance.Move.XYAndInteractNPC(-6890, -19454, "go to NPC")
    bot_instance.Dialogs.AtXY(-6890, -19454, 0x806B01, "take quest")   
    bot_instance.Move.XY(-12432, -15874, "Terrorweb Queen 1")
    bot_instance.Move.XYAndInteractNPC(-6957, -19478, "go to NPC")
    bot_instance.Dialogs.AtXY(-6957, -19478, 0x806B07, "Back to Chamber")
    bot_instance.Dialogs.AtXY(-6957, -19478, 0x8B, "Back to Chamber")
    bot_instance.States.AddCustomState(lambda: _record_quest_done("Terrorweb Queen"), "Record Terrorweb Queen done")
    
def Restore_Pit(bot_instance: Botting):
    bot_instance.States.AddCustomState(lambda: _toggle_wait_if_aggro(True), "Enable WaitIfInAggro")
    bot_instance.States.AddCustomState(lambda: _toggle_wait_for_party(True), "Enable WaitIfPartyMemberTooFar")
    bot_instance.States.AddCustomState(lambda: _toggle_move_to_party_member_if_dead(True), "Enable MoveToPartyMemberIfDead")
    bot_instance.Move.XY(14178, -57, "Restore Pit 1")
    bot_instance.States.AddCustomState(
        lambda: __import__("Py4GWCoreLib.EnemyBlacklist", fromlist=["EnemyBlacklist"]).EnemyBlacklist().remove_name("banished dream rider"),
        "Unblacklist Banished Dream Rider",
    )
    bot_instance.Move.XY(15323, 2970, "Restore Pit 2")
    bot_instance.Move.XY(15393, 406, "Restore Pit 3")
    bot_instance.Move.FollowPath([
        (15252, 316),
        (13451, 1123),
        (13181, 1419),
        (13076, 1547),
    ], step_name="Cross the Bridge")
    bot_instance.Move.XY(13216, 1428, "Restore Pit 4")
    bot_instance.Move.XY(13896, 3670, "Restore Pit 5")
    bot_instance.Move.XY(15382, 6581, "Restore Pit 6")
    bot_instance.Move.XY(10620, 2665, "Restore Pit 7")
    bot_instance.Move.XY(8644, 6242, "Restore Pit 8")
    bot_instance.Wait.ForTime(3000)
    bot_instance.States.AddCustomState(lambda: _record_quest_done("Restore Pit"), "Record Restore Pit done")

def Imprisoned_Spirits(bot_instance: Botting):
    bot_instance.States.AddCustomState(lambda: _toggle_wait_if_aggro(True), "Enable WaitIfInAggro")
    bot_instance.States.AddCustomState(lambda: _toggle_wait_for_party(False), "Enable WaitIfPartyMemberTooFar")
    bot_instance.States.AddCustomState(lambda: _toggle_move_to_party_member_if_dead(False), "Enable MoveToPartyMemberIfDead")
    bot_instance.States.AddCustomState(lambda: _get_adapter().set_looting_enabled(False), "Disable Looting")
    bot_instance.Move.XY(13212, 4978)
    _enqueue_imprisoned_spirits_flags(bot_instance)
    bot_instance.States.AddCustomState(lambda: _toggle_wait_for_party(False), "Disable WaitIfPartyMemberTooFar")
    bot_instance.Move.XY(8692, 6292, "go to NPC")
    bot_instance.Move.XYAndInteractNPC(8666, 6308, "go to NPC")
    bot_instance.Dialogs.AtXY(8666, 6308, 0x806901, "take quest")
    _is_timer: list[float] = [0.0]  # [monotonic start time], captured by closures below
    bot_instance.States.AddCustomState(
        lambda: _is_timer.__setitem__(0, time.monotonic()),
        "Start Imprisoned Spirits Timer",
    )
    bot_instance.Move.XY(13652, 6117)  # Run down towards the left team
    bot_instance.Wait.UntilCondition(
        lambda: time.monotonic() - _is_timer[0] >= 20.0
    )
    bot_instance.States.AddCustomState(
        lambda: _get_adapter().clear_flags(),
        "Clear Flags",
    )
    bot_instance.Move.XY(12593, 1814)
    bot_instance.Wait.ForTime(40000)
    bot_instance.Wait.UntilCondition(
        lambda: time.monotonic() - _is_timer[0] >= 80.0
    )
    bot_instance.States.AddCustomState(
        lambda: __import__("Py4GWCoreLib.EnemyBlacklist", fromlist=["EnemyBlacklist"]).EnemyBlacklist().remove_name("chained soul"),
        "Unblacklist Chained Soul",
    )
    bot_instance.Move.XY(10437, 5005)
    WaitTillQuestDone(bot_instance)
    bot_instance.States.AddCustomState(lambda: _get_adapter().set_looting_enabled(True), "Enable Looting")
    bot_instance.States.AddCustomState(
        lambda: __import__("Py4GWCoreLib.EnemyBlacklist", fromlist=["EnemyBlacklist"]).EnemyBlacklist().add_name("chained soul"),
        "Blacklist Chained Soul",
    )

    bot_instance.Move.XY(8692, 6292, "go to NPC")
    bot_instance.Dialogs.AtXY(8692, 6292, 0x8D, "Back to Chamber")
    bot_instance.States.AddCustomState(lambda: _record_quest_done("Imprisoned Spirits"), "Record Imprisoned Spirits done")
        

def Restore_Vale(bot_instance: Botting):

    bot_instance.States.AddCustomState(lambda: _toggle_wait_if_aggro(True), "Enable WaitIfInAggro")
    bot_instance.States.AddCustomState(lambda: _toggle_wait_for_party(True), "Enable WaitIfPartyMemberTooFar")
    bot_instance.States.AddCustomState(lambda: _toggle_move_to_party_member_if_dead(True), "Enable MoveToPartyMemberIfDead")

    bot_instance.Dialogs.AtXY(-5806, 12831, 0x806C03, "take quest")
    bot_instance.Dialogs.AtXY(-5806, 12831, 0x806C01, "take quest")
    bot_instance.Items.UseSummoningStone()
    bot_instance.Move.XY(-8660, 5655, "To the Vale 1")
    bot_instance.Move.XY(-9431, 1659, "To the Vale 2")
    bot_instance.Move.XY(-11123, 2531, "To the Vale 3")
    bot_instance.Move.XY(-11926, 1146 , "To the Vale 4")
    bot_instance.Move.XY(-10691, 98 , "To the Vale 5")
    bot_instance.Move.XY(-15424, 1319 , "To the Vale 6")
    bot_instance.Move.XY(-13246, 5110 , "To the Vale 7")
    bot_instance.Move.XYAndInteractNPC(-13275, 5261, "go to NPC")
    bot_instance.Wait.ForTime(3000)
    bot_instance.States.AddCustomState(lambda: _record_quest_done("Restore Vale"), "Record Restore Vale done")

def Wrathfull_Spirits(bot_instance: Botting):
    bot_instance.States.AddCustomState(lambda: _toggle_wait_if_aggro(True), "Enable WaitIfInAggro")
    bot_instance.States.AddCustomState(lambda: _toggle_wait_for_party(True), "Enable WaitIfPartyMemberTooFar")
    bot_instance.States.AddCustomState(lambda: _toggle_move_to_party_member_if_dead(True), "Enable MoveToPartyMemberIfDead")
    bot_instance.Move.XYAndInteractNPC(-13275, 5261, "go to NPC")
    bot_instance.Dialogs.AtXY(5755, 12769, 0x806E03, "Back to Chamber")
    bot_instance.Dialogs.AtXY(5755, 12769, 0x806E01, "Back to Chamber")
    bot_instance.Templates.Pacifist()
    bot_instance.States.AddCustomState(lambda: _toggle_wait_for_party(False), "Disable WaitIfPartyMemberTooFar")
    bot_instance.States.AddCustomState(lambda: _toggle_wait_if_aggro(False), "Disable WaitIfInAggro")
    #bot_instance.States.AddCustomState(lambda: _get_adapter().set_combat_enabled(False), "Disable Combat")
    bot_instance.States.AddCustomState(
        lambda: __import__("Py4GWCoreLib.EnemyBlacklist", fromlist=["EnemyBlacklist"]).EnemyBlacklist().add_name("tortured spirit"),
        "Blacklist Tortured Spirit",
    )
    bot_instance.Move.XY(-13422, 973, "Wrathfull Spirits 1")
    bot_instance.Templates.Aggressive()
    bot_instance.States.AddCustomState(
        lambda: __import__("Py4GWCoreLib.EnemyBlacklist", fromlist=["EnemyBlacklist"]).EnemyBlacklist().remove_name("tortured spirit"),
        "Unblacklist Tortured Spirit",
    )
    #bot_instance.States.AddCustomState(lambda: _get_adapter().set_combat_enabled(True), "Enable Combat")
    bot_instance.States.AddCustomState(lambda: _toggle_wait_for_party(True), "Enable WaitIfPartyMemberTooFar") 
    bot_instance.States.AddCustomState(lambda: _toggle_wait_if_aggro(True), "Enable WaitIfInAggro")
    bot_instance.Move.XY(-10207, 1746, "Wrathfull Spirits 2")
    bot_instance.Move.XY(-13566, -229, "Wrathfull Spirits 3")
    bot_instance.Move.XY(-13287, 1996, "Wrathfull Spirits 3")
    bot_instance.Move.XY(-14486, 7113, "Wrathfull Spirits 4")
    bot_instance.Move.XY(-15226, 4129 , "Wrathfull Spirits 5")
    bot_instance.Move.XYAndInteractNPC(-13275, 5261, "go to NPC")
    bot_instance.Dialogs.AtXY(5755, 12769, 0x806E07, "Take Reward")
    bot_instance.Dialogs.AtXY(5755, 12769, 0x8D, "Back to Chamber")
    bot_instance.Wait.ForTime(3000)
    bot_instance.States.AddCustomState(lambda: _record_quest_done("Wrathfull Spirits"), "Record Wrathfull Spirits done")

def Escort_of_Souls(bot_instance: Botting):
    bot_instance.States.AddCustomState(lambda: _toggle_wait_if_aggro(True), "Enable WaitIfInAggro")
    bot_instance.States.AddCustomState(lambda: _toggle_wait_for_party(True), "Enable WaitIfPartyMemberTooFar")
    bot_instance.States.AddCustomState(lambda: _toggle_move_to_party_member_if_dead(True), "Enable MoveToPartyMemberIfDead")
    bot_instance.Wait.ForTime(5000)
    bot_instance.Move.XY(-4764, 11845, "Escort of Souls 1")
    bot_instance.Move.XYAndInteractNPC(-5806, 12831, "go to NPC")
    bot_instance.Wait.ForTime(3000)
    bot_instance.Dialogs.AtXY(-5806, 12831, 0x806C03, "take quest")
    bot_instance.Dialogs.AtXY(-5806, 12831, 0x806C01, "take quest")
    bot_instance.Move.XY(-6833, 7077, "Escort of Souls 2")
    bot_instance.Move.XY(-9606, 2110, "Escort of Souls 3")
    bot_instance.Move.XYAndInteractNPC(-13275, 5261, "go to NPC")
    #bot_instance.Dialogs.AtXY(5755, 12769, 0x7F, "Back to Chamber")
    #bot_instance.Dialogs.AtXY(5755, 12769, 0x86, "Back to Chamber")
    bot_instance.Dialogs.AtXY(5755, 12769, 0x8D, "Back to Chamber")
    bot_instance.Wait.ForTime(3000)

def Unwanted_Guests(bot_instance: Botting):
    bot_instance.States.AddCustomState(lambda: _toggle_wait_if_aggro(True), "Enable WaitIfInAggro")
    bot_instance.States.AddCustomState(lambda: _toggle_wait_for_party(True), "Enable WaitIfPartyMemberTooFar")
    bot_instance.States.AddCustomState(lambda: _toggle_move_to_party_member_if_dead(True), "Enable MoveToPartyMemberIfDead")
    #The Quest
    #1st Keeper
    bot_instance.States.AddCustomState(
        lambda: __import__("Py4GWCoreLib.EnemyBlacklist", fromlist=["EnemyBlacklist"]).EnemyBlacklist().add_name("obsidian behemoth"),
        "Blacklist Obsidian Behemoth",
    )
    _move_with_unstuck(bot_instance, -2965, 10260, "1st Keeper approach")
    bot_instance.Wait.ForTime(5000)
    bot_instance.States.AddCustomState(lambda: _get_adapter().set_following_enabled(False), "Disable Following")
    bot_instance.States.AddCustomState(lambda: _get_adapter().set_forced_state(BehaviorState.CLOSE_TO_AGGRO),"Force Close_to_Aggro")
    bot_instance.States.AddCustomState(lambda: _toggle_wait_for_party(False), "Disable wait_for_party")

    bot_instance.Move.XYAndInteractNPC(-5806, 12831, "go to NPC")
    bot_instance.Dialogs.AtXY(-5806, 12831, 0x806701, "take quest")

    bot_instance.States.AddCustomState(lambda: _get_adapter().set_forced_state(None),"Release Close_to_Aggro")
    # Acquire the Keeper target several times to give CB enough frames to lock
    # onto it, then hold position for 20 s while it is being killed.
    FocusKeeperOfSouls(bot_instance)
    bot_instance.Wait.ForTime(500)
    FocusKeeperOfSouls(bot_instance)
    bot_instance.Wait.ForTime(500)
    FocusKeeperOfSouls(bot_instance)
    bot_instance.Wait.ForTime(20000)
    bot_instance.States.AddCustomState(lambda: _get_adapter().set_following_enabled(True), "Enable Following")
    bot_instance.States.AddCustomState(lambda: _get_adapter().set_forced_state(None),"Release Close_to_Aggro",)
    bot_instance.States.AddCustomState(lambda: _toggle_wait_for_party(True), "Enable WaitIfPartyMemberTooFar")

    #2nd Keeper
    bot_instance.Move.XYAndInteractNPC(-5806, 12831, "go to NPC")
    bot_instance.Dialogs.AtXY(-5806, 12831, 0x91, "take quest")
    _move_with_unstuck(bot_instance, -12953, 750, "2nd Keeper 1")
    _move_with_unstuck(bot_instance, -8371, 4865, "2nd Keeper 2")
    FocusKeeperOfSouls(bot_instance)
    bot_instance.Wait.ForTime(500)
    FocusKeeperOfSouls(bot_instance)
    _move_with_unstuck(bot_instance, -7589, 6801, "2nd Keeper killed")

    #3rd Keeper
    _move_with_unstuck(bot_instance, -4095, 12964, "3rd Keeper approach")
    FocusKeeperOfSouls(bot_instance)
    bot_instance.Wait.ForTime(500)
    FocusKeeperOfSouls(bot_instance)
    _move_with_unstuck(bot_instance, -647, 13356, "3rd Keeper killed")

    #4th Keeper
    _move_with_unstuck(bot_instance, 1098, 12215, "4th Keeper approach")
    FocusKeeperOfSouls(bot_instance)
    bot_instance.Wait.ForTime(500)
    FocusKeeperOfSouls(bot_instance)
    _move_with_unstuck(bot_instance, 3113, 9503, "4th Keeper killed")

    #5th Keeper
    _move_with_unstuck(bot_instance, 1586, 10362, "5th Keeper approach")
    FocusKeeperOfSouls(bot_instance)
    bot_instance.Wait.ForTime(500)
    FocusKeeperOfSouls(bot_instance)
    _move_with_unstuck(bot_instance, 367, 7214, "5th Keeper killed")

    #6th Keeper
    _move_with_unstuck(bot_instance, -3125, 916, "6th Keeper 1")
    _move_with_unstuck(bot_instance, -344, 2155, "6th Keeper 2")
    FocusKeeperOfSouls(bot_instance)
    bot_instance.Wait.ForTime(500)
    FocusKeeperOfSouls(bot_instance)
    _move_with_unstuck(bot_instance, 1256, 4623, "6th Keeper killed")

    bot_instance.States.AddCustomState(
        lambda: __import__("Py4GWCoreLib.EnemyBlacklist", fromlist=["EnemyBlacklist"]).EnemyBlacklist().remove_name("obsidian behemoth"),
        "Unblacklist Obsidian Behemoth",
    )
    bot_instance.States.AddCustomState(lambda: _record_quest_done("Unwanted Guests"), "Record Unwanted Guests done")

def Restore_Wastes(bot_instance: Botting):
    bot_instance.States.AddCustomState(lambda: _toggle_wait_if_aggro(True), "Enable WaitIfInAggro")
    bot_instance.States.AddCustomState(lambda: _toggle_wait_for_party(True), "Enable WaitIfPartyMemberTooFar")
    bot_instance.States.AddCustomState(lambda: _toggle_move_to_party_member_if_dead(True), "Enable MoveToPartyMemberIfDead")
    bot_instance.Templates.Aggressive()
    bot_instance.Properties.ApplyNow("pause_on_danger", "active", True)
    bot_instance.Move.XY(3891, 7572, "Restore Wastes 1")
    bot_instance.Move.XY(4106, 16031, "Restore Wastes 2")
    bot_instance.Move.XY(2486, 21723, "Restore Wastes 3")
    bot_instance.Move.XY(-1452, 21202, "Restore Wastes 4")
    bot_instance.Move.XY(542, 18310, "Restore Wastes 5")
    bot_instance.Wait.ForTime(3000)
    bot_instance.States.AddCustomState(lambda: _record_quest_done("Restore Wastes"), "Record Restore Wastes done")

def Servants_of_Grenth(bot_instance: Botting):
    bot_instance.States.AddCustomState(lambda: _toggle_wait_if_aggro(True), "Enable WaitIfInAggro")
    bot_instance.States.AddCustomState(lambda: _toggle_wait_for_party(True), "Enable WaitIfPartyMemberTooFar")
    bot_instance.States.AddCustomState(lambda: _toggle_move_to_party_member_if_dead(True), "Enable MoveToPartyMemberIfDead")
    bot_instance.Templates.Aggressive()
    bot_instance.Move.XY(2700, 19952, "Servants of Grenth 1")
    SERVANTS_OF_GRENTH_FLAG_POINTS = [
        (2559, 20301),
        (3032, 20148),
        (2813, 20590),
        (2516, 19665),
        (3231, 19472),
        (3691, 19979),
        (2039, 20175),
        ]
    _enqueue_spread_flags(bot_instance, SERVANTS_OF_GRENTH_FLAG_POINTS)
    bot_instance.States.AddCustomState(lambda: _toggle_wait_for_party(False), "Disable WaitIfPartyMemberTooFar")
    bot_instance.States.AddCustomState(lambda: _get_adapter().set_forced_state(BehaviorState.CLOSE_TO_AGGRO),"Force Close_to_Aggro",)
    bot_instance.Move.XYAndInteractNPC(554, 18384, "go to NPC")
    bot_instance.States.AddCustomState(lambda: _get_adapter().set_following_enabled(False), "Disable Following")
    #bot_instance.Dialogs.AtXY(5755, 12769, 0x806603, "Back to Chamber")
    bot_instance.Dialogs.AtXY(5755, 12769, 0x806601, "Back to Chamber")
    bot_instance.States.AddCustomState(lambda: _get_adapter().set_forced_state(None),"Release Close_to_Aggro",)
    
    bot_instance.Move.XY(2700, 19952, "Servants of Grenth 2")
    bot_instance.States.AddCustomState(lambda: _toggle_wait_for_party(True), "Enable WaitIfPartyMemberTooFar")
    bot_instance.States.AddCustomState(lambda: _get_adapter().set_following_enabled(True), "Enable Following")
    bot_instance.Party.UnflagAllHeroes()
    bot_instance.Party.FlagAllHeroes(3032, 20148)
    bot_instance.Party.UnflagAllHeroes()
    WaitTillQuestDone(bot_instance)
    bot_instance.Party.UnflagAllHeroes()
    bot_instance.States.AddCustomState(
        lambda: _get_adapter().clear_flags(),
        "Clear Flags",
    )
    bot_instance.Wait.ForTime(30000)
    bot_instance.States.AddCustomState(lambda: _record_quest_done("Servants of Grenth"), "Record Servants of Grenth done")
    

def _coro_reequip_sacrifice_armor() -> Generator[Any, Any, None]:
    """Re-equip any armor from the backpack if this is a sacrifice account.
    Called at the start of the Dhuum section to restore gear stripped in the previous run.
    """
    if not DhuumSettings.is_sacrifice(Player.GetAccountEmail()):
        return
    import PyInventory
    backpack = PyInventory.Bag(1, "Backpack")
    armor_ids = [
        item.item_id
        for item in backpack.GetItems()
        if Item.Type.IsArmor(item.item_id)
    ]
    if not armor_ids:
        return
    ConsoleLog(BOT_NAME, f"[Dhuum] Re-equipping {len(armor_ids)} armor piece(s) from backpack.", Py4GW.Console.MessageType.Info)
    for item_id in armor_ids:
        GLOBAL_CACHE.Inventory.EquipItem(item_id, Player.GetAgentID())
        yield from Routines.Yield.wait(750)


def _coro_strip_sacrifice_armor() -> Generator[Any, Any, None]:
    """Move all equipped armor pieces to the backpack if this is a sacrifice account.
    Stripped armor is re-equipped at the start of the next Dhuum section.
    """
    if not DhuumSettings.is_sacrifice(Player.GetAccountEmail()):
        return
    import PyInventory
    equipped_bag = PyInventory.Bag(22, "Equipped_Items")
    armor_ids = [
        item.item_id
        for item in equipped_bag.GetItems()
        if Item.Type.IsArmor(item.item_id)
    ]
    if not armor_ids:
        ConsoleLog(BOT_NAME, "[Dhuum] No equipped armor found to strip.", Py4GW.Console.MessageType.Info)
        return
    backpack = PyInventory.Bag(1, "Backpack")
    occupied_slots = {item.slot for item in backpack.GetItems()}
    backpack_size = backpack.GetSize()
    free_slots = [s for s in range(backpack_size) if s not in occupied_slots]
    if len(free_slots) < len(armor_ids):
        ConsoleLog(BOT_NAME, f"[Dhuum] Not enough free backpack slots to strip armor ({len(free_slots)} free, {len(armor_ids)} needed).", Py4GW.Console.MessageType.Warning)
    ConsoleLog(BOT_NAME, f"[Dhuum] Stripping {min(len(armor_ids), len(free_slots))} armor piece(s).", Py4GW.Console.MessageType.Info)
    for item_id, slot in zip(armor_ids, free_slots):
        GLOBAL_CACHE.Inventory.MoveItem(item_id, 1, slot)
        yield from Routines.Yield.wait(500)


def Dhuum(bot_instance: Botting):
    #Spirit Form BuffId = 3134
    bot_instance.States.AddHeader("Dhuum")
    bot_instance.States.AddCustomState(
        lambda: _get_adapter().toggle_dead_ally_rescue(False),
        "Disable Dead Ally Rescue",
    )
    bot_instance.States.AddCustomState(lambda: _get_adapter().set_forced_state(None),"Release Close_to_Aggro",)

    def _flag_sacrifice_accounts() -> None:
        flag_x, flag_y = -15022, 17277
        _get_adapter().clear_flags()

        sacrifice_emails = DhuumSettings.SacrificeEmails
        if not sacrifice_emails:
            ConsoleLog(BOT_NAME, "[Dhuum] No sacrifice accounts configured in Dhuum settings.", Py4GW.Console.MessageType.Warning)
            return

        cb_flagged_emails: list[str] = []
        for account in GLOBAL_CACHE.ShMem.GetAllAccountData():
            email = str(account.AccountEmail)
            if email not in sacrifice_emails:
                continue

            cb_index = len(cb_flagged_emails)
            if cb_index >= 12:
                break

            _get_adapter().set_flag_for_email(email, cb_index, flag_x, flag_y)
            cb_flagged_emails.append(email)

        if not cb_flagged_emails:
            ConsoleLog(BOT_NAME, "[Dhuum] No sacrifice accounts found in shared memory.", Py4GW.Console.MessageType.Warning)
            return

        ConsoleLog(
            BOT_NAME,
            f"[Dhuum] Flagged {len(cb_flagged_emails)} sacrifice account(s): {cb_flagged_emails}",
            Py4GW.Console.MessageType.Info,
        )

    def _flag_survivor_accounts() -> None:
        flag_x, flag_y = -14144, 17286

        my_email = Player.GetAccountEmail()
        sacrifice_emails = DhuumSettings.SacrificeEmails

        # Start after the sacrifice account indices to avoid overwriting them
        all_accounts = GLOBAL_CACHE.ShMem.GetAllAccountData()
        sacrifice_offset = sum(
            1 for account in all_accounts
            if str(account.AccountEmail) in sacrifice_emails
        )

        cb_flagged_emails: list[str] = []
        for account in all_accounts:
            email = str(account.AccountEmail)
            if email == my_email or email in sacrifice_emails:
                continue

            cb_index = sacrifice_offset + len(cb_flagged_emails)
            if cb_index >= 12:
                break

            _get_adapter().set_flag_for_email(email, cb_index, flag_x, flag_y)
            cb_flagged_emails.append(email)

        if not cb_flagged_emails:
            ConsoleLog(BOT_NAME, "[Dhuum] No survivor accounts to flag.", Py4GW.Console.MessageType.Info)
            return

        ConsoleLog(
            BOT_NAME,
            f"[Dhuum] Flagged {len(cb_flagged_emails)} survivor account(s): {cb_flagged_emails}",
            Py4GW.Console.MessageType.Info,
        )

    
    _KING_TARGET_X = -11278.0
    _KING_TARGET_Y =  17297.0
    _KING_MODEL_ID =  2403
    _KING_DEST_RADIUS   = 1500.0  # how close the King must be to his destination
    _KING_FOLLOW_RADIUS = 1000.0  # how close we trail behind the King
    _KING_TIMEOUT_S     = 600.0   # 10 min hard-timeout

    def _coro_follow_king_to_destination():
        """Follow model 2403 until it reaches the area around the destination coords."""
        deadline = time.time() + _KING_TIMEOUT_S
        ConsoleLog(BOT_NAME, "[Dhuum] Waiting for the King to walk to position ...", Py4GW.Console.MessageType.Info)
        while time.time() < deadline:
            king_id = next(
                (a for a in AgentArray.GetAgentArray() if int(Agent.GetModelID(a)) == _KING_MODEL_ID),
                None,
            )
            if king_id is None:
                yield from Routines.Yield.wait(500)
                continue

            kx, ky = Agent.GetXY(king_id)

            # Stop following once the King has reached his destination
            if Utils.Distance((kx, ky), (_KING_TARGET_X, _KING_TARGET_Y)) <= _KING_DEST_RADIUS:
                ConsoleLog(BOT_NAME, "[Dhuum] King has reached the position.", Py4GW.Console.MessageType.Info)
                return

            # Move towards the King if we are too far away
            px, py = Player.GetXY()
            if Utils.Distance((px, py), (kx, ky)) > _KING_FOLLOW_RADIUS:
                Player.Move(kx, ky)

            yield from Routines.Yield.wait(500)

        ConsoleLog(BOT_NAME, "[Dhuum] Timed out waiting for the King - continuing anyway.", Py4GW.Console.MessageType.Warning)

    bot_instance.States.AddCustomState(lambda: _toggle_wait_for_party(False), "Disable WaitIfPartyMemberTooFar")
    bot_instance.config.FSM.AddYieldRoutineStep(
        name="Follow King to Destination",
        coroutine_fn=_coro_follow_king_to_destination,
    )
    bot_instance.Move.XY(-11278, 17297, "Wait For the King")
    bot_instance.Wait.UntilCondition(
        lambda: any(
            int(Agent.GetModelID(agent_id)) == 2403
            and Utils.Distance(Player.GetXY(), Agent.GetXY(agent_id)) <= 1100
            for agent_id in AgentArray.GetAgentArray()
        )
    )  # Wait until King is within interaction range

    bot_instance.Wait.ForTime(10000)
    bot_instance.Dialogs.WithModel(2403, 0x846901, "Talk to The King and start Dhuum fight")
    bot_instance.Dialogs.WithModel(2403, 0x846901, "Talk to The King and start Dhuum fight")
    bot_instance.States.AddCustomState(_flag_sacrifice_accounts, "Flag Sacrifice Accounts")
    bot_instance.States.AddCustomState(_flag_survivor_accounts, "Flag Survivor Accounts")
    bot_instance.States.AddCustomState(
        lambda: bot_instance.Multibox.ApplyWidgetPolicy(enable_widgets=("Dhuum Helper",)),
        "Enable Dhuum Helper on all accounts",
    )

    bot_instance.Wait.ForTime(5000)  # Wait for the fight to properly start

    # Activate the Spirit Form watchdog for the duration of the fight.
    bot_instance.States.AddCustomState(lambda: _set_dhuum_fight_active(True), "Enable Dhuum Spirit Form Watchdog")
    bot_instance.config.FSM.AddYieldRoutineStep(
        name="Strip Sacrifice Armor",
        coroutine_fn=_coro_strip_sacrifice_armor,
    )
    bot_instance.Move.XY(-13987, 17291, "Move to Dhuum fight")
    #bot_instance.States.AddCustomState(lambda: _get_adapter().set_following_enabled(False), "Disable Following")
    bot_instance.Wait.ForTime(4000)  # Wait till some Allies die
    #Wait till Dhuum is dead
    bot_instance.Wait.UntilCondition(
        lambda: any(
            Agent.IsGadget(agent_id)
            and "underworld chest" in (Agent.GetNameByID(agent_id) or "").strip().lower()
            and Utils.Distance((-14381.0, 17283.0), Agent.GetXY(agent_id)) <= 300
            for agent_id in AgentArray.GetAgentArray()
        )
    )  # Wait until the Underworld Chest (Gadget) appears near (-14381, 17283)


    # Deactivate the Spirit Form watchdog — Dhuum is dead.
    bot_instance.States.AddCustomState(lambda: _set_dhuum_fight_active(False), "Disable Dhuum Spirit Form Watchdog")
    bot_instance.States.AddCustomState(lambda: _get_adapter().set_combat_enabled(False), "Disable Combat")
    bot_instance.config.FSM.AddYieldRoutineStep(
        name="Re-equip Sacrifice Armor",
        coroutine_fn=_coro_reequip_sacrifice_armor,
    )

    def _loot_underworld_chest():
        chest_id = next(
            (
                agent_id for agent_id in AgentArray.GetAgentArray()
                if Agent.IsGadget(agent_id)
                and "underworld chest" in (Agent.GetNameByID(agent_id) or "").strip().lower()
                and Utils.Distance((-14381.0, 17283.0), Agent.GetXY(agent_id)) <= 300
            ),
            None,
        )
        if chest_id is None:
            ConsoleLog(BOT_NAME, "[Dhuum] Underworld Chest not found for looting!", Py4GW.Console.MessageType.Warning)
            return

        my_email = Player.GetAccountEmail()
        current_map_id = Map.GetMapID()
        all_accounts = GLOBAL_CACHE.ShMem.GetAllAccountData()
        same_map_accounts = [
            acc for acc in all_accounts
            if acc.AgentData.Map.MapID == current_map_id
        ]

        ConsoleLog(BOT_NAME, f"[Dhuum] Looting chest with {len(same_map_accounts)} account(s)", Py4GW.Console.MessageType.Info)

        for account in same_map_accounts:
            email = str(account.AccountEmail)
            msg_index = GLOBAL_CACHE.ShMem.SendMessage(
                sender_email=my_email,
                receiver_email=email,
                command=SharedCommandType.InteractWithTarget,
                params=(chest_id, 0, 0, 0),
            )
            if msg_index < 0:
                ConsoleLog(BOT_NAME, f"[Dhuum] Failed to send InteractWithTarget to {email}", Py4GW.Console.MessageType.Warning)
            else:
                ConsoleLog(BOT_NAME, f"[Dhuum] Sent InteractWithTarget (chest) to {email}", Py4GW.Console.MessageType.Info)
            yield from Routines.Yield.wait(5000)

    #bot_instance.States.AddCustomState(lambda: _get_adapter().set_following_enabled(True), "Enable Following")
    bot_instance.States.AddCustomState(
        lambda: _get_adapter().clear_flags(),
        "Clear Flags",
    )        

    bot_instance.States.AddCustomState(_loot_underworld_chest, "Loot Underworld Chest")

    bot_instance.Wait.ForTime(5000)  # Wait for looting to finish    

    bot_instance.States.AddCustomState(_loot_underworld_chest, "Loot Underworld Chest")

    bot_instance.Wait.ForTime(5000)  # Wait for any stragglers to finish looting
    bot_instance.States.AddCustomState(lambda: _get_adapter().set_looting_enabled(False), "Disable Looting")
    bot_instance.Move.XY(-14324, 17549)
    bot_instance.States.AddCustomState(lambda: _get_adapter().set_looting_enabled(True), "Enable Looting")
    bot_instance.Wait.ForTime(5000)
    bot_instance.States.AddCustomState(lambda: _get_adapter().set_looting_enabled(False), "Disable Looting")
    bot_instance.Move.XY(-14243, 17017)
    bot_instance.States.AddCustomState(lambda: _get_adapter().set_looting_enabled(True), "Enable Looting")
    bot_instance.Wait.ForTime(5000)
    bot_instance.States.AddCustomState(lambda: _get_adapter().set_combat_enabled(True), "Enable Combat")
    bot_instance.States.AddCustomState(
        lambda: _get_adapter().toggle_dead_ally_rescue(True),
        "Enable Dead Ally Rescue",
    )
    bot_instance.States.AddCustomState(lambda: _record_quest_done("Dhuum"), "Record Dhuum done")



def _do_inventory_refill(bot_instance: Botting) -> None:
    """Travel to the configured location and restock kits/cons/materials via the modular_bot handlers."""
    if not InventorySettings.RefillEnabled:
        return

    # Ensure the map is fully loaded before any NPC interaction states run.
    # This guards against starting on a loading screen or right after a resign.
    bot_instance.Wait.UntilOnOutpost()

    from Sources.modular_bot.prebuilts.fow import (
        INVENTORY_MANAGEMENT_LOCATIONS,
        DEFAULT_INVENTORY_MANAGEMENT_LOCATION_KEY,
    )
    from Sources.modular_bot.recipes.step_context import StepContext
    from Sources.modular_bot.recipes.actions_movement import handle_travel_gh
    from Sources.modular_bot.recipes.actions_inventory import (
        handle_restock_kits,
        handle_restock_cons,
        handle_sell_materials,
        handle_deposit_materials,
    )

    location = str(InventorySettings.InventoryLocation or DEFAULT_INVENTORY_MANAGEMENT_LOCATION_KEY)

    def _make_ctx(step: dict) -> StepContext:
        return StepContext(
            bot=bot_instance,
            step=step,
            step_idx=0,
            recipe_name="UW_Inventory",
            step_type=step.get("type", ""),
            step_display=step.get("name", ""),
        )

    # ── Travel to inventory location ──────────────────────────────────
    if location == "guild_hall":
        handle_travel_gh(_make_ctx({"type": "travel_gh", "name": "Travel to Guild Hall", "multibox": True, "ms": 7000}))
    else:
        try:
            target_map_id = int(str(location).split("_", 1)[1])
        except (IndexError, ValueError):
            target_map_id = 0
        if target_map_id > 0:
            bot_instance.Map.Travel(target_map_id=target_map_id)
            bot_instance.Wait.ForTime(15000)

    # Wait for the map to be fully loaded before interacting with any NPCs.
    bot_instance.Wait.UntilOnOutpost()

    # ── Restock ID & Salvage Kits (3 rounds) ──────────────────────────
    if InventorySettings.RestockKits:
        kit_step = {"type": "restock_kits", "name": "Restock Kits", "id_kits": 2, "salvage_kits": 5, "multibox": True}
        for _ in range(3):
            handle_restock_kits(_make_ctx(kit_step))

    # ── Restock Cons from Xunlai Chest ────────────────────────────────
    if InventorySettings.RestockCons and BotSettings.UseCons:
        handle_restock_cons(_make_ctx({"type": "restock_cons", "name": "Restock Consumables"}))

    # ── Sell Materials ────────────────────────────────────────────────
    if InventorySettings.SellAllCommonMaterials:
        handle_sell_materials(_make_ctx({"type": "sell_materials", "name": "Sell All Common Materials", "multibox": True, "ms": 5000}))
    elif InventorySettings.SellNonConsMaterials:
        from Sources.modular_bot.prebuilts.fow import FOW_NON_CONS_COMMON_MATERIAL_MODELS
        from Py4GWCoreLib.enums_src.Item_enums import MaterialMap
        sell_names = [
            material_name
            for model_id, material_name in MaterialMap.items()
            if model_id in FOW_NON_CONS_COMMON_MATERIAL_MODELS
        ]
        handle_sell_materials(_make_ctx({"type": "sell_materials", "name": "Sell Non-Cons Materials", "multibox": True, "ms": 5000, "materials": sell_names}))

    # ── Deposit Full Material Stacks ──────────────────────────────────
    if InventorySettings.DepositMaterials:
        handle_deposit_materials(_make_ctx({"type": "deposit_materials", "name": "Deposit Full Material Stacks", "multibox": True, "ms": 5000}))

    # ── Buy Ectoplasm ─────────────────────────────────────────────────
    if InventorySettings.BuyEctoplasm:
        from Sources.modular_bot.recipes.actions_inventory import handle_buy_ectoplasm
        handle_buy_ectoplasm(_make_ctx({"type": "buy_ectoplasm", "name": "Buy Ectoplasm", "use_storage_gold": False, "multibox": True, "ms": 5000}))


def ResignAndRepeat(bot_instance: Botting):
    bot_instance.States.AddCustomState(_log_successful_run, "Log Successful Run")
    if BotSettings.Repeat:
        bot_instance.Multibox.ResignParty()


def _log_successful_run() -> None:
    """Append a timestamped successful-run entry to the wipe log file."""
    import json as _json
    elapsed_s = max(0, (Map.GetInstanceUptime() - _run_start_uptime_ms) // 1000) if _run_start_uptime_ms else 0
    elapsed_str = f"{elapsed_s // 3600:02d}:{(elapsed_s % 3600) // 60:02d}:{elapsed_s % 60:02d}"
    entry = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Run completed successfully. Duration: {elapsed_str}\n"
    try:
        with open(_WIPE_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(entry)
    except OSError as exc:
        ConsoleLog(BOT_NAME, f"[Run] Could not write run log: {exc}", Py4GW.Console.MessageType.Warning)
    # Persist per-quest instance uptimes for the avg column.
    if _quest_completion_times:
        for quest_name in _QUEST_ORDER:
            if quest_name in _quest_completion_times:
                elapsed_q = _quest_completion_times[quest_name] // 1000
                _quest_times_log.setdefault(quest_name, []).append(elapsed_q)
        try:
            with open(_QUEST_TIMES_FILE, "w", encoding="utf-8") as f:
                _json.dump(_quest_times_log, f, indent=2)
        except OSError as exc:
            ConsoleLog(BOT_NAME, f"[Run] Could not write quest times log: {exc}", Py4GW.Console.MessageType.Warning)
    ConsoleLog(BOT_NAME, "[Run] Successful run logged.", Py4GW.Console.MessageType.Info)

def Wait_for_Spawns(bot_instance: Botting, x, y):
    _TIMEOUT_S = 20.0

    bot_instance.Move.XY(x, y, "To the Vale")

    def _make_check(label: str):
        """Returns a condition callable that times out after _TIMEOUT_S seconds.
        On timeout: skips the current wait and continues."""
        deadline: float | None = None

        def runtime_check_logic():
            nonlocal deadline
            enemies = [e for e in AgentArray.GetEnemyArray() if Agent.IsAlive(e) and Agent.GetModelID(e) == 2380]

            if not enemies:
                print(f"No Mindblades found - Continuing... ({label})")
                deadline = None  # reset for any future reuse
                return True

            # Start (or keep) the timeout clock
            import time as _time
            now = _time.monotonic()
            if deadline is None:
                deadline = now + _TIMEOUT_S

            if now >= deadline:
                print(f"Mindblades timeout after {_TIMEOUT_S:.0f}s - skipping ({label})")
                deadline = None  # reset so next call restarts the clock
                return True  # unblock the wait and let the bot continue

            print(f"Mindblades ... Waiting. ({label})")
            bot_instance.Move.XY(x, y, "Go Back")
            return False

        return runtime_check_logic

    bot_instance.Wait.UntilCondition(_make_check("1"))
    bot_instance.Wait.ForTime(1000)
    bot_instance.Move.XY(x, y, "1")
    bot_instance.Wait.UntilCondition(_make_check("2"))
    bot_instance.Wait.ForTime(1000)
    bot_instance.Move.XY(x, y, "2")
    bot_instance.Wait.UntilCondition(_make_check("3"))
    bot_instance.Wait.ForTime(1000)
    bot_instance.Move.XY(x, y, "3")
    bot_instance.Wait.UntilCondition(_make_check("4"))


def _draw_help():
    PyImGui.text("Startup widget policy now runs on all active accounts:")

    PyImGui.separator()
    PyImGui.text("Current Status")
    PyImGui.text_wrapped("I'm working on creating a HeroAI version, but there are significant differences.")
    PyImGui.text_wrapped("High risk of getting stuck: 'Unwanted Guests,' 'Dhuum' timing edge cases.")
    PyImGui.text_wrapped("3d pathing in Pits is very rough, may cause getting stuck. Ranged leader works best.")
    PyImGui.text_wrapped("HM is HARDMODE. Never finished a run. Maybe you can?")

    PyImGui.separator()
    PyImGui.text_wrapped("For the Imprisoned Spirits quest, 1 or 2 durable damage dealers are recommended for the left team. You need to figure out which ones.")
    PyImGui.text_wrapped("In the Dhuum battle, 1-2 heroes will die and become ghosts. You can choose which ones.")

    PyImGui.separator()
    PyImGui.text_wrapped("The Inventory and Enter functions were borrowed from the fow bot—thanks for that")


def _draw_inventory_settings() -> None:
    from Sources.modular_bot.prebuilts.fow import INVENTORY_MANAGEMENT_LOCATIONS, DEFAULT_INVENTORY_MANAGEMENT_LOCATION_KEY

    changed = False
    new_val = PyImGui.checkbox("Enable Inventory Refill", InventorySettings.RefillEnabled)
    if new_val != InventorySettings.RefillEnabled:
        InventorySettings.RefillEnabled = new_val
        changed = True
    PyImGui.separator()
    PyImGui.begin_disabled(not InventorySettings.RefillEnabled)
    PyImGui.text_wrapped("After each run: travel to the selected location, restock, then return.")
    PyImGui.separator()

    # ── Location dropdown ─────────────────────────────────────────
    location_keys   = list(INVENTORY_MANAGEMENT_LOCATIONS.keys())
    location_labels = list(INVENTORY_MANAGEMENT_LOCATIONS.values())
    current_key = str(InventorySettings.InventoryLocation or DEFAULT_INVENTORY_MANAGEMENT_LOCATION_KEY)
    current_idx = location_keys.index(current_key) if current_key in location_keys else 0
    PyImGui.text("Inventory Location:")
    new_idx = PyImGui.combo("##inv_location", current_idx, location_labels)
    if new_idx != current_idx:
        InventorySettings.InventoryLocation = location_keys[new_idx]
        changed = True

    PyImGui.separator()

    # ── Restock ───────────────────────────────────────────────────
    new_val = PyImGui.checkbox("Restock ID & Salvage Kits (3 rounds)", InventorySettings.RestockKits)
    if new_val != InventorySettings.RestockKits:
        InventorySettings.RestockKits = new_val
        changed = True
    new_val = PyImGui.checkbox("Restock Consets from Xunlai Chest", InventorySettings.RestockCons)
    if new_val != InventorySettings.RestockCons:
        InventorySettings.RestockCons = new_val
        changed = True
    PyImGui.begin_disabled(not BotSettings.UseCons)
    PyImGui.text("  (requires 'Use Cons' to be enabled)")
    PyImGui.end_disabled()

    PyImGui.separator()

    # ── Materials ────────────────────────────────────────────────
    new_val = PyImGui.checkbox("Deposit Full Material Stacks to Chest", InventorySettings.DepositMaterials)
    if new_val != InventorySettings.DepositMaterials:
        InventorySettings.DepositMaterials = new_val
        changed = True
    new_val = PyImGui.checkbox("Sell Non-Cons Materials at Merchant", InventorySettings.SellNonConsMaterials)
    if new_val != InventorySettings.SellNonConsMaterials:
        InventorySettings.SellNonConsMaterials = new_val
        changed = True
    new_val = PyImGui.checkbox("Sell All Common Materials at Merchant", InventorySettings.SellAllCommonMaterials)
    if new_val != InventorySettings.SellAllCommonMaterials:
        InventorySettings.SellAllCommonMaterials = new_val
        changed = True
    new_val = PyImGui.checkbox("Buy Ectoplasm from Materials Trader", InventorySettings.BuyEctoplasm)
    if new_val != InventorySettings.BuyEctoplasm:
        InventorySettings.BuyEctoplasm = new_val
        changed = True

    PyImGui.end_disabled()
    if changed:
        InventorySettings.save()


def _draw_imprisoned_spirits_settings() -> None:
    PyImGui.text_wrapped(
        "Assign each multibox account to the Left or Right team for the Imprisoned Spirits quest."
    )
    PyImGui.separator()

    all_accounts = GLOBAL_CACHE.ShMem.GetAllAccountData()
    if not all_accounts:
        PyImGui.text("No multibox account data available.")
        return

    ImprisonedSpiritsSettings.apply_defaults_if_empty(all_accounts)

    my_email = Player.GetAccountEmail()

    table_flags = PyImGui.TableFlags.RowBg | PyImGui.TableFlags.BordersInnerV | PyImGui.TableFlags.BordersOuterH
    if PyImGui.begin_table("##imprisoned_teams", 3, table_flags, 0.0, 0.0):
        PyImGui.table_setup_column("Left",    PyImGui.TableColumnFlags.WidthFixed,   40.0)
        PyImGui.table_setup_column("Right",   PyImGui.TableColumnFlags.WidthFixed,   40.0)
        PyImGui.table_setup_column("Account", PyImGui.TableColumnFlags.WidthStretch, 0.0)
        PyImGui.table_headers_row()

        for account in all_accounts:
            email     = str(account.AccountEmail)
            char_name = str(account.AgentData.CharacterName) or email
            is_self   = email == my_email
            team      = ImprisonedSpiritsSettings.get_team(email)
            team_idx  = 0 if team == "left" else 1

            PyImGui.table_next_row()

            if is_self:
                PyImGui.begin_disabled(True)

            PyImGui.table_next_column()
            new_idx = PyImGui.radio_button(f"##left_{email}", team_idx, 0)

            PyImGui.table_next_column()
            new_idx = PyImGui.radio_button(f"##right_{email}", new_idx, 1)

            PyImGui.table_next_column()
            PyImGui.text(f"{char_name}  (this account)" if is_self else char_name)

            if is_self:
                PyImGui.end_disabled()
            elif new_idx != team_idx:
                ImprisonedSpiritsSettings.set_team(email, "left" if new_idx == 0 else "right")

        PyImGui.end_table()


def _draw_dhuum_settings() -> None:
    PyImGui.text_wrapped("Select the multibox accounts to be sacrificed in the Dhuum fight.")
    PyImGui.separator()

    my_email = Player.GetAccountEmail()
    all_accounts = GLOBAL_CACHE.ShMem.GetAllAccountData()

    if not all_accounts:
        PyImGui.text("No multibox account data available.")
        return

    for account in all_accounts:
        email = str(account.AccountEmail)
        char_name = str(account.AgentData.CharacterName) or email
        if email == my_email:
            PyImGui.begin_disabled(True)
            PyImGui.checkbox(f"{char_name}  (this account)", False)
            PyImGui.end_disabled()
        else:
            current = DhuumSettings.is_sacrifice(email)
            new_val = PyImGui.checkbox(char_name, current)
            if new_val != current:
                DhuumSettings.set_sacrifice(email, new_val)


def _draw_enter_settings() -> None:
    entrypoint_keys   = list(UW_ENTRYPOINTS.keys())
    entrypoint_labels = [label for label, _ in UW_ENTRYPOINTS.values()]
    current_key = str(EnterSettings.EntryPoint or DEFAULT_UW_ENTRYPOINT_KEY)
    current_idx = entrypoint_keys.index(current_key) if current_key in entrypoint_keys else 0

    PyImGui.text_wrapped("Select the outpost to travel to before using the scroll.")
    PyImGui.separator()
    PyImGui.text("Entry Outpost:")
    new_idx = PyImGui.combo("##uw_entrypoint", current_idx, entrypoint_labels)
    if new_idx != current_idx:
        EnterSettings.EntryPoint = entrypoint_keys[new_idx]
        EnterSettings.save()


def _draw_quest_settings():
    _snapshot = (BotSettings.Repeat, BotSettings.UseCons, BotSettings.HardMode, BotSettings.BotMode)
    BotSettings.Repeat   = PyImGui.checkbox("Resign and Repeat after", BotSettings.Repeat)
    BotSettings.UseCons  = PyImGui.checkbox("Use Cons", BotSettings.UseCons)
    BotSettings.HardMode = PyImGui.checkbox("Hard Mode", BotSettings.HardMode)
    PyImGui.separator()
    PyImGui.text("Bot Mode:")
    mode_idx = 0 if BotSettings.BotMode == "custom_behavior" else 1
    new_mode_idx = PyImGui.radio_button("Custom Behavior##botmode", mode_idx, 0)
    PyImGui.same_line(0, -1)
    new_mode_idx = PyImGui.radio_button("HeroAI##botmode", new_mode_idx, 1)
    BotSettings.BotMode = "custom_behavior" if new_mode_idx == 0 else "heroai"
    _current = (BotSettings.Repeat, BotSettings.UseCons, BotSettings.HardMode, BotSettings.BotMode)
    if _current != _snapshot:
        BotSettings.save()




bot.SetMainRoutine(bot_routine)

def _draw_debug_settings():
    global _DRAW_BLOCKED_AREAS_3D, _BLOCKED_AREA_RADIUS
    _DRAW_BLOCKED_AREAS_3D = PyImGui.checkbox("Draw Blocked Areas (3D)", _DRAW_BLOCKED_AREAS_3D)
    if _DRAW_BLOCKED_AREAS_3D:
        _BLOCKED_AREA_RADIUS = PyImGui.slider_float("Blocked Area Radius", _BLOCKED_AREA_RADIUS, 50.0, 600.0)

    PyImGui.separator()
    PyImGui.text("Spirit Form (3134) — Active accounts:")
    _SPIRIT_FORM_SKILL_ID = 3134
    _color_has_buff   = Utils.RGBToNormal(100, 255, 100, 255)
    _color_no_buff    = Utils.RGBToNormal(140, 140, 140, 255)
    try:
        accounts = GLOBAL_CACHE.ShMem.GetAllAccountData() or []
        current_map_id = Map.GetMapID()
        found_any = False
        for account in accounts:
            if not getattr(account, "IsSlotActive", True):
                continue
            email = str(getattr(account, "AccountEmail", "") or "").strip()
            if not email:
                continue
            in_same_map = getattr(account.AgentData.Map, "MapID", 0) == current_map_id
            has_buff = any(
                b.SkillId == _SPIRIT_FORM_SKILL_ID
                for b in account.AgentData.Buffs.Buffs
                if b.SkillId != 0
            )
            if not has_buff:
                continue
            found_any = True
            # Check if already flagged (in _already_flagged set of the watchdog)
            label = email
            PyImGui.text_colored(f"  {label}", _color_has_buff)
        if not found_any:
            PyImGui.text_colored("  (none)", _color_no_buff)
    except Exception as _e:
        PyImGui.text_colored(f"  Error reading ShMem: {_e}", Utils.RGBToNormal(255, 80, 80, 255))


def _draw_settings():
    if PyImGui.begin_tab_bar("##uw_settings_tabs"):
        if PyImGui.begin_tab_item("General"):
            _draw_quest_settings()
            PyImGui.separator()
            _draw_enter_settings()
            PyImGui.end_tab_item()
        if PyImGui.begin_tab_item("Inventory"):
            _draw_inventory_settings()
            PyImGui.end_tab_item()
        if PyImGui.begin_tab_item("Imprisoned Spirits"):
            _draw_imprisoned_spirits_settings()
            PyImGui.end_tab_item()
        if PyImGui.begin_tab_item("Dhuum"):
            _draw_dhuum_settings()
            PyImGui.end_tab_item()
        if PyImGui.begin_tab_item("Debug"):
            _draw_debug_settings()
            PyImGui.end_tab_item()
        PyImGui.end_tab_bar()


_WIPE_LOG_FILE = os.path.join(Py4GW.Console.get_projects_path(), "Widgets", "Config", "UnderworldBot_wipes.log")
_QUEST_TIMES_FILE = os.path.join(Py4GW.Console.get_projects_path(), "Widgets", "Config", "UnderworldBot_quest_times.json")

def _load_quest_times_log() -> dict[str, list[int]]:
    """Load per-quest elapsed-second lists from the JSON log, or return empty dict."""
    import json as _json
    try:
        with open(_QUEST_TIMES_FILE, "r", encoding="utf-8") as f:
            data = _json.load(f)
        if isinstance(data, dict):
            return {k: [int(v) for v in vs] for k, vs in data.items() if isinstance(vs, list)}
    except (OSError, ValueError):
        pass
    return {}

_quest_times_log: dict[str, list[int]] = _load_quest_times_log()

def _get_current_header(fsm) -> str:
    """Return the clean name of the nearest preceding [H] header step, or 'unknown'."""
    import re as _re
    try:
        steps = fsm.get_state_names()
        current_idx = fsm.get_current_state_number()
        if current_idx is None or current_idx < 0 or current_idx >= len(steps):
            current_idx = len(steps) - 1
        for i in range(current_idx, -1, -1):
            name = steps[i]
            if name.startswith("[H]"):
                name = _re.sub(r'^\[H\]\s*', '', name)
                name = _re.sub(r'_(?:\[\d+\]|\d+)$', '', name)
                return name
    except Exception:
        pass
    return "unknown"


def _log_wipe_step(fsm) -> None:
    """Append a timestamped wipe entry with the current FSM step name to the wipe log file."""
    step_name = fsm.get_current_step_name()
    header = _get_current_header(fsm)
    # Skip logging when the bot is already past the last quest section (END header).
    # This happens when a resign/map-change after a successful run triggers the wipe
    # callback before the FSM is torn down.
    if header == "END":
        return
    entry = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Wipe at step: {step_name} [{header}]\n"
    try:
        with open(_WIPE_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(entry)
    except OSError as exc:
        ConsoleLog(BOT_NAME, f"[WIPE] Could not write wipe log: {exc}", Py4GW.Console.MessageType.Warning)
    ConsoleLog(BOT_NAME, f"[WIPE] Logged wipe at step: {step_name} [{header}]", Py4GW.Console.MessageType.Warning)


def OnPartyWipe(bot: "Botting"):
    fsm = bot.config.FSM
    _log_wipe_step(fsm)
    fsm.pause()
    fsm.AddManagedCoroutine("OnWipe_Underworld", lambda: _on_party_wipe(bot))


def _on_party_wipe(bot: "Botting"):
    ConsoleLog(BOT_NAME, "[WIPE] Party wipe detected!", Py4GW.Console.MessageType.Warning)

    while Agent.IsDead(Player.GetAgentID()):
        yield from Routines.Yield.wait(1000)

        if not Routines.Checks.Map.MapValid():
            ConsoleLog(BOT_NAME, "[WIPE] Returned to outpost after wipe, restarting run...", Py4GW.Console.MessageType.Warning)
            yield from Routines.Yield.wait(3000)
            # Do NOT call _restart_main_loop() here — we are inside FSM.update()'s
            # managed-coroutines loop, so calling fsm.resume() would un-pause the FSM
            # mid-loop and allow execute() to run with a potentially stale current_state.
            # Instead, flag main() to do the restart before the next bot.Update().
            _request_wipe_restart("Returned to outpost after wipe")
            return

    ConsoleLog(BOT_NAME, "[WIPE] Player resurrected in instance, resuming...", Py4GW.Console.MessageType.Info)
    _request_wipe_restart("Player resurrected in instance")


def _draw_run_log() -> None:
    """Display the last 10 entries from the wipe/run log file."""
    if PyImGui.button("Refresh##run_log"):
        pass  # The read below happens every frame; button is a visual affordance only.
    PyImGui.same_line(0, -1)
    PyImGui.text(_WIPE_LOG_FILE)
    PyImGui.separator()
    try:
        with open(_WIPE_LOG_FILE, "r", encoding="utf-8") as f:
            lines = [l.rstrip("\n") for l in f.readlines() if l.strip()]
        last_10 = lines[-10:] if len(lines) > 10 else lines
        if not last_10:
            PyImGui.text_wrapped("(log is empty)")
        else:
            for line in reversed(last_10):
                PyImGui.text_wrapped(line)
    except FileNotFoundError:
        PyImGui.text_wrapped("(no log file yet — wipes and completed runs will appear here)")
    except OSError as exc:
        PyImGui.text_wrapped(f"Error reading log: {exc}")


def _log_crash(exc: BaseException, tb: str) -> None:
    """Append a timestamped crash entry with the full traceback to the log file."""
    step_name = "unknown"
    header = "unknown"
    try:
        step_name = bot.config.FSM.get_current_step_name()
        header = _get_current_header(bot.config.FSM)
    except Exception:
        pass
    entry = (
        f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] CRASH at step: {step_name} [{header}]\n"
        f"  {type(exc).__name__}: {exc}\n"
    )
    for line in tb.splitlines():
        entry += f"  {line}\n"
    entry += "\n"
    try:
        with open(_WIPE_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(entry)
    except OSError:
        pass  # Nothing we can do if the file itself fails


def _draw_main_additional_ui() -> None:
    """Rendered in the Main tab below the progress bars."""
    _color_done    = Utils.RGBToNormal(100, 255, 100, 255)
    _color_pending = Utils.RGBToNormal(140, 140, 140, 255)
    _color_avg     = Utils.RGBToNormal(255, 210, 80, 255)
    PyImGui.text("Quest Progress")
    if PyImGui.begin_table(
        "##uw_quest_table", 3,
        PyImGui.TableFlags.RowBg
        | PyImGui.TableFlags.BordersOuterH
        | PyImGui.TableFlags.BordersOuterV
        | PyImGui.TableFlags.BordersInnerV,
    ):
        PyImGui.table_setup_column("Quest", PyImGui.TableColumnFlags.WidthStretch)
        PyImGui.table_setup_column("Time",  PyImGui.TableColumnFlags.WidthFixed, 72)
        PyImGui.table_setup_column("Avg",   PyImGui.TableColumnFlags.WidthFixed, 72)
        PyImGui.table_headers_row()
        for quest_name in _QUEST_ORDER:
            PyImGui.table_next_row()
            PyImGui.table_set_column_index(0)
            done = quest_name in _quest_completion_times
            PyImGui.text_colored(quest_name, _color_done if done else _color_pending)
            PyImGui.table_set_column_index(1)
            history = _quest_times_log.get(quest_name, [])
            recent = history[-5:] if history else []
            avg_s = int(sum(recent) / len(recent)) if recent else None
            if done:
                uptime_s = _quest_completion_times[quest_name] // 1000
                h, rem = divmod(uptime_s, 3600)
                m, s = divmod(rem, 60)
                if avg_s is None:
                    time_color = _color_done
                elif uptime_s <= avg_s:
                    time_color = Utils.RGBToNormal(100, 255, 100, 255)
                else:
                    time_color = Utils.RGBToNormal(255, 80, 80, 255)
                PyImGui.text_colored(f"{h:02d}:{m:02d}:{s:02d}", time_color)
            else:
                PyImGui.text_colored("--:--:--", _color_pending)
            PyImGui.table_set_column_index(2)
            if avg_s is not None:
                ah, arem = divmod(avg_s, 3600)
                am, as_ = divmod(arem, 60)
                PyImGui.text_colored(f"{ah:02d}:{am:02d}:{as_:02d}", _color_avg)
            else:
                PyImGui.text_colored("--:--:--", _color_pending)
        PyImGui.end_table()


def main():
    global _pending_wipe_recovery, _pending_wipe_reason
    import traceback as _tb
    try:
        _draw_blocked_areas_overlay()
        _draw_active_path_overlay()
        if bot.config.fsm_running:
            _get_adapter().sync_runtime()
            # Watchdog: callback sometimes misses wipes — detect return to outpost by map ID
            if _entered_dungeon and Map.GetMapID() == 138:
                ConsoleLog(BOT_NAME, "[WIPE] Watchdog: back in outpost (map 138) without wipe callback — restarting.", Py4GW.Console.MessageType.Warning)
                _restart_main_loop(bot, "Watchdog: returned to map 138")
        # If a wipe-recovery was requested by a managed coroutine, perform the FSM
        # restart here — safely outside FSM.update()'s managed-coroutines loop.
        if _pending_wipe_recovery:
            _pending_wipe_recovery = False
            _restart_main_loop(bot, _pending_wipe_reason)

        bot.Update()
        bot.UI.draw_window(
            main_child_dimensions=(350, 570),
            additional_ui=_draw_main_additional_ui,
            extra_tabs=[("Run Log", _draw_run_log)],
        )
    except ValueError as exc:
        # CoreLib bug: FSM.update()'s except-StopIteration handler calls
        # managed_coroutines.remove(routine) without a try/except.  If the
        # routine was already removed from the list (rare edge case triggered
        # by _start_coroutines() or a wipe callback), the remove raises
        # ValueError.  The routine won't be in the next snapshot so the error
        # is self-healing — we just must not let it crash the script.
        if "list.remove" in str(exc):
            ConsoleLog(BOT_NAME,
                       "[WARN] Transient FSM coroutine list error (non-fatal) — bot continues.",
                       Py4GW.Console.MessageType.Warning)
        else:
            _log_crash(exc, _tb.format_exc())
            raise
    except Exception as exc:
        _log_crash(exc, _tb.format_exc())
        raise

if __name__ == "__main__":
    main()