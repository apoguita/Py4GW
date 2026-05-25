"""
frame_api_test.py - Comprehensive test & showcase of all 25 new frame functions.

Tests every new function added to the frame tree API:
  Navigation:  GetRelatedFrameID, GetChildFrameIdFromNameHash, IsAncestorOf, GetParentFrameIdDirect
  Lists:       GetOverlayFrameIDs, GetPopupFrameIDs
  Properties:  GetFrameLayer, SetFrameLayer, GetFrameCode, GetOpacity, GetUserParam, GetFrameTitleText
  Geometry:    GetFrameMinSize, GetFrameNativeSize, GetFrameClientBorder, GetFrameClipRect, GetFramePositionEx
  State:       GetStateBit, SetVisible, SetDisabled, ShowFrame, SetOpacity

Usage: Run as widget or standalone. Type a frame_id to inspect, or use the Quick Tests.
"""

from typing import Callable
from typing import TypeVar
import traceback

import PyImGui
import PyUIManager

T = TypeVar('T')


def safe_call(fn: Callable[..., T], *args, default: T, **kwargs) -> T:
    """Wrap calls that may raise and return a typed fallback value."""
    try:
        return fn(*args, **kwargs)
    except Exception as exc:
        log(f'{getattr(fn, "__name__", repr(fn))} failed: {exc}')
        return default


def describe_frame(frame_id: int) -> str:
    if frame_id == 0:
        return '(none)'
    try:
        frame = PyUIManager.UIFrame(frame_id)
        frame_hash = f' hash={frame.frame_hash}' if frame.frame_hash else ''
        state = []
        if frame.is_created:
            state.append('created')
        if frame.is_visible:
            state.append('visible')
        return f'#{frame_id}{frame_hash} type={frame.type} tpl={frame.template_type} [{", ".join(state) or "dead"}]'
    except Exception:
        return f'#{frame_id}'


FRAME_FIRST = 0
FRAME_LAST = 1
FRAME_NEXT = 2
FRAME_PREV = 3
RELATION_NAMES = {0: 'FirstChild', 1: 'LastChild', 2: 'NextSibling', 3: 'PrevSibling'}

STATE_VISIBLE = 0x2
STATE_CREATED = 0x4
STATE_DISABLED = 0x10
STATE_HIDDEN = 0x200

DEFAULT_OPEN = int(PyImGui.TreeNodeFlags.DefaultOpen)

g_frame_id = 0
g_log: list[str] = []
g_layer_value = 0
g_opacity_value = 1.0
g_test_bit = 0x200
g_hash_input = 'Game'
g_label_find = 0
g_last_frame_id = 0


def log(msg: str) -> None:
    g_log.append(msg)
    if len(g_log) > 50:
        g_log.pop(0)


def sync_frame_state(frame_id: int) -> None:
    global g_last_frame_id, g_layer_value, g_opacity_value
    if frame_id == g_last_frame_id:
        return

    g_last_frame_id = frame_id
    if frame_id == 0:
        g_layer_value = 0
        g_opacity_value = 1.0
        return

    g_layer_value = safe_call(PyUIManager.UIManager.get_frame_layer_by_frame_id, frame_id, default=0)
    g_opacity_value = safe_call(PyUIManager.UIManager.get_frame_opacity_by_frame_id, frame_id, default=1.0)


def quick_test_walk(parent_id: int, max_depth: int = 2) -> list[dict[str, object]]:
    """Walk frame subtree recursively using GetRelatedFrameID and dump properties."""
    results: list[dict[str, object]] = []
    _walk(parent_id, 0, max_depth, results, set())
    return results


def _walk(
    frame_id: int,
    depth: int,
    max_depth: int,
    results: list[dict[str, object]],
    visited: set[int],
) -> None:
    if frame_id == 0 or depth > max_depth or frame_id in visited:
        return

    visited.add(frame_id)
    results.append(
        {
            'id': frame_id,
            'depth': depth,
            'desc': describe_frame(frame_id),
            'layer': safe_call(PyUIManager.UIManager.get_frame_layer_by_frame_id, frame_id, default=0),
            'opacity': safe_call(PyUIManager.UIManager.get_frame_opacity_by_frame_id, frame_id, default=0.0),
        }
    )

    child = safe_call(PyUIManager.UIManager.get_related_frame_id, frame_id, FRAME_FIRST, 0, default=0)
    while child:
        _walk(child, depth + 1, max_depth, results, visited)
        child = safe_call(PyUIManager.UIManager.get_related_frame_id, frame_id, FRAME_NEXT, child, default=0)


def render() -> None:
    global g_frame_id, g_layer_value, g_opacity_value, g_test_bit, g_hash_input, g_label_find

    window_open = PyImGui.begin('Frame API Test - 25 Functions')
    try:
        if not window_open:
            return

        g_frame_id = int(PyImGui.input_int('Frame ID', g_frame_id, 1, 100, 0))
        if g_frame_id == 0:
            PyImGui.text('Enter a frame_id to inspect, or use Quick Tests below.')
            _render_quick_tests()
            return

        try:
            frame = PyUIManager.UIFrame(g_frame_id)
        except Exception as exc:
            PyImGui.text(f'Frame #{g_frame_id} not found: {exc}')
            return

        sync_frame_state(g_frame_id)

        if PyImGui.collapsing_header('1. Navigation'):
            parent_id = safe_call(PyUIManager.UIManager.get_parent_frame_id_direct, g_frame_id, default=0)
            PyImGui.text(f'  Parent (direct):  {describe_frame(parent_id)}')

        
            for kind, name in RELATION_NAMES.items():
                related_id = safe_call(PyUIManager.UIManager.get_related_frame_id, g_frame_id, kind, 0, default=0)
                PyImGui.text(f'  {name:<14}: {describe_frame(related_id)}')
                
            
            PyImGui.spacing()
            if PyImGui.button('Walk Children (First->Next)'):
                log('--- Walking children via GetRelatedFrameID ---')
                child = safe_call(PyUIManager.UIManager.get_related_frame_id, g_frame_id, FRAME_FIRST, 0, default=0)
                count = 0
                while child and count < 50:
                    log(f'  child: {describe_frame(child)}')
                    child = safe_call(PyUIManager.UIManager.get_related_frame_id, g_frame_id, FRAME_NEXT, child, default=0)
                    count += 1
                log(f'  total: {count} children')
            
            
            if parent_id:
                is_ancestor = safe_call(
                    PyUIManager.UIManager.is_ancestor_of_by_frame_id,
                    g_frame_id,
                    parent_id,
                    default=False,
                )
                PyImGui.text(f'  Is parent #{parent_id} ancestor of #{g_frame_id}? {"YES" if is_ancestor else "no"}')

            
            
            PyImGui.spacing()
            PyImGui.text('  NameHash / Label Helpers:')
            frame_hash = frame.frame_hash
            frame_label = safe_call(PyUIManager.UIManager.get_frame_label_by_frame_id, g_frame_id, default='')
            text_enc = "" #safe_call(PyUIManager.UIManager.get_text_label_encoded_by_frame_id, g_frame_id, default='')
            text_dec = "" #safe_call(PyUIManager.UIManager.get_text_label_decoded_by_frame_id, g_frame_id, default='')
            PyImGui.text(f'    frame_hash={frame_hash}')
            if frame_label:
                PyImGui.text(f'    frame_label={frame_label}')
            if text_enc:
                PyImGui.text(f'    text_label_encoded={text_enc}')
            if text_dec:
                PyImGui.text(f'    text_label_decoded={text_dec}')

            
            PyImGui.text('  NameHash Lookup (GetChildFromNameHash):')
            if frame_hash and parent_id:
                found = safe_call(
                    PyUIManager.UIManager.get_child_frame_id_from_name_hash,
                    parent_id,
                    frame_hash,
                    default=0,
                )
                PyImGui.text(f'    Searching parent={parent_id} hash={frame_hash} -> found=#{found}')
            else:
                PyImGui.text(f'    (need both parent and hash — parent={parent_id} hash={frame_hash})')
            
            
            
        if PyImGui.collapsing_header('2. Overlay / Popup Lists'):
            if PyImGui.button('Get Overlay Frames'):
                overlays = safe_call(PyUIManager.UIManager.get_overlay_frame_ids, default=[])
                log(f'Overlays: {len(overlays)} frames')
                for frame_id in overlays[:10]:
                    log(f'  overlay: {describe_frame(frame_id)}')
                if len(overlays) > 10:
                    log(f'  ... and {len(overlays) - 10} more')

            PyImGui.same_line(0,-1)
            if PyImGui.button('Get Popup Frames'):
                popups = safe_call(PyUIManager.UIManager.get_popup_frame_ids, default=[])
                log(f'Popups: {len(popups)} frames')
                for frame_id in popups[:10]:
                    log(f'  popup: {describe_frame(frame_id)}')
                if len(popups) > 10:
                    log(f'  ... and {len(popups) - 10} more')

        if PyImGui.collapsing_header('3. Properties'):
            layer = safe_call(PyUIManager.UIManager.get_frame_layer_by_frame_id, g_frame_id, default=0)
            code = safe_call(PyUIManager.UIManager.get_frame_code_by_frame_id, g_frame_id, default=0)
            opacity = safe_call(PyUIManager.UIManager.get_frame_opacity_by_frame_id, g_frame_id, default=0.0)
            user_param = safe_call(PyUIManager.UIManager.get_frame_user_param_by_frame_id, g_frame_id, default=0)
            title = safe_call(PyUIManager.UIManager.get_frame_title_by_frame_id, g_frame_id, default='(none)')

            PyImGui.text(f'  Layer:      {layer}')
            PyImGui.text(f'  Code:       {code}')
            PyImGui.text(f'  Opacity:    {opacity:.3f}')
            PyImGui.text(f'  UserParam:  0x{user_param:08X}')
            PyImGui.text(f'  Title:      {title}')

            PyImGui.spacing()
            PyImGui.text(f'  SetLayer (current={layer}):')
            g_layer_value = int(PyImGui.input_int('##layer', g_layer_value))
            PyImGui.same_line(0,-1)
            if PyImGui.button('Apply Layer'):
                ok = safe_call(
                    PyUIManager.UIManager.set_frame_layer_by_frame_id,
                    g_frame_id,
                    g_layer_value,
                    default=False,
                )
                log(f'  SetLayer({g_layer_value}) -> {ok}')

            PyImGui.text(f'  SetOpacity (current={opacity:.2f}):')
            g_opacity_value = float(PyImGui.slider_float('##opacity', g_opacity_value, 0.0, 1.0))
            PyImGui.same_line(0,-1)
            if PyImGui.button('Apply Opacity'):
                ok = safe_call(
                    PyUIManager.UIManager.set_frame_opacity_by_frame_id,
                    g_frame_id,
                    g_opacity_value,
                    0.0,
                    default=False,
                )
                log(f'  SetOpacity({g_opacity_value:.2f}) -> {ok}')

        if PyImGui.collapsing_header('4. Geometry'):
            min_size = safe_call(PyUIManager.UIManager.get_frame_min_size_by_frame_id, g_frame_id, default=(0.0, 0.0))
            native_size = safe_call(
                PyUIManager.UIManager.get_frame_native_size_by_frame_id,
                g_frame_id,
                default=(0.0, 0.0),
            )
            border = safe_call(
                PyUIManager.UIManager.get_frame_client_border_by_frame_id,
                g_frame_id,
                default=(0.0, 0.0, 0.0, 0.0),
            )
            clip_rect = safe_call(
                PyUIManager.UIManager.get_frame_clip_rect_by_frame_id,
                g_frame_id,
                default=(0.0, 0.0, 0.0, 0.0),
            )
            position_ex = safe_call(
                PyUIManager.UIManager.get_frame_position_ex_by_frame_id,
                g_frame_id,
                default=(0.0, 0.0, 0.0, 0.0, 0),
            )

            PyImGui.text(f'  MinSize:     ({min_size[0]:.1f}, {min_size[1]:.1f})')
            PyImGui.text(f'  NativeSize:  ({native_size[0]:.1f}, {native_size[1]:.1f})')
            PyImGui.text(
                f'  Border:      L={border[0]:.1f} T={border[1]:.1f} R={border[2]:.1f} B={border[3]:.1f}'
            )
            PyImGui.text(
                f'  ClipRect:    L={clip_rect[0]:.1f} T={clip_rect[1]:.1f} R={clip_rect[2]:.1f} B={clip_rect[3]:.1f}'
            )
            PyImGui.text(
                f'  PositionEx:  x={position_ex[0]:.1f} y={position_ex[1]:.1f} '
                f'w={position_ex[2]:.1f} h={position_ex[3]:.1f} flags=0x{int(position_ex[4]):X}'
            )

        if PyImGui.collapsing_header('5. State Bits'):
            state_get = PyUIManager.UIManager.get_frame_state_bit_by_frame_id
            is_visible = safe_call(state_get, g_frame_id, STATE_VISIBLE, default=False)
            is_created = safe_call(state_get, g_frame_id, STATE_CREATED, default=False)
            is_disabled = safe_call(state_get, g_frame_id, STATE_DISABLED, default=False)
            is_hidden = safe_call(state_get, g_frame_id, STATE_HIDDEN, default=False)

            PyImGui.text(f'  Visible  (0x{STATE_VISIBLE:X}):  {"YES" if is_visible else "no"}')
            PyImGui.text(f'  Created  (0x{STATE_CREATED:X}):  {"YES" if is_created else "no"}')
            PyImGui.text(f'  Disabled (0x{STATE_DISABLED:X}): {"YES" if is_disabled else "no"}')
            PyImGui.text(f'  Hidden   (0x{STATE_HIDDEN:X}):  {"YES" if is_hidden else "no"}')

            PyImGui.spacing()
            g_test_bit = int(
                PyImGui.input_int(
                    'Test custom bit (hex)',
                    g_test_bit,
                    1,
                    100,
                    int(PyImGui.InputTextFlags.CharsHexadecimal),
                )
            )
            PyImGui.same_line(0,-1)
            if PyImGui.button('Test'):
                result = safe_call(state_get, g_frame_id, g_test_bit, default=False)
                log(f'  State bit 0x{g_test_bit:X} = {result}')

            PyImGui.spacing()
            PyImGui.text('Visibility controls:')
            if PyImGui.button('Toggle Visible'):
                safe_call(PyUIManager.UIManager.set_frame_visible_by_frame_id, g_frame_id, not is_visible, default=False)
            PyImGui.same_line(0,-1)
            if PyImGui.button('Toggle Disabled'):
                safe_call(
                    PyUIManager.UIManager.set_frame_disabled_by_frame_id,
                    g_frame_id,
                    not is_disabled,
                    default=False,
                )
            PyImGui.same_line(0,-1)
            if PyImGui.button('ShowFrame'):
                safe_call(PyUIManager.UIManager.show_frame_by_frame_id, g_frame_id, True, default=False)
            PyImGui.same_line(0,-1)
            if PyImGui.button('HideFrame'):
                safe_call(PyUIManager.UIManager.show_frame_by_frame_id, g_frame_id, False, default=False)

        if PyImGui.collapsing_header('6. Raw Frame Info'):
            PyImGui.text(f'  frame_id:         {frame.frame_id}')
            PyImGui.text(f'  parent_id:        {frame.parent_id}')
            PyImGui.text(f'  frame_hash:       {frame.frame_hash}')
            PyImGui.text(f'  child_offset:     {frame.child_offset_id}')
            PyImGui.text(f'  type:             {frame.type}')
            PyImGui.text(f'  template_type:    {frame.template_type}')
            PyImGui.text(f'  is_created:       {frame.is_created}')
            PyImGui.text(f'  is_visible:       {frame.is_visible}')
            PyImGui.text(f'  visibility_flags: 0x{frame.visibility_flags:08X}')
            frame_state = getattr(frame, 'frame_state', 0)
            PyImGui.text(f'  frame_state:      0x{frame_state:08X}')
            PyImGui.text(f'  frame_layout:     0x{frame.frame_layout:08X}')

        if PyImGui.collapsing_header('7. Log'):
            for line in g_log:
                PyImGui.text(line)
    except Exception as exc:
        log(f'Render failed: {exc}')
        for line in traceback.format_exc().splitlines()[-5:]:
            log(line)
        PyImGui.text(f'Render error: {exc}')
    finally:
        PyImGui.end()


def _render_quick_tests() -> None:
    global g_hash_input, g_label_find

    PyImGui.spacing()
    PyImGui.text('Quick Tests (no frame_id needed):')

    if PyImGui.button('Test: GetOverlayFrameIDs'):
        overlays = safe_call(PyUIManager.UIManager.get_overlay_frame_ids, default=[])
        log(f'GetOverlayFrameIDs -> {len(overlays)} overlay frames')

    PyImGui.same_line(0,-1)
    if PyImGui.button('Test: GetPopupFrameIDs'):
        popups = safe_call(PyUIManager.UIManager.get_popup_frame_ids, default=[])
        log(f'GetPopupFrameIDs -> {len(popups)} popup frames')

    PyImGui.spacing()
    g_hash_input = PyImGui.input_text('Label to hash', g_hash_input)
    if PyImGui.button('Test: GetHashByLabel'):
        hash_value = safe_call(PyUIManager.UIManager.get_hash_by_label, g_hash_input, default=0)
        log(f'  hash("{g_hash_input}") = {hash_value}')

    PyImGui.same_line(0,-1)
    g_label_find = int(PyImGui.input_int('FrameID from hash', g_label_find))
    if PyImGui.button('Test: GetFrameIDByHash'):
        frame_id = safe_call(PyUIManager.UIManager.get_frame_id_by_hash, g_label_find, default=0)
        log(f'  GetFrameIDByHash({g_label_find}) -> {describe_frame(frame_id)}')

    PyImGui.spacing()
    if PyImGui.button('Test: GetFrameHierarchy'):
        hierarchy = safe_call(PyUIManager.UIManager.get_frame_hierarchy, default=[])
        log(f'GetFrameHierarchy -> {len(hierarchy)} entries')
        for entry in hierarchy[:5]:
            log(f'  parent_hash={entry[0]} frame_hash={entry[1]} parent_id={entry[2]} frame_id={entry[3]}')

    PyImGui.same_line(0,-1)
    if PyImGui.button('Test: GetFrameArray'):
        frame_array = safe_call(PyUIManager.UIManager.get_frame_array, default=[])
        log(f'GetFrameArray -> {len(frame_array)} frame IDs')
        log(f'  First 5: {frame_array[:5]}')

    PyImGui.spacing()
    if PyImGui.button('Test: GetFrameLogs (last 5)'):
        logs = safe_call(PyUIManager.UIManager.get_frame_logs, default=[])
        log(f'FrameLogs: {len(logs)} entries')
        for entry in logs[-5:]:
            log(f'  ts={entry[0]} id={entry[1]} label={entry[2]}')

    PyImGui.spacing()
    PyImGui.text('Log:')
    for line in g_log[-15:]:
        PyImGui.text(line)


def main() -> None:
    render()


if __name__ == '__main__':
    main()
