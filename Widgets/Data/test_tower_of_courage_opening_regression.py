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
    opening_source = source[source.index('def run_tower_of_courage_farm():'):source.index('\ndef reset_run():')]
    assert "SKILL_TEMPLATE = 'OgcTc5+8Z6ASn5uU4ABimsBKuEA'" in source
    assert 'SHROUD_OF_DISTRESS_SLOT = 1' in source
    assert 'SHADOW_FORM_SLOT = 2' in source
    assert 'DWARVEN_STABILITY_SLOT = 3' in source
    assert 'WHIRLING_DEFENSE_SLOT = 4' in source
    assert 'HEART_OF_SHADOW_SLOT = 5' in source
    assert 'I_AM_UNSTOPPABLE_SLOT = 6' in source
    assert 'DARK_ESCAPE_SLOT = 7' in source
    assert 'MENTAL_BLOCK_SLOT = 8' in source

    expected_opening_order = (
        "log_opening_phase('Casting Shadow Form, Dwarven Stability, and Dark Escape at FoW departure.')",
        'SHADOW_FORM_SLOT,',
        "'Shadow Form',",
        'DWARVEN_STABILITY_SLOT,',
        "'Dwarven Stability',",
        'DARK_ESCAPE_SLOT,',
        "'Dark Escape',",
        'follow_path_until_nearby_abyssal(',
        'INITIAL_PULL_PATH,',
        'if abyssal_detected:',
        "ActionQueueManager().ResetQueue('ACTION')",
        "'Abyssal detected during the initial pull. Casting I Am Unstoppable! immediately.'",
        'yield from Routines.Yield.wait(OPENING_PULL_SETTLE_MS)',
        'I_AM_UNSTOPPABLE_SLOT,',
        "'I Am Unstoppable!',",
        "'Casting Dwarven Stability and Mental Block before balling.'",
        'MENTAL_BLOCK_SLOT,',
        "'Mental Block',",
        'follow_path(ABYSSAL_BALL_PATH',
        'DWARVEN_STABILITY_SLOT,',
        "'Dwarven Stability',",
        'WHIRLING_DEFENSE_SLOT,',
        "'Whirling Defense',",
    )

    previous_position = -1
    for marker in expected_opening_order:
        position = opening_source.find(marker, previous_position + 1)
        assert position >= 0, f'Missing Tower of Courage opening step: {marker}'
        previous_position = position

    expected_route_anchors = (
        '(-21131.0, -2390.0)',
        '(-16494.0, -3113.0)',
        '(-14453.0, -3536.0)',
        '(-13684.0, -2077.0)',
        '(-14113.0, -418.0)',
        '(-15826.0, -3046.0)',
        '(-16002.0, -3031.0)',
        '(-16004.0, -3202.0)',
        '(-15272.0, -3004.0)',
        '(-14209.0, -2935.0)',
        '(-14535.0, -2615.0)',
        '(-14506.0, -2633.0)',
    )
    for anchor in expected_route_anchors:
        assert anchor in source, f'Missing proven Tower of Courage route anchor: {anchor}'

    assert 'DEATHS_CHARGE_SLOT' not in source
    assert 'or has_nearby_abyssal(),' in source
    assert 'if has_nearby_abyssal():\n            return True' in source
    assert 'heart_of_shadow_health_threshold=0.3' in opening_source
    assert 'build.ConfigureUpkeep(True, refresh_i_am_unstoppable=True)' in opening_source
    assert 'not Routines.Checks.Skills.IsSkillSlotReady(slot)' in source

    emergency_source = opening_source[
        opening_source.index('if abyssal_detected:'):opening_source.index(
            "log_opening_phase('Casting Dwarven Stability and Mental Block before balling.')"
        )
    ]
    assert 'MENTAL_BLOCK_SLOT' not in emergency_source

    print('Passed Tower of Courage scripted opening sequence regression check.')


if __name__ == '__main__':
    run()
