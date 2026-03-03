from Sources.oazix.CustomBehaviors.primitives.helpers.map_instance_helper import (
    classify_map_instance_transition,
)


def test_classify_map_instance_transition_detects_map_change():
    assert classify_map_instance_transition(1, 5000, 2, 100) == "map_change"


def test_classify_map_instance_transition_detects_instance_rollback():
    assert classify_map_instance_transition(1, 5000, 1, 100) == "instance_change"


def test_classify_map_instance_transition_ignores_normal_uptime_growth():
    assert classify_map_instance_transition(1, 5000, 1, 5200) == ""


def test_classify_map_instance_transition_ignores_first_sample():
    assert classify_map_instance_transition(0, 0, 1, 100) == ""
