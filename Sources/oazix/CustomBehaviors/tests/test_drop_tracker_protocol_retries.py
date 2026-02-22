from __future__ import annotations

from Sources.oazix.CustomBehaviors.tests.drop_tracker_protocol_harness import stress_delivery_simulation


def test_protocol_stress_delivery_retry_dedupe():
    # Covers chunk assembly + duplicate delivery filtering behavior.
    summary = stress_delivery_simulation(total_events=200, duplicate_rate=0.5, drop_rate=0.0)
    assert summary["missing"] == 0
    assert summary["extra"] == 0
    assert summary["corrupted"] == 0
    assert summary["duplicates_filtered"] > 0


def test_protocol_soak_delivery_retry_dedupe_name_integrity():
    summary = stress_delivery_simulation(total_events=5000, duplicate_rate=0.55, drop_rate=0.0)
    assert summary["missing"] == 0
    assert summary["extra"] == 0
    assert summary["corrupted"] == 0
    assert summary["duplicates_filtered"] > 1000
