"""ImGui mission selection UI for Reforged Mission Assistant."""

from __future__ import annotations

import PyImGui

from Sources.RootTerm.catalog import CAMPAIGN_FACTIONS
from Sources.RootTerm.catalog import CAMPAIGN_NAMES
from Sources.RootTerm.catalog import CAMPAIGN_NIGHTFALL
from Sources.RootTerm.catalog import CAMPAIGN_OTHER
from Sources.RootTerm.catalog import CAMPAIGN_PROPHECIES
from Sources.RootTerm.catalog import CATALOG
from Sources.RootTerm.catalog import filter_by_campaign
from Sources.RootTerm.config import is_playable
from Sources.RootTerm.consumables import STONE_LABELS
from Sources.RootTerm.options import OPTIONS

_CAMPAIGN_FILTER_LABELS = ['All', 'Prophecies', 'Factions', 'Nightfall', 'Eye of the North']
_CAMPAIGN_FILTER_VALUES = [-1, CAMPAIGN_PROPHECIES, CAMPAIGN_FACTIONS, CAMPAIGN_NIGHTFALL, CAMPAIGN_OTHER]


def draw_missions_tab() -> None:
    """Full Missions tab: filters, checklist, consumables."""
    PyImGui.text('Reforged Mission Assistant')
    PyImGui.text_wrapped('Ported missions are enabled. Other missions remain disabled until their routes are available.')
    PyImGui.separator()

    OPTIONS.hard_mode = PyImGui.checkbox('Hard Mode (Guardian)', OPTIONS.hard_mode)

    PyImGui.separator()
    PyImGui.text('Consumables')
    OPTIONS.use_essence = PyImGui.checkbox('Essence of Celerity', OPTIONS.use_essence)
    OPTIONS.use_armor = PyImGui.checkbox('Armor of Salvation', OPTIONS.use_armor)
    OPTIONS.use_grail = PyImGui.checkbox('Grail of Might', OPTIONS.use_grail)
    OPTIONS.use_stone = PyImGui.checkbox('Use Summoning Stone', OPTIONS.use_stone)
    if OPTIONS.use_stone:
        new_idx = PyImGui.combo('Stone', OPTIONS.stone_index, STONE_LABELS)
        if new_idx >= 0:
            OPTIONS.stone_index = new_idx

    PyImGui.separator()
    PyImGui.text('Campaign Filter')
    filter_idx = 0
    for i, val in enumerate(_CAMPAIGN_FILTER_VALUES):
        if val == OPTIONS.campaign_filter:
            filter_idx = i
            break
    new_filter = PyImGui.combo('Campaign', filter_idx, _CAMPAIGN_FILTER_LABELS)
    if new_filter >= 0:
        OPTIONS.campaign_filter = _CAMPAIGN_FILTER_VALUES[new_filter]

    if PyImGui.button('Select All Playable'):
        for entry in CATALOG:
            if is_playable(entry.quest_id):
                OPTIONS.set_selected(entry.quest_id, True)
    PyImGui.same_line(0, 8)
    if PyImGui.button('Clear Selection'):
        OPTIONS.selected.clear()

    PyImGui.separator()
    campaign = None if OPTIONS.campaign_filter < 0 else OPTIONS.campaign_filter
    entries = filter_by_campaign(campaign)

    if PyImGui.begin_child('MissionList', (0, 320), True, PyImGui.WindowFlags.NoFlag):
        current_campaign = None
        for entry in entries:
            if entry.campaign != current_campaign:
                current_campaign = entry.campaign
                PyImGui.separator()
                PyImGui.text(CAMPAIGN_NAMES.get(entry.campaign, 'Other'))
            playable = is_playable(entry.quest_id) and not entry.stub
            label = entry.name
            if entry.stub:
                label = f'{label} [stub]'
            elif not playable:
                label = f'{label} [Unavailable]'
            checked = OPTIONS.is_selected(entry.quest_id)
            if not playable:
                PyImGui.begin_disabled(True)
            new_val = PyImGui.checkbox(f'{label}##{entry.quest_id}', checked)
            if playable:
                OPTIONS.set_selected(entry.quest_id, new_val)
            if not playable:
                PyImGui.end_disabled()
        PyImGui.end_child()

    selected = [qid for qid in OPTIONS.get_selected_quest_ids() if is_playable(qid)]
    PyImGui.text(f'Selected playable: {len(selected)}')
    if OPTIONS.status_message:
        PyImGui.text_wrapped(OPTIONS.status_message)


def draw_main_summary() -> None:
    """Compact summary under the Botting Main tab."""
    selected = [qid for qid in OPTIONS.get_selected_quest_ids() if is_playable(qid)]
    mode = 'HM' if OPTIONS.hard_mode else 'NM'
    PyImGui.text(f'Queue: {len(selected)} mission(s) | {mode}')
    PyImGui.text('Configure selection in the Missions tab.')
    if OPTIONS.status_message:
        PyImGui.text_wrapped(OPTIONS.status_message)
