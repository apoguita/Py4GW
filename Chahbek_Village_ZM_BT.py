from __future__ import annotations

import random
from typing import Callable
from Py4GWCoreLib.routines_src.behaviourtrees_src.items import BTItems
from Py4GWCoreLib.BottingTree import BottingTree
from Py4GWCoreLib.IniManager import IniManager
from Py4GWCoreLib.enums_src.Model_enums import ModelID
from Py4GWCoreLib.native_src.internals.types import Vec2f
from Py4GWCoreLib.py4gwcorelib_src.BehaviorTree import BehaviorTree
from Sources.ApoSource.ApoBottingLib import wrappers as BT


MODULE_NAME = "Chahbek Village ZM Redux"
INI_PATH = "Widgets/Automation/Bots/Chahbek Village ZM Redux"
INI_FILENAME = "Chahbek_Village_ZM_Redux.ini"

# Maps
CHAHBEK_VILLAGE_OUTPOST = 544
CHAHBEK_VILLAGE_MISSION = 456
GREAT_TEMPLE_OF_BALTHAZAR = 248



# Items / NPC models
COPPER_Z_COIN_MODEL_ID = 31202
XUNLAI_AGENT_MODEL_ID = 221

# Old script district pool:
# region=2 with languages 4/5/9/10.
RANDOM_TRAVEL_REGION = 2
RANDOM_TRAVEL_LANGUAGES = (4, 5, 9, 10)

initialized = False
ini_key = ""
botting_tree: BottingTree | None = None


def ensure_botting_tree() -> BottingTree:
    global botting_tree

    if botting_tree is None:
        botting_tree = BottingTree.Create(
            MODULE_NAME,
            main_routine=get_execution_steps(),
            routine_name="SingleAccountSequence",
            repeat=True,
            multi_account=False,
            isolation_enabled=True,)

    return botting_tree


def RandomTravelToRegion(
    map_id: int,
    name: str | None = None,
    timeout_ms: int = 12_000,
) -> BehaviorTree:
    def _choose(_node: BehaviorTree.Node) -> BehaviorTree:
        language = random.choice(RANDOM_TRAVEL_LANGUAGES)
        return BT.Sequence(
            name=name or f"RandomTravel({map_id})",
            children=[
                BT.TravelToRegion(
                    outpost_id=map_id,
                    region=2,
                    district=1,
                    language=language,
                    log=True,
                    timeout_ms=timeout_ms,
                ),
                BT.WaitForMapLoad(
                    map_id=map_id,
                    timeout_ms=timeout_ms,
                ),
            ],
        )

    return BT.Subtree(
        name=name or f"RandomTravel({map_id})",
        subtree_fn=_choose,
    )


def EquipStarterWeaponByProfession() -> BehaviorTree:
    return BT.GetNodeByProfession(
        DervishNode=BT.EquipItemByModelID(15591, log=True),
        ParagonNode=BT.EquipItemByModelID(15593, log=True),
        ElementalistNode=BT.EquipItemByModelID(2742, log=True),
        MesmerNode=BT.EquipItemByModelID(2652, log=True),
        NecromancerNode=BT.EquipItemByModelID(2694, log=True),
        RangerNode=BT.EquipItemByModelID(477, log=True),
        WarriorNode=BT.EquipItemByModelID(2982, log=True),
        MonkNode=BT.EquipItemByModelID(2787, log=True),
    )


def InitializeBot() -> BehaviorTree:
    bot = ensure_botting_tree()

    return BT.Sequence(
        name="Initialize Bot",
        random_travel=False,
        hard_mode=False,
        children=[
            bot.Config.Aggressive(
                multi_account=False,
                auto_loot=True,
                resurrection_scroll=False,
            ),
            BT.StoreRerollContext(
                campaign_name="Nightfall",
                fallback_profession="Warrior",
            ),
            
        ],
    )





def TravelToChahbek() -> BehaviorTree:
    return BT.Sequence(
        name="Travel To Chahbek Village",
        children=[
            RandomTravelToRegion(
                CHAHBEK_VILLAGE_OUTPOST,
                name="Random Travel - Chahbek",
            ),
        ],
    )





def ConfigureFirstBattle() -> BehaviorTree:
    return BT.Sequence(
        name="Battle Setup",
        children=[
            BT.Wait(1_000),
            BT.SpawnBonusItems(log=True),
            EquipStarterWeaponByProfession(),
            BT.CreateParty(
                hero_ids=[6],
                henchman_ids=[1, 2],
                multibox_invite=False,
                log=True,
            ),
        ],
    )


def SkipTutorialDialog() -> BehaviorTree:
    return BT.Sequence(
        name="Skip Tutorial Dialog",
        children=[
            BT.MoveAndDialog(
                Vec2f(10289, 6405),
                0x82A501,
                log=True,
            ),
            BT.TravelGH(),
            BT.LeaveGH(),
            BT.WaitForMapLoad(
                map_id=CHAHBEK_VILLAGE_OUTPOST,
                timeout_ms=30_000,
            ),
        ],
    )


def TakeZaishenMission() -> BehaviorTree:
    return BT.Sequence(
        name="Take Zaishen Mission",
        children=[
            RandomTravelToRegion(
                GREAT_TEMPLE_OF_BALTHAZAR,
                name="Random Travel - Reward",
            ),
            BT.MoveAndAutoDialog(
                Vec2f(-5065.00, -5211.00),
                buttons=0,
                log=True,
            ),
        ],
    )


def MeetingFirstSpearJahdugar() -> BehaviorTree:
    return BT.Sequence(
        name="Meeting First Spear Jahdugar",
        children=[
            BT.MoveAndAutoDialog(
                Vec2f(3482, -5167),
                buttons=[0, 0],
                log=True,
            ),
        ],
    )


def EnterChahbekMission() -> BehaviorTree:
    return BT.Sequence(
        name="Chahbek Village Mission",
        children=[
            BT.MoveAndAutoDialog(
                Vec2f(3485, -5246),
                buttons=[1, 0],
                log=True,
            ),
            BT.Wait(2_000),
            BT.WaitUntilOnExplorable(timeout_ms=30_000),
            BTItems.UseConsumable(ModelID.Igneous_Summoning_Stone.value),
            BT.VanquishNode(
                name="Clear Chahbek First Path",
                steps=[
                    Vec2f(227, -5658),
                    Vec2f(-1144, -4378),
                    Vec2f(-2058, -3494),
                    Vec2f(-1725, -2551),
                    Vec2f(-2435.07, -6440.10),
                    Vec2f(-4212.00, -6730.00),
                ],
                clear_area_radius=400,
                pause_on_combat=True,
            ),

            BT.MoveAndInteractWithGadget(
                Vec2f(-4725, -1830),
                pause_on_combat=True,
                log=True,
            ),
            BT.FlagAllHeroes(-1891.88, 575.85),
            BT.Wait(2_000),

            BT.MoveAndInteractWithGadget(
                Vec2f(-1725, -2550),
                pause_on_combat=True,
                log=True,
            ),
            BT.Wait(1_500),
            BT.InteractWithGadgetAtXY(Vec2f(-1725, -2550)),

            BT.MoveAndInteractWithGadget(
                Vec2f(-4725, -1830),
                pause_on_combat=True,
                log=True,
            ),
            BT.MoveAndInteractWithGadget(
                Vec2f(-1731, -4138),
                pause_on_combat=True,
                log=True,
            ),
            BT.UnflagAllHeroes(),
            BT.Wait(2_000),
            BT.InteractWithGadgetAtXY(Vec2f(-1731, -4138)),

            BT.VanquishNode(
                name="Clear Chahbek Final Path",
                steps=[
                    Vec2f(-1891.88, 575.85),
                ],
                clear_area_radius=400,
                pause_on_combat=True,
            ),

            BT.WaitForMapLoad(
                map_id=CHAHBEK_VILLAGE_MISSION,
                timeout_ms=120_000,
            ),
        ],
    )

def EnterChahbekMission2() -> BehaviorTree:
    return BT.Sequence(
        name="Chahbek Village Mission",
        children=[
            RandomTravelToRegion(
                CHAHBEK_VILLAGE_OUTPOST,
                name="Random Travel - Chahbek Village"
            ),
            BT.SpawnBonusItems(log=True),
            BT.CreateParty(
                hero_ids=[6],
                henchman_ids=[1, 2],
                multibox_invite=False,
                log=True,
            ),
            BT.MoveAndAutoDialog(
                Vec2f(3485, -5246),
                buttons=[1, 0],
                log=True,
            ),
            BT.Wait(2_000),
            BT.WaitUntilOnExplorable(timeout_ms=30_000),
            BTItems.UseConsumable(ModelID.Igneous_Summoning_Stone.value),
            BT.VanquishNode(
                name="Clear Chahbek First Path",
                steps=[
                    Vec2f(227, -5658),
                    Vec2f(-1144, -4378),
                    Vec2f(-2058, -3494),
                    Vec2f(-1725, -2551),
                    Vec2f(-2435.07, -6440.10),
                    Vec2f(-4212.00, -6730.00),
                ],
                clear_area_radius=400,
                pause_on_combat=True,
            ),

            BT.MoveAndInteractWithGadget(
                Vec2f(-4725, -1830),
                pause_on_combat=True,
                log=True,
            ),
            BT.FlagAllHeroes(-1891.88, 575.85),
            BT.Wait(2_000),

            BT.MoveAndInteractWithGadget(
                Vec2f(-1725, -2550),
                pause_on_combat=True,
                log=True,
            ),
            BT.Wait(1_500),
            BT.InteractWithGadgetAtXY(Vec2f(-1725, -2550)),

            BT.MoveAndInteractWithGadget(
                Vec2f(-4725, -1830),
                pause_on_combat=True,
                log=True,
            ),
            BT.MoveAndInteractWithGadget(
                Vec2f(-1731, -4138),
                pause_on_combat=True,
                log=True,
            ),
            BT.UnflagAllHeroes(),
            BT.Wait(2_000),
            BT.InteractWithGadgetAtXY(Vec2f(-1731, -4138)),

            BT.VanquishNode(
                name="Clear Chahbek Final Path",
                steps=[
                    Vec2f(-1891.88, 575.85),
                ],
                clear_area_radius=400,
                pause_on_combat=True,
            ),

            BT.WaitForMapLoad(
                map_id=CHAHBEK_VILLAGE_MISSION,
                timeout_ms=120_000,
            ),
        ],
    )


def TakeReward() -> BehaviorTree:
    return BT.Sequence(
        name="Take Reward",
        children=[
            RandomTravelToRegion(
                GREAT_TEMPLE_OF_BALTHAZAR,
                name="Random Travel - Reward",
            ),
            BT.MoveAndAutoDialog(
                Vec2f(-5019.00, -5496.00),
                buttons=0,
                log=True,
            ),
        ],
    )


def UnlockXunlai() -> BehaviorTree:
    return BT.Sequence(
        name="Unlock Xunlai Storage",
        children=[
            BT.Move(
                [Vec2f(-7118.00, -6415.00)],
                pause_on_combat=False,
            ),
            BT.MoveAndAutoDialogByModelID(
                XUNLAI_AGENT_MODEL_ID,
                button_number=0,
                log=True,
            ),
            BT.TargetAgentByModelIDAndAutoDialog(
                XUNLAI_AGENT_MODEL_ID,
                buttons=0,
                log=True,
            ),
        ],
    )

def DepositRewards() -> BehaviorTree:
    return BT.Sequence(
        name="Deposit Reward And Gold",
        children=[
            BT.DepositModelToStorage(
                COPPER_Z_COIN_MODEL_ID,
            ),
            BT.DepositGoldKeep(
                gold_amount_to_leave_on_character=0,
            ),
        ],
    )


def RerollCharacter() -> BehaviorTree:
    return BT.Sequence(
        name="Reroll Character",
        children=[
            BT.StoreRerollContext(
                campaign_name="Nightfall",
                fallback_profession="Dervish",
            ),
            BT.DeleteCharacterFromBlackboard(
                character_name_key="reroll_character_name",
                timeout_ms=45_000,
            ),
            BT.ResolveRerollNewCharacterName(
                character_name_key="reroll_character_name",
                new_character_name_key="reroll_new_character_name",
            ),
            BT.CreateCharacterFromBlackboard(
                character_name_key="reroll_new_character_name",
                campaign_key="reroll_campaign",
                profession_key="reroll_primary_profession"
                ,
                timeout_ms=60_000,
            ),
            BT.Wait(3_000),
            BT.ResetActionQueues(),
        ],
    )


def RunChahbekPre() -> BehaviorTree:
    return BT.Sequence(
        name="Run Chahbek Village ZM",
        children=[
            ConfigureFirstBattle(),
            EnterChahbekMission(),
                    ],)

def RunChahbekZMission() -> BehaviorTree:
    return BT.Sequence(
        name="Run Chahbek Village ZM",
        children=[
            TakeZaishenMission(),
            EnterChahbekMission2(),
        ],
    )

def PrepareChahbek() -> BehaviorTree:
    return BT.Sequence(
        name="Prepare Chahbek Village ZM",
        children=[
            SkipTutorialDialog(),
            MeetingFirstSpearJahdugar(),


        ],
    )

def RewardChahbek() -> BehaviorTree:
    return BT.Sequence(
        name="Reward Chahbek Village ZM",
        children=[
            TakeReward(),
            UnlockXunlai(),
            DepositRewards(),
        ],
    )


def get_execution_steps() -> list[tuple[str, Callable[[], BehaviorTree]]]:
    return [
        ("Initialize Bot", InitializeBot),
        ("Prepare Chahbek", PrepareChahbek),
        ("Run Chahbek Pre", RunChahbekPre),
        ("Run Chahbek ZMission", RunChahbekZMission),
        ("Reward Chahbek", RewardChahbek),
        ("Reroll Character", RerollCharacter)
    ]


def main() -> None:
    global initialized, ini_key

    if not initialized:
        if not ini_key:
            ini_key = IniManager().ensure_key(INI_PATH, INI_FILENAME)
            if not ini_key:
                return
            IniManager().load_once(ini_key)

        ensure_botting_tree()
        initialized = True

    tree = ensure_botting_tree()
    tree.tick()
    tree.UI.draw_window()


if __name__ == "__main__":
    main()
    
