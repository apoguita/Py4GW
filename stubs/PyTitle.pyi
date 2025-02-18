from typing import Any, List

class PyTitle:
    title_id: int
    props: int
    current_points: int
    current_title_tier_index: int
    points_needed_current_rank: int
    next_title_tier_index: int
    points_needed_next_rank: int
    max_title_rank: int
    max_title_tier_index: int
    is_percentage_based: bool
    has_tiers: bool

    def __init__(self, title_id: int) -> None: ...
    def GetContext(self) -> None: ...