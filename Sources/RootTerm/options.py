"""Runtime options shared by the UI, runner, and consumables."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class BotOptions:
    hard_mode: bool = False
    use_essence: bool = False
    use_armor: bool = False
    use_grail: bool = False
    use_stone: bool = False
    stone_index: int = 0
    campaign_filter: int = -1  # -1 = All
    selected: dict[int, bool] = field(default_factory=dict)
    status_message: str = ''

    def is_selected(self, quest_id: int) -> bool:
        return bool(self.selected.get(quest_id, False))

    def set_selected(self, quest_id: int, value: bool) -> None:
        self.selected[quest_id] = value

    def get_selected_quest_ids(self) -> list[int]:
        return [qid for qid, on in self.selected.items() if on]

    def selection_key(self) -> tuple:
        return (
            self.hard_mode,
            self.use_essence,
            self.use_armor,
            self.use_grail,
            self.use_stone,
            self.stone_index,
            tuple(sorted(self.get_selected_quest_ids())),
        )


OPTIONS = BotOptions()
