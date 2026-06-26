from __future__ import annotations

import random
from typing import Callable

from Py4GWCoreLib.BottingTree import BottingTree
from Py4GWCoreLib.IniManager import IniManager
from Py4GWCoreLib.native_src.internals.types import Vec2f
from Py4GWCoreLib.py4gwcorelib_src.BehaviorTree import BehaviorTree
from Sources.ApoSource.ApoBottingLib import wrappers as BT


MODULE_NAME = "Chahbek Village ZM Redux"
INI_PATH = "Widgets/Automation/Bots/Chahbek Village ZM Redux"
INI_FILENAME = "Chahbek_Village_ZM_Redux.ini"

# Maps
CHAHBEK_VILLAGE_OUTPOST = 544
CHAHBEK_VILLAGE_MISSION = 456
EMBARK_BEACH = 857
GREAT_TEMPLE_OF_BALTHAZAR = 248

# Dialogs
DIALOG_SKIP_TUTORIAL = 0x82A501
DIALOG_SUNSPEAR_SCOUT = 0x84
DIALOG_ZAISHEN_MISSION_REWARD = 0x83D207
DIALOG_TAKE_CHAHBEK_ZM = 0x83D201
DIALOG_JAHDUGAR_1 = 0x82A507
DIALOG_JAHDUGAR_2 = 0x83A801
DIALOG_ENTER_MISSION_1 = 0x81
DIALOG_ENTER_MISSION_2 = 0x84
DIALOG_XUNLAI_1 = 0x84
DIALOG_XUNLAI_2 = 0x86

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
        )

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
            BT.SpawnBonusItems(log=True),
        ],
    )


def SkipTutorialDialog() -> BehaviorTree:
    return BT.Sequence(
        name="Skip Tutorial Dialog",
        children=[
            BT.MoveAndDialog(
                Vec2f(10289, 6405),
                DIALOG_SKIP_TUTORIAL,
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
            BT.MoveAndDialog(
                Vec2f(4626, -9617),
                DIALOG_SUNSPEAR_SCOUT,
                log=True,
            ),
            BT.WaitForMapLoad(
                map_id=EMBARK_BEACH,
                timeout_ms=15_000,
            ),
            BT.MoveAndDialog(
                Vec2f(-277.00, -3561.00),
                DIALOG_TAKE_CHAHBEK_ZM,
                log=True,
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


def MeetingFirstSpearJahdugar() -> BehaviorTree:
    return BT.Sequence(
        name="Meeting First Spear Jahdugar",
        children=[
            BT.MoveAndDialog(
                Vec2f(3482, -5167),
                DIALOG_JAHDUGAR_1,
                log=True,
            ),
            BT.MoveAndDialog(
                Vec2f(3482, -5167),
                DIALOG_JAHDUGAR_2,
                log=True,
            ),
        ],
    )


def ConfigureFirstBattle() -> BehaviorTree:
    return BT.Sequence(
        name="Battle Setup",
        children=[
            BT.Wait(1_000),
            EquipStarterWeaponByProfession(),
            BT.CreateParty(
                hero_ids=[6],
                henchman_ids=[1, 2],
                multibox_invite=False,
                log=True,
            ),
        ],
    )


def EnterChahbekMission() -> BehaviorTree:
    return BT.Sequence(
        name="Chahbek Village Mission",
        children=[
            BT.MoveAndDialog(
                Vec2f(3485, -5246),
                DIALOG_ENTER_MISSION_1,
                log=True,
            ),
            BT.MoveAndDialog(
                Vec2f(3485, -5246),
                DIALOG_ENTER_MISSION_2,
                log=True,
            ),
            BT.Wait(2_000),
            BT.WaitUntilOnExplorable(timeout_ms=30_000),

            BT.Move(Vec2f(2240, -3535), pause_on_combat=True),
            BT.Move(Vec2f(227, -5658), pause_on_combat=True),
            BT.Move(Vec2f(-1144, -4378), pause_on_combat=True),
            BT.Move(Vec2f(-2058, -3494), pause_on_combat=True),
            BT.Move(Vec2f(-1422.47, 1810.77), pause_on_combat=True),
            BT.Move(Vec2f(-1725, -2551), pause_on_combat=True),

            BT.MoveAndInteractWithGadget(
                Vec2f(-4725, -1830),
                pause_on_combat=True,
                log=True,
            ),
            BT.Wait(2_000),

            BT.MoveAndInteractWithGadget(
                Vec2f(-1725, -2550),
                pause_on_combat=True,
                log=True,
            ),
            BT.Wait(1_500),
            BT.InteractWithGadgetAtXY(
                Vec2f(-1725, -2550),
            ),

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
            BT.Wait(2_000),
            BT.InteractWithGadgetAtXY(
                Vec2f(-1731, -4138),
            ),

            BT.Move(Vec2f(-2331, -419), pause_on_combat=True),
            BT.Wait(10_000),
            BT.Move(Vec2f(-276.01, -1219.04), pause_on_combat=True),
            BT.Move(Vec2f(-1685, 1459), pause_on_combat=True),
            BT.Move(Vec2f(-2895, -6247), pause_on_combat=True),
            BT.Move(Vec2f(-3938, -6315), pause_on_combat=True),

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
                EMBARK_BEACH,
                name="Random Travel - Reward",
            ),
            BT.MoveAndDialog(
                Vec2f(-749.00, -3262.00),
                DIALOG_ZAISHEN_MISSION_REWARD,
                log=True,
            ),
        ],
    )


def UnlockXunlai() -> BehaviorTree:
    return BT.Sequence(
        name="Unlock Xunlai Storage",
        children=[
            BT.Move(
                [
                    Vec2f(220.88, -3018.91),
                ],
                pause_on_combat=False,
            ),
            BT.MoveAndDialogByModelID(
                XUNLAI_AGENT_MODEL_ID,
                DIALOG_XUNLAI_1,
                log=True,
            ),
            BT.TargetAndDialogByModelID(
                XUNLAI_AGENT_MODEL_ID,
                DIALOG_XUNLAI_2,
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
                profession_key="reroll_primary_profession",
                timeout_ms=60_000,
            ),
            BT.Wait(3_000),
            BT.ResetActionQueues(),
        ],
    )


def RunChahbek() -> BehaviorTree:
    return BT.Sequence(
        name="Run Chahbek Village ZM",
        children=[
            SkipTutorialDialog(),
            TakeZaishenMission(),
            TravelToChahbek(),
            MeetingFirstSpearJahdugar(),
            ConfigureFirstBattle(),
            EnterChahbekMission(),
            TakeReward(),
            UnlockXunlai(),
            DepositRewards(),
            RerollCharacter(),
        ],
    )


def get_execution_steps() -> list[tuple[str, Callable[[], BehaviorTree]]]:
    return [
        ("Initialize Bot", InitializeBot),
        ("Run Chahbek", RunChahbek),
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
