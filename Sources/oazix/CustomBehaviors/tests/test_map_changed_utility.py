from __future__ import annotations

import importlib
import sys
import types
import typing
from enum import Enum
from types import SimpleNamespace


class _FakeTimer:
    def __init__(self, _ms: int = 0) -> None:
        self._expired = True

    def IsExpired(self) -> bool:  # noqa: N802 - runtime API
        return bool(self._expired)

    def Reset(self) -> None:  # noqa: N802 - runtime API
        self._expired = True


class _FakeEventBus:
    def __init__(self) -> None:
        self.subscriptions: list[tuple[object, object, str]] = []
        self.published: list[tuple[object, object]] = []

    def subscribe(self, event_type, callback, subscriber_name: str = "") -> None:
        self.subscriptions.append((event_type, callback, str(subscriber_name)))

    def publish(self, event_type, state):
        self.published.append((event_type, state))
        if False:
            yield None


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
            self.allowed_states = allowed_states
            self.utility_skill_typology = utility_skill_typology
            self.execution_strategy = execution_strategy

    class _ScoreStaticDefinition:
        def __init__(self, score: float) -> None:
            self._score = float(score)

        def get_score(self) -> float:
            return float(self._score)

    pyimgui_mod = types.ModuleType("PyImGui")

    map_state = {"map_id": 1, "uptime_ms": 5000}
    py4gw_mod = types.ModuleType("Py4GWCoreLib")
    py4gw_mod.Map = SimpleNamespace(
        GetMapID=lambda: map_state["map_id"],
        GetInstanceUptime=lambda: map_state["uptime_ms"],
    )
    py4gw_mod.Routines = SimpleNamespace()
    py4gw_mod.Range = SimpleNamespace()

    py4gwcorelib_mod = types.ModuleType("Py4GWCoreLib.Py4GWcorelib")
    py4gwcorelib_mod.ThrottledTimer = _FakeTimer

    event_message_mod = types.ModuleType("Sources.oazix.CustomBehaviors.primitives.bus.event_message")
    event_message_mod.EventMessage = object

    event_type_mod = types.ModuleType("Sources.oazix.CustomBehaviors.primitives.bus.event_type")
    event_type_mod.EventType = SimpleNamespace(MAP_CHANGED="map_changed")

    event_bus_mod = types.ModuleType("Sources.oazix.CustomBehaviors.primitives.bus.event_bus")
    event_bus_mod.EventBus = _FakeEventBus

    helpers_mod = types.ModuleType("Sources.oazix.CustomBehaviors.primitives.helpers.custom_behavior_helpers")
    behavior_result_mod = types.ModuleType("Sources.oazix.CustomBehaviors.primitives.helpers.behavior_result")
    behavior_result_mod.BehaviorResult = SimpleNamespace(ACTION_PERFORMED=1)
    behavior_state_mod = types.ModuleType("Sources.oazix.CustomBehaviors.primitives.behavior_state")
    behavior_state_mod.BehaviorState = _BehaviorState
    common_score_mod = types.ModuleType("Sources.oazix.CustomBehaviors.primitives.scores.comon_score")
    common_score_mod.CommonScore = SimpleNamespace(DEAMON=SimpleNamespace(value=99.6))
    score_definition_mod = types.ModuleType("Sources.oazix.CustomBehaviors.primitives.scores.score_definition")
    score_definition_mod.ScoreDefinition = object
    custom_skill_mod = types.ModuleType("Sources.oazix.CustomBehaviors.primitives.skills.custom_skill")
    custom_skill_mod.CustomSkill = _CustomSkill
    custom_skill_utility_base_mod = types.ModuleType(
        "Sources.oazix.CustomBehaviors.primitives.skills.custom_skill_utility_base"
    )
    custom_skill_utility_base_mod.CustomSkillUtilityBase = _CustomSkillUtilityBase
    targeting_order_mod = types.ModuleType("Sources.oazix.CustomBehaviors.primitives.helpers.targeting_order")
    targeting_order_mod.TargetingOrder = object
    score_static_definition_mod = types.ModuleType("Sources.oazix.CustomBehaviors.primitives.scores.score_static_definition")
    score_static_definition_mod.ScoreStaticDefinition = _ScoreStaticDefinition
    utility_typology_mod = types.ModuleType("Sources.oazix.CustomBehaviors.primitives.skills.utility_skill_typology")
    utility_typology_mod.UtilitySkillTypology = SimpleNamespace(DAEMON="daemon")

    monkeypatch.setitem(sys.modules, "PyImGui", pyimgui_mod)
    monkeypatch.setitem(sys.modules, "Py4GWCoreLib", py4gw_mod)
    monkeypatch.setitem(sys.modules, "Py4GWCoreLib.Py4GWcorelib", py4gwcorelib_mod)
    monkeypatch.setitem(sys.modules, "Sources.oazix.CustomBehaviors.primitives.bus.event_message", event_message_mod)
    monkeypatch.setitem(sys.modules, "Sources.oazix.CustomBehaviors.primitives.bus.event_type", event_type_mod)
    monkeypatch.setitem(sys.modules, "Sources.oazix.CustomBehaviors.primitives.bus.event_bus", event_bus_mod)
    monkeypatch.setitem(sys.modules, "Sources.oazix.CustomBehaviors.primitives.helpers.custom_behavior_helpers", helpers_mod)
    monkeypatch.setitem(sys.modules, "Sources.oazix.CustomBehaviors.primitives.helpers.behavior_result", behavior_result_mod)
    monkeypatch.setitem(sys.modules, "Sources.oazix.CustomBehaviors.primitives.behavior_state", behavior_state_mod)
    monkeypatch.setitem(sys.modules, "Sources.oazix.CustomBehaviors.primitives.scores.comon_score", common_score_mod)
    monkeypatch.setitem(sys.modules, "Sources.oazix.CustomBehaviors.primitives.scores.score_definition", score_definition_mod)
    monkeypatch.setitem(sys.modules, "Sources.oazix.CustomBehaviors.primitives.skills.custom_skill", custom_skill_mod)
    monkeypatch.setitem(
        sys.modules,
        "Sources.oazix.CustomBehaviors.primitives.skills.custom_skill_utility_base",
        custom_skill_utility_base_mod,
    )
    monkeypatch.setitem(sys.modules, "Sources.oazix.CustomBehaviors.primitives.helpers.targeting_order", targeting_order_mod)
    monkeypatch.setitem(
        sys.modules,
        "Sources.oazix.CustomBehaviors.primitives.scores.score_static_definition",
        score_static_definition_mod,
    )
    monkeypatch.setitem(
        sys.modules,
        "Sources.oazix.CustomBehaviors.primitives.skills.utility_skill_typology",
        utility_typology_mod,
    )

    return map_state


def _import_module(monkeypatch):
    map_state = _install_runtime_stubs(monkeypatch)
    module_name = "Sources.oazix.CustomBehaviors.skills.deamon.map_changed"
    sys.modules.pop(module_name, None)
    return importlib.import_module(module_name), map_state


def test_map_changed_utility_detects_instance_rollback(monkeypatch):
    module, map_state = _import_module(monkeypatch)
    event_bus = _FakeEventBus()
    utility = module.MapChangedUtility(event_bus, [])

    map_state["map_id"] = 1
    map_state["uptime_ms"] = 100

    score = utility._evaluate(module.BehaviorState.IDLE, [])

    assert score == utility.score_definition.get_score()


def test_map_changed_utility_publishes_map_changed_for_instance_rollback(monkeypatch):
    module, map_state = _import_module(monkeypatch)
    event_bus = _FakeEventBus()
    utility = module.MapChangedUtility(event_bus, [])

    map_state["map_id"] = 1
    map_state["uptime_ms"] = 100

    assert utility._evaluate(module.BehaviorState.IDLE, []) == utility.score_definition.get_score()
    list(utility._execute(module.BehaviorState.IDLE))

    assert event_bus.published == [(module.EventType.MAP_CHANGED, module.BehaviorState.IDLE)]
