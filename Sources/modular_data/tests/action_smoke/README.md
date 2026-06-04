# Modular Action Smoke Tests

Runtime runner:

```powershell
python Sources\modular_data\tools\run_modular_action_smoke_tests.py
```

List all cases:

```powershell
python Sources\modular_data\tools\run_modular_action_smoke_tests.py --list
```

Run one case:

```powershell
python Sources\modular_data\tools\run_modular_action_smoke_tests.py --case wait.wait
```

Useful targeted runs:

```powershell
python Sources\modular_data\tools\run_modular_action_smoke_tests.py --case interact.npc
python Sources\modular_data\tools\run_modular_action_smoke_tests.py --case interact.gadget
python Sources\modular_data\tools\run_modular_action_smoke_tests.py --case interact.item
python Sources\modular_data\tools\run_modular_action_smoke_tests.py --case interact.dialog --dialog-id 0x86
python Sources\modular_data\tools\run_modular_action_smoke_tests.py --case interact.auto_dialog --dialog-button 1
python Sources\modular_data\tools\run_modular_action_smoke_tests.py --case interact.drop_bundle
```

Guarded cases are skipped by default:

```powershell
python Sources\modular_data\tools\run_modular_action_smoke_tests.py --include-combat
python Sources\modular_data\tools\run_modular_action_smoke_tests.py --include-party
python Sources\modular_data\tools\run_modular_action_smoke_tests.py --include-consumables
python Sources\modular_data\tools\run_modular_action_smoke_tests.py --include-risky
```

Detection is based on the compiled BehaviorTree returning `SUCCESS` or `FAILURE`.
Some actions only confirm that the BT action dispatched successfully; game-side
effects such as chat emotes, inventory use, resign, and abandon quest are not
independently verified.
