from Py4GWCoreLib import *
from Py4GWCoreLib.ImGui_src.ImGuisrc import ImGui
from Py4GWCoreLib.BottingTree import BottingTree
from Py4GWCoreLib.py4gwcorelib_src.BehaviorTree import BehaviorTree
from Py4GWCoreLib.routines_src.behaviourtrees_src.composite import BTComposite
from Py4GWCoreLib.routines_src.behaviourtrees_src.movement import BTMovement
from Py4GWCoreLib.routines_src.behaviourtrees_src.map import BTMap
from Py4GWCoreLib.routines_src.behaviourtrees_src.party import BTParty
from Py4GWCoreLib.routines_src.behaviourtrees_src.player import BTPlayer
from Py4GWCoreLib.routines_src.behaviourtrees_src.agents import BTAgents
import Py4GW
import PyImGui
import os
import time
import json
from dataclasses import dataclass
from typing import List, Dict, Optional

MODULE_NAME = "Lightbringer-Sunspear Sulfurous Wastes"
MODULE_ICON = "Textures/Skill_Icons/[1813] - Lightbringer.jpg"

_JUNUNDU_TUNNEL = 5  # slot 5 = Junundu Tunnel (1442), used for pre-move speed

_RANGE_AGGRO = Range.Earshot.value  # 1012 — OOC detection range for junundu fight nodes


class BotSettings:
    BOT_NAME             = "Lightbringer-Sunspear Sulfurous Wastes"
    # TODO: verify these map IDs in-game (from PyQuishAI TheSulfurousWastes_ids)
    OUTPOST_TO_TRAVEL    = 545    # Remains of Sahlahja
    EXPLORABLE_TO_TRAVEL = 444    # The Sulfurous Wastes
    COORD_TO_EXIT_MAP    = (2200.0, -4900.0)   # Walk from outpost gate into explorable

    # Sunspear Undead Blessing NPC (near junundu entrance)
    SUNSPEAR_NPC_COORDS = (-660.0, 16000.0)
    SUNSPEAR_DIALOG_1   = 0x83
    SUNSPEAR_DIALOG_2   = 0x85

    # Junundu wurm burrow entry point (gadget agent)
    JUNUNDU_ENTRY_COORDS = (-615.0, 13450.0)

    # Lightbringer Margonite Blessing NPC (mid-run, before margonite groups)
    LB_NPC_COORDS = (-20600.0, 7270.0)
    LB_DIALOG     = 0x85

    # Tome pickup: pick up + drop to trigger quest update
    TOME_COORDS = (-21300.0, -14000.0)

    # Boss spawn trigger item
    BOSS_SPAWN_APPROACH = (-16000.0, -13100.0)
    BOSS_SPAWN_COORDS   = (-18180.0, -13540.0)

    # Pass-through path between groups 4 and 5 — enemies here are unreachable;
    # HeroAI is disabled and heroes are flagged forward during traversal.
    PASS_THROUGH_COORDS: list[tuple[float, float]] = [
        (-5553.0,  11502.0),
        (-9904.0,  12412.0),
        (-12235.0, 10215.0),
        (-13478.0, 8572.0),
    ]

    # 31 combat group positions as (x, y, label)
    COMBAT_GROUPS: list[tuple[float, float, str]] = [
        (-800.0,    12000.0,  "First Undead Group 1"),
        (-1700.0,   9800.0,   "First Undead Group 2"),
        (-3000.0,   10900.0,  "Second Undead Group 1"),
        (-4500.0,   11500.0,  "Second Undead Group 2"),
        (-5500.0,   11250.0,  "Second Undead Group 3"),
        (-13250.0,  6750.0,   "Third Undead Group"),
        (-22000.0,  9000.0,   "First Margonite Group 1"),
        (-22350.0,  11100.0,  "First Margonite Group 2"),
        (-19000.0,  5700.0,   "Djinn Group 1"),
        (-20800.0,  600.0,    "Djinn Group 2"),
        (-22000.0,  -1200.0,  "Djinn Group 3"),
        (-21500.0,  -6000.0,  "Undead Ritualist Boss 1"),
        (-20400.0,  -7400.0,  "Undead Ritualist Boss 2"),
        (-19500.0,  -9500.0,  "Undead Ritualist Boss 3"),
        (-22000.0,  -9400.0,  "Third Margonite Group 1"),
        (-22800.0,  -9800.0,  "Third Margonite Group 2"),
        (-23000.0,  -10600.0, "Fourth Margonite Group 1"),
        (-23150.0,  -12250.0, "Fourth Margonite Group 2"),
        (-22800.0,  -13500.0, "Fifth Margonite Group 1"),
        (-21300.0,  -14000.0, "Fifth Margonite Group 2"),
        (-22800.0,  -13500.0, "Sixth Margonite Group 1"),
        (-23000.0,  -10600.0, "Sixth Margonite Group 2"),
        (-21500.0,  -9500.0,  "Sixth Margonite Group 3"),
        (-21000.0,  -9500.0,  "Seventh Margonite Group 1"),
        (-19500.0,  -8500.0,  "Seventh Margonite Group 2"),
        (-22000.0,  -9400.0,  "Temple Monolith Group 1"),
        (-23000.0,  -10600.0, "Temple Monolith Group 2"),
        (-22800.0,  -13500.0, "Temple Monolith Group 3"),
        (-19500.0,  -13100.0, "Temple Monolith Group 4"),
        (-18000.0,  -13100.0, "Temple Monolith Group 5"),
        (-18000.0,  -13100.0, "Margonite Boss Group"),
    ]

    TEXTURE = os.path.join(
        Py4GW.Console.get_projects_path(),
        "Textures", "Skill_Icons", "[1813] - Lightbringer.jpg",
    )


# ── Globals ─────────────────────────────────────────────────────────────────────
_botting_tree: BottingTree | None = None
_heroes_setup_done: bool = False
_diag_timer = ThrottledTimer(3000)  # diagnostic log every 3 s

# Multibox mode — commented out; single account + heroes only
# _SETTINGS_SECTION  = "Settings"
# _MULTIBOX_ALTS_KEY = "use_multibox_alts"
# _party_mode: int   = 0
# _mode_loaded: bool = False
# _ini_key: str            = ""
# _ini_key_initialized: bool = False


# ── Hero config ─────────────────────────────────────────────────────────────────
@dataclass
class _PartyHeroSlot:
    hero_id: int = 0
    template: str = ""


def _humanize_hero_name(enum_name: str) -> str:
    if enum_name == "None_":
        return "<Empty>"
    words: List[str] = []
    current = enum_name[0]
    for char in enum_name[1:]:
        if (char.isupper() and not current[-1].isupper()) or (char.isdigit() and not current[-1].isdigit()):
            words.append(current)
            current = char
        else:
            current += char
    words.append(current)
    return " ".join(words)


_HERO_OPTIONS: List[HeroType] = [HeroType.None_] + sorted(
    [h for h in HeroType if h != HeroType.None_],
    key=lambda h: _humanize_hero_name(h.name),
)
_HERO_OPTION_LABELS: List[str]          = [_humanize_hero_name(h.name) for h in _HERO_OPTIONS]
_HERO_ID_TO_OPTION_INDEX: Dict[int, int] = {int(h): i for i, h in enumerate(_HERO_OPTIONS)}

_HERO_ICON_FILENAMES: Dict[HeroType, str] = {
    HeroType.Norgu: "Norgu-icon.jpg",           HeroType.Goren: "Goren-icon.jpg",
    HeroType.Tahlkora: "Tahlkora-icon.jpg",      HeroType.MasterOfWhispers: "MasterOfWhispers-icon.jpg",
    HeroType.AcolyteJin: "AcolyteSousuke-icon.jpg", HeroType.Koss: "Koss-icon.jpg",
    HeroType.Dunkoro: "Dunkoro-icon.jpg",        HeroType.AcolyteSousuke: "AcolyteSousuke-icon.jpg",
    HeroType.Melonni: "Melonni-icon.jpg",        HeroType.ZhedShadowhoof: "ZhedShadowhoof-icon.jpg",
    HeroType.GeneralMorgahn: "GeneralMorgahn-icon.jpg", HeroType.MagridTheSly: "MargridTheSly-icon.jpg",
    HeroType.Zenmai: "Zenmai-icon.jpg",          HeroType.Olias: "Olias-icon.jpg",
    HeroType.Razah: "Razah-icon.jpg",            HeroType.MOX: "M.O.X.-icon.jpg",
    HeroType.KeiranThackeray: "KeiranThackeray-icon.jpg", HeroType.Jora: "Jora-icon.jpg",
    HeroType.PyreFierceshot: "Pyre_Fierceshot-icon.jpg", HeroType.Anton: "Anton-icon.jpg",
    HeroType.Livia: "Livia-icon.jpg",            HeroType.Hayda: "Hayda-icon.jpg",
    HeroType.Kahmu: "Kahmu-icon.jpg",            HeroType.Gwen: "Gwen-icon.jpg",
    HeroType.Xandra: "Xandra-icon.jpg",          HeroType.Vekk: "Vekk-icon.jpg",
    HeroType.Ogden: "Ogden_Stonehealer-icon.jpg", HeroType.Miku: "Miku-icon.jpg",
    HeroType.ZeiRi: "Zei_Ri-icon.jpg",
}

_DEFAULT_HERO_TEMPLATES: Dict[HeroType, str] = {}  # fill with preferred Junundu-ready templates

_hero_slots: List[_PartyHeroSlot] = [_PartyHeroSlot() for _ in range(7)]
_hero_config_dirty: bool  = False
_hero_config_status: str  = ""
_hero_import_source_index: int = 0

_BOT_SCRIPT_DIR   = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.getcwd()
_HERO_CONFIG_PATH = os.path.join(_BOT_SCRIPT_DIR, f"{BotSettings.BOT_NAME} Heroes.json")
_HERO_ICONS_BASE  = os.path.normpath(os.path.join(
    Py4GW.Console.get_projects_path(), "..", "Property-of-Wick-Divinus-and-Kendor",
    "PVE Skills Unlocker", "Textures", "Skill_Icons",
))
_HERO_SLOTS_COUNT = 7


# ── Junundu combat helpers ──────────────────────────────────────────────────────

def _skill_recharged(slot: int) -> bool:
    try:
        return GLOBAL_CACHE.SkillBar.GetSkillData(slot).recharge == 0
    except Exception:
        return False


def _use_skill(slot: int, target_id: int = 0) -> None:
    try:
        if target_id:
            GLOBAL_CACHE.SkillBar.UseSkill(slot, target_id)
        else:
            GLOBAL_CACHE.SkillBar.UseSkillTargetless(slot)
    except Exception:
        pass


def _speed_team() -> None:
    if _skill_recharged(_JUNUNDU_TUNNEL):
        _use_skill(_JUNUNDU_TUNNEL)


# ── BT Node builders ────────────────────────────────────────────────────────────

def _setup_heroai_junundu_node() -> BehaviorTree:
    """
    After entering the wurm:
    1. Force HeroAI to rediscover the JununduWurm build by clearing both the
       class-level scan cache and the instance-level build caches on HeroAI's
       own BuildRegistry — no widget restart required.
    2. Block skill slot 8 (Leave Junundu) in HeroAI options so it is never fired.
    """
    def _configure():
        import sys
        from Py4GWCoreLib.BuildMgr import BuildRegistry

        # 1. Clear the class-level filesystem scan cache.
        BuildRegistry.ClearCache()

        # 2. Find HeroAI's BuildRegistry instance via sys.modules and clear
        #    its per-instance build caches so _iter_matchable_builds rescans.
        for module in list(sys.modules.values()):
            heroai_build_obj = getattr(module, "heroai_build", None)
            if heroai_build_obj is None:
                continue
            registry = getattr(heroai_build_obj, "_build_registry", None)
            if registry is None:
                continue
            registry._cached_runtime_builds = None
            registry._cached_match_only_builds = None
            registry._cached_runtime_matchable_builds = None
            registry._cached_match_only_matchable_builds = None
            break

        # 3. Block Leave Junundu (slot 8, index 7) in HeroAI options.
        email = str(Player.GetAccountEmail() or "")
        if not email:
            Py4GW.Console.Log(MODULE_NAME, "[JununduSetup] No account email — skipping skill toggle.", Py4GW.Console.MessageType.Warning)
            return BehaviorTree.NodeState.SUCCESS
        options = GLOBAL_CACHE.ShMem.GetHeroAIOptionsFromEmail(email)
        if options is None:
            Py4GW.Console.Log(MODULE_NAME, "[JununduSetup] HeroAI options not found — skipping skill toggle.", Py4GW.Console.MessageType.Warning)
            return BehaviorTree.NodeState.SUCCESS
        skills = getattr(options, "Skills", None)
        if skills is not None:
            for i in range(min(7, len(skills))):
                skills[i] = True   # enable slots 1-7
            if len(skills) > 7:
                skills[7] = False  # block slot 8 = Leave Junundu (1443)
            Py4GW.Console.Log(MODULE_NAME, f"[JununduSetup] Skills configured: slots 1-7 enabled, slot 8 blocked. len={len(skills)}", Py4GW.Console.MessageType.Info)
        else:
            Py4GW.Console.Log(MODULE_NAME, "[JununduSetup] options.Skills is None — skill toggle skipped.", Py4GW.Console.MessageType.Warning)
        GLOBAL_CACHE.ShMem.SetHeroAIOptionsByEmail(email, options)
        Py4GW.Console.Log(MODULE_NAME, "[JununduSetup] HeroAI setup complete. Registry caches cleared.", Py4GW.Console.MessageType.Success)
        return BehaviorTree.NodeState.SUCCESS

    return BehaviorTree(BehaviorTree.ActionNode(_configure, name="SetupHeroAIJunundu"))


def _junundu_pass_through_node(path: list[tuple[float, float]]) -> BehaviorTree:
    """Move through path with HeroAI disabled; heroes are flagged to each waypoint."""

    def _disable_heroai(node: BehaviorTree.Node) -> BehaviorTree.NodeState:
        node.blackboard['headless_heroai_enabled_request'] = False
        node.blackboard['headless_heroai_reset_runtime_request'] = False
        return BehaviorTree.NodeState.SUCCESS

    def _enable_heroai(node: BehaviorTree.Node) -> BehaviorTree.NodeState:
        node.blackboard['headless_heroai_enabled_request'] = True
        node.blackboard['headless_heroai_reset_runtime_request'] = True
        return BehaviorTree.NodeState.SUCCESS

    wp_nodes: list[BehaviorTree] = []
    for (wx, wy) in path:
        def _flag(x=wx, y=wy) -> BehaviorTree.NodeState:
            GLOBAL_CACHE.Party.Heroes.FlagAllHeroes(x, y)
            return BehaviorTree.NodeState.SUCCESS
        wp_nodes.append(BehaviorTree(BehaviorTree.ActionNode(_flag, name=f"Flag({int(wx)},{int(wy)})")))
        wp_nodes.append(BTMovement.Move(wx, wy, pause_on_combat=False))

    return BTComposite.Sequence(
        BehaviorTree.ActionNode(_disable_heroai, name="DisableHeroAI"),
        *wp_nodes,
        BTParty.UnflagAllHeroes(),
        BehaviorTree.ActionNode(_enable_heroai, name="EnableHeroAI"),
        name="PassThroughPath",
    )


def _junundu_fight_node(x: float, y: float, label: str = "") -> BehaviorTree:
    """Move to (x,y) and wait for HeroAI to clear the group."""
    node_label = label or f"{int(x)},{int(y)}"

    def _start(node: BehaviorTree.Node) -> BehaviorTree.NodeState:
        Py4GW.Console.Log(MODULE_NAME, f"[Planner] → {node_label} ({x:.0f},{y:.0f})", Py4GW.Console.MessageType.Info)
        _speed_team()
        return BehaviorTree.NodeState.SUCCESS

    return BTComposite.Sequence(
        BehaviorTree.ActionNode(_start, name="Start"),
        BTMovement.Move(x, y, pause_on_combat=False),
        BTAgents.WaitUntilOutOfCombat(range=_RANGE_AGGRO, timeout_ms=120000),
        name=f"JFight_{node_label}",
    )


def _sunspear_blessing_node() -> BehaviorTree:
    x, y = BotSettings.SUNSPEAR_NPC_COORDS
    return BTComposite.Sequence(
        BTMovement.Move(x, y, pause_on_combat=False),
        BTMovement.DialogAtXY(x, y, BotSettings.SUNSPEAR_DIALOG_1, target_distance=500.0),
        BTPlayer.Wait(1000),
        BTMovement.DialogAtXY(x, y, BotSettings.SUNSPEAR_DIALOG_2, target_distance=500.0),
        BTPlayer.Wait(1000),
        name="SunspearBlessing",
    )


def _enter_junundu_node() -> BehaviorTree:
    x, y = BotSettings.JUNUNDU_ENTRY_COORDS
    return BTComposite.Sequence(
        BTMovement.Move(x, y, pause_on_combat=False),
        BTParty.FlagAllHeroes(x, y),
        BTPlayer.Wait(2000),
        BTMovement.InteractWithGadgetAtXY(x, y, target_distance=300.0),
        BTPlayer.Wait(3500),
        BTParty.UnflagAllHeroes(),
        name="EnterJunundu",
    )


def _lb_blessing_node() -> BehaviorTree:
    x, y = BotSettings.LB_NPC_COORDS

    def _speed(node: BehaviorTree.Node) -> BehaviorTree.NodeState:
        _speed_team()
        return BehaviorTree.NodeState.SUCCESS

    return BTComposite.Sequence(
        BehaviorTree.ActionNode(_speed, name="SpeedLB"),
        BTMovement.Move(x, y, pause_on_combat=False),
        BTMovement.DialogAtXY(x, y, BotSettings.LB_DIALOG, target_distance=500.0),
        BTPlayer.Wait(1000),
        name="LightbringerBlessing",
    )


def _pickup_and_drop_node(x: float, y: float) -> BehaviorTree:
    def _speed(node: BehaviorTree.Node) -> BehaviorTree.NodeState:
        _speed_team()
        return BehaviorTree.NodeState.SUCCESS

    return BTComposite.Sequence(
        BehaviorTree.ActionNode(_speed, name="SpeedPickup"),
        BTMovement.Move(x, y, pause_on_combat=False),
        BTPlayer.Wait(500),
        BTAgents.TargetNearestItemXY(x, y, 200.0),
        BTPlayer.InteractTarget(),
        BTPlayer.Wait(2000),
        BTParty.DropBundle(),
        BTPlayer.Wait(1000),
        name=f"PickupAndDrop({int(x)},{int(y)})",
    )


def _boss_spawn_trigger_node(x: float, y: float) -> BehaviorTree:
    """Move to the boss spawn gadget and interact with it to trigger the boss group."""
    return BTComposite.Sequence(
        BTMovement.Move(x, y, pause_on_combat=False),
        BTPlayer.Wait(500),
        BTMovement.InteractWithGadgetAtXY(x, y, target_distance=300.0),
        BTPlayer.Wait(2000),
        name=f"BossSpawnTrigger({int(x)},{int(y)})",
    )


# ── Hero setup nodes ─────────────────────────────────────────────────────────────

def _setup_heroes_node() -> BehaviorTree:
    def _kick() -> BehaviorTree.NodeState:
        GLOBAL_CACHE.Party.Heroes.KickAllHeroes()
        return BehaviorTree.NodeState.SUCCESS

    def _add() -> BehaviorTree.NodeState:
        seen: set = set()
        for slot in _hero_slots:
            hero_id = int(slot.hero_id)
            if hero_id > 0 and hero_id not in seen:
                seen.add(hero_id)
                GLOBAL_CACHE.Party.Heroes.AddHero(hero_id)
        return BehaviorTree.NodeState.SUCCESS

    def _load_templates() -> BehaviorTree.NodeState:
        template_map = {int(s.hero_id): s.template for s in _hero_slots if s.template}
        hero_count = GLOBAL_CACHE.Party.GetHeroCount()
        for pos in range(1, hero_count + 1):
            agent_id = GLOBAL_CACHE.Party.Heroes.GetHeroAgentIDByPartyPosition(pos)
            if agent_id > 0:
                hero_id = GLOBAL_CACHE.Party.Heroes.GetHeroIDByAgentID(agent_id)
                template = template_map.get(hero_id, "")
                if template:
                    GLOBAL_CACHE.SkillBar.LoadHeroSkillTemplate(pos, template)
        return BehaviorTree.NodeState.SUCCESS

    return BTComposite.Sequence(
        BehaviorTree.ActionNode(_kick, aftercast_ms=500, name="KickHeroes"),
        BehaviorTree.ActionNode(_add, aftercast_ms=1000, name="AddHeroes"),
        BehaviorTree.ActionNode(_load_templates, aftercast_ms=500, name="LoadTemplates"),
        name="SetupHeroes",
    )


# Multibox party setup — commented out
# def _multibox_party_setup_node() -> BehaviorTree:
#     ...summon alts and invite them to party...


def _maybe_setup_heroes_node() -> BehaviorTree:
    def _check_skip() -> bool:
        return _heroes_setup_done

    def _mark_done() -> BehaviorTree.NodeState:
        global _heroes_setup_done
        _heroes_setup_done = True
        return BehaviorTree.NodeState.SUCCESS

    def _build_setup(node: BehaviorTree.Node) -> BehaviorTree:
        return _setup_heroes_node()

    return BehaviorTree(
        BehaviorTree.SelectorNode(
            name="MaybeSetupHeroes",
            children=[
                BehaviorTree.ConditionNode(_check_skip, name="AlreadySetup"),
                BehaviorTree.SequenceNode(
                    name="DoSetup",
                    children=[
                        BehaviorTree.SubtreeNode(_build_setup, name="SetupSubtree"),
                        BehaviorTree.ActionNode(_mark_done, name="MarkDone"),
                    ],
                ),
            ],
        )
    )


def _combat_mode_node() -> BehaviorTree:
    def _get_mode(node: BehaviorTree.Node) -> BehaviorTree:
        return _get_bot().Config.Aggressive()

    return BehaviorTree(
        BehaviorTree.SubtreeNode(_get_mode, name="ConfigureCombatMode")
    )


def _resign_node() -> BehaviorTree:
    def _do_resign() -> BehaviorTree.NodeState:
        Player.SendChatCommand("resign")
        return BehaviorTree.NodeState.SUCCESS

    return BTComposite.Sequence(
        BehaviorTree.ActionNode(_do_resign, aftercast_ms=1000, name="Resign"),
        BTMap.WaitforMapLoad(map_id=BotSettings.OUTPOST_TO_TRAVEL, timeout=30000),
        name="ResignAndWait",
    )


# ── Farm sequence ────────────────────────────────────────────────────────────────

def _build_farm_sequence() -> list[BehaviorTree]:
    G = BotSettings.COMBAT_GROUPS
    sx, sy = BotSettings.BOSS_SPAWN_APPROACH

    steps: list[BehaviorTree] = [
        # One-time setup (hero setup is flag-guarded; travel and hard-mode are idempotent)
        BTMap.TravelToOutpost(outpost_id=BotSettings.OUTPOST_TO_TRAVEL),
        _maybe_setup_heroes_node(),
        BTMap.SetHardMode(hard_mode=True),

        # Loop body
        BTMap.TravelToOutpost(outpost_id=BotSettings.OUTPOST_TO_TRAVEL),
        BTMovement.MoveAndExitMap(
            x=BotSettings.COORD_TO_EXIT_MAP[0],
            y=BotSettings.COORD_TO_EXIT_MAP[1],
            target_map_id=BotSettings.EXPLORABLE_TO_TRAVEL,
        ),
        BTParty.FlagAllHeroes(*BotSettings.JUNUNDU_ENTRY_COORDS),
        _combat_mode_node(),

        # Farm run
        _sunspear_blessing_node(),
        _enter_junundu_node(),
        _setup_heroai_junundu_node(),

        # Groups 0-4: undead clusters around junundu entrance
        *[_junundu_fight_node(G[i][0], G[i][1], G[i][2]) for i in range(5)],

        # Pass-through path to Third Undead Group (HeroAI disabled; enemies unreachable)
        _junundu_pass_through_node(BotSettings.PASS_THROUGH_COORDS),
        _junundu_fight_node(G[5][0], G[5][1], G[5][2]),

        # Lightbringer Margonite Blessing (granted before first margonite group)
        _lb_blessing_node(),

        # Groups 6-19: margonites, djinn, ritualist bosses
        *[_junundu_fight_node(G[i][0], G[i][1], G[i][2]) for i in range(6, 20)],

        # Tome pickup at group-19 position (triggers quest update)
        _pickup_and_drop_node(BotSettings.TOME_COORDS[0], BotSettings.TOME_COORDS[1]),

        # Groups 20-29: sixth/seventh margonites + temple monoliths
        *[_junundu_fight_node(G[i][0], G[i][1], G[i][2]) for i in range(20, 30)],

        # Boss spawn: approach then interact with the spawn gadget
        BTMovement.Move(sx, sy, pause_on_combat=False),
        _boss_spawn_trigger_node(BotSettings.BOSS_SPAWN_COORDS[0], BotSettings.BOSS_SPAWN_COORDS[1]),

        # Final boss group (group 30)
        _junundu_fight_node(G[30][0], G[30][1], G[30][2]),

        # Return and resign
        BTMap.TravelToOutpost(outpost_id=BotSettings.OUTPOST_TO_TRAVEL),
        _resign_node(),
    ]

    return steps


# ── BottingTree factory ──────────────────────────────────────────────────────────

def _get_bot() -> BottingTree:
    global _botting_tree
    if _botting_tree is None:
        def _configure(tree: BottingTree) -> None:
            tree.Config.ConfigureUpkeepTrees(
                disable_looting=False,
                enable_party_wipe_recovery=True,
                enable_outpost_imp_service=False,
                enable_explorable_imp_service=False,
            )
            tree.pause_on_combat = False  # Junundu is always in combat; planner must keep ticking

        _seq = BTComposite.Sequence(*_build_farm_sequence(), name="LBSSFarmLoop")
        _loop = BehaviorTree(BehaviorTree.RepeaterForeverNode(_seq.root, name="FarmLoopForever"))
        _botting_tree = BottingTree.Create(
            BotSettings.BOT_NAME,
            main_routine=_loop,
            routine_name="LBSSFarmLoop",
            configure_fn=_configure,
        )
        _botting_tree.UI.override_draw_config(lambda: _draw_settings())
        _botting_tree.UI.override_draw_help(lambda: _draw_help())

    return _botting_tree


# ── Settings persistence ─────────────────────────────────────────────────────────

# Multibox mode persistence — commented out
# def _ensure_ini_key() -> str: ...
# def _load_mode_setting() -> None: ...
# def _save_mode_setting() -> None: ...


# ── UI ──────────────────────────────────────────────────────────────────────────

def _draw_settings():
    PyImGui.text("Bot Settings")
    PyImGui.separator()
    PyImGui.text("Single Account with Heroes")


def _draw_help():
    title_color = Color(255, 200, 100, 255)
    ImGui.push_font("Regular", 20)
    PyImGui.text_colored(BotSettings.BOT_NAME, title_color.to_tuple_normalized())
    ImGui.pop_font()
    PyImGui.spacing()
    PyImGui.separator()
    PyImGui.text("Farms Lightbringer and Sunspear title points via Junundu wurms")
    PyImGui.text("in the Sulfurous Wastes. Kills all 31 mob groups per run.")
    PyImGui.spacing()
    PyImGui.text_colored("Requirements:", title_color.to_tuple_normalized())
    PyImGui.bullet_text("Start at Remains of Sahlahja outpost")
    PyImGui.bullet_text("Have the quest 'A Show of Force' active (recommended)")
    PyImGui.bullet_text("Have the quest 'Requiem for a Brain' active (recommended)")
    PyImGui.bullet_text("Rune of Doom in inventory (recommended)")
    PyImGui.bullet_text("Holy damage weapons equipped on player and heroes")
    PyImGui.bullet_text("Low-level heroes to share XP (optional)")
    PyImGui.spacing()
    PyImGui.text_colored("Credits:", title_color.to_tuple_normalized())
    PyImGui.bullet_text("Original AutoIt3 script by caustic-kronos (Kronos/Night/Svarog)")
    PyImGui.bullet_text("Py4GW port by george-ctrl")


def tooltip():
    PyImGui.begin_tooltip()
    title_color = Color(255, 200, 100, 255)
    ImGui.push_font("Regular", 20)
    PyImGui.text_colored(BotSettings.BOT_NAME, title_color.to_tuple_normalized())
    ImGui.pop_font()
    PyImGui.spacing()
    PyImGui.separator()
    PyImGui.text("Farms Lightbringer + Sunspear via Junundu in the Sulfurous Wastes.")
    PyImGui.spacing()
    PyImGui.text_colored("Requirements:", title_color.to_tuple_normalized())
    PyImGui.bullet_text("Remains of Sahlahja outpost")
    PyImGui.bullet_text("Credits: caustic-kronos (original Au3), george-ctrl (Py4GW port)")
    PyImGui.end_tooltip()


# ── Hero config I/O ─────────────────────────────────────────────────────────────

def _load_hero_config():
    global _hero_slots, _hero_config_dirty, _hero_config_status
    if not os.path.exists(_HERO_CONFIG_PATH):
        _hero_config_status = ""
        return
    try:
        with open(_HERO_CONFIG_PATH, "r", encoding="utf-8") as f:
            raw = json.load(f)
        _hero_slots = _parse_hero_config_entries(raw)
        _hero_config_dirty = False
        _hero_config_status = "Loaded."
    except Exception as exc:
        _hero_config_status = f"Load error: {exc}"


def _save_hero_config():
    global _hero_config_dirty, _hero_config_status
    payload = [{"hero_id": int(s.hero_id), "template": s.template} for s in _hero_slots]
    try:
        os.makedirs(os.path.dirname(_HERO_CONFIG_PATH), exist_ok=True)
        with open(_HERO_CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
        _hero_config_dirty = False
        _hero_config_status = "Saved."
    except Exception as exc:
        _hero_config_status = f"Save error: {exc}"


def _reset_hero_config():
    global _hero_slots, _hero_config_dirty, _hero_config_status
    _hero_slots = [_PartyHeroSlot() for _ in range(_HERO_SLOTS_COUNT)]
    _hero_config_dirty = True
    _hero_config_status = "Reset to empty."


def _parse_hero_config_entries(raw) -> List[_PartyHeroSlot]:
    slots: List[_PartyHeroSlot] = []
    for i in range(_HERO_SLOTS_COUNT):
        entry = raw[i] if isinstance(raw, list) and i < len(raw) else {}
        hero_id = int(entry.get("hero_id", 0) or 0)
        if hero_id not in _HERO_ID_TO_OPTION_INDEX:
            hero_id = 0
        slots.append(_PartyHeroSlot(hero_id=hero_id, template=str(entry.get("template", "") or "")))
    return slots


def _list_importable_hero_configs() -> List[str]:
    try:
        files = [
            os.path.join(_BOT_SCRIPT_DIR, e)
            for e in os.listdir(_BOT_SCRIPT_DIR)
            if e.endswith(" Heroes.json") and os.path.isfile(os.path.join(_BOT_SCRIPT_DIR, e))
        ]
        files.sort(key=lambda p: os.path.basename(p).lower())
        return files
    except OSError:
        return []


def _hero_import_label(path: str) -> str:
    name = os.path.splitext(os.path.basename(path))[0]
    return name[:-7] if name.endswith(" Heroes") else name


def _import_hero_config(path: str):
    global _hero_slots, _hero_config_dirty, _hero_config_status
    try:
        with open(path, "r", encoding="utf-8") as f:
            raw = json.load(f)
        _hero_slots = _parse_hero_config_entries(raw)
        _hero_config_dirty = True
        _save_hero_config()
        _hero_config_status = f"Imported from {_hero_import_label(path)} and saved."
    except Exception as exc:
        _hero_config_status = f"Import error: {exc}"


def _get_hero_icon_path(hero_id: int) -> Optional[str]:
    try:
        hero_type = HeroType(hero_id)
    except ValueError:
        return None
    filename = _HERO_ICON_FILENAMES.get(hero_type)
    if not filename:
        return None
    path = os.path.join(_HERO_ICONS_BASE, filename)
    return path if os.path.exists(path) else None


def _draw_hero_icon(hero_id: int, size: int = 24):
    path = _get_hero_icon_path(hero_id)
    if path:
        try:
            cx, cy = PyImGui.get_cursor_screen_pos()
            ImGui.DrawTextureInDrawList(pos=(float(cx), float(cy)), size=(float(size), float(size)), texture_path=path)
        except Exception:
            try:
                ImGui.DrawTexture(texture_path=path, width=size, height=size)
            except Exception:
                pass
    PyImGui.dummy(int(size), int(size))


def _draw_hero_combo(label: str, hero_id: int) -> int:
    current_index = _HERO_ID_TO_OPTION_INDEX.get(hero_id, 0)
    preview = _HERO_OPTION_LABELS[current_index]
    if PyImGui.begin_combo(label, preview, PyImGui.ImGuiComboFlags.NoFlag):
        for index, hero in enumerate(_HERO_OPTIONS):
            if hero != HeroType.None_:
                _draw_hero_icon(int(hero), size=20)
            else:
                PyImGui.dummy(20, 20)
            PyImGui.same_line(0.0, 8.0)
            if PyImGui.selectable(f"{_HERO_OPTION_LABELS[index]}##{label}_{index}", index == current_index, 0, [0.0, 0.0]):
                current_index = index
        PyImGui.end_combo()
    return int(_HERO_OPTIONS[current_index])


def _draw_hero_slot_editor(slot_index: int):
    global _hero_config_dirty
    slot = _hero_slots[slot_index]
    combo_label_width = 70.0

    PyImGui.text(f"Hero {slot_index + 1}")
    PyImGui.same_line(combo_label_width, 8.0)
    _draw_hero_icon(slot.hero_id, size=24)
    PyImGui.same_line(0.0, 8.0)
    PyImGui.set_next_item_width(PyImGui.get_content_region_avail()[0])
    new_hero_id = _draw_hero_combo(f"##hero_{slot_index}", slot.hero_id)
    if new_hero_id != slot.hero_id:
        slot.hero_id = new_hero_id
        if slot.hero_id == HeroType.None_.value:
            slot.template = ""
        elif not slot.template.strip():
            try:
                hero_type = HeroType(slot.hero_id)
            except ValueError:
                hero_type = HeroType.None_
            slot.template = _DEFAULT_HERO_TEMPLATES.get(hero_type, "")
        _hero_config_dirty = True

    PyImGui.text("Template")
    PyImGui.same_line(0.0, 8.0)
    if PyImGui.small_button(f"Clear##slot_{slot_index}"):
        if slot.hero_id != HeroType.None_.value or slot.template:
            slot.hero_id = HeroType.None_.value
            slot.template = ""
            _hero_config_dirty = True
    PyImGui.set_next_item_width(PyImGui.get_content_region_avail()[0])
    new_template = PyImGui.input_text(f"##template_{slot_index}", slot.template)
    if new_template != slot.template:
        slot.template = new_template
        _hero_config_dirty = True


def _draw_hero_settings_tab():
    global _hero_import_source_index
    PyImGui.text("Configure up to 7 heroes for Single Account mode.")
    PyImGui.push_style_color(PyImGui.ImGuiCol.Text, (0.7, 0.7, 0.7, 1.0))
    PyImGui.text("Heroes are added in order; duplicates and empty slots are skipped.")
    PyImGui.pop_style_color(1)
    PyImGui.spacing()

    if _hero_config_dirty:
        PyImGui.push_style_color(PyImGui.ImGuiCol.Text, (1.0, 0.8, 0.2, 1.0))
        PyImGui.text("Unsaved changes")
        PyImGui.pop_style_color(1)
    elif _hero_config_status:
        PyImGui.push_style_color(PyImGui.ImGuiCol.Text, (0.6, 0.9, 0.6, 1.0))
        PyImGui.text(_hero_config_status)
        PyImGui.pop_style_color(1)

    if PyImGui.button("Save", 100, 26):
        _save_hero_config()
    PyImGui.same_line(0, 8)
    if PyImGui.button("Reload", 100, 26):
        _load_hero_config()
    PyImGui.same_line(0, 8)
    if PyImGui.button("Reset", 100, 26):
        _reset_hero_config()

    import_paths = _list_importable_hero_configs()
    if import_paths:
        if _hero_import_source_index >= len(import_paths):
            _hero_import_source_index = 0
        import_labels = [_hero_import_label(p) for p in import_paths]
        _hero_import_source_index = PyImGui.combo("Import Team From", _hero_import_source_index, import_labels)
        if PyImGui.button("Import Team", 120, 26):
            _import_hero_config(import_paths[_hero_import_source_index])
    else:
        PyImGui.push_style_color(PyImGui.ImGuiCol.Text, (0.7, 0.7, 0.7, 1.0))
        PyImGui.text("Import Team: save another title bot hero lineup first.")
        PyImGui.pop_style_color(1)

    PyImGui.separator()
    if PyImGui.begin_child("HeroSlotsChild", (0, -1), True):
        for i in range(_HERO_SLOTS_COUNT):
            _draw_hero_slot_editor(i)
            if i < _HERO_SLOTS_COUNT - 1:
                PyImGui.separator()
    PyImGui.end_child()


# ── Title statistics ─────────────────────────────────────────────────────────────

_session_baselines: dict[str, dict[str, int]] = {}
_session_start_times: dict[str, float] = {}


def _get_title_track_accounts():
    accounts = list(GLOBAL_CACHE.ShMem.GetAllAccountData())
    own_email = Player.GetAccountEmail()
    filtered = [a for a in accounts if getattr(a, "AccountEmail", "") == own_email]
    if filtered:
        return filtered
    own_name = Player.GetName()
    filtered = [a for a in accounts if getattr(a.AgentData, "CharacterName", "") == own_name]
    return filtered if filtered else (accounts[:1] if len(accounts) == 1 else [])


def _draw_single_title(name: str, pts: int, tiers, label: str):
    tier_name = "Unranked"
    tier_rank = 0
    tier_max_rank = len(tiers)
    next_required = tiers[0].required if tiers else 0
    for i, tier in enumerate(tiers):
        if pts >= tier.required:
            tier_rank = i + 1
            tier_name = tier.name
            next_required = tiers[i + 1].required if i + 1 < len(tiers) else tier.required
        else:
            next_required = tier.required
            break
    is_maxed = bool(tiers) and pts >= tiers[-1].required
    tier_missing = max(next_required - pts, 0)

    PyImGui.text(f"{label}: {tier_name} [{tier_rank}/{tier_max_rank}]")
    PyImGui.text(f"Total Points: {pts:,}")
    if is_maxed:
        PyImGui.text("Next Rank: Maxed")
        PyImGui.progress_bar(1.0, -1, 0, "Complete")
        PyImGui.text_colored("Maximum rank achieved.", (0.4, 1.0, 0.4, 1.0))
    else:
        PyImGui.text(f"Points To Go: {tier_missing:,}")
        frac = min(pts / max(next_required, 1), 1.0)
        PyImGui.progress_bar(frac, -1, 0, f"{pts:,} / {next_required:,}")


def _draw_title_track():
    global _session_baselines, _session_start_times
    now = time.time()
    accounts = _get_title_track_accounts()
    if not accounts:
        PyImGui.text("No local account statistics available yet.")
        return

    lb_tiers  = TITLE_TIERS.get(TitleID.Lightbringer, [])
    ss_tiers  = TITLE_TIERS.get(TitleID.Sunspear, [])
    lb_idx = int(TitleID.Lightbringer)
    ss_idx = int(TitleID.Sunspear)

    for account in accounts:
        char_name = account.AgentData.CharacterName
        lb_pts = account.TitlesData.Titles[lb_idx].CurrentPoints
        ss_pts = account.TitlesData.Titles[ss_idx].CurrentPoints

        if char_name not in _session_baselines:
            _session_baselines[char_name] = {"lb": lb_pts, "ss": ss_pts}
            _session_start_times[char_name] = now

        bl = _session_baselines[char_name]
        elapsed = now - _session_start_times[char_name]
        formatted_time = time.strftime('%H:%M:%S', time.gmtime(elapsed))

        lb_gained = lb_pts - bl["lb"]
        ss_gained = ss_pts - bl["ss"]
        lb_hr = int(lb_gained / elapsed * 3600) if elapsed > 0 else 0
        ss_hr = int(ss_gained / elapsed * 3600) if elapsed > 0 else 0

        PyImGui.separator()
        ImGui.push_font("Regular", 18)
        PyImGui.text(f"Statistics – {char_name}")
        ImGui.pop_font()
        PyImGui.spacing()

        _draw_single_title(char_name, lb_pts, lb_tiers, "Lightbringer")
        PyImGui.text(f"  +{lb_gained:,} pts ({lb_hr:,}/hr)")
        PyImGui.spacing()
        _draw_single_title(char_name, ss_pts, ss_tiers, "Sunspear")
        PyImGui.text(f"  +{ss_gained:,} pts ({ss_hr:,}/hr)")
        PyImGui.spacing()
        PyImGui.text(f"Session running: {formatted_time}")


# ── Main ─────────────────────────────────────────────────────────────────────────

_hero_config_loaded = False
_EXPANDED_TAB_CHILD_SIZE = (500, 620)


def _draw_statistics_tab() -> None:
    if PyImGui.begin_child("LBSSStatisticsTabChild", _EXPANDED_TAB_CHILD_SIZE, False):
        _draw_title_track()
    PyImGui.end_child()


def _draw_heroes_tab() -> None:
    if PyImGui.begin_child("LBSSHeroesTabChild", _EXPANDED_TAB_CHILD_SIZE, False):
        _draw_hero_settings_tab()
    PyImGui.end_child()


def main():
    global _hero_config_loaded
    if not _hero_config_loaded:
        _load_hero_config()
        _hero_config_loaded = True
    if Map.IsMapLoading():
        return
    bot = _get_bot()
    bot.tick()

    if _diag_timer.IsExpired():
        _diag_timer.Reset()
        bb = bot.GetBlackboardValue
        px, py = Agent.GetXY(Player.GetAgentID())
        Py4GW.Console.Log(MODULE_NAME,
            f"[Diag] pos=({px:.0f},{py:.0f})"
            f" combat={bb('COMBAT_ACTIVE', False)}"
            f" casting={Agent.IsCasting(Player.GetAgentID())}"
            f" pause_mv={bb('PAUSE_MOVEMENT', False)}"
            f" planner={bb('PLANNER_STATUS','?')}"
            f" move_state={bb('move_state','?')}"
            f" move_reason={bb('move_current_pause_reason','')}"
            f" stall={bb('move_stall_retry_count',0)}",
            Py4GW.Console.MessageType.Info)
    bot.UI.draw_window(
        icon_path=BotSettings.TEXTURE,
        extra_tabs=[
            ("Statistics", _draw_statistics_tab),
            ("Heroes",     _draw_heroes_tab),
        ],
    )


if __name__ == "__main__":
    main()
