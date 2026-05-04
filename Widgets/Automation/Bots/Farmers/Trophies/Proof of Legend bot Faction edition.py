from __future__ import annotations

from typing import Callable

from Py4GWCoreLib import Map, Player, UIManager
from Py4GWCoreLib.BottingTree import BottingTree
from Py4GWCoreLib.Quest import Quest
from Py4GWCoreLib.py4gwcorelib_src.BehaviorTree import BehaviorTree
from Py4GWCoreLib.routines_src.BehaviourTrees import BT as RoutinesBT
from Py4GWCoreLib.native_src.internals.types import Vec2f
from Sources.ApoSource.ApoBottingLib import wrappers as BT


MODULE_NAME = "Proof of Legend bot Faction edition by Wick Divinus"
MODULE_ICON = "Textures\\Module_Icons\\Leveler - Factions.png"

KAINENG_CENTER_MAP_ID = 194

initialized = False
botting_tree: BottingTree | None = None


def V(x: float, y: float) -> Vec2f:
    return Vec2f(float(x), float(y))


def LongMove(points: Vec2f | list[Vec2f], timeout_ms: int = 60000) -> BehaviorTree:
    path = points if isinstance(points, list) else [points]
    return Sequence(
        "Long Timeout Move",
        [
            RoutinesBT.Movement.Move(
                x=point.x,
                y=point.y,
                tolerance=75.0,
                timeout_ms=timeout_ms,
                pause_on_combat=True,
                log=False,
            )
            for point in path
        ],
    )


def map_id(name: str) -> int:
    return Map.GetMapIDByName(name)


def Action(name: str, action_fn: Callable[[], object], aftercast_ms: int = 250) -> BehaviorTree:
    def _run() -> BehaviorTree.NodeState:
        result = action_fn()
        if result is False:
            return BehaviorTree.NodeState.FAILURE
        return BehaviorTree.NodeState.SUCCESS

    return BehaviorTree(
        BehaviorTree.ActionNode(
            name=name,
            action_fn=_run,
            aftercast_ms=aftercast_ms,
        )
    )


def Sequence(name: str, children: list[BehaviorTree | BehaviorTree.Node]) -> BehaviorTree:
    return BehaviorTree(
        BehaviorTree.SequenceNode(
            name=name,
            children=children,
        )
    )


def OptionalTree(name: str, tree: BehaviorTree | BehaviorTree.Node) -> BehaviorTree:
    return BehaviorTree(
        BehaviorTree.SelectorNode(
            name=name,
            children=[
                tree,
                BehaviorTree.SucceederNode(name=f"{name} Fallback"),
            ],
        )
    )
def ensure_botting_tree() -> BottingTree:
    global botting_tree

    if botting_tree is None:
        botting_tree = BottingTree.Create(
            MODULE_NAME,
            main_routine=get_execution_steps(),
            routine_name="Factions Leveler Sequence",
            repeat=True,
            reset=False,
            configure_fn=lambda tree: tree.Config.ConfigureUpkeepTrees(
                disable_looting=True,
                restore_isolation_on_stop=True,
                enable_outpost_imp_service=True,
                enable_explorable_imp_service=True,
                imp_log=False,
                enable_party_wipe_recovery=True,
            ),
        )

    return botting_tree
def AddHenchmen() -> BehaviorTree:
    def _build_henchmen_tree(_node: BehaviorTree.Node) -> BehaviorTree:
        party_size = Map.GetMaxPartySize()
        current_map_id = Map.GetMapID()

        if party_size <= 4:
            henchmen_list = [1, 2, 3]
        elif current_map_id == map_id("Seitung Harbor"):
            henchmen_list = [2, 3, 1, 6, 5]
        elif current_map_id == 213:
            henchmen_list = [2, 3, 1, 8, 5]
        elif current_map_id == map_id("The Marketplace"):
            henchmen_list = [6, 9, 5, 1, 4, 7, 3]
        elif Map.IsMapIDMatch(current_map_id, KAINENG_CENTER_MAP_ID):
            henchmen_list = [2, 10, 4, 8, 7, 9, 12]
        elif current_map_id == map_id("Boreal Station"):
            henchmen_list = [7, 9, 2, 3, 4, 6, 5]
        else:
            henchmen_list = [2, 3, 5, 6, 7, 9, 10]

        return Sequence(
            "Add Henchmen",
            [
                BT.AddHenchmanList(henchmen_list),
                BT.Wait(1000),
            ],
        )

    return BehaviorTree(
        BehaviorTree.SubtreeNode(
            name="Add Henchmen",
            subtree_fn=_build_henchmen_tree,
        )
    )


def EquipStarterWeapon() -> BehaviorTree:
    equip_tree = Sequence(
        "Equip Starter Weapon",
        [
            BT.StoreProfessionNames(),
            BehaviorTree.SwitchNode(
                name="EquipStarterWeaponByProfession",
                selector_fn=lambda node: node.blackboard.get("player_primary_profession_name", ""),
                cases=[
                    ("Assassin", lambda: BT.EquipItemByModelID(6387)),
                    ("Elementalist", lambda: BT.EquipItemByModelID(2724)),
                    ("Mesmer", lambda: BT.EquipItemByModelID(2652)),
                    ("Monk", lambda: BT.EquipItemByModelID(2787)),
                    ("Necromancer", lambda: BT.EquipItemByModelID(2694)),
                    ("Ranger", lambda: BT.EquipItemByModelID(477)),
                    ("Ritualist", lambda: BT.EquipItemByModelID(6498)),
                    ("Warrior", lambda: BT.EquipItemByModelID(2982)),
                ],
                default_case=BehaviorTree.FailerNode(name="UnknownStarterWeaponProfession"),
            ),
        ],
    )
    return OptionalTree("Equip Starter Weapon", equip_tree)


def EquipSkillBar() -> BehaviorTree:
    def _level_bucket() -> str:
        level = Player.GetLevel()
        if level < 3:
            return "starter"
        if level < 20:
            return "leveling"
        return "final"

    return Sequence(
        "Equip Skill Bar",
        [
            BT.StoreProfessionNames(),
            BehaviorTree.SwitchNode(
                name="EquipSkillBarByProfessionAndLevel",
                selector_fn=lambda node: (
                    node.blackboard.get("player_primary_profession_name", ""),
                    _level_bucket(),
                ),
                cases=[
                    (("Warrior", "starter"), lambda: BT.LoadSkillbar("OQAAAAAAAAAAAAAA")),
                    (("Ranger", "starter"), lambda: BT.LoadSkillbar("OgAAAAAAAAAAAAAA")),
                    (("Monk", "starter"), lambda: BT.LoadSkillbar("OwAAAAAAAAAAAAAA")),
                    (("Necromancer", "starter"), lambda: BT.LoadSkillbar("OABAAAAAAAAAAAAA")),
                    (("Mesmer", "starter"), lambda: BT.LoadSkillbar("OQBAAAAAAAAAAAAA")),
                    (("Elementalist", "starter"), lambda: BT.LoadSkillbar("OgBAAAAAAAAAAAAA")),
                    (("Ritualist", "starter"), lambda: BT.LoadSkillbar("OACAAAAAAAAAAAAA")),
                    (("Assassin", "starter"), lambda: BT.LoadSkillbar("OwBAAAAAAAAAAAAA")),
                    (("Warrior", "leveling"), lambda: BT.LoadSkillbar("OQUBIskDcdG0DaAKUECA")),
                    (("Ranger", "leveling"), lambda: BT.LoadSkillbar("OgUBIskDcdG0DaAKUECA")),
                    (("Monk", "leveling"), lambda: BT.LoadSkillbar("OwUBIskDcdG0DaAKUECA")),
                    (("Necromancer", "leveling"), lambda: BT.LoadSkillbar("OAVBIskDcdG0DaAKUECA")),
                    (("Mesmer", "leveling"), lambda: BT.LoadSkillbar("OQBBIskDcdG0DaAKUECA")),
                    (("Elementalist", "leveling"), lambda: BT.LoadSkillbar("OgVBIskDcdG0DaAKUECA")),
                    (("Ritualist", "leveling"), lambda: BT.LoadSkillbar("OAWBIskDcdG0DaAKUECA")),
                    (("Assassin", "leveling"), lambda: BT.LoadSkillbar("OAWBIskDcdG0DaAKUECA")),
                    (("Warrior", "final"), lambda: BT.LoadSkillbar("OQUCErwSOw1ZQPoBoQRIA")),
                    (("Ranger", "final"), lambda: BT.LoadSkillbar("OgUCErwSOw1ZQPoBoQRIA")),
                    (("Monk", "final"), lambda: BT.LoadSkillbar("OwUCErwSOw1ZQPoBoQRIA")),
                    (("Necromancer", "final"), lambda: BT.LoadSkillbar("OAVCErwSOw1ZQPoBoQRIA")),
                    (("Mesmer", "final"), lambda: BT.LoadSkillbar("OQBCErwSOw1ZQPoBoQRIA")),
                    (("Elementalist", "final"), lambda: BT.LoadSkillbar("OgVCErwSOw1ZQPoBoQRIA")),
                    (("Ritualist", "final"), lambda: BT.LoadSkillbar("OAWCErwSOw1ZQPoBoQRIA")),
                    (("Assassin", "final"), lambda: BT.LoadSkillbar("OwVCErwSOw1ZQPoBoQRIA")),
                ],
                default_case=BehaviorTree.FailerNode(name="UnknownSkillBarProfessionOrLevel"),
            ),
        ],
    )


def PrepareForBattle() -> BehaviorTree:
    bot = ensure_botting_tree()
    return Sequence(
            "Prepare For Battle",
            [
                bot.Config.Aggressive(
                    auto_loot=False,
                ),
                EquipStarterWeapon(),
            EquipSkillBar(),
            BT.LeaveParty(),
            AddHenchmen(),
        ],
    )


def QuestDialog(
    name: str,
    pos: Vec2f,
    dialog_id: int,
    quest_id: int | None = None,
    mode: str = "action",
    wait_ms: int = 500,
    target_distance: float = 200.0,
) -> BehaviorTree:
    def _quest_state_matches() -> BehaviorTree.NodeState:
        if quest_id is None or mode == "action":
            return BehaviorTree.NodeState.SUCCESS
        active_quest = Quest.GetActiveQuest()
        if mode == "accept":
            return BehaviorTree.NodeState.SUCCESS if active_quest == quest_id else BehaviorTree.NodeState.FAILURE
        if mode == "complete":
            return BehaviorTree.NodeState.SUCCESS if active_quest != quest_id else BehaviorTree.NodeState.FAILURE
        return BehaviorTree.NodeState.SUCCESS

    def _cancel_skill_reward_window() -> BehaviorTree.NodeState:
        cancel_button_frame_id = UIManager.GetFrameIDByHash(784833442)
        if cancel_button_frame_id and UIManager.FrameExists(cancel_button_frame_id):
            UIManager.FrameClick(cancel_button_frame_id)
        return BehaviorTree.NodeState.SUCCESS

    attempt = Sequence(
        f"{name} Attempt",
        [
            BT.MoveAndDialog(pos, dialog_id=dialog_id, target_distance=target_distance),
            BT.Wait(wait_ms),
            BehaviorTree.ActionNode(
                name=f"{name} Cancel Skill Reward Window",
                action_fn=_cancel_skill_reward_window,
                aftercast_ms=500,
            ),
            BehaviorTree.ConditionNode(
                name=f"{name} Result",
                condition_fn=_quest_state_matches,
            ),
        ],
    )

    return BehaviorTree(
        BehaviorTree.RepeaterUntilSuccessNode(
            attempt.root,
            timeout_ms=30000,
            name=name,
        )
    )


def EnterChallenge() -> BehaviorTree:
    return Sequence(
        "Enter Challenge",
        [
            Action("Click Enter Challenge", Map.EnterChallenge, aftercast_ms=500),
            BT.WaitUntilOnExplorable(timeout_ms=60000),
        ],
    )


def SendDialog(dialog_id: int, name: str | None = None) -> BehaviorTree:
    return Action(
        name or f"Send Dialog {hex(dialog_id)}",
        lambda: Player.SendDialog(dialog_id),
        aftercast_ms=500,
    )


def InitializeBot() -> BehaviorTree:
    return Sequence(
        "Initialize Bot",
        [
            BT.ResetActionQueues(),
        ],
    )


def Exit_Monastery_Overlook() -> BehaviorTree:
    return Sequence(
        "Exit Monastery Overlook",
        [
            BT.MoveAndDialog(V(-7048, 5817), dialog_id=0x85),
            BT.WaitForMapLoad(map_id=map_id("Shing Jea Monastery")),
        ],
    )


def Unlock_Secondary_Profession() -> BehaviorTree:
    bot = ensure_botting_tree()
    return Sequence(
        "Unlock Secondary Profession",
        [
            BT.Travel(random_travel=True, target_map_name="Shing Jea Monastery"),
            bot.Config.Pacifist(),
            BT.MoveAndExitMap(V(-3480, 9460), target_map_name="Linnok Courtyard"),
            BT.Move(V(-159, 9174)),
            BT.StoreProfessionNames(),
            BehaviorTree.SwitchNode(
                name="AcceptSecondaryProfessionByPrimary",
                selector_fn=lambda node: node.blackboard.get("player_primary_profession_name", ""),
                cases=[
                    ("Mesmer", lambda: QuestDialog("Accept - Choose Your Secondary Profession", V(-92, 9217), 0x813D08, quest_id=317, mode="accept")),
                ],
                default_case=QuestDialog("Accept - Choose Your Secondary Profession", V(-92, 9217), 0x813D0E, quest_id=317, mode="accept").root,
            ),
            QuestDialog("Complete - Choose Your Secondary Profession", V(-92, 9217), 0x813D07, quest_id=317, mode="complete", wait_ms=3000),
            BT.Wait(3000),
            QuestDialog("Accept - A Formal Introduction", V(-92, 9217), 0x813E01, quest_id=318, mode="accept"),
            BT.MoveAndExitMap(V(-3762, 9471), target_map_name="Shing Jea Monastery"),
        ],
    )


def Unlock_Xunlai_Storage() -> BehaviorTree:
    unlock_attempt = Sequence(
        "Unlock Xunlai Storage",
        [
            BT.Move([
                V(-4958, 9472),
                V(-5465, 9727),
                V(-4791, 10140),
                V(-3945, 10328),
                V(-3825.09, 10386.81),
            ]),
            BT.MoveAndDialog(V(-3825.09, 10386.81), dialog_id=0x84),
        ],
    )
    return OptionalTree("Unlock Xunlai Storage", unlock_attempt)


def To_Minister_Chos_Estate() -> BehaviorTree:
    bot = ensure_botting_tree()
    return Sequence(
        "To Minister Cho's Estate",
        [
            BT.Travel(random_travel=True, target_map_name="Shing Jea Monastery"),
            BT.MoveAndExitMap(V(-14961, 11453), target_map_name="Sunqua Vale"),
            bot.Config.Pacifist(),
            BT.Move([V(16182.62, -7841.86), V(6611.58, 15847.51)]),
            QuestDialog("Step 1 - A Formal Introduction", V(6637, 16147), 0x80000B),
            BT.WaitForMapLoad(map_id=214),
            QuestDialog("Complete - A Formal Introduction", V(7884, -10029), 0x813E07, quest_id=318, mode="complete"),
        ],
    )


def Unlock_Skills_Trainer() -> BehaviorTree:
    return Sequence(
        "Unlock Skills Trainer",
        [
            BT.Travel(random_travel=True, target_map_name="Shing Jea Monastery"),
            BT.MoveAndDialog(V(-8790.00, 10366.00), dialog_id=0x84),
            BT.Wait(3000),
            RoutinesBT.Player.BuySkill(57),
            BT.Wait(250),
            RoutinesBT.Player.BuySkill(25),
            BT.Wait(250),
            RoutinesBT.Player.BuySkill(860),
        ],
    )


def Minister_Chos_Estate_Mission() -> BehaviorTree:
    bot = ensure_botting_tree()
    return Sequence(
        "Minister Cho's Estate Mission",
        [
            BT.Travel(random_travel=True, target_map_id=214),
            PrepareForBattle(),
            EnterChallenge(),
            LongMove([V(6220.76, -7360.73), V(5523.95, -7746.41)]),
            BT.Wait(15000),
            LongMove(V(591.21, -9071.10)),
            BT.Wait(30000),
            LongMove([V(4889, -5043), V(4268.49, -3621.66)]),
            BT.Wait(20000),
            LongMove([V(6216, -1108), V(2617, 642), V(1706.90, 1711.44)]),
            BT.Wait(30000),
            LongMove([V(333.32, 1124.44), V(-3337.14, -4741.27)]),
            BT.Wait(35000),
            bot.Config.Aggressive(
                auto_loot=False,
            ),
            LongMove([
                V(-4661.99, -6285.81),
                V(-7454, -7384),
                V(-9138, -4191),
                V(-7109, -25),
                V(-7443, 2243),
            ]),
            BT.Wait(5000),
            LongMove(V(-16924, 2445)),
            BT.MoveAndInteract(V(-17031, 2448)),
            BT.WaitForMapLoad(map_id=251, timeout_ms=60000),
        ],
    )


def Deposit_Proof_Of_Legend() -> BehaviorTree:
    return Sequence(
        "Deposit Proof of Legend",
        [
            BT.Travel(random_travel=True, target_map_id=251),
            BT.DepositModelToStorage(37841),
            BT.DepositGoldKeep(0),
        ],
    )


def LogoutAndDeleteState() -> BehaviorTree:
    return Sequence(
        "Reroll: Logout > Delete > Recreate",
        [
            BT.StoreRerollContext(
                campaign_name="Factions",
                fallback_profession="Warrior",
            ),
            BT.DeleteCharacterFromBlackboard(
                character_name_key="reroll_character_name",
                timeout_ms=45000,
            ),
            BT.ResolveRerollNewCharacterName(
                character_name_key="reroll_character_name",
                new_character_name_key="reroll_new_character_name",
            ),
            BT.CreateCharacterFromBlackboard(
                character_name_key="reroll_new_character_name",
                campaign_key="reroll_campaign",
                profession_key="reroll_primary_profession",
                timeout_ms=60000,
            ),
            BT.Wait(3000),
            BT.ResetActionQueues(),
        ],
    )


def get_execution_steps() -> list[tuple[str, Callable[[], BehaviorTree]]]:
    return [
        ("Initialize Bot", InitializeBot),
        ("Exit Monastery Overlook", Exit_Monastery_Overlook),
        ("Unlock Secondary Profession", Unlock_Secondary_Profession),
        ("Unlock Xunlai Storage", Unlock_Xunlai_Storage),
        ("To Minister Cho's Estate", To_Minister_Chos_Estate),
        ("Unlock Skills Trainer", Unlock_Skills_Trainer),
        ("Minister Cho's Estate Mission", Minister_Chos_Estate_Mission),
        ("Deposit Proof Of Legend", Deposit_Proof_Of_Legend),
        ("Reroll: Logout > Delete > Recreate", LogoutAndDeleteState),
    ]


def main() -> None:
    global initialized

    if not initialized:
        ensure_botting_tree()
        initialized = True

    tree = ensure_botting_tree()
    tree.tick()
    tree.UI.draw_window()


if __name__ == "__main__":
    main()
