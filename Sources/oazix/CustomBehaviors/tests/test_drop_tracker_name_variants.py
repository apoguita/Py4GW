import sys
import types

if "Py4GWCoreLib" not in sys.modules:
    fake_core = types.ModuleType("Py4GWCoreLib")
    setattr(fake_core, "Item", types.SimpleNamespace())
    setattr(fake_core, "Py4GW", types.SimpleNamespace())
    sys.modules["Py4GWCoreLib"] = fake_core

from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_item_stats_runtime import (
    _compose_inscribable_name,
    _compose_old_school_name,
    _infer_name_variant,
)


def test_infer_name_variant_prefers_explicit_inscribable_hint():
    assert _infer_name_variant("Fiery", "of Fortitude", "Strength and Honor", True) == "inscribable"
    assert _infer_name_variant("Fiery", "", "Strength and Honor", True) == "inscribable"


def test_infer_name_variant_prefers_explicit_old_school_hint():
    assert _infer_name_variant("Fiery", "", "Strength and Honor", False) == "old_school"
    assert _infer_name_variant("Fiery", "of Fortitude", "Strength and Honor", False) == "old_school"


def test_compose_old_school_name_adds_suffix_path():
    composed = _compose_old_school_name("Long Sword", "Fiery", "of Fortitude")
    assert composed == "Fiery Long Sword of Fortitude"


def test_compose_inscribable_name_adds_inherent_path():
    composed = _compose_inscribable_name("Long Sword", "Fiery", "Strength and Honor")
    assert composed == "Fiery Long Sword (Strength and Honor)"


def test_compose_name_skips_duplicate_labels():
    assert _compose_old_school_name("Fiery Long Sword", "Fiery", "of Fortitude") == "Fiery Long Sword of Fortitude"
    assert _compose_inscribable_name("Long Sword (Strength and Honor)", "", "Strength and Honor") == ""
