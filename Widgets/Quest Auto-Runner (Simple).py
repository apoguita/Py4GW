import importlib.util
import os

from Py4GWCoreLib import ConsoleLog
from Py4GWCoreLib import Console

MODULE_NAME = "Quest Auto-Runner (Simple) Widget"
BOT_FILENAME = "Quest Auto-Runner (Simple).py"
BOT_MODULE_NAME = "quest_auto_runner_simple_bot"

__widget__ = {
    "name": "Quest Auto-Runner (Simple)",
    "enabled": False,
    "category": "Bots",
    "subcategory": "Helpers",
    "icon": "ICON_RUNNING",
    "quickdock": True,
}

_bot_module = None


def _get_bot_path():
    try:
        script_directory = os.path.dirname(os.path.abspath(__file__))
    except NameError:
        script_directory = os.getcwd()
    return os.path.abspath(os.path.join(script_directory, os.pardir, "Bots", BOT_FILENAME))


def _load_bot_module():
    global _bot_module
    if _bot_module is not None:
        return _bot_module

    bot_path = _get_bot_path()
    if not os.path.exists(bot_path):
        ConsoleLog(MODULE_NAME, f"Bot script not found at {bot_path}", Console.MessageType.Error)
        return None

    spec = importlib.util.spec_from_file_location(BOT_MODULE_NAME, bot_path)
    if spec is None or spec.loader is None:
        ConsoleLog(MODULE_NAME, f"Failed to load bot module spec from {bot_path}", Console.MessageType.Error)
        return None

    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except Exception as exc:
        ConsoleLog(MODULE_NAME, f"Failed to load bot module: {exc}", Console.MessageType.Error)
        return None

    _bot_module = module
    return _bot_module


def configure():
    pass


def main():
    module = _load_bot_module()
    if module is None:
        return

    if hasattr(module, "main") and callable(module.main):
        module.main()
