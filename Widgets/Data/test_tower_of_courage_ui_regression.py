from pathlib import Path


FARMER_PATH = (
    Path(__file__).resolve().parents[2]
    / 'Widgets'
    / 'Automation'
    / 'Bots'
    / 'Farmers'
    / 'Materials'
    / 'Obsidian Shards'
    / 'tower_of_courage_farmer.py'
)


def run() -> None:
    source = FARMER_PATH.read_text(encoding='utf-8')
    assert "MODULE_ICON = 'Textures\\\\Module_Icons\\\\Tower of Courage Obsidian Shard Farmer.png'" in source
    assert 'def main_window_extra_ui() -> None:' in source
    assert "PyImGui.text('Run statistics')" in source
    assert "PyImGui.text(f'Successful runs: {runtime.completed_runs}')" in source
    assert "PyImGui.text(f'Failed runs: {runtime.failed_runs}')" in source
    assert 'bot.UI.draw_window(additional_ui=main_window_extra_ui)' in source

    print('Passed Tower of Courage main-window counter regression check.')


if __name__ == '__main__':
    run()
