import importlib
import sys
import types


class _FakeSender:
    def __init__(self) -> None:
        self.live_debug_detailed = True
        self.debug_pipeline_logs = False
        self.calls: list[tuple[str, str, dict]] = []

    def _append_live_debug_log(self, event: str, message: str, **fields):
        self.calls.append((str(event), str(message), dict(fields)))


def test_candidate_pipeline_summary_uses_global_throttle_key(monkeypatch):
    py4gw_core = types.ModuleType("Py4GWCoreLib")
    py4gw_core.Py4GW = types.SimpleNamespace(
        Console=types.SimpleNamespace(
            Log=lambda *_args, **_kwargs: None,
            MessageType=types.SimpleNamespace(Info=0),
        )
    )
    monkeypatch.setitem(sys.modules, "Py4GWCoreLib", py4gw_core)
    module_name = "Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_candidate_pipeline"
    sys.modules.pop(module_name, None)
    pipeline = importlib.import_module(module_name)

    sender = _FakeSender()
    candidate_events = [{"reason": "new_slot", "name": "Holy Staff", "qty": 1, "item_id": 42, "model_id": 500}]

    pipeline.log_candidate_pipeline(
        sender,
        candidate_events=candidate_events,
        suppressed_by_model_delta=2,
        suppressed_world_events=[{"reason": "stack_increase"}],
    )

    summary_calls = [call for call in sender.calls if call[0] == "candidate_pipeline_summary"]
    assert len(summary_calls) == 1
    _event, _message, fields = summary_calls[0]
    assert fields.get("dedupe_key") == "candidate_pipeline_summary"
    assert float(fields.get("dedupe_interval_s", 0.0)) == 2.0
