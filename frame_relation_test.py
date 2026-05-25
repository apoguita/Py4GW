"""
frame_relation_test.py - Test frame tree navigation and property APIs.

Usage: Run as a widget or standalone script. Enter a frame_id to inspect.
"""

from typing import Callable
from typing import TypeVar
import traceback

import PyImGui
import PyUIManager

T = TypeVar('T')


def safe_call(fn: Callable[..., T], *args, default: T, **kwargs) -> T:
    try:
        return fn(*args, **kwargs)
    except Exception as exc:
        append_output(f'{getattr(fn, "__name__", repr(fn))} failed: {exc}')
        return default


class FrameChild:
    FirstChild = 0
    LastChild = 1
    NextSibling = 2
    PrevSibling = 3
    _names = {0: 'FirstChild', 1: 'LastChild', 2: 'NextSibling', 3: 'PrevSibling'}

    @classmethod
    def name(cls, kind: int) -> str:
        return cls._names.get(kind, f'?{kind}')


STATE_VISIBLE = 0x2
STATE_CREATED = 0x4
STATE_DISABLED = 0x10
STATE_HIDDEN = 0x200
DEFAULT_OPEN = int(PyImGui.TreeNodeFlags.DefaultOpen)

g_frame_id = 0
g_output = ''


def append_output(message: str) -> None:
    global g_output
    if g_output:
        g_output = f'{g_output}\n{message}'
    else:
        g_output = message


def render() -> None:
    global g_frame_id, g_output

    window_open = PyImGui.begin('Frame API Test')
    try:
        if not window_open:
            return

        g_frame_id = int(PyImGui.input_int('Frame ID', g_frame_id))

        if g_frame_id == 0:
            PyImGui.text('Enter a frame_id to inspect')
            return

        frame = safe_call(PyUIManager.UIFrame, g_frame_id, default=None)
        if frame is None:
            PyImGui.text(f'Frame #{g_frame_id} not found')
            return

        if PyImGui.collapsing_header('Navigation (Relation Walker)', DEFAULT_OPEN):
            if PyImGui.button('Get First Child'):
                child_id = safe_call(
                    PyUIManager.UIManager.get_related_frame_id,
                    g_frame_id,
                    FrameChild.FirstChild,
                    0,
                    default=0,
                )
                g_output = f'FirstChild = {child_id}'
            PyImGui.same_line()
            if PyImGui.button('Get Last Child'):
                child_id = safe_call(
                    PyUIManager.UIManager.get_related_frame_id,
                    g_frame_id,
                    FrameChild.LastChild,
                    0,
                    default=0,
                )
                g_output = f'LastChild = {child_id}'
            PyImGui.same_line()
            if PyImGui.button('Get Next Sibling'):
                child_id = safe_call(
                    PyUIManager.UIManager.get_related_frame_id,
                    g_frame_id,
                    FrameChild.NextSibling,
                    0,
                    default=0,
                )
                g_output = f'NextSibling = {child_id}'
            PyImGui.same_line()
            if PyImGui.button('Get Prev Sibling'):
                child_id = safe_call(
                    PyUIManager.UIManager.get_related_frame_id,
                    g_frame_id,
                    FrameChild.PrevSibling,
                    0,
                    default=0,
                )
                g_output = f'PrevSibling = {child_id}'

            if g_output:
                PyImGui.text(g_output)

        if PyImGui.collapsing_header('Frame Properties', DEFAULT_OPEN):
            layer = safe_call(PyUIManager.UIManager.get_frame_layer_by_frame_id, g_frame_id, default=0)
            code = safe_call(PyUIManager.UIManager.get_frame_code_by_frame_id, g_frame_id, default=0)
            title = safe_call(PyUIManager.UIManager.get_frame_title_by_frame_id, g_frame_id, default='(none)')
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

            PyImGui.text(f'  Layer:      {layer}')
            PyImGui.text(f'  Code:       {code}')
            PyImGui.text(f'  Title:      {title}')
            PyImGui.text(f'  MinSize:    ({min_size[0]:.1f}, {min_size[1]:.1f})')
            PyImGui.text(f'  NativeSize: ({native_size[0]:.1f}, {native_size[1]:.1f})')
            PyImGui.text(f'  Border:     (L={border[0]:.1f}, T={border[1]:.1f}, R={border[2]:.1f}, B={border[3]:.1f})')
            PyImGui.text(
                f'  ClipRect:   (L={clip_rect[0]:.1f}, T={clip_rect[1]:.1f}, R={clip_rect[2]:.1f}, B={clip_rect[3]:.1f})'
            )
            PyImGui.text(
                f'  PositionEx: (x={position_ex[0]:.1f}, y={position_ex[1]:.1f}, '
                f'w={position_ex[2]:.1f}, h={position_ex[3]:.1f}, flags=0x{int(position_ex[4]):X})'
            )

        if PyImGui.collapsing_header('State Bits', DEFAULT_OPEN):
            state_get = PyUIManager.UIManager.get_frame_state_bit_by_frame_id
            visible = safe_call(state_get, g_frame_id, STATE_VISIBLE, default=False)
            created = safe_call(state_get, g_frame_id, STATE_CREATED, default=False)
            disabled = safe_call(state_get, g_frame_id, STATE_DISABLED, default=False)
            hidden = safe_call(state_get, g_frame_id, STATE_HIDDEN, default=False)

            PyImGui.text(f'  Visible  (0x{STATE_VISIBLE:X}):  {"YES" if visible else "no"}')
            PyImGui.text(f'  Created  (0x{STATE_CREATED:X}):  {"YES" if created else "no"}')
            PyImGui.text(f'  Disabled (0x{STATE_DISABLED:X}): {"YES" if disabled else "no"}')
            PyImGui.text(f'  Hidden   (0x{STATE_HIDDEN:X}):  {"YES" if hidden else "no"}')

            PyImGui.spacing()
            if PyImGui.button('Toggle Visible'):
                safe_call(PyUIManager.UIManager.set_frame_visible_by_frame_id, g_frame_id, not visible, default=False)
            PyImGui.same_line()
            if PyImGui.button('Toggle Disabled'):
                safe_call(
                    PyUIManager.UIManager.set_frame_disabled_by_frame_id,
                    g_frame_id,
                    not disabled,
                    default=False,
                )

        if PyImGui.collapsing_header('Ancestry', DEFAULT_OPEN):
            parent_id = safe_call(PyUIManager.UIManager.get_parent_frame_id_direct, g_frame_id, default=0)
            PyImGui.text(f'  Parent: {parent_id}')
            if parent_id:
                is_ancestor = safe_call(
                    PyUIManager.UIManager.is_ancestor_of_by_frame_id,
                    g_frame_id,
                    parent_id,
                    default=False,
                )
                PyImGui.text(f'  Is parent ancestor: {is_ancestor}')

        if PyImGui.collapsing_header('Raw Frame Info'):
            PyImGui.text(f'  frame_id:       {frame.frame_id}')
            PyImGui.text(f'  parent_id:      {frame.parent_id}')
            PyImGui.text(f'  frame_hash:     {frame.frame_hash}')
            PyImGui.text(f'  child_offset:   {frame.child_offset_id}')
            PyImGui.text(f'  type:           {frame.type}')
            PyImGui.text(f'  template_type:  {frame.template_type}')
            PyImGui.text(f'  is_created:     {frame.is_created}')
            PyImGui.text(f'  is_visible:     {frame.is_visible}')
            PyImGui.text(f'  visibility_flags: 0x{frame.visibility_flags:08X}')
            frame_state = getattr(frame, 'frame_state', 0)
            PyImGui.text(f'  frame_state:    0x{frame_state:08X}')
            PyImGui.text(f'  frame_layout:   0x{frame.frame_layout:08X}')

        if g_output:
            PyImGui.separator()
            PyImGui.text_wrapped(g_output)
    except Exception as exc:
        append_output(f'Render failed: {exc}')
        for line in traceback.format_exc().splitlines()[-5:]:
            append_output(line)
        PyImGui.text_wrapped(g_output)
    finally:
        PyImGui.end()


def main() -> None:
    render()


if __name__ == '__main__':
    main()
