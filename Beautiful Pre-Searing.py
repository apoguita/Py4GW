import Py4GW
import PyImGui
from typing import Callable, TypeAlias

from Py4GWCoreLib.BottingTree import BottingTree
from Py4GWCoreLib.ImGui import ImGui
from Py4GWCoreLib.IniManager import IniManager

from Sources.ApoSource.beautiful_pre_searing_src.acquire_belt_pouch import AcquireBeltPouch
from Sources.ApoSource.beautiful_pre_searing_src.acquire_weapon import AcquireWeapon
from Sources.ApoSource.beautiful_pre_searing_src.globals import ITEMS_BLACKLIST

from Sources.ApoSource.beautiful_pre_searing_src.debug import dump_tree_diagnostics
from Sources.ApoSource.beautiful_pre_searing_src.globals import *
from Sources.ApoSource.beautiful_pre_searing_src.helpers import *
from Sources.ApoSource.beautiful_pre_searing_src.tree_builder import CommonMapExit, ensure_botting_tree
from Sources.ApoSource.beautiful_pre_searing_src.unlock_pet import UnlockPet
from Sources.ApoSource.beautiful_pre_searing_src.getting_started import GetGettingStartedSequence
from Sources.ApoSource.beautiful_pre_searing_src.farming_routines import *
from Sources.ApoSource.beautiful_pre_searing_src.outpost_unlock import *

BANNER_WIDTH = 350
BANNER_HEIGHT = 175
initialized = False
INI_KEY = ""
INI_PATH = "Widgets/BeautifulPreSearing"
INI_FILENAME = "BeautifulPreSearing.ini"
projects_root = Py4GW.Console.get_projects_path()
TEXTURE_PATH = f"{projects_root}/Sources/ApoSource/beautiful_pre_searing_src/resources/Beautiful Pre-Searing-banner.png"

draw_move_path = True
draw_move_path_labels = False
draw_move_path_thickness = 4.0
draw_move_waypoint_radius = 15.0
draw_move_current_waypoint_radius = 20.0
selected_debug_tree_name = "Getting Started"
TreeBuilder: TypeAlias = Callable[[], BehaviorTree | None]

def CharrAtTheGate() -> BehaviorTree:
    from Py4GWCoreLib.Player import Player
    from Py4GWCoreLib.Quest import Quest

    def _is_level_10_or_higher() -> bool:
        return int(Player.GetLevel() or 0) >= 10

    def _has_charr_at_the_gate_quest() -> bool:
        return CHARR_AT_THE_GATE_QUEST_ID in set(Quest.GetQuestLogIds() or [])

    def _refresh_charr_at_the_gate_quest() -> BehaviorTree.NodeState:
        if not _has_charr_at_the_gate_quest():
            return BehaviorTree.NodeState.SUCCESS
        Quest.SetActiveQuest(CHARR_AT_THE_GATE_QUEST_ID)
        Quest.RequestQuestInfo(CHARR_AT_THE_GATE_QUEST_ID, update_marker=True)
        return BehaviorTree.NodeState.SUCCESS

    def _abandon_charr_at_the_gate_quest() -> BehaviorTree.NodeState:
        Quest.AbandonQuest(CHARR_AT_THE_GATE_QUEST_ID)
        return BehaviorTree.NodeState.SUCCESS

    single_cycle = BehaviorTree.SequenceNode(
        name="CharrAtTheGateSingleCycle",
        children=[
            LogMessage("Traveling to Ascalon City for Charr At The Gate"),
            BT.TravelToOutpost(ASCALON_CITY_MAP_ID),
            equip_build_for_level(),
            merchant_cleanup(
                exclude_models=ITEMS_BLACKLIST,
                destroy_zero_value_items=True,
            ),
            BehaviorTree.SelectorNode(
                name="EnsureCharrAtTheGateQuest",
                children=[
                    BehaviorTree.SequenceNode(
                        name="QuestAlreadyInLog",
                        children=[
                            BehaviorTree.ConditionNode(
                                name="HasCharrAtTheGateQuest",
                                condition_fn=_has_charr_at_the_gate_quest,
                            ),
                            LogMessage("Charr At The Gate quest already in log"),
                        ],
                    ),
                    BehaviorTree.SequenceNode(
                        name="AcquireCharrAtTheGateQuest",
                        children=[
                            LogMessage("Acquiring Charr At The Gate quest from Prince Rurik"),
                            BT.MoveAndAutoDialog(RURIK_COORDS, button_number=0),
                            BT.AutoDialog(),
                            BT.Wait(300),
                            BehaviorTree.ConditionNode(
                                name="HasCharrAtTheGateQuestAfterAcquire",
                                condition_fn=_has_charr_at_the_gate_quest,
                            ),
                        ],
                    ),
                ],
            ),
            exit_current_map(),
            LogMessage("Following Rurik's path"),
            BottingTree.DisableHeroAITree(),
            BT.Move(RURIK_EXPLORABLE_COORDS),
            BT.Wait(2000),
            BT.Move(CHARR_AT_THE_GATE_PATH_COORDS),
            BT.WaitForClearEnemiesInArea(Vec2f(-4636.60, 11331.79), allowed_alive_enemies=1),
            LogMessage("Bailing out!"),
            BT.TravelToOutpost(ASCALON_CITY_MAP_ID),
            BottingTree.EnableHeroAITree(),
            BehaviorTree.ActionNode(
                name="RefreshCharrAtTheGateQuest",
                action_fn=_refresh_charr_at_the_gate_quest,
                aftercast_ms=250,
            ),
            BehaviorTree.SelectorNode(
                name="AbandonCompletedQuestOrRepeat",
                children=[
                    BehaviorTree.SequenceNode(
                        name="CompletedQuestCleanup",
                        children=[
                            BehaviorTree.ConditionNode(
                                name="HasCompletedCharrAtTheGateQuest",
                                condition_fn=lambda: _has_charr_at_the_gate_quest() and Quest.IsQuestCompleted(CHARR_AT_THE_GATE_QUEST_ID),
                            ),
                            LogMessage("Charr At The Gate completed unexpectedly, abandoning quest"),
                            BehaviorTree.ActionNode(
                                name="AbandonCharrAtTheGateQuest",
                                action_fn=_abandon_charr_at_the_gate_quest,
                                aftercast_ms=250,
                            ),
                        ],
                    ),
                    BehaviorTree.SequenceNode(
                        name="QuestStillRepeatable",
                        children=[
                            LogMessage("Charr At The Gate still repeatable, starting next cycle"),
                        ],
                    ),
                ],
            ),
            BehaviorTree.FailerNode(name="RepeatCharrAtTheGateLoop"),
        ],
    )

    return BehaviorTree(
        BehaviorTree.RepeaterUntilSuccessNode(
            name="CharrAtTheGateUntilLevel10",
            child=BehaviorTree.SelectorNode(
                name="Level10ReachedOrRepeatCharrAtTheGate",
                children=[
                    BehaviorTree.SequenceNode(
                        name="ReachedLevel10",
                        children=[
                            BehaviorTree.ConditionNode(
                                name="IsLevel10OrHigher",
                                condition_fn=_is_level_10_or_higher,
                            ),
                            LogMessage("Reached level 10, stopping Charr At The Gate loop"),
                        ],
                    ),
                    single_cycle,
                ],
            ),
        )
    )
    

def WarriorExtraSkills() -> BehaviorTree:
    return BehaviorTree(
            BehaviorTree.SequenceNode(
                name="Unlock Warrior Extra Skills",
                children=[
                    LogMessage("Traveling to Barradin State"),
                    BT.TravelToOutpost(BARRADIN_STATE_MAP_ID),
                    merchant_cleanup(
                        exclude_models=ITEMS_BLACKLIST,
                        destroy_zero_value_items=True,
                    ),
                    BT.MoveAndAutoDialog(LITTLE_THOM_COORDS),
                    BT.AutoDialog(),
                    LogMessage("Warrior Extra skills Unlocked"),
                ],
            )
        )

    
def RangerExtraSkills() -> BehaviorTree:
    return CommonMapExit(
        travel_map_id=ASCALON_CITY_MAP_ID,
        path_tree=BehaviorTree(
            BehaviorTree.SequenceNode(
                name="Unlock Ranger Secondary Profession",
                children=[
                    LogMessage("Moving to Barradin State exit"),
                    BT.Move(GO_TO_GREEN_HILLS_COUNTY_COORDS),
                    BT.WaitForMapLoad(GREEN_HILLS_COUNTY_MAP_ID),
                    BT.MoveAndAutoDialog(WARMASTER_GRAST_COORDS),
                    BT.AutoDialog(),
                    BT.MoveAndKill(Vec2f(11586.69, 4460.53), Range.Earshot.value),
                    BT.MoveAndAutoDialog(WARMASTER_GRAST_COORDS),
                    BT.AutoDialog(),
                    BT.TravelToOutpost(BARRADIN_STATE_MAP_ID),
                    BT.LoadSkillbar("OgESglcFaVxAAAAIA+m2"),
                    BT.MoveAndAutoDialog(DUKE_BARRADIN_COORDS),
                    BT.AutoDialog(),
                    BT.LoadSkillbar("OgESglcFaVxAAAAIA+m2"),
                    LogMessage("Warrior secondary Unlocked"),

                ],
            )
        ),
        exclude_models=ITEMS_BLACKLIST,
    )
    
    
def MonkExtraSkills() -> BehaviorTree:
    return CommonMapExit(
        travel_map_id=ASCALON_CITY_MAP_ID,
        path_tree=BehaviorTree(
            BehaviorTree.SequenceNode(
                name="Unlock Monk Secondary Profession",
                children=[
                    LogMessage("Moving to Barradin State exit"),
                    BT.Move(GO_TO_GREEN_HILLS_COUNTY_COORDS),
                    BT.WaitForMapLoad(GREEN_HILLS_COUNTY_MAP_ID),
                    BT.MoveAndAutoDialog(GADDEN_THE_PROTECTOR_COORDS),
                    BT.AutoDialog(),
                    BT.TravelToOutpost(ASHFORD_ABBEY_MAP_ID),
                    BT.LoadSkillbar("OwISglcFgkf023bGAAAA"),
                    BT.MoveAndAutoDialog(BROTHER_MHENLO_COORDS, button_number=1),
                    BT.AutoDialog(),
                    LogMessage("Monk Extra skills Unlocked"),
                ],
            )
        ),
        exclude_models=ITEMS_BLACKLIST,
    )
    
def NecromancerExtraSkills() -> BehaviorTree:
    return CommonMapExit(
        travel_map_id=ASHFORD_ABBEY_MAP_ID,
        path_tree=BehaviorTree(
            BehaviorTree.SequenceNode(
                name="Unlock Necromancer Extra Skills",
                children=[
                    LogMessage("Moving to Necromancer Munne"),
                    BT.MoveAndAutoDialog(NECROMANCER_MUNNE_COORDS, button_number=1),
                    BT.AutoDialog(),
                    BT.TravelToOutpost(ASHFORD_ABBEY_MAP_ID),
                    LogMessage("Necromancer Extra skills Unlocked"),
                ],
            )
        ),
        exclude_models=ITEMS_BLACKLIST,
        alternate_exit="The Catacombs",
    )
    
def MesmerExtraSkills() -> BehaviorTree:
    return BehaviorTree(
            BehaviorTree.SequenceNode(
                name="MesmerExtraSkills",
                children=[
                    BT.LogMessage("traveling to foibles fair to unlock mesmer extra skills"),
                    BT.TravelToOutpost(FOIBLES_FAIR_MAP_ID),
                    merchant_cleanup(
                        exclude_models=ITEMS_BLACKLIST,
                        destroy_zero_value_items=True,
                    ),
                    BT.MoveAndAutoDialog(VASAAR_COORDS),
                    BT.AutoDialog(),
                    BT.LogMessage("Mesmer Extra skills Unlocked"),
                ]
            )
        )

def ElementalistExtraSkills() -> BehaviorTree:
    return BehaviorTree(
            BehaviorTree.SequenceNode(
                name="ElementalistExtraSkills",
                children=[
                    BT.LogMessage("traveling to foibles fair to unlock elementalist extra skills"),
                    BT.TravelToOutpost(FOIBLES_FAIR_MAP_ID),
                    merchant_cleanup(
                        exclude_models=ITEMS_BLACKLIST,
                        destroy_zero_value_items=True,
                    ),
                    BT.MoveAndAutoDialog(RALENA_STORMBRINGER_COORDS),
                    BT.Wait(150),
                    BT.AutoDialog(),
                    CommonMapExit(
                        travel_map_id=FOIBLES_FAIR_MAP_ID,
                        path_tree=BehaviorTree(
                            BehaviorTree.SequenceNode(
                                name="Unlock Elementalist Extra Skills",
                                children=[
                                    LogMessage("Moving to Elementalist Aziure"),
                                    BT.MoveAndAutoDialog(ELEMENTALIST_AZIURE_COORDS),
                                    BT.Wait(150),
                                    BT.AutoDialog(),
                                    BT.TravelToOutpost(FOIBLES_FAIR_MAP_ID),
                                    LogMessage("Elementalist Extra skills Unlocked"),
                                ],
                            )
                        ),
                        exclude_models=ITEMS_BLACKLIST,
                    ),
                    BT.LogMessage("Elementalist Extra skills Unlocked"),
                ]
            )
        )
    
def AcquireExtraSkills() -> BehaviorTree:
    tree = BehaviorTree.SequenceNode(
        name="Profession specific extra skills sequence",
        children=[
            BT.StoreProfessionNames(),
            BehaviorTree.SwitchNode(
                selector_fn=lambda node: node.blackboard.get("player_primary_profession_name", ""),
                cases=[
                    ("Warrior", lambda: WarriorExtraSkills()),
                    ("Ranger", lambda: RangerExtraSkills()),
                    ("Monk", lambda: MonkExtraSkills()),
                    ("Necromancer", lambda: NecromancerExtraSkills()),
                    ("Mesmer", lambda: MesmerExtraSkills()),
                    ("Elementalist", lambda: ElementalistExtraSkills()),
                ],
                name="RunProfessionSequence",
            ),
        ],
    )
    return BehaviorTree(tree)

def CommonExtraSkills() -> BehaviorTree:
    tree = BehaviorTree.SequenceNode(
        name="Common extra skills sequence",
        children=[
            CommonMapExit(
                travel_map_id=FORT_RANIK_MAP_ID,
                path_tree=BehaviorTree(
                    BehaviorTree.SequenceNode(
                        name="Unlock Common Ranger Extra Skills",
                        children=[
                            LogMessage("Moving to Ivor Trueshot"),
                            BT.MoveAndAutoDialog(IVOR_TRUESHOT_COORDS),
                            BT.Wait(150),
                            BT.AutoDialog(),
                            LogMessage("Ivor Trueshot Extra skills Unlocked"),
                        ],
                    )
                ),
                exclude_models=ITEMS_BLACKLIST,
            ),
            CommonMapExit(
                travel_map_id=FOIBLES_FAIR_MAP_ID,
                path_tree=BehaviorTree(
                    BehaviorTree.SequenceNode(
                        name="Unlock Common Ranger Extra Skills Aidan",
                        children=[
                            LogMessage("Moving to Aidan"),
                            BT.MoveAndAutoDialog(AIDAN_COORDS),
                            BT.Wait(150),
                            BT.AutoDialog(),
                            LogMessage("Aidan Extra skills Unlocked"),
                        ],
                    )
                ),
                exclude_models=ITEMS_BLACKLIST,
            ),
        ]
    )
    return BehaviorTree(tree)


def GettingStartedTree():
    return GetGettingStartedSequence(
        print_to_console=PRINT_TO_CONSOLE,
    )


def RunAllGettingStartedTree() -> BehaviorTree:
    return named_planner_steps_to_sequence(
        "RunAllGettingStarted",
        [
            *GettingStartedTree(),
            ("Unlock Pet", lambda: UnlockPet()),
            ("Acquire Weapon", lambda: AcquireWeapon()),
            ("Acquire Belt Pouch", lambda: AcquireBeltPouch(exclude_models=ITEMS_BLACKLIST)),
        ],
    )

ModelID.Ebon_Spider_Leg

def RunAllContentTree() -> BehaviorTree:
    return BehaviorTree(
        BehaviorTree.SequenceNode(
            name="RunAllContent",
            children=[
                subtree_step("Run All Getting Started", lambda: RunAllGettingStartedTree()),
                subtree_step("Run All Outpost Unlocks", lambda: RunAllOutpostUnlocksTree()),
                subtree_step("Run All Skills and Professions", lambda: RunAllSkillsAndProfessionsTree()),
                #subtree_step("Run All Farms", lambda: RunAllFarmsTree()),
            ],
        )
    )


def RunAllSkillsAndProfessionsTree() -> BehaviorTree:
    return BehaviorTree(
        BehaviorTree.SequenceNode(
            name="RunAllSkillsAndProfessions",
            children=[
                subtree_step("Unlock Extra Skills", lambda: AcquireExtraSkills()),
                subtree_step("Unlock Common Extra Skills", lambda: CommonExtraSkills()),
            ],
        )
    )


def _draw_help_marker(text: str) -> None:
    PyImGui.same_line(0, 6)
    ImGui.text("(?)")
    ImGui.show_tooltip(text)


def _draw_section_header(
    botting_tree: BottingTree,
    title: str,
    summary: str,
    tooltip: str,
    runner_name: str,
    runner_tree: Callable[[], BehaviorTree],
) -> None:
    ImGui.text(title)
    _draw_help_marker(tooltip)
    ImGui.text(summary)
    _draw_tree_button(
        botting_tree,
        runner_name,
        runner_tree,
        start_label=f"Run Section##{runner_name}",
    )
    ImGui.separator()


def _draw_compact_tree_entry(
    botting_tree: BottingTree,
    name: str,
    summary: str,
    tooltip: str,
    run_tree: BehaviorTree | TreeBuilder | None = None,
) -> None:
    ImGui.text(name)
    _draw_help_marker(tooltip)
    ImGui.text(summary)
    _draw_tree_button(
        botting_tree,
        name,
        run_tree,
        start_label=f"Run##{name}",
    )
    ImGui.separator()


def _draw_compact_named_steps_entry(
    botting_tree: BottingTree,
    name: str,
    summary: str,
    tooltip: str,
    steps_builder: Callable[[], list[tuple[str, Callable[[], BehaviorTree]]]],
    sequence_name: str,
) -> None:
    ImGui.text(name)
    _draw_help_marker(tooltip)
    ImGui.text(summary)
    _draw_named_steps_button(
        botting_tree,
        name,
        steps_builder,
        sequence_name=sequence_name,
        start_label=f"Run##{name}",
    )
    ImGui.separator()


def _draw_welcome_tab() -> None:
    ImGui.push_font("Bold", 22)
    ImGui.text("Welcome to Beautiful Pre-Searing!")
    ImGui.pop_font()

    if ImGui.collapsing_header("About this script", flags=0):
        ImGui.text_wrapped("This script is a comprehensive collection of quests and activities for the Pre-Searing area.")
        ImGui.text_wrapped("Use the Controls tab for all routines. Sections are grouped under compact collapsing headers.")
        ImGui.separator()

    if ImGui.collapsing_header("How to use", flags=0):
        ImGui.bullet_text("Set your looting filters")
        ImGui.bullet_text("Deactivate Automatic Handling in Inventory+")
        ImGui.bullet_text("Deactivate HeroAI or any other combat automator")
        ImGui.bullet_text("Create a new character")
        ImGui.bullet_text('Use "Run All Content" or a section runner to begin')
        ImGui.separator()

    ImGui.separator()


def _draw_controls_tab(botting_tree: BottingTree) -> None:
    ImGui.text("All routines")
    _draw_help_marker("Runs the broad progression flow. Use section runners below if you want a narrower scope.")
    ImGui.text("Starter progression, pet, weapon, belt pouch, and outpost unlocks.")
    _draw_tree_button(
        botting_tree,
        "Run All Content",
        lambda: RunAllContentTree(),
        start_label="Run All",
    )
    ImGui.separator()

    if ImGui.collapsing_header("Getting Started"):
        _draw_section_header(
            botting_tree,
            "Getting Started",
            "Main setup, pet unlock, weapon, and belt pouch.",
            "Runs the early progression block: starter quests, ranger pet unlock, weapon acquisition, and belt pouch.",
            "Run All Getting Started",
            lambda: RunAllGettingStartedTree(),
        )
        _draw_compact_named_steps_entry(
            botting_tree,
            "Getting Started",
            "Starter quest chain.",
            "Completes the early setup quests that unlock core pre-searing progression.",
            lambda: GettingStartedTree(),
            sequence_name="All quests sequence",
        )
        _draw_compact_tree_entry(
            botting_tree,
            "Unlock Pet",
            "Charm pet and unlock secondary.",
            "Captures the pet and completes the ranger secondary unlock path.",
            lambda: UnlockPet(),
        )
        _draw_compact_tree_entry(
            botting_tree,
            "Acquire Weapon",
            "Best-effort weapon progression.",
            "Attempts bonus/collector weapon progression and handles the warrior prep flow.",
            lambda: AcquireWeapon(),
        )
        _draw_compact_tree_entry(
            botting_tree,
            "Acquire Belt Pouch",
            "Inventory upgrade.",
            "Farms skale fins, exchanges for the belt pouch, and equips it.",
            lambda: AcquireBeltPouch(exclude_models=ITEMS_BLACKLIST),
        )

    if ImGui.collapsing_header("Outpost Unlocks"):
        _draw_section_header(
            botting_tree,
            "Outpost Unlocks",
            "Unlock travel paths and outposts.",
            "Runs the full outpost unlock sequence for the script's current pre-searing coverage.",
            "Run All Outpost Unlocks",
            lambda: RunAllOutpostUnlocksTree(),
        )
        _draw_compact_tree_entry(
            botting_tree,
            "Unlock Wizard's Folly",
            "Ashford -> Wizard's Folly -> Foible's Fair.",
            "Unlocks Wizard's Folly and the onward path toward Foible's Fair.",
            lambda: UnlockWizardsFolly(),
        )
        _draw_compact_tree_entry(
            botting_tree,
            "Unlock Barradin State",
            "Ascalon -> Green Hills -> Barradin.",
            "Unlocks Barradin State through the Green Hills route.",
            lambda: UnlockBarradinState(),
        )
        _draw_compact_tree_entry(
            botting_tree,
            "Unlock Fort Ranik",
            "Ashford -> Regent Valley -> Fort Ranik.",
            "Unlocks Fort Ranik using the Regent Valley route.",
            lambda: UnlockFortRanik(),
        )

    if ImGui.collapsing_header("Farms"):
        _draw_section_header(
            botting_tree,
            "Farms",
            "Repeatable material and item farming.",
            "Runs the farm section. Currently this is mainly the skale fin farm path.",
            "Run All Farms",
            lambda: RunAllFarmsTree(),
        )
        _draw_compact_tree_entry(
            botting_tree,
            "Skale Fin Farm",
            "Reusable skale fin loop.",
            "Farms skales for fins using the reusable route helper. Useful for belt pouch support or manual stock.",
            lambda: SkaleFarmLoopTree(),
        )

    if ImGui.collapsing_header("Quests"):
        ImGui.text("Quests")
        _draw_help_marker("Standalone quest routines that do not belong under the broader setup, unlock, or farm sections.")
        ImGui.text("Single-quest runs and quest-specific helpers.")
        ImGui.separator()
        _draw_compact_tree_entry(
            botting_tree,
            "Charr At The Gate",
            "Follow Rurik route and bail out.",
            "Runs the Charr At The Gate quest routine, following Rurik's path and exiting afterward.",
            lambda: CharrAtTheGate(),
        )

    if ImGui.collapsing_header("Skills and Professions"):
        _draw_section_header(
            botting_tree,
            "Skills and Professions",
            "Profession-specific and common skill unlocks.",
            "Runs both profession-specific extra skill unlocks and the shared/common extra skill routes.",
            "Run All Skills and Professions",
            lambda: RunAllSkillsAndProfessionsTree(),
        )
        _draw_compact_tree_entry(
            botting_tree,
            "Unlock Extra Skills",
            "Profession-specific unlock chain.",
            "Chooses the current primary profession route and unlocks its extra pre-searing skills.",
            lambda: AcquireExtraSkills(),
        )
        _draw_compact_tree_entry(
            botting_tree,
            "Unlock Common Extra Skills",
            "Shared ranger-related skill routes.",
            "Runs the common extra skill routes that are not tied to a single primary profession.",
            lambda: CommonExtraSkills(),
        )


#region getting started tab
def _draw_getting_started_tab(botting_tree: BottingTree) -> None:
    global selected_debug_tree_name

    _draw_tree_button(
        botting_tree,
        "Run All Getting Started",
        lambda: RunAllGettingStartedTree(),
        start_label="Run All Getting Started",
    )

    ImGui.separator()

    if ImGui.collapsing_header("1. Prepare Your Character"):
        ImGui.text_wrapped("This routine will complete important early quests that unlock essential features and quality of life improvements for the rest of the content in Pre-Searing.")
        ImGui.separator()

        _draw_named_steps_button(
            botting_tree,
            "Getting Started",
            lambda: GettingStartedTree(),
            sequence_name="All quests sequence",
            start_label="Getting Started",
        )
        _draw_tree_button(
            botting_tree,
            "Charr At The Gate",
            lambda: CharrAtTheGate(),
            start_label="Charr At The Gate",
        )


    if ImGui.collapsing_header("2. Capture Pet and Unlock Secondary Profession"):
        ImGui.text_wrapped("This routine will capture the pet from the first quest and complete the necessary steps to unlock the secondary profession.")
        ImGui.text_wrapped("This is a separate routine because it involves a lot of waiting for the pet capture to succeed, which can take a long time and is not required to be done early on.")
        ImGui.separator()

        _draw_tree_button(
            botting_tree,
            "Unlock Pet",
            lambda: UnlockPet(),
            start_label="Unlock Pet",
        )

    if ImGui.collapsing_header("3. Acquire a Weapon"):
        ImGui.text_wrapped("This section will cover acquiring a weapon for your character")
        ImGui.text_wrapped("Nevermore Flatbow is the best weapon to acquire in Pre-Searing, we will attempt to acquire it")
        ImGui.text_wrapped("If Nevermore is not available, we will fall back to Farming material for Buying a bow with a collector")
        ImGui.separator()

        _draw_tree_button(
            botting_tree,
            "Acquire Weapon",
            lambda: AcquireWeapon(),
            start_label="Acquire Weapon",
        )

    if ImGui.collapsing_header("4. Acquire a Belt Pouch"):
        ImGui.text_wrapped("This section will cover acquiring a belt pouch for your character")
        ImGui.text_wrapped("Belt pouches are a very useful item that increase your inventory space, and the one available in Pre-Searing is very easy to acquire")
        ImGui.separator()

        _draw_tree_button(
            botting_tree,
            "Acquire Belt Pouch",
            lambda: AcquireBeltPouch(
                exclude_models=ITEMS_BLACKLIST,
            ),
            start_label="Acquire Belt Pouch",
        )


#region outpost unlocks tab
def _draw_outpost_unlocks_tab(botting_tree: BottingTree) -> None:
    global selected_debug_tree_name

    _draw_tree_button(
        botting_tree,
        "Run All Outpost Unlocks",
        lambda: RunAllOutpostUnlocksTree(),
        start_label="Run All Outpost Unlocks",
    )
    ImGui.separator()

    if ImGui.collapsing_header("5. Unlock Wizard's Folly"):
        ImGui.text_wrapped("This routine travels from Ashford Abbey through Wizard's Folly and into Foible's Fair to unlock the outpost path.")
        ImGui.separator()

        _draw_tree_button(
            botting_tree,
            "Unlock Wizard's Folly",
            lambda: UnlockWizardsFolly(),
            start_label="Unlock Wizard's Folly",
        )
                
    if ImGui.collapsing_header("6. Unlock Barradin State"):
        ImGui.text_wrapped("This routine travels from Ascalon City through Green Hills County and into Barradin State to unlock the outpost path.")
        ImGui.separator()

        _draw_tree_button(
            botting_tree,
            "Unlock Barradin State",
            lambda: UnlockBarradinState(),
            start_label="Unlock Barradin State",
        )
                
    if ImGui.collapsing_header("7. Unlock Fort Ranik"):
        ImGui.text_wrapped("This routine travels from Ashford Abbey through Regent Valley and into Fort Ranik to unlock the outpost path.")
        ImGui.separator()

        _draw_tree_button(
            botting_tree,
            "Unlock Fort Ranik",
            lambda: UnlockFortRanik(),
            start_label="Unlock Fort Ranik",
        )


#region farming tab
def _draw_farming_tab(botting_tree: BottingTree) -> None:
    global selected_debug_tree_name

    _draw_tree_button(
        botting_tree,
        "Run All Farms",
        lambda: RunAllFarmsTree(),
        start_label="Run All Farms",
    )
    ImGui.separator()

    if ImGui.collapsing_header("1. Skale Fin Farm"):
        ImGui.text_wrapped("Placeholder skale fin farming routine using the reusable farming helper.")
        ImGui.text_wrapped("Update the start map, kill path, model id, and target quantity in this script if you want to customize the farm.")
        ImGui.separator()

        _draw_tree_button(
            botting_tree,
            "Skale Fin Farm",
            lambda: SkaleFarmLoopTree(),
            start_label="Start Skale Fin Farm",
        )
        
def _draw_skills_and_professions_tab(botting_tree: BottingTree) -> None:
    global selected_debug_tree_name

    _draw_tree_button(
        botting_tree,
        "Unlock Extra Skills",
        lambda: AcquireExtraSkills(),
        start_label="Unlock Extra Skills",
    )
    
    _draw_tree_button(
        botting_tree,
        "Unlock Common Extra Skills",
        lambda: CommonExtraSkills(),
        start_label="Unlock Common Extra Skills",
    )


#region Debug Tab
def _draw_debug_tab() -> None:
    global selected_debug_tree_name
    botting_tree = ensure_botting_tree()

    _draw_tree_button(
        botting_tree,
        "HeroAI Only",
        None,
        start_label="Start HeroAI Only",
    )
    ImGui.separator()

    tree_names = [
        "Getting Started",
        "HeroAI Only",
        "Unlock Pet",
        "Unlock Wizard's Folly",
        "Unlock Barradin State",
        "Unlock Fort Ranik",
        "Acquire Weapon",
        "Acquire Belt Pouch",
        "Skale Fin Farm",
        "Unlock Warrior Secondary Profession",
    ]
    current_tree_index = tree_names.index(selected_debug_tree_name) if selected_debug_tree_name in tree_names else 0

    if botting_tree.IsStarted():
        ImGui.text_wrapped(f"Active routine: {selected_debug_tree_name}")
        ImGui.text_wrapped("Stop the current routine to switch the debug context.")
    else:
        new_tree_index = PyImGui.combo("Debug Tree", current_tree_index, tree_names)
        if 0 <= new_tree_index < len(tree_names) and tree_names[new_tree_index] != selected_debug_tree_name:
            selected_debug_tree_name = tree_names[new_tree_index]
            if selected_debug_tree_name == "Getting Started":
                botting_tree.SetCurrentNamedPlannerSteps(
                    GettingStartedTree(),
                    name="All quests sequence",
                    auto_start=False,
                )
            elif selected_debug_tree_name == "HeroAI Only":
                botting_tree.SetCurrentTree(None, auto_start=False)
            elif selected_debug_tree_name == "Unlock Pet":
                botting_tree.SetCurrentTree(UnlockPet(), auto_start=False)
            elif selected_debug_tree_name == "Unlock Wizard's Folly":
                botting_tree.SetCurrentTree(UnlockWizardsFolly(), auto_start=False)
            elif selected_debug_tree_name == "Unlock Barradin State":
                botting_tree.SetCurrentTree(UnlockBarradinState(), auto_start=False)
            elif selected_debug_tree_name == "Unlock Fort Ranik":
                botting_tree.SetCurrentTree(UnlockFortRanik(), auto_start=False)
            elif selected_debug_tree_name == "Acquire Weapon":
                botting_tree.SetCurrentTree(AcquireWeapon(), auto_start=False)
            elif selected_debug_tree_name == "Acquire Belt Pouch":
                botting_tree.SetCurrentTree(
                    AcquireBeltPouch(
                        exclude_models=ITEMS_BLACKLIST,
                    ),
                    auto_start=False,
                )
            elif selected_debug_tree_name == "Skale Fin Farm":
                botting_tree.SetCurrentTree(SkaleFarmLoopTree(), auto_start=False)

    if PyImGui.button("Dump Tree Diagnostics"):
        dump_tree_diagnostics(botting_tree, selected_debug_tree_name)
    PyImGui.same_line(0, -1)
    ImGui.text_wrapped("Prints the live tree state and copies the dump to the clipboard.")


    if ImGui.collapsing_header("Draw Move Path Debug Options"):
        global draw_move_path, draw_move_path_labels, draw_move_path_thickness, draw_move_waypoint_radius, draw_move_current_waypoint_radius
        draw_move_path = PyImGui.checkbox("Draw Move Path", draw_move_path)
        draw_move_path_labels = PyImGui.checkbox("Draw Path Labels", draw_move_path_labels)
        draw_move_path_thickness = PyImGui.slider_float("Path Thickness", draw_move_path_thickness, 1.0, 6.0)
        draw_move_waypoint_radius = PyImGui.slider_float("Waypoint Radius", draw_move_waypoint_radius, 15.0, 100.0)
        draw_move_current_waypoint_radius = PyImGui.slider_float("Current Waypoint Radius", draw_move_current_waypoint_radius, 20.0, 120.0)

    botting_tree.DrawDebugConsole(
        child_id="BeautifulPreSearingLog",
        height=200,
        reverse_order=True,
        show_controls=True,
    )


#region tree button
def _draw_tree_button(
    botting_tree: BottingTree,
    name: str,
    run_tree: BehaviorTree | TreeBuilder | None = None,
    start_label: str | None = None,
) -> None:
    global selected_debug_tree_name
    start_button_label = start_label or f"Run {name}"
    if botting_tree.IsStarted() and selected_debug_tree_name == name:
        if PyImGui.button(f"Stop {name}"):
            botting_tree.Stop()
        PyImGui.same_line(0, -1)
        if botting_tree.IsPaused():
            if PyImGui.button(f"Unpause {name}"):
                botting_tree.Pause(False)
        else:
                if PyImGui.button(f"Pause {name}"):
                    botting_tree.Pause(True)
    else:
        if PyImGui.button(start_button_label):
            selected_debug_tree_name = name
            start_tree_with_heroai_enabled(
                botting_tree,
                run_tree() if callable(run_tree) else run_tree,
            )


def _draw_named_steps_button(
    botting_tree: BottingTree,
    name: str,
    steps_builder: Callable[[], list[tuple[str, Callable[[], BehaviorTree]]]],
    sequence_name: str,
    start_label: str | None = None,
) -> None:
    global selected_debug_tree_name
    start_button_label = start_label or f"Run {name}"
    if botting_tree.IsStarted() and selected_debug_tree_name == name:
        if PyImGui.button(f"Stop {name}"):
            botting_tree.Stop()
        PyImGui.same_line(0, -1)
        if botting_tree.IsPaused():
            if PyImGui.button(f"Unpause {name}"):
                botting_tree.Pause(False)
        else:
            if PyImGui.button(f"Pause {name}"):
                botting_tree.Pause(True)
    else:
        if PyImGui.button(start_button_label):
            selected_debug_tree_name = name
            start_named_steps_with_heroai_enabled(
                botting_tree,
                steps_builder(),
                name=sequence_name,
            )

#region draw
def draw() -> None:
    global INI_KEY, selected_debug_tree_name
    if not INI_KEY:
        return

    botting_tree = ensure_botting_tree()
    PyImGui.set_next_window_size((BANNER_WIDTH + 20, 0))
    if ImGui.Begin(ini_key=INI_KEY, name="Beautiful Pre-Searing", flags=PyImGui.WindowFlags.AlwaysAutoResize):
        if ImGui.begin_tab_bar("MainTabBar##BeautifulPreSearing"):
            if ImGui.begin_tab_item("Welcome"):
                ImGui.DrawTexture(TEXTURE_PATH, BANNER_WIDTH, BANNER_HEIGHT)
                ImGui.separator()
                _draw_welcome_tab()
                _draw_tree_button(
                    botting_tree,
                    "Run All Content",
                    lambda: RunAllContentTree(),
                    start_label="Run All Content",
                )
                ImGui.end_tab_item()
            if ImGui.begin_tab_item("Controls"):
                _draw_controls_tab(botting_tree)
                ImGui.end_tab_item()
            if ImGui.begin_tab_item("Debug"):
                _draw_debug_tab()
                ImGui.end_tab_item()
            ImGui.end_tab_bar()
    ImGui.End(ini_key=INI_KEY)

#region main
def _add_config_vars() -> None:
    global INI_KEY
    IniManager().add_bool(INI_KEY, "draw_move_path", "Display", "DrawMovePath", default=True)
    IniManager().add_bool(INI_KEY, "draw_move_path_labels", "Display", "DrawMovePathLabels", default=False)
    IniManager().add_float(INI_KEY, "draw_move_path_thickness", "Display", "DrawMovePathThickness", default=2.0)
    IniManager().add_float(INI_KEY, "draw_move_waypoint_radius", "Display", "DrawMoveWaypointRadius", default=45.0)
    IniManager().add_float(INI_KEY, "draw_move_current_waypoint_radius", "Display", "DrawMoveCurrentWaypointRadius", default=65.0)



def main() -> None:
    global INI_KEY, initialized

    if not initialized:
        if not INI_KEY:
            INI_KEY = IniManager().ensure_key(INI_PATH, INI_FILENAME)
            if not INI_KEY:
                return
            _add_config_vars()
            IniManager().load_once(INI_KEY)

        ensure_botting_tree().SetCurrentNamedPlannerSteps(
            GettingStartedTree(),
            name="All quests sequence",
            auto_start=False,
        )
        initialized = True

    botting_tree = ensure_botting_tree()
    botting_tree.tick()

    if draw_move_path:
        botting_tree.DrawMovePath(
            draw_labels=draw_move_path_labels,
            path_thickness=draw_move_path_thickness,
            waypoint_radius=draw_move_waypoint_radius,
            current_waypoint_radius=draw_move_current_waypoint_radius,
        )


if __name__ == "__main__":
    main()
