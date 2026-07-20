"""
Killroy Stonekin Punch-Out Extravaganza - BT-tree edition.
With BT Killroy routine + GH reset + simple KO fast-spam in main().
"""

from typing import Callable, Optional
import os
import sys
import time

from Py4GWCoreLib import Agent
from Py4GWCoreLib import AgentArray
from Py4GWCoreLib import HeroType
from Py4GWCoreLib import Party
from Py4GWCoreLib import Player
from Py4GWCoreLib import PyImGui
from Py4GWCoreLib import Range
from Py4GWCoreLib.BottingTree import BottingTree
from Py4GWCoreLib.IniManager import IniManager
from Py4GWCoreLib.routines_src.BehaviourTrees import BT as CoreBT
import Py4GW

from Sources.ApoSource.ApoBottingLib import wrappers as BT

import PySkillbar
from Py4GWCoreLib import Routines, ActionQueueManager

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else os.getcwd())


MODULE_NAME = 'Killroy Stonekin BT'
MODULE_ICON = 'Textures\\Module_Icons\\Leveler - Killroy Stonekin.png'
ROUTINE_NAME = 'KillroyStonekinSequence'
INI_PATH = 'Widgets/Automation/Bots/Templates'
INI_FILENAME = 'KillroyStonekinBT.ini'
LOOTING_ACTIVE = False

EYE_OF_THE_NORTH_MAP_ID = 642
GUNNARS_HOLD_MAP_ID = 644
KILLROY_MAP_ID = 703
BRASS_KNUCKLES_MODEL_ID = 24897

KILLROY_POS = (17341.00, -4796.00)
KILLROY_ACCEPT_QUEST_DIALOG = 0x835803
KILLROY_ENTER_KILLROY_DIALOG = 0x835801
KILLROY_EXIT_KILLROY_DIALOG = 0x85
KILLROY_REWARD_DIALOG = 0x835807

KILLROY_UNLOCK_ACCEPT_DIALOG = 0x835A01
KILLROY_UNLOCK_EXIT_DIALOG = 0x84
KILLROY_UNLOCK_REWARD_DIALOG = 0x835A07

KILLROY_PATH = [
    (-15115.72, -15375.61),
    (-11299.54, -16402.40),
    (-7284.53, -16235.58),
    (-4397.42, -16123.15),
    (-1385.20, -14400.23),
    (505.33, -14073.99),
    (2959.12, -15991.76),
    (5740.82, -15543.48),
    (7157.02, -15755.44),
    (12249.79, -16291.74),
]

KILLROY_GADGET_POS = (13275.00, -16039.00)
KILLROY_EQUIP_POS = (19290.50, -11552.23)

COMBAT_WAIT_TIME_MS = 3500

botting_tree: Optional[BottingTree] = None
ini_key = ''
initialized = False
planner_synced = False

# simple KO spam helper
_skillbar: Optional[PySkillbar.Skillbar] = None


# ============================================================
# Existing BT routines (Aggressive / Pacifist templates)
# ============================================================

def KillroyAggressive():
    return ensure_botting_tree().Config.AggressiveTree(
        auto_loot=None,
        resurrection_scroll=False,
        reset_hero_ai=False,
    )


def KillroyPacifist():
    return ensure_botting_tree().Config.PacifistTree(
        resurrection_scroll=False,
        reset_hero_ai=False,
    )


# ============================================================
# Invite heroes for XP (BT version of FSM InviteHeroesForXP)
# ============================================================

def InviteHeroesForXP():
    leveling_heroes = [
        HeroType.Koss,
        HeroType.Dunkoro,
        HeroType.Tahlkora,
        HeroType.Melonni,
        HeroType.Olias,
        HeroType.AcolyteJin,
        HeroType.AcolyteSousuke,
    ]

    hero_ids = [int(hero.value) for hero in leveling_heroes]

    return BT.Sequence(
        name='Invite Heroes For XP',
        children=[
            BT.LeaveParty(),
            BT.CreateParty(hero_ids=hero_ids, log=False),
            BT.Wait(1000),
        ],
    )


# ============================================================
# Killroy Map Farm (BT version of KillroyMap FSM routine)
# ============================================================

def KillroyMapRoutine():
    return BT.Sequence(
        name='Killroy Map Routine',
        children=[
            BT.LeaveParty(),
            BT.Travel(target_map_id=GUNNARS_HOLD_MAP_ID, random_travel=True),
            KillroyAggressive(),
            BT.MoveAndDialog(KILLROY_POS, KILLROY_ACCEPT_QUEST_DIALOG),
            BT.Wait(500),
            BT.MoveAndDialog(KILLROY_POS, KILLROY_ENTER_KILLROY_DIALOG),
            BT.Wait(500),
            BT.MoveAndDialog(KILLROY_POS, KILLROY_EXIT_KILLROY_DIALOG),
            BT.Wait(500),
            BT.WaitUntilOnExplorable(),
            BT.MoveAndKill(KILLROY_PATH),
            BT.WaitUntilOutOfCombat(),
            BT.Wait(1000),
            BT.MoveAndInteractWithGadget(KILLROY_GADGET_POS),
            BT.Wait(2000),
            KillroyPacifist(),
            BT.Wait(COMBAT_WAIT_TIME_MS),
            BT.Travel(target_map_id=GUNNARS_HOLD_MAP_ID, random_travel=True),
            BT.Wait(1500),
            InviteHeroesForXP(),
            BT.Wait(1000),
            BT.HandleAutoQuest(pos=KILLROY_POS, buttons=0, log=True),
            BT.LeaveParty(),
            BT.Travel(target_map_id=EYE_OF_THE_NORTH_MAP_ID, random_travel=True),
            BT.Travel(target_map_id=GUNNARS_HOLD_MAP_ID, random_travel=True),
            BT.WaitUntilOnOutpost(),
        ],
    )



# ============================================================
# Planner parts (steps for BottingTree planner)
# ============================================================

KILLROY_PLANNER_PARTS: list[tuple[str, Callable[[], object]]] = [
    ('Killroy XP Farm - Run', KillroyMapRoutine),
]



# ============================================================
# BottingTree configuration and runtime upkeep
# ============================================================

def ConfigureRuntimeUpkeep(tree: BottingTree):
    return tree.Config.ConfigureUpkeep(
        looting_enabled=LOOTING_ACTIVE,
        restore_isolation_on_stop=True,
        enable_party_wipe_recovery=False,
        heroai_state_logging=False,
        consumable_upkeeps=[],
    )


def ensure_botting_tree() -> BottingTree:
    global botting_tree
    if botting_tree is None:
        botting_tree = BottingTree.Create(
            MODULE_NAME,
            routine_name=ROUTINE_NAME,
            repeat=True,
            reset=False,
            pause_on_combat=False,
            multi_account=False,
            auto_loot=LOOTING_ACTIVE,
            configure_fn=ConfigureRuntimeUpkeep,
        )
        botting_tree.UI.override_draw_config(draw_settings_tab)
    return botting_tree


def build_killroy_steps() -> list[tuple[str, Callable[[], object]]]:
    return [
        (f'{index:02d}. {name}', lambda builder=builder: builder())
        for index, (name, builder) in enumerate(KILLROY_PLANNER_PARTS, start=1)
    ]


def sync_planner_routine(force: bool = False) -> None:
    global planner_synced
    tree = ensure_botting_tree()
    if tree.IsStarted():
        return
    if planner_synced and not force:
        return
    tree.SetNamedPlannerSteps(build_killroy_steps(), name=ROUTINE_NAME, repeat=True)
    planner_synced = True


# ============================================================
# Simple KO fast-spam in main() (no States, no Parallel)
# ============================================================

def ko_tick():
    global _skillbar
    if _skillbar is None:
        _skillbar = PySkillbar.Skillbar()

    # if map invalid, do nothing
    if not Routines.Checks.Map.MapValid():
        return

    # basic energy check
    energy = Agent.GetEnergy(Player.GetAgentID())
    max_energy = Agent.GetMaxEnergy(Player.GetAgentID())

    # if we're down / low energy, spam revive skill
    if energy < 0.9999:
        for _ in range(5):
            ActionQueueManager().AddAction("FAST", _skillbar.UseSkillTargetless, 8)


# ============================================================
# UI / settings
# ============================================================

def draw_settings_tab() -> None:
    tree = ensure_botting_tree()
    tree.pause_on_combat = PyImGui.checkbox('Pause Planner On Combat', tree.pause_on_combat)

    looting_enabled = PyImGui.checkbox('Looting', tree.IsLootingEnabled())
    if looting_enabled != tree.IsLootingEnabled():
        tree.SetLootingEnabled(looting_enabled)

    tree.DrawMovePathDebugOptions()


def _register_ini_vars(key: str) -> None:
    IniManager().add_bool(key, 'initialized', 'Runtime', 'initialized', default=True)


# ============================================================
# Main entrypoint
# ============================================================

def main() -> None:
    global initialized, ini_key
    if not initialized:
        if not ini_key:
            ini_key = IniManager().ensure_key(INI_PATH, INI_FILENAME)
            if not ini_key:
                return
            _register_ini_vars(ini_key)
            IniManager().load_once(ini_key)
        ensure_botting_tree()
        sync_planner_routine(force=True)
        initialized = True

    # per-tick KO spam
    ko_tick()

    tree = ensure_botting_tree()
    tree.tick()
    sync_planner_routine()
    tree.UI._ensure_window_factory()
    tree.UI._draw_managed_window()
    tree.DrawMovePathIfEnabled()
    
    # Widget GUI integration
    icon_path = os.path.join(Py4GW.Console.get_projects_path(), "Sources", "ApoSource", "textures", "Killroy Stonekin Punch-Out Extravaganza-art.png")
    tree.UI.draw_window(icon_path=icon_path)


if __name__ == '__main__':
    main()
