
from Py4GWCoreLib import Botting, Routines, Agent, AgentArray, Player, Utils, AutoPathing, GLOBAL_CACHE, ConsoleLog, Map, Pathing, FlagPreference, Party, IniHandler, Range
from Py4GWCoreLib.enums_src.Model_enums import ModelID
from Py4GWCoreLib.enums_src.Map_enums import name_to_map_id
import os
import time
from typing import Any, Generator
from Py4GWCoreLib.enums_src.Multiboxing_enums import SharedCommandType
from pathlib import Path
import PyImGui
import Py4GW

# ==================================================================
#                      POSSIBLE IMPROVEMENTS
# ==================================================================
#
# [ ] Better antistuck at Unwanted Guests
# [X] Kill the Chained Souls when we wait until the quest is done
# [X] Blacklist Dreamrider to improve Plains speed
# [X] Add inventory management
# [ ] Unequip armor at Dhuum to sacrifice selected heroes
# [ ] Add HeroAI
# [ ] Take the Dhuum quest earlier
# [ ] Fix moving to dead ally
# [ ] Make Pits quest saver
#
# ==================================================================



#3078 Dhuum Ghost buff
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
_entered_dungeon: bool = False  # set True once map 72 is loaded; watchdog uses this
_king_frozenwind_model_id: int = 2403

UW_MAP_ID = 72
UW_SCROLL_MODEL_ID = int(ModelID.Passage_Scroll_Uw.value)  # 3746
UW_ENTRYPOINTS: dict[str, tuple[str, int]] = {
    "embark_beach":       ("Embark Beach",       int(name_to_map_id["Embark Beach"])),
    "temple_of_the_ages": ("Temple of the Ages", int(name_to_map_id["Temple of the Ages"])),
    "chantry_of_secrets": ("Chantry of Secrets", int(name_to_map_id["Chantry of Secrets"])),
    "zin_ku_corridor":    ("Zin Ku Corridor",     int(name_to_map_id["Zin Ku Corridor"])),
}
DEFAULT_UW_ENTRYPOINT_KEY = "embark_beach"


def _mark_entered_dungeon() -> None:
    global _entered_dungeon
    _entered_dungeon = True


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

    @classmethod
    def save(cls) -> None:
        _ini.write_key(BOT_NAME, "quest_repeat",    str(cls.Repeat))
        _ini.write_key(BOT_NAME, "quest_use_cons",  str(cls.UseCons))
        _ini.write_key(BOT_NAME, "quest_hardmode",  str(cls.HardMode))


class EnterSettings:
    """Settings for how the bot travels to and enters the Underworld."""
    EntryPoint: str = str(_ini.read_key(BOT_NAME, "enter_entrypoint", DEFAULT_UW_ENTRYPOINT_KEY) or DEFAULT_UW_ENTRYPOINT_KEY)

    @classmethod
    def save(cls) -> None:
        _ini.write_key(BOT_NAME, "enter_entrypoint", str(cls.EntryPoint))


_MISSING_HEROAI_FEATURES_LOGGED: set[str] = set()
_WAIT_FOR_PARTY_ENABLED: bool = True
_WAIT_FOR_PARTY_MAX_DISTANCE: float = float(Range.Spellcast.value * 1.25)
_WAIT_FOR_PARTY_PXSTACK_AFTER_MS: int = 4000


def _log_missing_heroai_feature(feature: str) -> None:
    if feature in _MISSING_HEROAI_FEATURES_LOGGED:
        return
    _MISSING_HEROAI_FEATURES_LOGGED.add(feature)
    ConsoleLog(
        BOT_NAME,
        f"[HeroAI][TODO] Missing HeroAI equivalent for '{feature}'.",
        Py4GW.Console.MessageType.Warning,
    )


class HeroAIForcedState:
    CLOSE_TO_AGGRO = "close_to_aggro"


class _HeroAIFlaggingManager:
    def __init__(self) -> None:
        self._email_by_flag_index: dict[int, str] = {}

    def clear_all_flags(self) -> None:
        self._email_by_flag_index.clear()
        Party.Heroes.UnflagAllHeroes()

    def auto_assign_emails_if_none_assigned(self) -> None:
        if self._email_by_flag_index:
            return
        my_email = Player.GetAccountEmail()
        accounts = GLOBAL_CACHE.ShMem.GetAllAccountData() or []
        idx = 0
        for account in accounts:
            email = str(account.AccountEmail)
            if not email or email == my_email:
                continue
            self._email_by_flag_index[idx] = email
            idx += 1

    def set_flag_account_email(self, index: int, email: str) -> None:
        self._email_by_flag_index[int(index)] = str(email)

    def set_flag_position(self, index: int, x: int, y: int) -> None:
        hero_slot = int(index) + 1
        # TODO: HeroAI does not expose a strict email->hero-slot routing API like CustomBehavior.
        # Fallback: map flag index to native hero slot.
        _ = self._email_by_flag_index.get(int(index))
        Party.Heroes.FlagHero(hero_slot, x, y)


class _HeroAIPartyFacade:
    def __init__(self) -> None:
        self.party_flagging_manager = _HeroAIFlaggingManager()

    def set_party_custom_target(self, target_agent_id: int) -> None:
        if target_agent_id:
            Player.ChangeTarget(int(target_agent_id))
            bot.Player.CallTarget()
            

    def set_party_is_blessing_enabled(self, enabled: bool) -> None:
        if enabled:
            _log_missing_heroai_feature("party blessing enable/disable")

    def set_party_is_following_enabled(self, enabled: bool) -> None:
        if not enabled:
            _log_missing_heroai_feature("global follow hard-disable")

    def set_party_is_looting_enabled(self, enabled: bool) -> None:
        if not enabled:
            _log_missing_heroai_feature("global looting enable/disable")

    def set_party_is_combat_enabled(self, enabled: bool) -> None:
        if not enabled:
            _log_missing_heroai_feature("global combat hard-disable")

    def set_party_forced_state(self, forced_state: str | None) -> None:
        if forced_state is not None:
            _log_missing_heroai_feature("forced party behavior state lock")


_HEROAI_PARTY = _HeroAIPartyFacade()


def HeroAIParty() -> _HeroAIPartyFacade:
    return _HEROAI_PARTY


def _is_party_too_far(max_distance: float) -> bool:
    player_pos: tuple[float, float] = Player.GetXY()
    ally_ids: list[int] = AgentArray.GetAllyArray()
    if not ally_ids:
        return False

    living_allies = AgentArray.Filter.ByCondition(ally_ids, lambda aid: Agent.IsAlive(aid))
    if not living_allies:
        return False

    allies_in_range = AgentArray.Filter.ByDistance(living_allies, player_pos, max_distance)
    return len(allies_in_range) < len(living_allies)


def _heroai_wait_for_party_watchdog(bot_instance: Botting):
    paused_by_watchdog = False
    waited_since_ms = 0
    pixelstack_sent = False

    while True:
        yield from Routines.Yield.wait(250)

        if not bot_instance.config.fsm_running:
            continue

        if not _WAIT_FOR_PARTY_ENABLED:
            if paused_by_watchdog:
                bot_instance.config.FSM.resume()
                paused_by_watchdog = False
            waited_since_ms = 0
            pixelstack_sent = False
            continue

        if not _is_party_too_far(_WAIT_FOR_PARTY_MAX_DISTANCE):
            if paused_by_watchdog:
                bot_instance.config.FSM.resume()
                ConsoleLog(BOT_NAME, "[HeroAI] Party regrouped, resuming FSM.", Py4GW.Console.MessageType.Info)
            paused_by_watchdog = False
            waited_since_ms = 0
            pixelstack_sent = False
            continue

        if not paused_by_watchdog:
            bot_instance.config.FSM.pause()
            paused_by_watchdog = True
            waited_since_ms = 0
            pixelstack_sent = False
            ConsoleLog(BOT_NAME, "[HeroAI] Party too far, pausing FSM and waiting for regroup.", Py4GW.Console.MessageType.Warning)

        waited_since_ms += 250
        if not pixelstack_sent and waited_since_ms >= _WAIT_FOR_PARTY_PXSTACK_AFTER_MS:
            bot_instance.Multibox.PixelStack()
            pixelstack_sent = True
            ConsoleLog(BOT_NAME, "[HeroAI] Regroup timeout reached, requesting PixelStack.", Py4GW.Console.MessageType.Warning)


def _toggle_wait_for_party(enabled: bool) -> None:
    global _WAIT_FOR_PARTY_ENABLED
    _WAIT_FOR_PARTY_ENABLED = enabled


def _setup_heroai_integration(bot_instance: Botting) -> None:
    # TODO: Wire explicit HeroAI runtime controls if/when a stable API becomes available.
    ConsoleLog(BOT_NAME, "[HeroAI] Using native/FSM integration path.", Py4GW.Console.MessageType.Info)
    bot_instance.config.FSM.AddManagedCoroutine(
        "HeroAI_WaitForPartyWatchdog",
        lambda: _heroai_wait_for_party_watchdog(bot_instance),
    )


def _sync_heroai_runtime() -> None:
    # TODO: No HeroAI daemon bootstrap hook exists in this mission framework yet.
    return


def _reactivate_heroai_for_step(bot_instance: Botting, step_label: str) -> None:
    # TODO: HeroAI has no per-section utility reinjection API equivalent to CustomBehavior.
    ConsoleLog(BOT_NAME, f"[HeroAI] Section setup: {step_label}", Py4GW.Console.MessageType.Info)

def _enqueue_section(bot_instance: Botting, attr_name: str, label: str, section_fn):
    bot_instance.States.AddHeader(label)
    bot_instance.States.AddCustomState(
        lambda l=label: _reactivate_heroai_for_step(bot_instance, l),
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
    global _entered_dungeon
    _entered_dungeon = False
    target = MAIN_LOOP_HEADER_NAME
    fsm = bot_instance.config.FSM
    fsm.pause()
    try:
        if target:
            fsm.jump_to_state_by_name(target)
            ConsoleLog(BOT_NAME, f"[WIPE] {reason} - restarting at {target}.", Py4GW.Console.MessageType.Info)
        else:
            ConsoleLog(BOT_NAME, "[WIPE] MAIN_LOOP header missing, restarting from first state.", Py4GW.Console.MessageType.Warning)
            fsm.jump_to_state_by_step_number(0)
    except ValueError:
        ConsoleLog(BOT_NAME, f"[WIPE] Header '{target}' not found, restarting from first state.", Py4GW.Console.MessageType.Error)
        fsm.jump_to_state_by_step_number(0)
    finally:
        fsm.resume()

def _enemy_blacklist():
    return __import__("Py4GWCoreLib.EnemyBlacklist", fromlist=["EnemyBlacklist"]).EnemyBlacklist()


def _enemy_blacklist_add(name: str) -> None:
    _enemy_blacklist().add_name(name)


def _enemy_blacklist_remove(name: str) -> None:
    _enemy_blacklist().remove_name(name)


def _add_clear_flags_state(bot_instance: Botting, label: str = "Clear Flags") -> None:
    bot_instance.States.AddCustomState(
        lambda: HeroAIParty().party_flagging_manager.clear_all_flags(),
        label,
    )


def _flag_both(party_pos: int, flag_index: int, x, y) -> None:
    # CB: set flag via shared memory.
    HeroAIParty().party_flagging_manager.set_flag_position(flag_index, x, y)
    # HeroAI/native GW: set flag directly.
    agent_id = GLOBAL_CACHE.Party.Heroes.GetHeroAgentIDByPartyPosition(party_pos)
    if agent_id:
        GLOBAL_CACHE.Party.Heroes.FlagHero(agent_id, x, y)


def _enqueue_spread_flags(bot_instance: Botting, flag_points: list[tuple[int, int]]) -> None:
    """Clear flags, auto-assign emails, then set CB + HeroAI flags for each position.
    Only heroes are flagged (player/party leader is excluded automatically)."""
    _add_clear_flags_state(bot_instance)
    bot_instance.States.AddCustomState(
        lambda: HeroAIParty().party_flagging_manager.auto_assign_emails_if_none_assigned(),
        "Assign Flag Emails",
    )
    for idx, (flag_x, flag_y) in enumerate(flag_points):  # 0-based for CB
        bot_instance.States.AddCustomState(
            lambda i=idx, x=flag_x, y=flag_y: HeroAIParty().party_flagging_manager.set_flag_position(i, x, y),
            f"Set CB Flag {idx}",
        )
        bot_instance.Party.FlagHero(idx + 1, flag_x, flag_y)  # 1-based for native GW


def _enqueue_imprisoned_spirits_flags(bot_instance: Botting) -> None:
    """Clear flags, then assign left/right team accounts to their respective flag positions.
    The player's own account is excluded (it navigates via the bot FSM directly).
    Left accounts -> LEFT_POINTS sequentially; right accounts -> RIGHT_POINTS sequentially."""
    LEFT_POINTS  = [(13849, 6602), (13876, 6752), (13985, 6840), (13598, 6779)]
    RIGHT_POINTS = [(12871, 2512), (12640, 2485), (12402, 2472), (12137, 2444), (12150, 2139)]

    def _set_team_flags() -> None:
        manager      = HeroAIParty().party_flagging_manager
        manager.clear_all_flags()
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
            manager.set_flag_account_email(cb_idx, email)
            manager.set_flag_position(cb_idx, x, y)
            ConsoleLog(BOT_NAME, f"[Imprisoned] Left  [{cb_idx}] {email} -> ({x},{y})", Py4GW.Console.MessageType.Info)
            cb_idx  += 1
            left_pt += 1

        right_pt = 0
        for email in right_emails:
            if email == my_email:
                continue
            if right_pt >= len(RIGHT_POINTS):
                break
            x, y = RIGHT_POINTS[right_pt]
            manager.set_flag_account_email(cb_idx, email)
            manager.set_flag_position(cb_idx, x, y)
            ConsoleLog(BOT_NAME, f"[Imprisoned] Right [{cb_idx}] {email} -> ({x},{y})", Py4GW.Console.MessageType.Info)
            cb_idx   += 1
            right_pt += 1

        ConsoleLog(BOT_NAME, f"[Imprisoned] Flagged {cb_idx} account(s) total.", Py4GW.Console.MessageType.Info)

    bot_instance.States.AddCustomState(_set_team_flags, "Set Imprisoned Spirits Team Flags")


def WaitTillQuestDone(bot_instance: Botting) -> None:
    from Py4GWCoreLib.Quest import Quest
    bot_instance.Wait.UntilCondition(
        lambda: (Quest.GetActiveQuest() > 0) and Quest.IsQuestCompleted(Quest.GetActiveQuest())
    )



def _move_with_unstuck(
    bot_instance: Botting,
    target_x: float,
    target_y: float,
    step_name: str = "",
    stuck_check_ms: int = 2000,
    stuck_threshold: float = 120.0,
    backup_ms: int = 1000,
    max_retries: int = 30,
    timeout: int = 60_000,
    recalc_interval_ms: int = 4000,
) -> None:
    """Move to (target_x, target_y) using navmesh A* pathfinding. Never skips the step.

    Setup: one import block per call, then the retry loop.

    Retry loop (while True - runs until the target is reached):

    0. Early-exit: already within `tolerance` -> return.

      1. Refresh avoid-points:
           Re-collect positions of all alive blacklisted enemies on EVERY path build
           so the route always reflects current patrol positions.

      2. Path building:
           Always builds the standard navmesh path first (AutoPathing).
           If blacklisted enemies are present, also builds a penalty-weighted
                     detour path (_AStarBlocking, quadratic soft penalty within 100 units --
           tight radius so only the directly blocked nodes are penalised).
           The two paths are compared by total Euclidean length:
                     - Detour shorter -> route around the enemy.
                     - Standard shorter or equal -> walk straight through (no other way).
             No edge-hugging side effects.

      3. Path following in short segments (recalc_interval_ms, default 4 s):
           Each segment runs FollowPath for at most recalc_interval_ms.
           After each segment:
                     - Reached target -> return.
                     - Made progress (moved closer) -> rebuild path with fresh enemy
             positions; attempt counter NOT incremented.
                     - No progress (truly stuck) -> fall through to recovery (Step 5).

      4. Max-retries reset with patrol wait:
           After `max_retries` failed attempts, wait 5 s then reset attempt = 0.
           The step is NEVER abandoned.

      5. Recovery (between failed attempts):
           /stuck -> wait 1 s -> distance check -> walk backwards -> wait 300 ms
           -> increment attempt counter -> back to step 0.
    """
    import math

    def _coro():
        import heapq as _heapq
        from Py4GWCoreLib.Pathing import AutoPathing, AStar, AStarNode, chaikin_smooth_path, densify_path2d
        from Py4GWCoreLib.EnemyBlacklist import EnemyBlacklist
        tolerance = 150.0
        tx, ty = target_x, target_y

        # Tight penalty radius: only penalise nodes that are within 100 units of
        # an enemy -- close enough that the standard A* would pass through.
        # Because the radius is small, the detour is compact and natural-looking.
        # The comparison with the standard path (see below) ensures we only take
        # the detour when it is actually shorter, so we still walk straight through
        # a narrow corridor if there is no room to go around.
        _SOFT_AVOID_RADIUS = 100.0
        _SOFT_PENALTY      = 5000.0

        # Local A* subclass: avoids blacklisted-enemy positions.
        class _AStarBlocking(AStar):
            def __init__(self, navmesh, avoid_points):
                super().__init__(navmesh)
                self._avoid_points = avoid_points

            def _min_dist_to_avoid_points(self, node_id: int) -> float:
                if not self._avoid_points:
                    return float("inf")
                nx, ny = self.navmesh.get_position(node_id)
                return min(math.hypot(nx - ax, ny - ay) for ax, ay in self._avoid_points)

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
                        d = self._min_dist_to_avoid_points(nb)
                        penalty = 0.0
                        if d < _SOFT_AVOID_RADIUS:
                            # Quadratic: strong near centre, zero at boundary
                            ratio = (_SOFT_AVOID_RADIUS - d) / _SOFT_AVOID_RADIUS
                            penalty = ratio * ratio * _SOFT_PENALTY
                        nc = cost[cur.id] + self.heuristic(cur.id, nb) + penalty
                        if nb not in cost or nc < cost[nb]:
                            cost[nb] = nc
                            _heapq.heappush(ol, AStarNode(nb, nc, nc + self.heuristic(nb, g_id), cur.id))
                            came[nb] = cur.id
                return False

        attempt = 0
        while True:
            px, py = Player.GetXY()
            if math.sqrt((tx - px) ** 2 + (ty - py) ** 2) <= tolerance:
                return  # already there

            # Refresh enemy positions on every attempt.
            # Enemies patrol; stale positions from the coroutine start would
            # waste detours around enemies that have already moved away.
            _navmesh = AutoPathing().get_navmesh()
            _avoid_points: list[tuple[float, float]] = []
            if _navmesh:
                _bl = EnemyBlacklist()
                for _eid in AgentArray.GetEnemyArray():
                    if _bl.is_blacklisted(_eid) and Agent.IsAlive(_eid):
                        _ex, _ey = Agent.GetXY(_eid)
                        _avoid_points.append((_ex, _ey))

            # Step 1: build navmesh path.
            ConsoleLog(
                BOT_NAME,
                f"[Move] Building path to ({tx:.0f},{ty:.0f}) attempt {attempt + 1}"
                + (f" (avoiding {len(_avoid_points)} blacklisted enemies)" if _avoid_points else ""),
                Py4GW.Console.MessageType.Info,
            )
            # Always build the standard navmesh path first.
            path = yield from AutoPathing().get_path_to(tx, ty)

            if _avoid_points and _navmesh:
                # Build the penalty-weighted detour path and compare lengths.
                # If the detour is shorter (or equal) it routes around the bubble.
                # If the only route IS through the bubble, the standard path will
                # be shorter -> we use it directly, avoiding edge-hugging behaviour.
                _cpx, _cpy = Player.GetXY()
                _ast = _AStarBlocking(_navmesh, _avoid_points)
                if _ast.search((_cpx, _cpy), (tx, ty)):
                    _raw    = _ast.get_path()
                    _sm     = _navmesh.smooth_path_by_los(_raw, margin=100, step_dist=200.0)
                    _detour = densify_path2d(_sm)

                    def _path_len(pts):
                        return sum(
                            math.hypot(pts[i][0] - pts[i-1][0], pts[i][1] - pts[i-1][1])
                            for i in range(1, len(pts))
                        )

                    _len_std    = _path_len(path)    if path    else float("inf")
                    _len_detour = _path_len(_detour) if _detour else float("inf")

                    if _len_detour < _len_std:
                        ConsoleLog(
                            BOT_NAME,
                            f"[Move] Using detour path ({_len_detour:.0f} vs {_len_std:.0f} units) to avoid {len(_avoid_points)} enemies.",
                            Py4GW.Console.MessageType.Info,
                        )
                        path = _detour
                    else:
                        ConsoleLog(
                            BOT_NAME,
                            f"[Move] No shorter detour found ({_len_detour:.0f} vs {_len_std:.0f} units) - walking through.",
                            Py4GW.Console.MessageType.Info,
                        )

            _path_to_follow = path if path else [(tx, ty)]
            if not path:
                ConsoleLog(
                    BOT_NAME,
                    f"[Move] No navmesh path to ({tx:.0f},{ty:.0f}), using direct move.",
                    Py4GW.Console.MessageType.Info,
                )

            # Step 3: follow in short segments and rebuild after each segment.
            # Run FollowPath for at most recalc_interval_ms per segment.
            # This lets us refresh enemy positions between segments so the
            # path always routes around their current position.
            _dist_before = math.hypot(tx - px, ty - py)
            reached = yield from Routines.Yield.Movement.FollowPath(
                path_points=_path_to_follow,
                tolerance=tolerance,
                timeout=recalc_interval_ms,
            )
            if reached:
                return

            # Check whether we made progress during the segment.
            _nx, _ny = Player.GetXY()
            _dist_after = math.hypot(tx - _nx, ty - _ny)
            _progress = _dist_before - _dist_after

            if _progress > stuck_threshold:
                # Moving in the right direction - rebuild path, do not count as retry.
                continue

            # No meaningful progress -> treat as a stuck attempt.
            ConsoleLog(
                BOT_NAME,
                f"[Move] No progress toward ({tx:.0f},{ty:.0f}) on attempt {attempt + 1} "
                f"(moved {_progress:.0f} units).",
                Py4GW.Console.MessageType.Warning,
            )

            if attempt >= max_retries:
                ConsoleLog(
                    BOT_NAME,
                    f"[Move] Max retries reached for ({tx:.0f},{ty:.0f}) - waiting 5 s for enemies to clear, then retrying.",
                    Py4GW.Console.MessageType.Warning,
                )
                yield from Routines.Yield.wait(5000)
                attempt = 0
                continue

            # Step 5: recovery before the next attempt.
            Player.SendChatCommand("stuck")
            yield from Routines.Yield.wait(1000)

            cpx, cpy = Player.GetXY()
            if math.sqrt((tx - cpx) ** 2 + (ty - cpy) ** 2) <= tolerance:
                return  # /stuck teleported us close enough

            yield from Routines.Yield.Movement.WalkBackwards(backup_ms)
            yield from Routines.Yield.wait(300)
            attempt += 1

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
        HeroAIParty().set_party_custom_target(closest_enemy)

    bot_instance.States.AddCustomState(_focus_logic, "Focus Keeper of Souls")

def bot_routine(bot: Botting):

    global MAIN_LOOP_HEADER_NAME
    bot.Events.OnPartyWipeCallback(lambda: OnPartyWipe(bot))
    HeroAIParty().set_party_is_blessing_enabled(True)
    _setup_heroai_integration(bot)
    _configure_startup_combat_widgets(bot)
    
    bot.Templates.Aggressive()
    

    # Set up the FSM states properly
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


def _configure_startup_combat_widgets(bot_instance: Botting) -> None:
    def _active_multibox_emails() -> list[str]:
        emails: list[str] = []
        for account in (GLOBAL_CACHE.ShMem.GetAllAccountData() or []):
            email = str(getattr(account, "AccountEmail", "") or "").strip()
            if not email:
                continue
            if not bool(getattr(account, "IsSlotActive", True)):
                continue
            if bool(getattr(account, "IsIsolated", False)):
                continue
            emails.append(email)
        return emails

    def _broadcast_widget_command(widget_name: str, command: SharedCommandType, action_label: str) -> None:
        sender_email = Player.GetAccountEmail()
        recipients = _active_multibox_emails()

        for account_email in recipients:
            GLOBAL_CACHE.ShMem.SendMessage(
                sender_email,
                account_email,
                command,
                (0, 0, 0, 0),
                (widget_name, "", "", ""),
            )

        ConsoleLog(
            BOT_NAME,
            f"[Startup] {action_label} '{widget_name}' for {len(recipients)} active account(s).",
            Py4GW.Console.MessageType.Info,
        )

    bot_instance.States.AddCustomState(
        lambda: ConsoleLog(BOT_NAME, "[Startup] Disabling CustomBehavior widgets on all accounts.", Py4GW.Console.MessageType.Info),
        "[Startup] Log Disable CustomBehavior Widgets",
    )
    bot_instance.States.AddCustomState(
        lambda: _broadcast_widget_command("CustomBehaviors", SharedCommandType.DisableWidget, "Broadcasted disable"),
        "Disable CustomBehaviors on active accounts",
    )
    bot_instance.States.AddCustomState(
        lambda: _broadcast_widget_command("Custom Behavior", SharedCommandType.DisableWidget, "Broadcasted disable"),
        "Disable Custom Behavior on active accounts",
    )
    bot_instance.States.AddCustomState(
        lambda: _broadcast_widget_command("Custom Behaviors: Utility AI", SharedCommandType.DisableWidget, "Broadcasted disable"),
        "Disable CustomBehavior Widgets on all accounts",
    )
    bot_instance.Wait.ForTime(2000)
    bot_instance.States.AddCustomState(
        lambda: ConsoleLog(BOT_NAME, "[Startup] Enabling HeroAI widget on all accounts.", Py4GW.Console.MessageType.Info),
        "[Startup] Log Enable HeroAI Widget",
    )
    bot_instance.States.AddCustomState(
        lambda: _broadcast_widget_command("HeroAI", SharedCommandType.EnableWidget, "Broadcasted enable"),
        "Enable HeroAI on active accounts",
    )
    bot_instance.States.AddCustomState(
        lambda: _broadcast_widget_command("Dhuum Helper", SharedCommandType.EnableWidget, "Broadcasted enable"),
        "Enable Dhuum Helper on active accounts",
    )

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

    # Inventory refill at guild hall/configured outpost.
    bot_instance.Multibox.KickAllAccounts()
    _do_inventory_refill(bot_instance)

    if BotSettings.UseCons:
        # Withdraw consets (Essence, Grail, Armor) per account from Xunlai chest
        bot_instance.Multibox.RestockConset(10)

    # Leave any existing party (multibox-aware).
    handle_leave_party(_make_ctx({"type": "leave_party", "name": "Leave Party", "multibox": True}))

    # Travel to the selected entry point.
    entrypoint_name, entrypoint_map_id = UW_ENTRYPOINTS.get(
        EnterSettings.EntryPoint, UW_ENTRYPOINTS[DEFAULT_UW_ENTRYPOINT_KEY]
    )
    handle_random_travel(_make_ctx({
        "type": "random_travel",
        "name": f"Travel to {entrypoint_name}",
        "target_map_id": entrypoint_map_id,
    }))

    # Form party.
    handle_summon_all_accounts(_make_ctx({"type": "summon_all_accounts", "name": "Summon Alts", "ms": 5000}))

    # Wait until every account has loaded into the entrypoint map (up to 90 s).
    _expected_map = entrypoint_map_id
    bot_instance.Wait.UntilCondition(
        lambda: all(int(acc.AgentData.Map.MapID) == _expected_map for acc in GLOBAL_CACHE.ShMem.GetAllAccountData()),
        duration=20000,
    )

    handle_invite_all_accounts(_make_ctx({"type": "invite_all_accounts", "name": "Invite Alts"}))

    # Apply hard mode before using the scroll.
    handle_set_hard_mode(_make_ctx({"type": "set_hard_mode", "name": "Set Hard Mode", "enabled": BotSettings.HardMode}))

    # Use UW scroll (model 3746).
    handle_use_item(_make_ctx({"type": "use_item", "name": "Use UW Scroll", "model_id": UW_SCROLL_MODEL_ID}))

    # Wait until inside the Underworld.
    handle_wait_map_change(_make_ctx({"type": "wait_map_change", "name": "Wait For UW", "target_map_id": UW_MAP_ID}))

    bot_instance.States.AddCustomState(_mark_entered_dungeon, "Mark entered dungeon")
    bot_instance.Properties.ApplyNow("pause_on_danger", "active", True)

    


def enable_default_party_behavior(bot_instance: Botting):
    """
    Enable the baseline party behavior toggles used across Underworld missions.
    """
    bot_instance.States.AddCustomState(lambda: _toggle_wait_for_party(True), "Enable WaitIfPartyMemberTooFar")
    bot_instance.States.AddCustomState(lambda: HeroAIParty().set_party_is_following_enabled(True), "Enable Follow")
    bot_instance.States.AddCustomState(lambda: HeroAIParty().set_party_is_looting_enabled(True), "Enable Looting")


def Clear_the_Chamber(bot_instance: Botting):
    bot_instance.States.AddHeader("Clear the Chamber")
    bot_instance.States.AddCustomState(
        lambda: _reactivate_heroai_for_step(bot_instance, "Clear the Chamber"),
        "[Setup] Clear the Chamber",
    )
    #blacklist here
    bot_instance.States.AddCustomState(
        lambda: _enemy_blacklist_add("obsidian guardian"),
        "Blacklist Obsidian Guardian",
    )
    bot_instance.States.AddCustomState(
        lambda: _enemy_blacklist_add("vengeful aatxe"),
        "Blacklist Vengeful Aatxe",
    )
    bot_instance.States.AddCustomState(
        lambda: _enemy_blacklist_add("chained soul"),
        "Blacklist Chained Soul",
    )
    bot_instance.States.AddCustomState(
        lambda: _enemy_blacklist_remove("wastfull spirit"),
        "Unblacklist Wastfull Spirit",
    )
    bot_instance.States.AddCustomState(
        lambda: _enemy_blacklist_remove("obsidian behemoth"),
        "Unblacklist Obsidian Behemoth",
    )
    bot_instance.States.AddCustomState(
        lambda: _enemy_blacklist_remove("banished dream rider"),
        "Unblacklist Banished Dream Rider",
    )
    enable_default_party_behavior(bot_instance)
    bot_instance.States.AddCustomState(lambda: HeroAIParty().set_party_is_combat_enabled(False), "Disable Combat")
    #bot_instance.Move.XYAndInteractNPC(295, 7221, "go to NPC")
    #bot_instance.Dialogs.AtXY(295, 7221, 0x806501, "take quest")
    bot_instance.Dialogs.WithEncName("Lost Soul",0x806501, "Take Clear the Chamber")
    bot_instance.States.AddCustomState(lambda: HeroAIParty().set_party_is_combat_enabled(True), "Enable Combat")
    bot_instance.Move.XY(769, 6564, "Prepare to clear the chamber")
    bot_instance.States.AddCustomState(lambda: HeroAIParty().set_party_forced_state(HeroAIForcedState.CLOSE_TO_AGGRO),"Force Close_to_Aggro",)
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

    bot_instance.States.AddCustomState(lambda: HeroAIParty().set_party_forced_state(None),"Release Close_to_Aggro",)

    bot_instance.States.AddCustomState(lambda: _toggle_wait_for_party(True), "Enable WaitIfPartyMemberTooFar")

    bot_instance.Move.XY(-1505, 6352, "Left")
    bot_instance.Move.XY(-755, 8982, "Mid")
    bot_instance.Move.XY(1259, 10214, "Right")
    bot_instance.Move.XY(-3729, 13414, "Right")
    bot_instance.Move.XY(-5855, 11202, "Clear the Room")
    bot_instance.Wait.ForTime(3000)
    
    bot_instance.Move.XYAndInteractNPC(-5806, 12831, "go to NPC")
    bot_instance.Dialogs.WithEncName("Reaper of the Labyrinth",0x806D01, "Take Restoring Grenth's Monuments")
    #bot_instance.Dialogs.AtXY(-5806, 12831, 0x806D01, "take quest")
    bot_instance.Wait.ForTime(3000)

def Pass_The_Mountains(bot_instance: Botting):
    bot_instance.States.AddCustomState(lambda: _toggle_wait_for_party(True), "Enable WaitIfPartyMemberTooFar")
    bot_instance.Move.XY(-1355 , 10210, "Pass the Mountains 0")
    bot_instance.Move.XY(-220, 1691, "Pass the Mountains 1")
    bot_instance.Move.XY(7035, 1973, "Pass the Mountains 2")
    bot_instance.Move.XY(8089, -3303, "Pass the Mountains 3")
    bot_instance.Move.XY(8121, -6054, "Pass the Mountains 4")
    

def Restore_Mountains(bot_instance: Botting):
    bot_instance.States.AddCustomState(lambda: _toggle_wait_for_party(True), "Enable WaitIfPartyMemberTooFar")
    bot_instance.Move.XY(7013, -7582, "Restore the Mountains 1")
    bot_instance.Move.XY(1420, -9126, "Restore the Mountains 2")
    bot_instance.Move.XY(-8373, -5016, "Restore the Mountains 3")
    bot_instance.Wait.ForTime(5000)

def Deamon_Assassin(bot_instance: Botting):
    bot_instance.States.AddCustomState(lambda: _toggle_wait_for_party(True), "Enable WaitIfPartyMemberTooFar")
    #bot_instance.Move.XYAndInteractNPC(-8250, -5171, "go to NPC")
    #bot_instance.Dialogs.AtXY(-8250, -5171, 0x806801, "take quest")
    bot_instance.Dialogs.WithEncName("Reaper of the Twin Serpent Mountains",0x806801, "Take Deamon Assassin")
    bot_instance.Move.XY(-3645, -5820, "Deamon Assassin 1")
    WaitTillQuestDone(bot_instance)

def Restore_Planes(bot_instance: Botting):
    bot_instance.States.AddCustomState(lambda: _toggle_wait_for_party(True), "Enable WaitIfPartyMemberTooFar")
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
        lambda: _enemy_blacklist_add("banished dream rider"),
        "Blacklist Banished Dream Rider",
    )
    bot_instance.Move.XY(13837, -14736, "Restore Planes 1 left Rider")
    bot_instance.States.AddCustomState(
        lambda: _enemy_blacklist_remove("banished dream rider"),
        "Unblacklist Banished Dream Rider",
    )
    Wait_for_Spawns(bot_instance,13790, -15568)
    Wait_for_Spawns(bot_instance,11287, -17921)


def The_Four_Horsemen(bot_instance: Botting):
    bot_instance.States.AddCustomState(lambda: _toggle_wait_for_party(True), "Enable WaitIfPartyMemberTooFar")
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
    _enqueue_spread_flags(bot_instance, THE_FOUR_HORSEMEN_FLAG_POINTS)
    bot_instance.States.AddCustomState(lambda: HeroAIParty().set_party_is_looting_enabled(False), "Disable Looting")
    bot_instance.States.AddCustomState(lambda: _toggle_wait_for_party(False), "Disable WaitIfPartyMemberTooFar")
    bot_instance.States.AddCustomState(lambda: HeroAIParty().set_party_forced_state(HeroAIForcedState.CLOSE_TO_AGGRO),"Force Close_to_Aggro",)
    bot_instance.Move.XYAndInteractNPC(11371, -17990, "go to NPC")
    bot_instance.Dialogs.AtXY(-8250, -5171, 0x806A01, "take quest")  
    bot_instance.States.AddCustomState(lambda: HeroAIParty().set_party_forced_state(None),"Release Close_to_Aggro",)

    bot_instance.Wait.ForTime(35000)

    bot_instance.Move.XYAndInteractNPC(11371, -17990, "TP to Chamber")
    #bot_instance.Dialogs.AtXY(11371, -17990, 0x7F, "take quest")
    #bot_instance.Dialogs.AtXY(11371, -17990, 0x86, "take quest") 
    bot_instance.Dialogs.AtXY(11371, -17990, 0x8D, "take quest") 
    _add_clear_flags_state(bot_instance)

    bot_instance.Wait.ForTime(1000)

    bot_instance.Move.XYAndInteractNPC(-5782, 12819, "TP back to Chaos")
    #bot_instance.Dialogs.AtXY(11371, -17990, 0x7F, "take quest")
    #bot_instance.Dialogs.AtXY(11371, -17990, 0x84, "take quest") 
    bot_instance.Dialogs.AtXY(11371, -17990, 0x8B, "take quest") 
    bot_instance.Wait.ForTime(1000)
    bot_instance.States.AddCustomState(lambda: HeroAIParty().set_party_is_following_enabled(True), "Enable Following")
    THE_FOUR_HORSEMEN_FLAG_POINTS_2 = [
        (11318, -17670),
        (11318, -17670),
        (11221, -18335),
        (11479, -18361),
        (11806, -18134),
        (11697, -17748),
        (11354, -17530),
    ]
    _enqueue_spread_flags(bot_instance, THE_FOUR_HORSEMEN_FLAG_POINTS_2)
    bot_instance.Party.UnflagAllHeroes()
    WaitTillQuestDone(bot_instance)
    _add_clear_flags_state(bot_instance)
    bot_instance.Move.XYAndInteractNPC(11371, -17990, "go to NPC")
    bot_instance.Dialogs.AtXY(-8250, -5171, 0x806A07, "take quest")  
    bot_instance.States.AddCustomState(lambda: HeroAIParty().set_party_is_following_enabled(True), "Enable Follow")
    bot_instance.States.AddCustomState(lambda: _toggle_wait_for_party(True), "Enable WaitIfPartyMemberTooFar")
    bot_instance.States.AddCustomState(lambda: HeroAIParty().set_party_is_looting_enabled(True), "Enable Looting")

def Restore_Pools(bot_instance: Botting):
    bot_instance.States.AddCustomState(lambda: _toggle_wait_for_party(True), "Enable WaitIfPartyMemberTooFar")
    '''
    Wait_for_Spawns(bot_instance,4647, -16833)
    Wait_for_Spawns(bot_instance,2098, -15543)
    '''
    bot_instance.States.AddCustomState(
        lambda: _enemy_blacklist_add("banished dream rider"),
        "Blacklist Banished Dream Rider",
    )
    bot_instance.Move.XY(-12703, -10990, "Restore Pools 1")
    bot_instance.Move.XY(-11849, -11986, "Restore Pools 2")
    bot_instance.Move.XY(-5974, -19739, "Restore Pools 3")
    bot_instance.Move.XY(-7217, -19394, "Restore Pools 4")
    bot_instance.Move.XY(-5688, -19471, "Restore Pools 4")

def Terrorweb_Queen(bot_instance: Botting):
    bot_instance.States.AddCustomState(lambda: _toggle_wait_for_party(True), "Enable WaitIfPartyMemberTooFar")
    bot_instance.Move.XYAndInteractNPC(-6890, -19454, "go to NPC")
    bot_instance.Dialogs.AtXY(-6890, -19454, 0x806B01, "take quest")   
    bot_instance.Move.XY(-12375, -15578, "Terrorweb Queen 1")
    bot_instance.Move.XYAndInteractNPC(-6957, -19478, "go to NPC")
    bot_instance.Dialogs.AtXY(-6957, -19478, 0x806B07, "Back to Chamber")
    bot_instance.Dialogs.AtXY(-6957, -19478, 0x8B, "Back to Chamber")
    
def Restore_Pit(bot_instance: Botting):
    bot_instance.States.AddCustomState(lambda: _toggle_wait_for_party(True), "Enable WaitIfPartyMemberTooFar")
    bot_instance.Move.XY(14178, -57, "Restore Pit 1")
    bot_instance.States.AddCustomState(
        lambda: _enemy_blacklist_remove("banished dream rider"),
        "Unblacklist Banished Dream Rider",
    )
    bot_instance.Move.XY(15323, 2970, "Restore Pit 2")
    bot_instance.Move.XY(15393, 406, "Restore Pit 3")
    bot_instance.Move.FollowPath([
        (15252, 316),
        (13451, 1123),
        (13181, 1419),
        (13076, 1547),
    ], step_name="Over the Bridge")
    bot_instance.Move.XY(13216, 1428, "Restore Pit 4")
    bot_instance.Move.XY(13896, 3670, "Restore Pit 5")
    bot_instance.Move.XY(15382, 6581, "Restore Pit 6")
    bot_instance.Move.XY(10620, 2665, "Restore Pit 7")
    bot_instance.Move.XY(8644, 6242, "Restore Pit 8")
    bot_instance.Wait.ForTime(3000)

def Imprisoned_Spirits(bot_instance: Botting):
    bot_instance.States.AddCustomState(lambda: _toggle_wait_for_party(True), "Enable WaitIfPartyMemberTooFar")
    bot_instance.States.AddCustomState(lambda: HeroAIParty().set_party_is_looting_enabled(False), "Disable Looting")
    bot_instance.Move.XY(13212, 4978)
    _enqueue_imprisoned_spirits_flags(bot_instance)
    bot_instance.States.AddCustomState(lambda: _toggle_wait_for_party(False), "Disable WaitIfPartyMemberTooFar")
    bot_instance.Move.XY(8692, 6292, "go to NPC")
    bot_instance.Move.XYAndInteractNPC(8666, 6308, "go to NPC")
    bot_instance.Dialogs.AtXY(8666, 6308, 0x806901, "take quest")  
    bot_instance.Move.XY(13652, 6117) #Runter rennen zum linken team
    _add_clear_flags_state(bot_instance)
    bot_instance.Move.XY(12593, 1814)
    bot_instance.Wait.ForTime(30000)
    bot_instance.States.AddCustomState(
        lambda: _enemy_blacklist_remove("chained soul"),
        "Unblacklist Chained Soul",
    )
    bot_instance.Move.XY(10437, 5005)
    WaitTillQuestDone(bot_instance)
    bot_instance.States.AddCustomState(lambda: HeroAIParty().set_party_is_looting_enabled(True), "Enable Looting")
    ##warten bis quest fertig

    bot_instance.Move.XY(8692, 6292, "go to NPC")
    bot_instance.Dialogs.AtXY(8692, 6292, 0x8D, "Back to Chamber")
        

def Restore_Vale(bot_instance: Botting):

    bot_instance.States.AddCustomState(lambda: _toggle_wait_for_party(True), "Enable WaitIfPartyMemberTooFar")

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

def Wrathfull_Spirits(bot_instance: Botting):
    bot_instance.States.AddCustomState(lambda: _toggle_wait_for_party(True), "Enable WaitIfPartyMemberTooFar")
    bot_instance.Move.XYAndInteractNPC(-13275, 5261, "go to NPC")
    bot_instance.Dialogs.AtXY(5755, 12769, 0x806E03, "Back to Chamber")
    bot_instance.Dialogs.AtXY(5755, 12769, 0x806E01, "Back to Chamber")
    bot_instance.Templates.Pacifist()
    bot_instance.States.AddCustomState(lambda: _toggle_wait_for_party(False), "Disable WaitIfPartyMemberTooFar")
    #bot_instance.States.AddCustomState(lambda: HeroAIParty().set_party_is_combat_enabled(False), "Disable Combat")
    bot_instance.States.AddCustomState(
        lambda: _enemy_blacklist_add("tortured spirit"),
        "Blacklist Tortured Spirit",
    )
    bot_instance.Move.XY(-13422, 973, "Wrathfull Spirits 1")
    bot_instance.Templates.Aggressive()
    bot_instance.States.AddCustomState(
        lambda: _enemy_blacklist_remove("tortured spirit"),
        "Unblacklist Tortured Spirit",
    )
    #bot_instance.States.AddCustomState(lambda: HeroAIParty().set_party_is_combat_enabled(True), "Enable Combat")
    bot_instance.States.AddCustomState(lambda: _toggle_wait_for_party(True), "Enable WaitIfPartyMemberTooFar") 
    bot_instance.Move.XY(-10207, 1746, "Wrathfull Spirits 2")
    bot_instance.Move.XY(-13287, 1996, "Wrathfull Spirits 3")
    bot_instance.Move.XY(-14486, 7113, "Wrathfull Spirits 4")
    bot_instance.Move.XY(-15226, 4129 , "Wrathfull Spirits 5")
    bot_instance.Move.XYAndInteractNPC(-13275, 5261, "go to NPC")
    bot_instance.Dialogs.AtXY(5755, 12769, 0x806E07, "Take Reward")
    bot_instance.Dialogs.AtXY(5755, 12769, 0x8D, "Back to Chamber")
    bot_instance.Wait.ForTime(3000)

def Escort_of_Souls(bot_instance: Botting):
    bot_instance.States.AddCustomState(lambda: _toggle_wait_for_party(True), "Enable WaitIfPartyMemberTooFar")
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
    bot_instance.States.AddCustomState(lambda: _toggle_wait_for_party(True), "Enable WaitIfPartyMemberTooFar")
    #The Quest
    #1st Keeper
    bot_instance.States.AddCustomState(
        lambda: _enemy_blacklist_add("obsidian behemoth"),
        "Blacklist Obsidian Behemoth",
    )
    _move_with_unstuck(bot_instance, -2965, 10260, "1st Keeper approach")
    bot_instance.Wait.ForTime(5000)
    bot_instance.States.AddCustomState(lambda: HeroAIParty().set_party_is_following_enabled(False), "Disable Following")
    bot_instance.States.AddCustomState(lambda: HeroAIParty().set_party_forced_state(HeroAIForcedState.CLOSE_TO_AGGRO),"Force Close_to_Aggro")
    bot_instance.States.AddCustomState(lambda: _toggle_wait_for_party(False), "Disable wait_for_party")

    bot_instance.Move.XYAndInteractNPC(-5806, 12831, "go to NPC")
    bot_instance.Dialogs.AtXY(-5806, 12831, 0x806701, "take quest")

    bot_instance.States.AddCustomState(lambda: HeroAIParty().set_party_forced_state(None),"Release Close_to_Aggro")
    FocusKeeperOfSouls(bot_instance)
    bot_instance.Wait.ForTime(500)
    FocusKeeperOfSouls(bot_instance)
    bot_instance.Wait.ForTime(500)
    FocusKeeperOfSouls(bot_instance)
    bot_instance.Wait.ForTime(20000)
    bot_instance.States.AddCustomState(lambda: HeroAIParty().set_party_is_following_enabled(True), "Enable Following")
    bot_instance.States.AddCustomState(lambda: HeroAIParty().set_party_forced_state(None),"Release Close_to_Aggro",)
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
        lambda: _enemy_blacklist_remove("obsidian behemoth"),
        "Unblacklist Obsidian Behemoth",
    )

def Restore_Wastes(bot_instance: Botting):
    bot_instance.States.AddCustomState(lambda: _toggle_wait_for_party(True), "Enable WaitIfPartyMemberTooFar")
    bot_instance.Templates.Aggressive()
    bot_instance.Properties.ApplyNow("pause_on_danger", "active", True)
    bot_instance.Move.XY(3891, 7572, "Restore Wastes 1")
    bot_instance.Move.XY(4106, 16031, "Restore Wastes 2")
    bot_instance.Move.XY(2486, 21723, "Restore Wastes 3")
    bot_instance.Move.XY(-1452, 21202, "Restore Wastes 4")
    bot_instance.Move.XY(542, 18310, "Restore Wastes 5")
    bot_instance.Wait.ForTime(3000)

def Servants_of_Grenth(bot_instance: Botting):
    bot_instance.States.AddCustomState(lambda: _toggle_wait_for_party(True), "Enable WaitIfPartyMemberTooFar")
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
    bot_instance.States.AddCustomState(lambda: HeroAIParty().set_party_forced_state(HeroAIForcedState.CLOSE_TO_AGGRO),"Force Close_to_Aggro",)
    bot_instance.Move.XYAndInteractNPC(554, 18384, "go to NPC")
    bot_instance.States.AddCustomState(lambda: HeroAIParty().set_party_is_following_enabled(False), "Disable Following")
    #bot_instance.Dialogs.AtXY(5755, 12769, 0x806603, "Back to Chamber")
    bot_instance.Dialogs.AtXY(5755, 12769, 0x806601, "Back to Chamber")
    bot_instance.States.AddCustomState(lambda: HeroAIParty().set_party_forced_state(None),"Release Close_to_Aggro",)
    
    bot_instance.Move.XY(2700, 19952, "Servants of Grenth 2")
    bot_instance.States.AddCustomState(lambda: _toggle_wait_for_party(True), "Enable WaitIfPartyMemberTooFar")
    bot_instance.States.AddCustomState(lambda: HeroAIParty().set_party_is_following_enabled(True), "Enable Following")
    bot_instance.Party.UnflagAllHeroes()
    bot_instance.Party.FlagAllHeroes(3032, 20148)
    bot_instance.Party.UnflagAllHeroes()
    WaitTillQuestDone(bot_instance)
    bot_instance.Party.UnflagAllHeroes()
    _add_clear_flags_state(bot_instance)
    bot_instance.Wait.ForTime(30000)
    

def Dhuum(bot_instance: Botting):
    bot_instance.States.AddHeader("Dhuum")
    bot_instance.States.AddCustomState(lambda: HeroAIParty().set_party_forced_state(None),"Release Close_to_Aggro",)

    def _flag_sacrifice_accounts() -> None:
        flag_x, flag_y = -15022, 17277
        manager = HeroAIParty().party_flagging_manager
        manager.clear_all_flags()

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

            manager.set_flag_account_email(cb_index, email)
            manager.set_flag_position(cb_index, flag_x, flag_y)
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
        manager = HeroAIParty().party_flagging_manager

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

            manager.set_flag_account_email(cb_index, email)
            manager.set_flag_position(cb_index, flag_x, flag_y)
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
    
    bot_instance.Move.XY(-13987, 17291, "Move to Dhuum fight")
    bot_instance.States.AddCustomState(lambda: HeroAIParty().set_party_is_following_enabled(False), "Disable Following")
    bot_instance.Wait.ForTime(2000)  # Wait till some Allies die
    #Wait till Dhuum is dead
    bot_instance.Wait.UntilCondition(
        lambda: any(
            Agent.IsGadget(agent_id)
            and "underworld chest" in (Agent.GetNameByID(agent_id) or "").strip().lower()
            and Utils.Distance((-14381.0, 17283.0), Agent.GetXY(agent_id)) <= 300
            for agent_id in AgentArray.GetAgentArray()
        )
    )  # Wait until the Underworld Chest (Gadget) appears near (-14381, 17283)


    bot_instance.States.AddCustomState(lambda: HeroAIParty().set_party_is_combat_enabled(False), "Disable Combat")


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

    bot_instance.States.AddCustomState(lambda: HeroAIParty().set_party_is_following_enabled(True), "Enable Following")
    _add_clear_flags_state(bot_instance)

    bot_instance.States.AddCustomState(_loot_underworld_chest, "Loot Underworld Chest")

    bot_instance.Wait.ForTime(5000)  # Wait for looting to finish    

    bot_instance.States.AddCustomState(_loot_underworld_chest, "Loot Underworld Chest")

    bot_instance.Wait.ForTime(5000)  # Wait for any stragglers to finish looting
    bot_instance.States.AddCustomState(lambda: HeroAIParty().set_party_is_looting_enabled(False), "Disable Looting")
    bot_instance.Move.XY(-14324, 17549)
    bot_instance.States.AddCustomState(lambda: HeroAIParty().set_party_is_looting_enabled(True), "Enable Looting")
    bot_instance.Wait.ForTime(5000)
    bot_instance.States.AddCustomState(lambda: HeroAIParty().set_party_is_looting_enabled(False), "Disable Looting")
    bot_instance.Move.XY(-14243, 17017)
    bot_instance.States.AddCustomState(lambda: HeroAIParty().set_party_is_looting_enabled(True), "Enable Looting")
    bot_instance.Wait.ForTime(5000)
    bot_instance.States.AddCustomState(lambda: HeroAIParty().set_party_is_combat_enabled(True), "Enable Combat")



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

    # Travel to inventory location.
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

    # Restock ID and salvage kits (3 rounds).
    if InventorySettings.RestockKits:
        kit_step = {"type": "restock_kits", "name": "Restock Kits", "id_kits": 2, "salvage_kits": 5, "multibox": True}
        for _ in range(3):
            handle_restock_kits(_make_ctx(kit_step))

    # Restock cons from Xunlai chest.
    if InventorySettings.RestockCons and BotSettings.UseCons:
        handle_restock_cons(_make_ctx({"type": "restock_cons", "name": "Restock Consumables"}))

    # Sell materials.
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

    # Deposit full material stacks.
    if InventorySettings.DepositMaterials:
        handle_deposit_materials(_make_ctx({"type": "deposit_materials", "name": "Deposit Full Material Stacks", "multibox": True, "ms": 5000}))

    # Buy ectoplasm.
    if InventorySettings.BuyEctoplasm:
        from Sources.modular_bot.recipes.actions_inventory import handle_buy_ectoplasm
        handle_buy_ectoplasm(_make_ctx({"type": "buy_ectoplasm", "name": "Buy Ectoplasm", "use_storage_gold": False, "multibox": True, "ms": 5000}))


def ResignAndRepeat(bot_instance: Botting):
    if BotSettings.Repeat:
        bot_instance.Multibox.ResignParty()

def Wait_for_Spawns(bot_instance: Botting, x, y):
    _TIMEOUT_S = 100.0

    bot_instance.Move.XY(x, y, "To the Vale")

    def _make_check(label: str):
        """Returns a condition callable that times out after _TIMEOUT_S seconds.
        On timeout: moves toward the nearest Mindblade instead of waiting."""
        _deadline = [None]  # mutable cell so the lambda can write to it

        def runtime_check_logic():
            enemies = [e for e in AgentArray.GetEnemyArray() if Agent.IsAlive(e) and Agent.GetModelID(e) == 2380]

            if not enemies:
                print(f"No Mindblades found - Continuing... ({label})")
                bot_instance.Move.XY(x, y, "Go Back")
                _deadline[0] = None  # reset for any future reuse
                return True

            # Start (or keep) the timeout clock
            import time as _time
            now = _time.monotonic()
            if _deadline[0] is None:
                _deadline[0] = now + _TIMEOUT_S

            if now >= _deadline[0]:
                # Timeout: charge the nearest Mindblade
                px, py = Player.GetXY()
                nearest = min(enemies, key=lambda e: Utils.Distance((px, py), Agent.GetXY(e)))
                ex, ey = Agent.GetXY(nearest)
                print(f"Mindblades timeout after {_TIMEOUT_S:.0f}s - moving toward nearest ({label})")
                Player.Move(ex, ey)
                _deadline[0] = None  # reset so next call restarts the clock
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
    PyImGui.text("Hey, this is my first bot in Python, be gentle :)")
    PyImGui.separator()
    PyImGui.text_wrapped("This Bot automates the Underworld")
    PyImGui.text("This version runs with HeroAI/native controls and no CustomBehavior dependencies.")
    PyImGui.text_wrapped("Some former CustomBehavior-only controls are marked as TODO where HeroAI has no equivalent API.")
    PyImGui.text_wrapped("Some quests are not easy to automate, so I recommend to watch the bot at least the first time to see how it works")
    PyImGui.text_wrapped("Some quests are missing, I will add them when I have time, but feel free to contribute :)")
    PyImGui.text_wrapped("Some quests are just not easy, because its the Underworld")
    PyImGui.separator()
    PyImGui.text("What is working Well:")
    PyImGui.bullet_text("Restoring Grenth's Monuments (exept Pits)")
    PyImGui.bullet_text("Wrathfull Spirits, Escort of Souls, Servants of Grenth, Deamon Assassin, The Four Horsemen, Terrorweb Queen")
    PyImGui.text("What is working Bad:")
    PyImGui.bullet_text("Imprisoned Spirits, Restore Pits")
    PyImGui.text("What is not implemented::")
    PyImGui.bullet_text("Unwanted Guests, The Nightman Cometh (Dhuum)")
    PyImGui.separator()
    PyImGui.text("Req:")
    PyImGui.bullet_text("Highend Team")
    PyImGui.bullet_text("For faster runs use Pcons (via Pcons widget)")
    PyImGui.bullet_text("You have to do the missing quests manually")
    PyImGui.bullet_text("Main Account sometimes leaves the team alone - Dont be the Healer")
    PyImGui.bullet_text("You should either have some evas or 1 melee char to trigger traps in the mountains")
    PyImGui.separator()
    PyImGui.bullet_text("Have fun :) - sch0l0ka")


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

    # Location dropdown.
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

    # Restock settings.
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

    # Material settings.
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
        "Assign each multibox account to the Left or Right team for the Imprisoned Spirits quest." \
        "Right team is generally more dangerus. An Sos could be helpfull for the left side."
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
    _snapshot = (BotSettings.Repeat, BotSettings.UseCons, BotSettings.HardMode)
    BotSettings.Repeat   = PyImGui.checkbox("Resign and Repeat after", BotSettings.Repeat)
    BotSettings.UseCons  = PyImGui.checkbox("Use Cons", BotSettings.UseCons)
    BotSettings.HardMode = PyImGui.checkbox("Hard Mode", BotSettings.HardMode)
    _current = (BotSettings.Repeat, BotSettings.UseCons, BotSettings.HardMode)
    if _current != _snapshot:
        BotSettings.save()




bot.SetMainRoutine(bot_routine)

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
        PyImGui.end_tab_bar()


def OnPartyWipe(bot: "Botting"):
    fsm = bot.config.FSM
    fsm.pause()
    fsm.AddManagedCoroutine("OnWipe_Underworld", lambda: _on_party_wipe(bot))


def _on_party_wipe(bot: "Botting"):
    ConsoleLog(BOT_NAME, "[WIPE] Party wipe detected!", Py4GW.Console.MessageType.Warning)

    while Agent.IsDead(Player.GetAgentID()):
        yield from Routines.Yield.wait(1000)

        if not Routines.Checks.Map.MapValid():
            ConsoleLog(BOT_NAME, "[WIPE] Returned to outpost after wipe, restarting run...", Py4GW.Console.MessageType.Warning)
            yield from Routines.Yield.wait(3000)
            _restart_main_loop(bot, "Returned to outpost after wipe")
            return

    ConsoleLog(BOT_NAME, "[WIPE] Player resurrected in instance, resuming...", Py4GW.Console.MessageType.Info)
    _restart_main_loop(bot, "Player resurrected in instance")


def main():
    if bot.config.fsm_running:
        _sync_heroai_runtime()
        # Watchdog: callback sometimes misses wipes - detect return to outpost by map ID.
        if _entered_dungeon and Map.GetMapID() == 138:
            ConsoleLog(BOT_NAME, "[WIPE] Watchdog: back in outpost (map 138) without wipe callback - restarting.", Py4GW.Console.MessageType.Warning)
            _restart_main_loop(bot, "Watchdog: returned to map 138")
    bot.Update()
    bot.UI.draw_window()

if __name__ == "__main__":
    main()
