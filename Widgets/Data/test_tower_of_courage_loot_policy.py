from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

FARMER_PATH = (
    ROOT
    / 'Widgets'
    / 'Automation'
    / 'Bots'
    / 'Farmers'
    / 'Materials'
    / 'Obsidian Shards'
    / 'tower_of_courage_farmer.py'
)

from Sources.tower_of_courage.loot_policy import CHAOS_AXE_MODEL_ID
from Sources.tower_of_courage.loot_policy import DARK_REMAINS_MODEL_ID
from Sources.tower_of_courage.loot_policy import OBSIDIAN_SHARD_MODEL_ID
from Sources.tower_of_courage.loot_policy import PASSAGE_SCROLL_FOW_MODEL_ID
from Sources.tower_of_courage.loot_policy import RUBY_MODEL_ID
from Sources.tower_of_courage.loot_policy import SAPPHIRE_MODEL_ID
from Sources.tower_of_courage.loot_policy import should_pick_up_item


def run() -> None:
    cases = [
        ('obsidian shard', OBSIDIAN_SHARD_MODEL_ID, False, False, 0, '', True),
        ('dark remains', DARK_REMAINS_MODEL_ID, False, False, 0, '', True),
        ('ruby', RUBY_MODEL_ID, False, False, 0, '', True),
        ('sapphire', SAPPHIRE_MODEL_ID, False, False, 0, '', True),
        ('FoW passage scroll', PASSAGE_SCROLL_FOW_MODEL_ID, False, False, 0, '', True),
        ('white q7 weapon', 50001, True, False, 7, 'White', False),
        ('blue q7 weapon', 50002, True, False, 7, 'Blue', False),
        ('purple q7 weapon', 50003, True, False, 7, 'Purple', True),
        ('gold q7 weapon', 50004, True, False, 7, 'Gold', True),
        ('white q8 weapon', 50005, True, False, 8, 'White', False),
        ('blue q8 weapon', 50006, True, False, 8, 'Blue', False),
        ('purple q8 weapon', 50007, True, False, 8, 'Purple', True),
        ('gold q8 weapon', 50008, True, False, 8, 'Gold', True),
        ('white q9 Chaos Axe', CHAOS_AXE_MODEL_ID, True, False, 9, 'White', False),
        ('blue q9 Chaos Axe', CHAOS_AXE_MODEL_ID, True, False, 9, 'Blue', False),
        ('purple q9 Chaos Axe', CHAOS_AXE_MODEL_ID, True, False, 9, 'Purple', False),
        ('gold q9 Chaos Axe', CHAOS_AXE_MODEL_ID, True, False, 9, 'Gold', True),
        ('white q9 shield', 50009, True, True, 9, 'White', False),
        ('blue q9 shield', 50010, True, True, 9, 'Blue', False),
        ('purple q9 shield', 50011, True, True, 9, 'Purple', False),
        ('gold q9 shield', 50012, True, True, 9, 'Gold', True),
        ('generic gold q9 weapon', 50013, True, False, 9, 'Gold', False),
        ('gold q10 Chaos Axe', CHAOS_AXE_MODEL_ID, True, False, 10, 'Gold', False),
        ('gold q10 shield', 50014, True, True, 10, 'Gold', False),
        ('unrelated material', 929, False, False, 0, '', False),
    ]

    for name, model_id, is_weapon, is_shield, requirement, rarity_name, expected in cases:
        actual = should_pick_up_item(model_id, is_weapon, is_shield, requirement, rarity_name)
        assert actual is expected, f'{name}: expected {expected}, got {actual}'

    farmer_source = FARMER_PATH.read_text(encoding='utf-8')
    assert 'from Sources.tower_of_courage import loot_policy' in farmer_source
    assert 'loot_policy = importlib.reload(loot_policy)' in farmer_source
    assert 'return loot_policy.should_pick_up_item(' in farmer_source

    print(f'Passed {len(cases)} Tower of Courage loot policy checks.')


if __name__ == '__main__':
    run()
