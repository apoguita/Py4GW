from __future__ import annotations

OBSIDIAN_SHARD_MODEL_ID = 945
DARK_REMAINS_MODEL_ID = 522
RUBY_MODEL_ID = 937
SAPPHIRE_MODEL_ID = 938
PASSAGE_SCROLL_FOW_MODEL_ID = 22280
CHAOS_AXE_MODEL_ID = 111

ALWAYS_PICK_UP_MODEL_IDS = {
    OBSIDIAN_SHARD_MODEL_ID,
    DARK_REMAINS_MODEL_ID,
    RUBY_MODEL_ID,
    SAPPHIRE_MODEL_ID,
    PASSAGE_SCROLL_FOW_MODEL_ID,
}


def should_pick_up_item(model_id: int, is_weapon: bool, requirement: int, rarity_name: str) -> bool:
    if model_id in ALWAYS_PICK_UP_MODEL_IDS:
        return True

    if not is_weapon:
        return False

    if requirement in {7, 8} and rarity_name in {'Purple', 'Gold'}:
        return True

    return model_id == CHAOS_AXE_MODEL_ID and requirement == 9
