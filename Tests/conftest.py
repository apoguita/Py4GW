"""
Root conftest.py -- mocks all native C extension modules before any Py4GWCoreLib import.

The Py4GW framework injects ~22 native modules (Py4GW, PyPathing, PyOverlay, etc.)
into the Python runtime when running inside the game process. Outside that context
(i.e. in tests), we install MagicMock stand-ins so the full Py4GWCoreLib import chain
succeeds without a live game.
"""

import sys
from collections import namedtuple
from types import SimpleNamespace
from unittest.mock import MagicMock

# ---------------------------------------------------------------------------
# 1. Save real stdout/stderr (Py4GWCoreLib.__init__ redirects them)
# ---------------------------------------------------------------------------
_real_stdout = sys.stdout
_real_stderr = sys.stderr

# ---------------------------------------------------------------------------
# 2. Install mocks for every native C extension module
# ---------------------------------------------------------------------------
NATIVE_MODULES = [
    "Py4GW",
    "PyScanner",
    "PyImGui",
    "PyAgent",
    "PyPlayer",
    "PyParty",
    "PyItem",
    "PyInventory",
    "PySkill",
    "PySkillbar",
    "PyMerchant",
    "PyEffects",
    "PyKeystroke",
    "PyOverlay",
    "PyQuest",
    "PyPathing",
    "PyUIManager",
    "PyCamera",
    "Py2DRenderer",
    "PyCombatEvents",
    "PyPointers",
    "PyCallback",
]

for _name in NATIVE_MODULES:
    if _name not in sys.modules:
        sys.modules[_name] = MagicMock()

# ---------------------------------------------------------------------------
# 3. Wire specific attributes that production code accesses structurally
# ---------------------------------------------------------------------------

# PyOverlay.Point2D -- used as a constructor returning an object with .x/.y
Point2D = namedtuple("Point2D", ["x", "y"])
sys.modules["PyOverlay"].Point2D = Point2D

# Py4GW.Console.Log(tag, msg, level) and Py4GW.Console.MessageType.*
_py4gw = sys.modules["Py4GW"]
_console = MagicMock()
_msg_type = MagicMock()
_msg_type.Info = "Info"
_msg_type.Error = "Error"
_msg_type.Warning = "Warning"
_console.MessageType = _msg_type
_py4gw.Console = _console
_py4gw.Game = MagicMock()

# PyCallback.Phase.PreUpdate -- every context module calls .enable() at import
_pycb = sys.modules["PyCallback"]
_pycb.PyCallback = MagicMock()
_pycb.Phase = MagicMock()
_pycb.Phase.PreUpdate = "PreUpdate"

# PyPointers -- context modules call PyPointers.PyPointers.Get*Ptr()
_pyptr = sys.modules["PyPointers"]
_pyptr.PyPointers = MagicMock()

# PyImGui.ImGuiCol -- Style.py creates StyleColor instances at class-definition
# time, accessing .name on each enum member. MagicMock's .name creates a child
# mock instead of returning a string, so we need a proper fake enum.
class _FakeEnumValue:
    def __init__(self, name: str):
        self.name = name
        self.value = 0
    def __bool__(self) -> bool:
        return True
    def __repr__(self) -> str:
        return f"ImGuiCol.{self.name}"

class _FakeEnum:
    __members__: dict[str, _FakeEnumValue] = {}
    def __getattr__(self, name: str) -> _FakeEnumValue:
        if name.startswith("_"):
            raise AttributeError(name)
        val = _FakeEnumValue(name)
        self.__members__[name] = val
        return val
    def __or__(self, other):
        return self  # support `PyImGui.ImGuiCol | None` type annotations

sys.modules["PyImGui"].ImGuiCol = _FakeEnum()

# ---------------------------------------------------------------------------
# 4. Now it is safe to import from Py4GWCoreLib (triggers __init__.py chain)
# ---------------------------------------------------------------------------
import Py4GWCoreLib  # noqa: F401, E402

# ---------------------------------------------------------------------------
# 5. Restore stdout/stderr (Py4GWCoreLib.__init__ redirects them)
# ---------------------------------------------------------------------------
sys.stdout = _real_stdout
sys.stderr = _real_stderr


# ---------------------------------------------------------------------------
# Pytest hooks
# ---------------------------------------------------------------------------
def pytest_addoption(parser):
    parser.addoption(
        "--update-snapshots",
        action="store_true",
        default=False,
        help="Regenerate regression snapshot files instead of comparing.",
    )
