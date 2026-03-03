from __future__ import annotations

import importlib
import sys
import types
import typing
from enum import Enum
from types import SimpleNamespace


def _set_module_attrs(module: types.ModuleType, **attrs: object) -> types.ModuleType:
    for name, value in attrs.items():
        setattr(module, name, value)
    return module


class _FakeTimer:
    def __init__(self, _ms: int = 0) -> None:
        self._stopped = False

    def Stop(self) -> None:  # noqa: N802 - runtime API
        self._stopped = True

    def IsStopped(self) -> bool:  # noqa: N802 - runtime API
        return bool(self._stopped)

    def Reset(self) -> None:  # noqa: N802 - runtime API
        self._stopped = False

    def IsExpired(self) -> bool:  # noqa: N802 - runtime API
        return True


class _FakeSlotEmail:
    def __init__(self, value: str = "") -> None:
        self.value = value


class _FakeChestConfig:
    def __init__(self, slot_count: int = 12) -> None:
        self.ChestStatus = [0] * int(slot_count)
        self.SlotEmails = [_FakeSlotEmail("") for _ in range(int(slot_count))]
        self.ChestAgentID = 0
        self.MapInstanceID = 0
        self.ChestReported = False


class _FakeStruct:
    def __init__(self) -> None:
        self.ChestOpeningConfig = _FakeChestConfig()


class _FakeWidgetMemoryManager:
    struct = _FakeStruct()
    widget_data = SimpleNamespace(
        is_enabled=True,
        is_chesting_enabled=True,
    )

    def _get_struct(self):
        return type(self).struct

    def GetCustomBehaviorWidgetData(self):
        return type(self).widget_data


class _FakeEventBus:
    def __init__(self) -> None:
        self.subscriptions: list[tuple[object, object, str]] = []

    def subscribe(self, event_type, callback, subscriber_name: str = "") -> None:
        self.subscriptions.append((event_type, callback, str(subscriber_name)))


def _install_runtime_stubs(monkeypatch):
    monkeypatch.setattr(typing, "override", lambda fn: fn, raising=False)

    class _BehaviorState(Enum):
        IN_AGGRO = 1
        FAR_FROM_AGGRO = 5
        CLOSE_TO_AGGRO = 6
        IDLE = 10

    class _CustomSkill:
        def __init__(self, skill_name: str) -> None:
            self.skill_name = str(skill_name)

    class _CustomSkillUtilityBase:
        def __init__(
            self,
            event_bus,
            skill,
            in_game_build,
            score_definition,
            mana_required_to_cast=0,
            allowed_states=None,
            utility_skill_typology=None,
            execution_strategy=None,
        ) -> None:
            self.event_bus = event_bus
            self.custom_skill = skill
            self.in_game_build = in_game_build
            self.score_definition = score_definition
            self.mana_required_to_cast = mana_required_to_cast
            self.allowed_states = allowed_states
            self.utility_skill_typology = utility_skill_typology
            self.execution_strategy = execution_strategy
            self.is_enabled = True

    class _ScoreStaticDefinition:
        def __init__(self, score: float) -> None:
            self._score = float(score)

        def get_score(self) -> float:
            return float(self._score)

    pyimgui_mod = _set_module_attrs(
        types.ModuleType("PyImGui"),
        bullet_text=lambda *_args, **_kwargs: None,
    )

    py4gw_mod = _set_module_attrs(
        types.ModuleType("Py4GWCoreLib"),
        GLOBAL_CACHE=SimpleNamespace(
            Inventory=SimpleNamespace(),
        ),
        AgentArray=SimpleNamespace(
            GetEnemyArray=lambda: [],
            Filter=SimpleNamespace(
                ByCondition=lambda arr, _fn: list(arr),
                ByDistance=lambda arr, _xy, _dist: list(arr),
            ),
        ),
        Agent=SimpleNamespace(
            IsAlive=lambda _agent_id: True,
            GetXY=lambda _agent_id: (0.0, 0.0),
            IsValid=lambda _agent_id: True,
        ),
        Party=SimpleNamespace(
            GetPlayerCount=lambda: 1,
        ),
        Routines=SimpleNamespace(),
        Range=SimpleNamespace(Earshot=SimpleNamespace(value=0)),
        Player=SimpleNamespace(
            GetXY=lambda: (0.0, 0.0),
            GetAccountEmail=lambda: "self@test",
            GetName=lambda: "Tester",
        ),
        Map=SimpleNamespace(
            GetMapID=lambda: 123,
            IsExplorable=lambda: True,
        ),
    )

    py4gwcorelib_mod = _set_module_attrs(
        types.ModuleType("Py4GWCoreLib.Py4GWcorelib"),
        ActionQueueManager=lambda: SimpleNamespace(ResetAllQueues=lambda: None),
        ThrottledTimer=_FakeTimer,
    )

    uimanager_mod = _set_module_attrs(
        types.ModuleType("Py4GWCoreLib.UIManager"),
        UIManager=SimpleNamespace(IsLockedChestWindowVisible=lambda: False),
    )

    model_enums_mod = _set_module_attrs(
        types.ModuleType("Py4GWCoreLib.enums_src.Model_enums"),
        ModelID=SimpleNamespace(Lockpick=SimpleNamespace(value=1)),
    )

    event_message_mod = _set_module_attrs(
        types.ModuleType("Sources.oazix.CustomBehaviors.primitives.bus.event_message"),
        EventMessage=type("EventMessage", (), {"__init__": lambda self, data=None: setattr(self, "data", data)}),
    )

    event_type_mod = _set_module_attrs(
        types.ModuleType("Sources.oazix.CustomBehaviors.primitives.bus.event_type"),
        EventType=SimpleNamespace(MAP_CHANGED="map_changed", CHEST_OPENED="chest_opened"),
    )

    event_bus_mod = _set_module_attrs(
        types.ModuleType("Sources.oazix.CustomBehaviors.primitives.bus.event_bus"),
        EventBus=_FakeEventBus,
    )

    constants_mod = _set_module_attrs(
        types.ModuleType("Sources.oazix.CustomBehaviors.primitives.constants"),
        DEBUG=False,
    )

    helpers_mod = _set_module_attrs(
        types.ModuleType("Sources.oazix.CustomBehaviors.primitives.helpers.custom_behavior_helpers"),
        CustomBehaviorHelperParty=SimpleNamespace(is_party_leader=lambda: True),
        Resources=SimpleNamespace(get_nearest_locked_chest=lambda _dist: 0),
        Helpers=SimpleNamespace(wait_for=lambda _ms: iter(())),
    )

    behavior_result_mod = _set_module_attrs(
        types.ModuleType("Sources.oazix.CustomBehaviors.primitives.helpers.behavior_result"),
        BehaviorResult=SimpleNamespace(ACTION_PERFORMED=1, ACTION_SKIPPED=2),
    )

    behavior_state_mod = _set_module_attrs(
        types.ModuleType("Sources.oazix.CustomBehaviors.primitives.behavior_state"),
        BehaviorState=_BehaviorState,
    )

    custom_behavior_party_mod = _set_module_attrs(
        types.ModuleType("Sources.oazix.CustomBehaviors.primitives.parties.custom_behavior_party"),
        CustomBehaviorParty=lambda: SimpleNamespace(
            get_shared_lock_manager=lambda: SimpleNamespace(try_aquire_lock=lambda _key: True, release_lock=lambda _key: None)
        ),
    )

    common_score_mod = _set_module_attrs(
        types.ModuleType("Sources.oazix.CustomBehaviors.primitives.scores.comon_score"),
        CommonScore=SimpleNamespace(LOOT=SimpleNamespace(value=1.1)),
    )

    custom_skill_mod = _set_module_attrs(
        types.ModuleType("Sources.oazix.CustomBehaviors.primitives.skills.custom_skill"),
        CustomSkill=_CustomSkill,
    )

    custom_skill_utility_base_mod = _set_module_attrs(
        types.ModuleType("Sources.oazix.CustomBehaviors.primitives.skills.custom_skill_utility_base"),
        CustomSkillUtilityBase=_CustomSkillUtilityBase,
    )

    score_static_definition_mod = _set_module_attrs(
        types.ModuleType("Sources.oazix.CustomBehaviors.primitives.scores.score_static_definition"),
        ScoreStaticDefinition=_ScoreStaticDefinition,
    )

    execution_strategy_mod = _set_module_attrs(
        types.ModuleType("Sources.oazix.CustomBehaviors.primitives.skills.utility_skill_execution_strategy"),
        UtilitySkillExecutionStrategy=SimpleNamespace(
            STOP_EXECUTION_ONCE_SCORE_NOT_HIGHEST="stop",
        ),
    )

    utility_typology_mod = _set_module_attrs(
        types.ModuleType("Sources.oazix.CustomBehaviors.primitives.skills.utility_skill_typology"),
        UtilitySkillTypology=SimpleNamespace(DAEMON="daemon"),
    )

    shared_memory_mod = _set_module_attrs(
        types.ModuleType("Sources.oazix.CustomBehaviors.primitives.parties.custom_behavior_shared_memory"),
        CustomBehaviorWidgetMemoryManager=_FakeWidgetMemoryManager,
    )

    monkeypatch.setitem(sys.modules, "PyImGui", pyimgui_mod)
    monkeypatch.setitem(sys.modules, "Py4GWCoreLib", py4gw_mod)
    monkeypatch.setitem(sys.modules, "Py4GWCoreLib.Py4GWcorelib", py4gwcorelib_mod)
    monkeypatch.setitem(sys.modules, "Py4GWCoreLib.UIManager", uimanager_mod)
    monkeypatch.setitem(sys.modules, "Py4GWCoreLib.enums_src.Model_enums", model_enums_mod)
    monkeypatch.setitem(sys.modules, "Sources.oazix.CustomBehaviors.primitives.bus.event_message", event_message_mod)
    monkeypatch.setitem(sys.modules, "Sources.oazix.CustomBehaviors.primitives.bus.event_type", event_type_mod)
    monkeypatch.setitem(sys.modules, "Sources.oazix.CustomBehaviors.primitives.bus.event_bus", event_bus_mod)
    monkeypatch.setitem(sys.modules, "Sources.oazix.CustomBehaviors.primitives.constants", constants_mod)
    monkeypatch.setitem(sys.modules, "Sources.oazix.CustomBehaviors.primitives.helpers.custom_behavior_helpers", helpers_mod)
    monkeypatch.setitem(sys.modules, "Sources.oazix.CustomBehaviors.primitives.helpers.behavior_result", behavior_result_mod)
    monkeypatch.setitem(sys.modules, "Sources.oazix.CustomBehaviors.primitives.behavior_state", behavior_state_mod)
    monkeypatch.setitem(
        sys.modules,
        "Sources.oazix.CustomBehaviors.primitives.parties.custom_behavior_party",
        custom_behavior_party_mod,
    )
    monkeypatch.setitem(sys.modules, "Sources.oazix.CustomBehaviors.primitives.scores.comon_score", common_score_mod)
    monkeypatch.setitem(sys.modules, "Sources.oazix.CustomBehaviors.primitives.skills.custom_skill", custom_skill_mod)
    monkeypatch.setitem(
        sys.modules,
        "Sources.oazix.CustomBehaviors.primitives.skills.custom_skill_utility_base",
        custom_skill_utility_base_mod,
    )
    monkeypatch.setitem(
        sys.modules,
        "Sources.oazix.CustomBehaviors.primitives.scores.score_static_definition",
        score_static_definition_mod,
    )
    monkeypatch.setitem(
        sys.modules,
        "Sources.oazix.CustomBehaviors.primitives.skills.utility_skill_execution_strategy",
        execution_strategy_mod,
    )
    monkeypatch.setitem(
        sys.modules,
        "Sources.oazix.CustomBehaviors.primitives.skills.utility_skill_typology",
        utility_typology_mod,
    )
    monkeypatch.setitem(
        sys.modules,
        "Sources.oazix.CustomBehaviors.primitives.parties.custom_behavior_shared_memory",
        shared_memory_mod,
    )

    _FakeWidgetMemoryManager.struct = _FakeStruct()
    _FakeWidgetMemoryManager.widget_data = SimpleNamespace(
        is_enabled=True,
        is_chesting_enabled=True,
    )


def _import_module(monkeypatch):
    _install_runtime_stubs(monkeypatch)
    module_name = "Sources.oazix.CustomBehaviors.skills.looting.open_near_chest_utility"
    sys.modules.pop(module_name, None)
    return importlib.import_module(module_name)


def test_map_changed_resets_shared_chest_config(monkeypatch):
    module = _import_module(monkeypatch)
    event_bus = _FakeEventBus()
    utility = module.OpenNearChestUtility(event_bus, [])
    manager = module.CustomBehaviorWidgetMemoryManager() if hasattr(module, "CustomBehaviorWidgetMemoryManager") else _FakeWidgetMemoryManager()
    config = manager._get_struct().ChestOpeningConfig
    config.ChestAgentID = 777
    config.MapInstanceID = 999
    config.ChestReported = True
    config.ChestStatus[0] = 97
    config.ChestStatus[1] = 1
    config.SlotEmails[0].value = "leader@test"
    config.SlotEmails[1].value = "follower@test"
    utility.opened_chest_agent_ids = {777}
    utility.failed_chest_agent_ids = {888}
    utility.my_slot_index = 4
    utility.interrupted_chest_agent_id = 777

    list(utility.map_changed(None))

    assert utility.opened_chest_agent_ids == set()
    assert utility.failed_chest_agent_ids == set()
    assert utility.my_slot_index == -1
    assert utility.interrupted_chest_agent_id == 0
    assert config.ChestAgentID == 0
    assert config.MapInstanceID == 123
    assert config.ChestReported is False
    assert all(int(status) == 0 for status in config.ChestStatus)
    assert all(not slot.value for slot in config.SlotEmails)


def test_precheck_resets_stale_map_bound_chest_state(monkeypatch):
    module = _import_module(monkeypatch)
    event_bus = _FakeEventBus()
    utility = module.OpenNearChestUtility(event_bus, [])
    manager = _FakeWidgetMemoryManager()
    config = manager._get_struct().ChestOpeningConfig
    config.ChestAgentID = 444
    config.MapInstanceID = 321
    config.ChestReported = True
    config.ChestStatus[0] = 99
    config.SlotEmails[0].value = "leader@test"

    result = utility.are_common_pre_checks_valid(module.BehaviorState.IDLE)

    assert result is True
    assert config.ChestAgentID == 0
    assert config.MapInstanceID == 123
    assert config.ChestReported is False
    assert all(int(status) == 0 for status in config.ChestStatus)
    assert all(not slot.value for slot in config.SlotEmails)
