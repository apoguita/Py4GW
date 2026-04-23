from __future__ import annotations

import time
from typing import Callable

import PyImGui

from Py4GWCoreLib.BottingTree import BottingTree
from Py4GWCoreLib.IniManager import IniManager
from Py4GWCoreLib.py4gwcorelib_src.BehaviorTree import BehaviorTree
from Py4GWCoreLib.routines_src.BehaviourTrees import BT as RoutinesBT
from Py4GWCoreLib.native_src.internals.types import Vec2f
from Py4GWCoreLib.enums_src.Model_enums import ModelID
from Py4GWCoreLib.Player import Player
from Sources.ApoSource.ApoBottingLib import wrappers as BT
from Py4GWCoreLib.enums_src.GameData_enums import Range


MODULE_NAME = "Chahbek Farmer"
INI_PATH = "Widgets/Automation/Bots/Templates"
INI_FILENAME = "ChahbekFarmer.ini"
NEHDUKAH_ENC_STRING = "\\x8101\\x246C\\xFDB5\\xB6AD\\x56AB"

initialized = False
ini_key = ""
botting_tree: BottingTree | None = None
selected_start_index = 0


def PartyWipeRecoveryService() -> BehaviorTree:
    state = {
        "active": False,
        "step_name": "",
        "last_return_ms": 0.0,
        "last_log_ms": 0.0,
    }

    def _reset_state(node: BehaviorTree.Node) -> None:
        state["active"] = False
        state["step_name"] = ""
        state["last_return_ms"] = 0.0
        state["last_log_ms"] = 0.0
        node.blackboard["party_wipe_recovery_active"] = False

    def _tick_party_wipe_service(node: BehaviorTree.Node) -> BehaviorTree.NodeState:
        from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE
        from Py4GWCoreLib.Map import Map
        from Py4GWCoreLib.routines_src.Checks import Checks
        from Py4GWCoreLib.py4gwcorelib_src.ActionQueue import ActionQueueManager

        now = time.monotonic() * 1000.0
        is_wiped = bool(Checks.Party.IsPartyWiped() or GLOBAL_CACHE.Party.IsPartyDefeated())

        if not state["active"]:
            if not is_wiped:
                node.blackboard["party_wipe_recovery_active"] = False
                return BehaviorTree.NodeState.RUNNING

            step_name = str(node.blackboard.get("current_step_name", "") or "")
            if not step_name:
                step_name = get_execution_steps()[0][0]

            state["active"] = True
            state["step_name"] = step_name
            state["last_return_ms"] = 0.0
            state["last_log_ms"] = now
            node.blackboard["party_wipe_recovery_active"] = True
            node.blackboard["party_wipe_recovery_step_name"] = step_name
            ActionQueueManager().ResetAllQueues()
            return BehaviorTree.NodeState.RUNNING

        node.blackboard["party_wipe_recovery_active"] = True
        node.blackboard["party_wipe_recovery_step_name"] = state["step_name"]

        if Map.IsMapReady() and Map.IsOutpost() and GLOBAL_CACHE.Party.IsPartyLoaded():
            node.blackboard["restart_step_name_request"] = state["step_name"]
            _reset_state(node)
            return BehaviorTree.NodeState.SUCCESS

        if now - state["last_return_ms"] >= 1000.0:
            GLOBAL_CACHE.Party.ReturnToOutpost()
            state["last_return_ms"] = now

        return BehaviorTree.NodeState.RUNNING

    return BehaviorTree(
        BehaviorTree.ActionNode(
            name="PartyWipeRecoveryService",
            action_fn=_tick_party_wipe_service,
            aftercast_ms=0,
        )
    )


def configure_upkeep_trees(tree: BottingTree) -> BottingTree:
    tree.DisableLooting()
    tree.SetRestoreIsolationOnStop(True)
    tree.SetUpkeepTrees([
        (
            "OutpostImpService",
            lambda: RoutinesBT.Upkeepers.OutpostImpService(
                target_bag=1,
                slot=0,
                log=False,
            ),
        ),
        (
            "ExplorableImpService",
            lambda: RoutinesBT.Upkeepers.ExplorableImpService(
                log=False,
            ),
        ),
        (
            "PartyWipeRecoveryService",
            PartyWipeRecoveryService,
        ),
    ])
    return tree


def ensure_botting_tree() -> BottingTree:
    global botting_tree

    if botting_tree is None:
        botting_tree = configure_upkeep_trees(BottingTree())

    return botting_tree


def ConfigurePacifistEnv() -> BehaviorTree:
    return BehaviorTree(
        BehaviorTree.SequenceNode(
            name="Configure Pacifist Env",
            children=[
                BottingTree.DisableHeroAITree(),
                BottingTree.DisableLootingTree(),
            ],
        )
    )


def ConfigureAggressiveEnv() -> BehaviorTree:
    return BehaviorTree(
        BehaviorTree.SequenceNode(
            name="Configure Aggressive Env",
            children=[
                BottingTree.EnableHeroAITree(),
                BottingTree.DisableLootingTree(),
            ],
        )
    )


def Skip_Tutorial() -> BehaviorTree:
    return BehaviorTree(
        BehaviorTree.SequenceNode(
            name="Skip Tutorial",
            children=[
                BT.MoveAndDialog(Vec2f(10289, 6405), dialog_id=0x82A501),
                BT.LeaveGH(),
                BT.WaitForMapLoad(map_id=544),
            ],
        )
    )


def Into_Chahbek_Village() -> BehaviorTree:
    return BehaviorTree(
        BehaviorTree.SequenceNode(
            name="Quest: Into Chahbek Village",
            children=[
                BT.TravelToOutpost(544),
                BT.MoveAndDialog(Vec2f(3493, -5247), dialog_id=0x82A507),
                BT.MoveAndDialog(Vec2f(3493, -5247), dialog_id=0x82C501),
                BT.OpenHero(),
                BT.Wait(100),
                BT.OpenSkillsAndAttributes(),
                BT.Wait(100),
            ],
        )
    )


def Quiz_the_Recruits() -> BehaviorTree:
    return BehaviorTree(
        BehaviorTree.SequenceNode(
            name="Quest: Quiz the Recruits",
            children=[
                BT.TravelToOutpost(544),
                BT.Move(Vec2f(4750, -6105)),
                BT.MoveAndDialog(Vec2f(4750, -6105), dialog_id=0x82C504),
                BT.MoveAndDialog(Vec2f(5019, -6940), dialog_id=0x82C504),
                BT.MoveAndDialog(Vec2f(3540, -6253), dialog_id=0x82C504),
                BT.MoveAndDialog(Vec2f(3485, -5246), dialog_id=0x82C507),
            ],
        )
    )


def PrepareForBattle(hero_list: list[int] | None = None, henchman_list: list[int] | None = None) -> BehaviorTree:
    return BehaviorTree(
        BehaviorTree.SequenceNode(
            name="PrepareForBattle",
            children=[
                ConfigureAggressiveEnv(),
                EquipSkillBar(),
                BT.LeaveParty(),
                BT.AddHeroList(hero_list or []),
                BT.AddHenchmanList(henchman_list or []),
            ],
        )
    )


def Equip_Weapon() -> BehaviorTree:
    return BehaviorTree(
        BehaviorTree.SequenceNode(
            name="Equip Weapon",
            children=[
                BT.StoreProfessionNames(),
                BehaviorTree.SwitchNode(
                    name="EquipStarterWeaponByProfession",
                    selector_fn=lambda node: node.blackboard.get("player_primary_profession_name", ""),
                    cases=[
                        ("Dervish", lambda: BT.EquipItemByModelID(15591)),
                        ("Paragon", lambda: BT.EquipItemByModelID(15593)),
                        ("Elementalist", lambda: BT.EquipItemByModelID(2742)),
                        ("Mesmer", lambda: BT.EquipItemByModelID(2652)),
                        ("Necromancer", lambda: BT.EquipItemByModelID(2694)),
                        ("Ranger", lambda: BT.EquipItemByModelID(477)),
                        ("Warrior", lambda: BT.EquipItemByModelID(2982)),
                        ("Monk", lambda: BT.EquipItemByModelID(2787)),
                    ],
                    default_case=BehaviorTree.FailerNode(name="UnknownStarterWeaponProfession"),
                ),
            ],
        )
    )


def Never_Fight_Alone() -> BehaviorTree:
    return BehaviorTree(
        BehaviorTree.SequenceNode(
            name="Quest: Never Fight Alone",
            children=[
                BT.TravelToOutpost(544),
                PrepareForBattle(hero_list=[6], henchman_list=[1, 2]),
                BT.SpawnAndDestroyBonusItems(
                    exclude_list=[ModelID.Igneous_Summoning_Stone.value],
                ),
                Equip_Weapon(),
                BT.MoveAndDialog(Vec2f(3433, -5900), dialog_id=0x82C701),
                BT.MoveAndDialog(Vec2f(3433, -5900), dialog_id=0x82C707),
            ],
        )
    )


def Chahbek_Village_Mission() -> BehaviorTree:
    return BehaviorTree(
        BehaviorTree.SequenceNode(
            name="Chahbek Village Mission",
            children=[
                BT.TravelToOutpost(544),
                BT.LoadHeroSkillbar(1, "OQASEF6EC1vcNABWAAAA"),
                BT.MoveAndDialog(Vec2f(3485, -5246), dialog_id=0x81),
                BT.MoveAndDialog(Vec2f(3485, -5246), dialog_id=0x84),
                BT.Wait(2000),
                BT.WaitUntilOnExplorable(),
                ConfigureAggressiveEnv(),
                BT.Move(Vec2f(2240, -3535)),
                BT.Move(Vec2f(227, -5658)),
                BT.Move(Vec2f(-1144, -4378)),
                BT.Move(Vec2f(-2058, -3494)),
                BT.Move(Vec2f(-4725, -1830)),
                BT.InteractWithGadgetAtXY(Vec2f(-4725, -1830)),
                BT.Move(Vec2f(-1725, -2551)),
                BT.InteractWithGadgetAtXY(Vec2f(-1725, -2550)),
                BT.Wait(1500),
                BT.InteractWithGadgetAtXY(Vec2f(-1725, -2550)),
                BT.Move(Vec2f(-4725, -1830)),
                BT.InteractWithGadgetAtXY(Vec2f(-4725, -1830)),
                BT.Move(Vec2f(-1731, -4138)),
                BT.InteractWithGadgetAtXY(Vec2f(-1731, -4138)),
                BT.Wait(2000),
                BT.InteractWithGadgetAtXY(Vec2f(-1731, -4138)),
                BT.MoveAndKill(Vec2f(-2331, -419)),
                BT.MoveAndKill(Vec2f(-1685, 1459)),
                BT.MoveAndKill(Vec2f(-2895, -6247)),
                BT.MoveAndKill(Vec2f(-3938, -6315)),
                BT.WaitForMapToChange(map_id=456),
            ],
        )
    )


def Chahbek_Village_Mission_2() -> BehaviorTree:
    return BehaviorTree(
        BehaviorTree.SequenceNode(
            name="Chahbek Village Mission_2",
            children=[
                BT.TravelToOutpost(544),
                PrepareForBattle(hero_list=[6], henchman_list=[1, 2]),
                BT.LoadHeroSkillbar(1, "OQASEF6EC1vcNABWAAAA"),
                BT.MoveAndDialog(Vec2f(3485, -5246), dialog_id=0x81),
                BT.MoveAndDialog(Vec2f(3485, -5246), dialog_id=0x84),
                BT.Wait(2000),
                BT.WaitUntilOnExplorable(),
                ConfigureAggressiveEnv(),
                BT.Move(Vec2f(2240, -3535)),
                BT.Move(Vec2f(227, -5658)),
                BT.Move(Vec2f(-1144, -4378)),
                BT.Move(Vec2f(-2058, -3494)),
                BT.Move(Vec2f(-4725, -1830)),
                BT.InteractWithGadgetAtXY(Vec2f(-4725, -1830)),
                BT.Move(Vec2f(-1725, -2551)),
                BT.InteractWithGadgetAtXY(Vec2f(-1725, -2550)),
                BT.Wait(1500),
                BT.InteractWithGadgetAtXY(Vec2f(-1725, -2550)),
                BT.Move(Vec2f(-4725, -1830)),
                BT.InteractWithGadgetAtXY(Vec2f(-4725, -1830)),
                BT.Move(Vec2f(-1731, -4138)),
                BT.InteractWithGadgetAtXY(Vec2f(-1731, -4138)),
                BT.Wait(2000),
                BT.InteractWithGadgetAtXY(Vec2f(-1731, -4138)),
                BT.Move(Vec2f(-2331, -419)),
                BT.Move(Vec2f(-1685, 1459)),
                BT.Move(Vec2f(-2895, -6247)),
                BT.Move(Vec2f(-3938, -6315)),
                BT.WaitForMapToChange(map_id=456, timeout_ms=60000),
            ],
        )
    )


def Get_Skills() -> BehaviorTree:
    def _skill_route(dialog_pos: Vec2f, return_to_trainer: bool = False) -> BehaviorTree:
        children = [
            BT.Move(dialog_pos),
            BT.DialogAtXY(dialog_pos, dialog_id=0x7F, target_distance=100.0),
        ]
        if return_to_trainer:
            children.append(BT.Move(Vec2f(-12200, 473)))
        return BehaviorTree(
            BehaviorTree.SequenceNode(
                name="GetProfessionSkillsRoute",
                children=children,
            )
        )

    return BehaviorTree(
        BehaviorTree.SequenceNode(
            name="Get Skills",
            children=[
                ConfigurePacifistEnv(),
                BT.StoreProfessionNames(),
                BehaviorTree.SwitchNode(
                    name="GetSkillsByProfession",
                    selector_fn=lambda node: node.blackboard.get("player_primary_profession_name", ""),
                    cases=[
                        ("Dervish", lambda: _skill_route(Vec2f(-12107, -705), return_to_trainer=True)),
                        ("Paragon", lambda: _skill_route(Vec2f(-10724, -3364), return_to_trainer=True)),
                        ("Elementalist", lambda: _skill_route(Vec2f(-12011, -639), return_to_trainer=True)),
                        ("Mesmer", lambda: _skill_route(Vec2f(-7149, 1830))),
                        ("Necromancer", lambda: _skill_route(Vec2f(-6557, 1837))),
                        ("Ranger", lambda: _skill_route(Vec2f(-9498, 1426), return_to_trainer=True)),
                        ("Warrior", lambda: _skill_route(Vec2f(-9663, 1506), return_to_trainer=True)),
                        ("Monk", lambda: _skill_route(Vec2f(-11658, -1414), return_to_trainer=True)),
                    ],
                    default_case=BehaviorTree.FailerNode(name="UnknownGetSkillsProfession"),
                ),
            ],
        )
    )


def Primary_Training() -> BehaviorTree:
    return BehaviorTree(
        BehaviorTree.SequenceNode(
            name="Quest: Primary Training",
            children=[
                BT.MoveAndDialog(Vec2f(-7234.90, 4793.62), dialog_id=0x825801),
                Get_Skills(),
                BT.MoveAndDialog(Vec2f(-7234.90, 4793.62), dialog_id=0x825807),
                BT.CancelSkillRewardWindow(),
            ],
        )
    )


def A_Personal_Vault() -> BehaviorTree:
    return BehaviorTree(
        BehaviorTree.SequenceNode(
            name="Quest: A Personal Vault",
            children=[
                BT.TravelToRandomDistrict(target_map_id=449),
                BT.MoveAndDialog(Vec2f(-9251, 11826), dialog_id=0x82A101),
                BT.MoveAndDialog(Vec2f(-7761, 14393), dialog_id=0x84),
                BT.MoveAndDialog(Vec2f(-9251, 11826), dialog_id=0x82A107),
            ],
        )
    )


def Material_Girl() -> BehaviorTree:
    return BehaviorTree(
        BehaviorTree.SequenceNode(
            name="Quest: Material Girl",
            children=[
                BT.TravelToRandomDistrict(target_map_id=449),
                BT.Move(Vec2f(-10839.96, 9197.05)),
                BT.MoveAndDialog(Vec2f(-11363, 9066), dialog_id=0x826101),
                PrepareForBattle(hero_list=[], henchman_list=[1, 3, 4]),
                BT.MoveAndExitMap(Vec2f(-9326, 18151), target_map_id=430),
                ConfigureAggressiveEnv(),
                BT.Move(Vec2f(18460, 1002)),
                BT.MoveAndDialog(Vec2f(18460, 1002), dialog_id=0x85),
                BT.Move(Vec2f(9675, 1038)),
                BT.MoveAndDialog(Vec2f(9282, -1199), dialog_id=0x826104),
                BT.MoveAndKill(Vec2f(9464, -2639),clear_area_radius=Range.Spellcast.value),
                BT.MoveAndKill(Vec2f(11183, -7728),clear_area_radius=Range.Spellcast.value),
                BT.MoveAndKill(Vec2f(9681, -9300),clear_area_radius=Range.Spellcast.value),
                BT.MoveAndKill(Vec2f(7555, -6791),clear_area_radius=Range.Spellcast.value),
                BT.MoveAndKill(Vec2f(5073, -4850),clear_area_radius=Range.Spellcast.value),
                BT.MoveAndDialog(Vec2f(9292, -1220), dialog_id=0x826104),
                BT.MoveAndDialog(Vec2f(-1782, 2790), dialog_id=0x828801),
                BT.Move(Vec2f(-3145, 2412)),
                BT.MoveAndExitMap(Vec2f(-3236, 4503), target_map_id=431),
                BT.Wait(2000),
                BT.TravelToRandomDistrict(target_map_id=449),
                BT.MoveAndDialog(Vec2f(-10024, 8590), dialog_id=0x828804),
                BT.DialogAtXY(Vec2f(-10024, 8590), dialog_id=0x828807),
                BT.MoveAndDialog(Vec2f(-11356, 9066), dialog_id=0x826107),
            ],
        )
    )


def Hog_Hunt() -> BehaviorTree:
    return BehaviorTree(
        BehaviorTree.SequenceNode(
            name="Quest: Hog Hunt",
            children=[
                BT.TravelToRandomDistrict(target_map_id=431),
                PrepareForBattle(hero_list=[], henchman_list=[1, 3, 4]),
                BT.MoveAndExitMap(Vec2f(-3172, 3271), target_map_id=430),
                ConfigureAggressiveEnv(),
                BT.Move(Vec2f(-1840.23, 2432.96)),
                BT.MoveAndDialog(Vec2f(-1297, 3229), dialog_id=0x85),
                BT.Move(Vec2f(-269.29, 1981)),
                BT.Move(Vec2f(-1894.08, 2403.29)),
                BT.Wait(90000),
                BT.MoveAndDialogByModelID(NEHDUKAH_ENC_STRING, dialog_id=0x828D01),
                BT.Move(Vec2f(-6038.05, 2229.41)),
                BT.Move(Vec2f(-10117.84, 3935.15)),
                BT.Move(Vec2f(-12969.55, 9102.46)),
                BT.WaitUntilOnCombat(),
                BT.MoveAndKill(Vec2f(-12743.11, 8789.06), clear_area_radius=Range.Spellcast.value),
                BT.Move(Vec2f(-8175.91, 7331.07)),
                BT.Move(Vec2f(-6762.51, 2301.88)),
                BT.Move(Vec2f(-149.15, 1838.02)),
                BT.Move(Vec2f(-1158.39, 1917.86)),
                BT.MoveAndDialogByModelID(NEHDUKAH_ENC_STRING, dialog_id=0x828D07),
                BT.TravelToRandomDistrict(target_map_id=431),
            ],
        )
    )


def To_Champions_Dawn() -> BehaviorTree:
    return BehaviorTree(
        BehaviorTree.SequenceNode(
            name="To Champion's Dawn",
            children=[
                BT.TravelToRandomDistrict(target_map_id=431),
                PrepareForBattle(hero_list=[], henchman_list=[1, 3, 4]),
                BT.MoveAndExitMap(Vec2f(-3172, 3271), target_map_id=430),
                ConfigureAggressiveEnv(),
                BT.Move(Vec2f(-1840.23, 2432.96)),
                BT.MoveAndDialog(Vec2f(-1297, 3229), dialog_id=0x85),
                BT.Move(Vec2f(-4507, 616)),
                BT.Move(Vec2f(-7611, -5953)),
                BT.Move(Vec2f(-18083, -11907)),
                BT.MoveAndExitMap(Vec2f(-19518, -13021), target_map_id=479),
            ],
        )
    )


def Identity_Theft() -> BehaviorTree:
    return BehaviorTree(
        BehaviorTree.SequenceNode(
            name="Quest: Identity Theft",
            children=[
                BT.TravelToRandomDistrict(target_map_id=449),
                BT.Move(Vec2f(-7519.91, 14468.26)),
                BT.MoveAndDialog(Vec2f(-10461, 15229), dialog_id=0x827201),
                BT.TravelToRandomDistrict(target_map_id=479),
                BT.MoveAndDialog(Vec2f(25345, 8604), dialog_id=0x827204),
                PrepareForBattle(hero_list=[], henchman_list=[1, 6, 7]),
                BT.MoveAndExitMap(Vec2f(22483, 6115), target_map_id=432),
                ConfigureAggressiveEnv(),
                BT.MoveAndDialog(Vec2f(20215, 5285), dialog_id=0x85),
                BT.AddModelToLootWhitelist(15850),
                BT.MoveAndKill(Vec2f(14429, 10337), clear_area_radius=Range.Spellcast.value),
                BT.WaitUntilOutOfCombat(),
                ConfigurePacifistEnv(),
                BT.LootItems(),
                BT.Wait(1000),
                BT.TravelToRandomDistrict(target_map_id=449),
                BT.Move(Vec2f(-7519.91, 14468.26)),
                BT.MoveAndDialog(Vec2f(-10461, 15229), dialog_id=0x827207),
            ],
        )
    )


def Quality_Steel() -> BehaviorTree:
    return BehaviorTree(
        BehaviorTree.SequenceNode(
            name="Quest: Quality Steel",
            children=[
                BT.TravelToRandomDistrict(target_map_id=449),
                BT.MoveAndDialog(Vec2f(-11208, 8815), dialog_id=0x826001),
                BT.TravelToRandomDistrict(target_map_id=431),
                BT.MoveAndDialog(Vec2f(-4076, 5362), dialog_id=0x826004),
                BT.MoveAndDialog(Vec2f(-2866, 7093), dialog_id=0x84),
                PrepareForBattle(hero_list=[], henchman_list=[1, 3, 4]),
                BT.MoveAndExitMap(Vec2f(-3172, 3271), target_map_id=430),
                ConfigureAggressiveEnv(),
                BT.Move(Vec2f(-1840.23, 2432.96)),
                BT.MoveAndDialog(Vec2f(-1297, 3229), dialog_id=0x85),
                BT.Move(Vec2f(-3225, 1749)),
                BT.Move(Vec2f(-995, -2423)),
                BT.MoveAndKill(Vec2f(-513, 67), clear_area_radius=Range.Spellcast.value),
                BT.TravelToRandomDistrict(target_map_id=449),
                BT.MoveAndDialog(Vec2f(-11208, 8815), dialog_id=0x826007),
            ],
        )
    )


def Craft1stWeapon() -> BehaviorTree:
    def _craft_and_equip(output_model_id: int, material_model_id: int) -> BehaviorTree:
        return BehaviorTree(
            BehaviorTree.SequenceNode(
                name=f"CraftAndEquipFirstWeapon({output_model_id})",
                children=[
                    BT.CraftItem(
                        output_model_id=output_model_id,
                        cost=20,
                        trade_model_ids=[material_model_id],
                        quantity_list=[1],
                    ),
                    BT.EquipItemByModelID(output_model_id),
                ],
            )
        )

    return BehaviorTree(
        BehaviorTree.SequenceNode(
            name="Craft 1st Weapon",
            children=[
                BT.StoreProfessionNames(),
                BehaviorTree.SwitchNode(
                    name="CraftFirstWeaponByProfession",
                    selector_fn=lambda node: node.blackboard.get("player_primary_profession_name", ""),
                    cases=[
                        ("Warrior", lambda: _craft_and_equip(16227, ModelID.Iron_Ingot.value)),
                        ("Ranger", lambda: _craft_and_equip(15777, ModelID.Iron_Ingot.value)),
                        ("Paragon", lambda: _craft_and_equip(18711, ModelID.Iron_Ingot.value)),
                        ("Dervish", lambda: _craft_and_equip(16227, ModelID.Iron_Ingot.value)),
                        ("Elementalist", lambda: _craft_and_equip(18896, ModelID.Wood_Plank.value)),
                        ("Mesmer", lambda: _craft_and_equip(18712, ModelID.Iron_Ingot.value)),
                        ("Monk", lambda: _craft_and_equip(18901, ModelID.Wood_Plank.value)),
                        ("Necromancer", lambda: _craft_and_equip(18893, ModelID.Wood_Plank.value)),
                    ],
                    default_case=BehaviorTree.FailerNode(name="UnknownCraftWeaponProfession"),
                ),
            ],
        )
    )


def EquipSkillBar() -> BehaviorTree:
    def _level_bucket() -> int:
        level = Player.GetLevel()
        return level if level <= 5 else 6

    return BehaviorTree(
        BehaviorTree.SequenceNode(
            name="Equip Skill Bar",
            children=[
                BT.StoreProfessionNames(),
                BehaviorTree.SwitchNode(
                    name="EquipSkillBarByProfessionAndLevel",
                    selector_fn=lambda node: (
                        node.blackboard.get("player_primary_profession_name", ""),
                        _level_bucket(),
                    ),
                    cases=[
                        (("Dervish", 2), lambda: BT.LoadSkillbar("OgChkSj4V6KAGw/X7LCe8C")),
                        (("Dervish", 3), lambda: BT.LoadSkillbar("OgCjkOrCbMiXp74dADAAAAABAA")),
                        (("Dervish", 4), lambda: BT.LoadSkillbar("OgCjkOrCbMiXp74dADAAAAABAA")),
                        (("Dervish", 5), lambda: BT.LoadSkillbar("OgCjkOrCbMiXp74dADAAAAABAA")),
                        (("Dervish", 6), lambda: BT.LoadSkillbar("OgGjkyrDLTiXSX7gDYPXfXjbYcA")),
                        (("Paragon", 2), lambda: BT.LoadSkillbar("OQCjUOmBqMw4HMQuCHjBAYcBAA")),
                        (("Paragon", 3), lambda: BT.LoadSkillbar("OQCjUOmBqMw4HMQuCHjBAYcBAA")),
                        (("Paragon", 4), lambda: BT.LoadSkillbar("OQCjUWmCaNw4HMQuCDAAAYcBAA")),
                        (("Paragon", 5), lambda: BT.LoadSkillbar("OQGkUemyZgKEM2DmDGQ2VBQoAAGH")),
                        (("Paragon", 6), lambda: BT.LoadSkillbar("OQGjUymDKTwYPYOYAZLYXFAhYcA")),
                        (("Elementalist", 2), lambda: BT.LoadSkillbar("OgBDozGsAGTrwFbNAAIA")),
                        (("Elementalist", 3), lambda: BT.LoadSkillbar("OgBDozGsAGTrwFbNAAIA")),
                        (("Elementalist", 4), lambda: BT.LoadSkillbar("OgBDo2OMNGDahwoYYNAAAAMO")),
                        (("Elementalist", 5), lambda: BT.LoadSkillbar("OgBDo2OMNGDahwoYYNAAAAMO")),
                        (("Elementalist", 6), lambda: BT.LoadSkillbar("OgVDErwsN0COwFAoeTzzgVMO")),
                        (("Monk", 2), lambda: BT.LoadSkillbar("OwAU0C38CYEZEltkf5cmAImA")),
                        (("Monk", 3), lambda: BT.LoadSkillbar("OwAU0CH9CoEtElZkf5EAAImA")),
                        (("Monk", 4), lambda: BT.LoadSkillbar("OwAU0CH9CoEtElZkf5EAAImA")),
                        (("Monk", 5), lambda: BT.LoadSkillbar("OwAU0CH9CoEtElZkf5EAAImA")),
                        (("Monk", 6), lambda: BT.LoadSkillbar("OwUEEqwD6ywBuA308cPAKgSiJA")),
                        (("Warrior", 2), lambda: BT.LoadSkillbar("OQARErprIUAABAuCGHAAAA")),
                        (("Warrior", 3), lambda: BT.LoadSkillbar("OQARErprIUAABAuCGHAAAA")),
                        (("Warrior", 4), lambda: BT.LoadSkillbar("OQARErprIUAABAuCGHAAAA")),
                        (("Warrior", 5), lambda: BT.LoadSkillbar("OQARErprIUAABAuCGHAAAA")),
                        (("Warrior", 6), lambda: BT.LoadSkillbar("OQojExVTKTdFCF/XDYcFBA7gYcA")),
                        (("Necromancer", 2), lambda: BT.LoadSkillbar("OABDQRJWAplpAAAAAAAA")),
                        (("Necromancer", 3), lambda: BT.LoadSkillbar("OABDQTNmMphMRboK8IAAAAMO")),
                        (("Necromancer", 4), lambda: BT.LoadSkillbar("OABDQTNmMphMRboK8IAAAAMO")),
                        (("Necromancer", 5), lambda: BT.LoadSkillbar("OAVDIXN2McgqwFAo2DgCCAMO")),
                        (("Necromancer", 6), lambda: BT.LoadSkillbar("OAVEEqwFZ3wBqCXAgaPAKknx4A")),
                        (("Mesmer", 2), lambda: BT.LoadSkillbar("OQBDAhITAoohAAAAAAAA")),
                        (("Mesmer", 3), lambda: BT.LoadSkillbar("OQBDAhMTAooBHEBFAAIA")),
                        (("Mesmer", 4), lambda: BT.LoadSkillbar("OQBDAhgTAooBHEBFAAIA")),
                        (("Mesmer", 5), lambda: BT.LoadSkillbar("OQBDAhgTMogLAHgIAF6BAVBA")),
                        (("Mesmer", 6), lambda: BT.LoadSkillbar("OQBEAaYCP2gCuAcg8MUoHAUx4A")),
                        (("Ranger", 2), lambda: BT.LoadSkillbar("OgATcDskjQx+WAAAAAAAAAA")),
                        (("Ranger", 3), lambda: BT.LoadSkillbar("OgATcDsknQx++4xGAAAACAA")),
                        (("Ranger", 4), lambda: BT.LoadSkillbar("OgAScLsMAAfzxZ5gxBAAABA")),
                        (("Ranger", 5), lambda: BT.LoadSkillbar("OgESIpLNdFfDUBAAA4KXFMO")),
                        (("Ranger", 6), lambda: BT.LoadSkillbar("OgETI5LjHqrw3AqYHkqQvC1AjDA")),
                    ],
                    default_case=BehaviorTree.FailerNode(name="UnknownSkillBarProfessionOrLevel"),
                ),
            ],
        )
    )


def Craft_First_Weapon() -> BehaviorTree:
    return BehaviorTree(
        BehaviorTree.SequenceNode(
            name="Craft first weapon",
            children=[
                BT.TravelToRandomDistrict(target_map_id=449),
                BT.MoveAndInteract(Vec2f(-11270, 8785)),
                BT.Wait(1000),
                Craft1stWeapon(),
                EquipSkillBar(),
            ],
        )
    )


def A_Hidden_Threat() -> BehaviorTree:
    return BehaviorTree(
        BehaviorTree.SequenceNode(
            name="Quest: A Hidden Threat",
            children=[
                BT.TravelToRandomDistrict(target_map_id=431),
                PrepareForBattle(hero_list=[], henchman_list=[1, 2, 4]),
                BT.MoveAndDialog(Vec2f(-1835, 6505), dialog_id=0x825A01),
                BT.MoveAndExitMap(Vec2f(-3172, 3271), target_map_id=430),
                ConfigureAggressiveEnv(),
                BT.Move(Vec2f(-1840.23, 2432.96)),
                BT.MoveAndDialog(Vec2f(-1297, 3229), dialog_id=0x85),
                ConfigureAggressiveEnv(),
                BT.Move(Vec2f(-4680.29, 1867.42)),
                BT.Move(Vec2f(-13276, -151)),
                BT.Move(Vec2f(-17946.33, 2426.69)),
                BT.Move(Vec2f(-17614.74, 11699.77)),
                BT.Move(Vec2f(-18657.45, 14601.87)),
                BT.Move(Vec2f(-16911.47, 19039.31)),
                BT.WaitUntilOnCombat(),
                BT.WaitUntilOutOfCombat(),
                BT.TravelToRandomDistrict(target_map_id=431),
                BT.MoveAndDialog(Vec2f(-1835, 6505), dialog_id=0x825A07),
            ],
        )
    )


def Deposit_Proof_Of_Legend() -> BehaviorTree:
    return BehaviorTree(
        BehaviorTree.SequenceNode(
            name="Deposit Proof of Legend",
            children=[
                BT.TravelToRandomDistrict(target_map_id=449),
                BT.DepositModelToStorage(37841),
                BT.DepositGoldKeep(0),
            ],
        )
    )


def LogoutAndDeleteState() -> BehaviorTree:
    return BehaviorTree(
        BehaviorTree.SequenceNode(
            name="Reroll: Logout > Delete > Recreate",
            children=[
                BT.StoreRerollContext(
                    campaign_name="Nightfall",
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
    )


def InitializeBot() -> BehaviorTree:
    return BehaviorTree(
        BehaviorTree.SequenceNode(
            name="Initialize Bot",
            children=[
                BT.ResetActionQueues(),
            ],
        )
    )


def MarkCurrentStep(step_name: str) -> BehaviorTree:
    def _mark_current_step(node: BehaviorTree.Node) -> BehaviorTree.NodeState:
        node.blackboard["current_step_name"] = step_name
        return BehaviorTree.NodeState.SUCCESS

    return BehaviorTree(
        BehaviorTree.ActionNode(
            name=f"MarkCurrentStep({step_name})",
            action_fn=_mark_current_step,
            aftercast_ms=0,
        )
    )


def get_execution_steps() -> list[tuple[str, Callable[[], BehaviorTree]]]:
    return [
        ("Initialize Bot", InitializeBot),
        ("Skip Tutorial", Skip_Tutorial),
        ("Into Chahbek Village", Into_Chahbek_Village),
        ("Quiz the Recruits", Quiz_the_Recruits),
        ("Never Fight Alone", Never_Fight_Alone),
        ("Chahbek Village Mission", Chahbek_Village_Mission),
        ("Primary Training", Primary_Training),
        ("A Personal Vault", A_Personal_Vault),
        ("Material Girl", Material_Girl),
        ("Hog Hunt", Hog_Hunt),
        ("To Champion's Dawn", To_Champions_Dawn),
        ("Identity Theft", Identity_Theft),
        ("Quality Steel", Quality_Steel),
        ("Craft First Weapon", Craft_First_Weapon),
        ("A Hidden Threat", A_Hidden_Threat),
        ("Chahbek Village Mission 2", Chahbek_Village_Mission_2),
        ("Deposit Proof Of Legend", Deposit_Proof_Of_Legend),
        ("Reroll: Logout > Delete > Recreate", LogoutAndDeleteState),
    ]


def build_execution_sequence(start_index: int = 0, name: str = "Proof of Legend Sequence") -> BehaviorTree:
    steps = get_execution_steps()
    bounded_start = max(0, min(start_index, len(steps) - 1))
    return BehaviorTree(
        BehaviorTree.SequenceNode(
            name=name,
            children=[
                BehaviorTree.SequenceNode(
                    name=f"Step: {label}",
                    children=[
                        MarkCurrentStep(label).root,
                        builder().root,
                    ],
                )
                for label, builder in steps[bounded_start:]
            ],
        )
    )


def build_execution_loop(start_index: int = 0) -> BehaviorTree:
    return BehaviorTree(
        BehaviorTree.SequenceNode(
            name="Proof of Legend Loop",
            children=[
                build_execution_sequence(start_index, name="Selected Start Pass"),
                BehaviorTree.RepeaterForeverNode(
                    build_execution_sequence(0, name="Full Loop Pass").root,
                    name="Loop: restart routine",
                ),
            ],
        )
    )


def process_restart_request(tree: BottingTree) -> None:
    restart_step_name = str(tree.GetBlackboardValue("restart_step_name_request", "") or "")
    if not restart_step_name:
        return

    tree.ClearBlackboardValue("restart_step_name_request")
    tree.ClearBlackboardValue("current_step_name")

    steps = get_execution_steps()
    labels = [label for label, _ in steps]
    restart_index = labels.index(restart_step_name) if restart_step_name in labels else 0
    tree.SetCurrentTree(
        build_execution_loop(restart_index),
        auto_start=True,
    )


def draw_window() -> None:
    global selected_start_index

    tree = ensure_botting_tree()
    steps = get_execution_steps()
    labels = [label for label, _ in steps]
    current_step_name = str(tree.GetBlackboardValue("current_step_name", "Idle") or "Idle")

    if PyImGui.begin(MODULE_NAME, PyImGui.WindowFlags.AlwaysAutoResize):
        PyImGui.text(f"Current Step: {current_step_name}")
        if tree.IsStarted():
            if PyImGui.button("Stop"):
                tree.Stop()
            PyImGui.same_line(0, -1)
            if tree.IsPaused():
                if PyImGui.button("Resume"):
                    tree.Pause(False)
            else:
                if PyImGui.button("Pause"):
                    tree.Pause(True)
        else:
            selected_start_index = PyImGui.combo(
                "Start At",
                selected_start_index,
                labels,
            )
            if PyImGui.button("Start"):
                tree.SetCurrentTree(
                    build_execution_loop(selected_start_index),
                    auto_start=True,
                )
        tree.DrawMovePathDebugOptions()
    PyImGui.end()


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
    process_restart_request(tree)
    tree.DrawMovePathIfEnabled()
    draw_window()


if __name__ == "__main__":
    main()
