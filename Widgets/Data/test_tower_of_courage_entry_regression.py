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
    assert "CHAMPION_OF_BALTHAZAR_NAME = 'Champion of Balthazar'" in source
    assert 'TEMPLE_ENTRY_DIALOG_IDS = (0x85, 0x86)' in source

    expected_entry_order = (
        "Player.SendChatCommand('kneel')",
        'champion_id = yield from wait_for_champion_of_balthazar()',
        'yield from Routines.Yield.Player.InteractAgent(champion_id, log=False)',
        'for dialog_id in TEMPLE_ENTRY_DIALOG_IDS:',
        'yield from Routines.Yield.Map.WaitforMapLoad(',
    )

    previous_position = -1
    for marker in expected_entry_order:
        position = source.find(marker, previous_position + 1)
        assert position >= 0, f'Missing Tower of Courage temple entry step: {marker}'
        previous_position = position

    print('Passed Tower of Courage temple entry sequence regression check.')


if __name__ == '__main__':
    run()
