import json
import os

import PyImGui
import PyUIManager

from Py4GWCoreLib import UIManager, Color, ColorPalette
from Py4GWCoreLib.py4gwcorelib_src.Timer import ThrottledTimer


MODULE_NAME = "Frame Viewer"
SCRIPT_DIR = os.getcwd()


class ViewerState:
    def __init__(self):
        self.refresh_throttle = ThrottledTimer(500)
        self.frame_ids = []
        self.frames = {}  # frame_id -> PyUIManager.UIFrame
        self.children_by_parent = {}
        self.root_ids = []
        self.runtime_paths = {}  # frame_id -> "hash,offset,offset..." or "hash" or ""
        self.draw_enabled = {}  # frame_id -> bool
        self.open_cards = {}  # frame_id -> bool
        self.selected_frame_id = 0  # kept for overlay emphasis / compatibility
        self.auto_refresh = True
        self.show_only_visible = False
        self.show_only_created = False
        self.show_alias_in_tree = True
        self.show_runtime_path_in_tree = False
        self.max_nodes_drawn = 3000

        # Alias sources
        self.alias_source_json = os.path.join("Py4GWCoreLib", "frame_aliases.json")
        self.alias_index_json = os.path.join(SCRIPT_DIR, "frame_alias_index.json")
        self.hash_aliases = {}  # int hash -> alias
        self.path_aliases = {}  # str path -> alias
        self.alias_generation_info = "Alias index not loaded"
        # Node colors (debug-focused)
        self.color_identified_hash = ColorPalette.GetColor("gw_green")
        self.color_identified_path = ColorPalette.GetColor("turquoise")
        self.color_hashed_unidentified = ColorPalette.GetColor("dark_cyan")
        self.color_nohash_unidentified = ColorPalette.GetColor("gw_white")
        self.color_hidden_identified = ColorPalette.GetColor("rosy_brown")
        self.color_hidden_unidentified = ColorPalette.GetColor("gw_elementalist")
        self.color_not_created_identified = ColorPalette.GetColor("midnight_violet")
        self.color_not_created_unidentified = ColorPalette.GetColor("slate_gray")

        # Kept for compatibility, but overlays now use node_color(frame).to_color()
        self.status = "Ready"
        self.last_root_id = 0
        self._draw_counter = 0

    def update(self, force=False):
        if not force:
            if not self.auto_refresh:
                return
            if not self.refresh_throttle.IsExpired():
                return

        try:
            self.frame_ids = list(PyUIManager.UIManager.get_frame_array())
            new_frames = {}
            for fid in self.frame_ids:
                try:
                    frame = self.frames.get(fid)
                    if frame is None:
                        frame = PyUIManager.UIFrame(fid)
                    else:
                        frame.get_context()
                    new_frames[fid] = frame
                except Exception:
                    continue

            self.frames = new_frames
            self._rebuild_tree()
            self._rebuild_runtime_paths()
            try:
                self.last_root_id = int(PyUIManager.UIManager.get_root_frame_id())
            except Exception:
                self.last_root_id = 0

            self.draw_enabled = {fid: v for fid, v in self.draw_enabled.items() if fid in self.frames and v}
            self.open_cards = {fid: v for fid, v in self.open_cards.items() if fid in self.frames and v}
            if self.selected_frame_id and self.selected_frame_id not in self.frames:
                self.selected_frame_id = 0

            self.status = f"Updated {len(self.frames)} frames"
        except Exception as exc:
            self.status = f"Update error: {exc}"

        self.refresh_throttle.Reset()

    def _rebuild_tree(self):
        children_by_parent = {}
        root_ids = []
        for fid, frame in self.frames.items():
            pid = int(getattr(frame, "parent_id", 0) or 0)
            children_by_parent.setdefault(pid, []).append(fid)

        for pid in children_by_parent:
            children_by_parent[pid].sort()

        for fid, frame in self.frames.items():
            pid = int(getattr(frame, "parent_id", 0) or 0)
            if pid == 0 or pid not in self.frames:
                root_ids.append(fid)

        self.children_by_parent = children_by_parent
        self.root_ids = sorted(root_ids)

    def _rebuild_runtime_paths(self):
        cache = {}

        def build_path(fid):
            if fid in cache:
                return cache[fid]
            frame = self.frames.get(fid)
            if frame is None:
                cache[fid] = ""
                return ""

            frame_hash = int(getattr(frame, "frame_hash", 0) or 0)
            if frame_hash:
                cache[fid] = str(frame_hash)
                return cache[fid]

            offsets = []
            current = frame
            seen = set()
            while current is not None:
                current_id = int(getattr(current, "frame_id", 0) or 0)
                if current_id in seen:
                    cache[fid] = ""
                    return ""
                seen.add(current_id)

                parent_id = int(getattr(current, "parent_id", 0) or 0)
                offsets.append(str(int(getattr(current, "child_offset_id", 0) or 0)))
                if parent_id == 0:
                    cache[fid] = ""
                    return ""
                parent = self.frames.get(parent_id)
                if parent is None:
                    cache[fid] = ""
                    return ""
                parent_hash = int(getattr(parent, "frame_hash", 0) or 0)
                if parent_hash:
                    cache[fid] = f"{parent_hash}," + ",".join(reversed(offsets))
                    return cache[fid]
                current = parent

            cache[fid] = ""
            return ""

        for fid in self.frames.keys():
            build_path(fid)
        self.runtime_paths = cache

    def count_hashed(self):
        return sum(1 for f in self.frames.values() if int(getattr(f, "frame_hash", 0) or 0) != 0)

    def count_visible(self):
        return sum(1 for f in self.frames.values() if bool(getattr(f, "is_visible", False)))

    def count_created(self):
        return sum(1 for f in self.frames.values() if bool(getattr(f, "is_created", False)))

    def count_ident_hash(self):
        count = 0
        for f in self.frames.values():
            _alias, source = self.identified_alias(f)
            if source == "hash":
                count += 1
        return count

    def count_ident_path(self):
        count = 0
        for f in self.frames.values():
            _alias, source = self.identified_alias(f)
            if source == "path":
                count += 1
        return count

    def repeated_hashes(self):
        counts = {}
        for f in self.frames.values():
            h = int(getattr(f, "frame_hash", 0) or 0)
            if h:
                counts[h] = counts.get(h, 0) + 1
        return {h: c for h, c in counts.items() if c > 1}

    def identified_alias(self, frame):
        frame_id = int(getattr(frame, "frame_id", 0) or 0)
        h = int(getattr(frame, "frame_hash", 0) or 0)
        if h and h in self.hash_aliases:
            alias = str(self.hash_aliases[h]).strip()
            if alias:
                return alias, "hash"
        path = self.runtime_paths.get(frame_id, "")
        if path and path in self.path_aliases:
            alias = str(self.path_aliases[path]).strip()
            if alias:
                return alias, "path"
        return "", ""

    def node_color(self, frame) -> Color:
        created = bool(getattr(frame, "is_created", False))
        visible = bool(getattr(frame, "is_visible", False))
        hashed = int(getattr(frame, "frame_hash", 0) or 0) != 0
        alias, source = self.identified_alias(frame)
        identified = bool(alias)

        if not created:
            return self.color_not_created_identified if identified else self.color_not_created_unidentified
        if not visible:
            return self.color_hidden_identified if identified else self.color_hidden_unidentified
        if identified and source == "hash":
            return self.color_identified_hash
        if identified and source == "path":
            return self.color_identified_path
        if hashed:
            return self.color_hashed_unidentified
        return self.color_nohash_unidentified

    def passes_filter(self, frame):
        if self.show_only_visible and not bool(getattr(frame, "is_visible", False)):
            return False
        if self.show_only_created and not bool(getattr(frame, "is_created", False)):
            return False
        return True

    def draw_overlays(self):
        ui = UIManager()
        for fid, enabled in list(self.draw_enabled.items()):
            if not enabled or fid not in self.frames:
                continue
            # Always draw with the frame's debug color (including its configured alpha).
            color = self.node_color(self.frames[fid])
            intcolor = color.opacity(90).to_color()
            try:
                ui.DrawFrame(fid, intcolor)
            except Exception:
                pass

    def generate_alias_index(self):
        try:
            with open(self.alias_source_json, "r", encoding="utf-8") as f:
                raw = json.load(f)
        except Exception as exc:
            self.alias_generation_info = f"Source alias read failed: {exc}"
            return False

        if not isinstance(raw, dict):
            self.alias_generation_info = "Source alias JSON is not a dictionary"
            return False

        hash_aliases = {}
        path_aliases = {}
        skipped = 0
        for key, value in raw.items():
            if not isinstance(value, str):
                skipped += 1
                continue
            k = str(key)
            parts = [p for p in k.split(",") if p]
            if not parts:
                skipped += 1
                continue
            if len(parts) == 1:
                try:
                    hash_aliases[str(int(parts[0]))] = value
                except ValueError:
                    skipped += 1
            else:
                path_aliases[k] = value

        payload = {
            "meta": {
                "generated_from": self.alias_source_json,
                "hash_count": len(hash_aliases),
                "path_count": len(path_aliases),
                "skipped": skipped,
            },
            "hash_aliases": hash_aliases,
            "path_aliases": path_aliases,
        }
        try:
            with open(self.alias_index_json, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=4, sort_keys=True)
        except Exception as exc:
            self.alias_generation_info = f"Alias index write failed: {exc}"
            return False

        self.alias_generation_info = (
            f"Generated {os.path.basename(self.alias_index_json)} "
            f"(hash={len(hash_aliases)} path={len(path_aliases)} skipped={skipped})"
        )
        self.load_alias_index()
        return True

    def load_alias_index(self):
        self.hash_aliases = {}
        self.path_aliases = {}
        try:
            with open(self.alias_index_json, "r", encoding="utf-8") as f:
                raw = json.load(f)
        except FileNotFoundError:
            self.alias_generation_info = "Alias index not found (click Generate Alias Index)"
            return False
        except Exception as exc:
            self.alias_generation_info = f"Alias index load failed: {exc}"
            return False

        if not isinstance(raw, dict):
            self.alias_generation_info = "Alias index JSON malformed"
            return False

        for k, v in (raw.get("hash_aliases", {}) or {}).items():
            if isinstance(v, str):
                try:
                    self.hash_aliases[int(str(k))] = v
                except ValueError:
                    pass
        for k, v in (raw.get("path_aliases", {}) or {}).items():
            if isinstance(v, str):
                self.path_aliases[str(k)] = v

        self.alias_generation_info = (
            f"Loaded alias index (hash={len(self.hash_aliases)} path={len(self.path_aliases)})"
        )
        return True


state = ViewerState()
state.load_alias_index()


def _toggle_draw(fid: int):
    state.draw_enabled[fid] = not state.draw_enabled.get(fid, False)


def _toggle_card(fid: int):
    state.open_cards[fid] = not state.open_cards.get(fid, False)
    if state.open_cards.get(fid, False):
        state.selected_frame_id = fid


def _compact_node_label(fid: int, frame):
    frame_hash = int(getattr(frame, "frame_hash", 0) or 0)
    alias, alias_kind = state.identified_alias(frame)
    if alias:
        base = f"{alias}"
        if state.show_alias_in_tree:
            base += " [HASH-ALIAS]" if alias_kind == "hash" else " [PATH-ALIAS]"
    else:
        base = (
            f"ID:{fid} H:{frame_hash if frame_hash else 'N/A'} "
            f"O:{int(getattr(frame, 'child_offset_id', 0) or 0)}"
        )
    if state.show_runtime_path_in_tree:
        runtime_path = state.runtime_paths.get(fid, "")
        if runtime_path:
            base += f" Path:{runtime_path}"
    return base


def _draw_frame_node(fid: int, depth: int = 0):
    if state._draw_counter >= state.max_nodes_drawn:
        return
    frame = state.frames.get(fid)
    if frame is None:
        return

    children = state.children_by_parent.get(fid, [])
    if not state.passes_filter(frame):
        for cid in children:
            _draw_frame_node(cid, depth)
        return

    state._draw_counter += 1
    label = _compact_node_label(fid, frame)

    if children:
        PyImGui.push_style_color(PyImGui.ImGuiCol.Text, state.node_color(frame).to_tuple_normalized())
        opened = PyImGui.tree_node(f"{label}##tree_{fid}")
        PyImGui.pop_style_color(1)
        PyImGui.same_line(0, -1)
        if PyImGui.small_button(f"{'Hide' if state.draw_enabled.get(fid, False) else 'Draw'}##draw_{fid}"):
            _toggle_draw(fid)
        PyImGui.same_line(0, -1)
        if PyImGui.small_button(f"{'CloseCard' if state.open_cards.get(fid, False) else 'Card'}##card_{fid}"):
            _toggle_card(fid)
        if opened:
            for cid in children:
                _draw_frame_node(cid, depth + 1)
            PyImGui.tree_pop()
    else:
        PyImGui.text_colored(label, state.node_color(frame).to_tuple_normalized())
        PyImGui.same_line(0, -1)
        if PyImGui.small_button(f"{'Hide' if state.draw_enabled.get(fid, False) else 'Draw'}##draw_{fid}"):
            _toggle_draw(fid)
        PyImGui.same_line(0, -1)
        if PyImGui.small_button(f"{'CloseCard' if state.open_cards.get(fid, False) else 'Card'}##card_{fid}"):
            _toggle_card(fid)


def _draw_frame_card(fid: int):
    if fid not in state.frames:
        return
    f = state.frames[fid]
    alias, alias_kind = state.identified_alias(f)
    runtime_path = state.runtime_paths.get(fid, "")
    frame_hash = int(getattr(f, "frame_hash", 0) or 0)
    title = alias if alias else f"Frame {fid}"
    title = f"{title}##frame_card_{fid}"

    open_flag = state.open_cards.get(fid, False)
    if not open_flag:
        return

    if not PyImGui.begin(title):
        PyImGui.end()
        return

    # Header row
    PyImGui.text_colored(f"Frame {fid}", state.node_color(f).to_tuple_normalized())
    PyImGui.same_line(0, -1)
    if PyImGui.small_button(f"{'Hide Overlay' if state.draw_enabled.get(fid, False) else 'Draw Overlay'}##draw_selected_{fid}"):
        _toggle_draw(fid)
    PyImGui.same_line(0, -1)
    if PyImGui.small_button(f"Close Card##close_card_{fid}"):
        state.open_cards[fid] = False
        PyImGui.end()
        return

    if alias:
        PyImGui.text(f"Alias ({'HASH-ALIAS' if alias_kind == 'hash' else 'PATH-ALIAS'}): {alias}")
    else:
        PyImGui.text("Alias: <unidentified>")

    PyImGui.separator()
    PyImGui.text(f"Frame Hash: {frame_hash}")
    PyImGui.text(f"Parent ID: {int(getattr(f, 'parent_id', 0) or 0)}")
    PyImGui.text(f"Child Offset ID: {int(getattr(f, 'child_offset_id', 0) or 0)}")
    PyImGui.text(f"Runtime Path: {runtime_path or 'N/A'}")
    PyImGui.text(f"Created: {bool(getattr(f, 'is_created', False))}")
    PyImGui.text(f"Visible: {bool(getattr(f, 'is_visible', False))}")
    PyImGui.text(f"Type: {int(getattr(f, 'type', 0) or 0)}")
    PyImGui.text(f"Template Type: {int(getattr(f, 'template_type', 0) or 0)}")
    PyImGui.text(f"Visibility Flags: {int(getattr(f, 'visibility_flags', 0) or 0)}")
    try:
        rel = f.relation
        PyImGui.text(f"Relation Parent ID: {int(getattr(rel, 'parent_id', 0) or 0)}")
        PyImGui.text(f"Relation Hash ID: {int(getattr(rel, 'frame_hash_id', 0) or 0)}")
    except Exception:
        pass
    try:
        pos = f.position
        PyImGui.text(
            f"Rect: L{pos.left_on_screen} T{pos.top_on_screen} R{pos.right_on_screen} B{pos.bottom_on_screen}"
        )
        PyImGui.text(
            f"Content: L{pos.content_left} T{pos.content_top} R{pos.content_right} B{pos.content_bottom}"
        )
    except Exception:
        pass

    # Quick actions for nearby relations
    if PyImGui.button(f"Open Parent Card##open_parent_{fid}"):
        pid = int(getattr(f, "parent_id", 0) or 0)
        if pid in state.frames:
            state.open_cards[pid] = True
            state.selected_frame_id = pid
    PyImGui.same_line(0, -1)
    if PyImGui.button(f"Open First Child Card##open_child_{fid}"):
        children = state.children_by_parent.get(fid, [])
        if children:
            cid = children[0]
            state.open_cards[cid] = True
            state.selected_frame_id = cid

    PyImGui.end()


def _draw_open_cards():
    open_ids = [fid for fid, is_open in state.open_cards.items() if is_open]
    for fid in open_ids:
        # frame may have disappeared after rebuild
        if fid not in state.frames:
            state.open_cards[fid] = False
            continue
        _draw_frame_card(fid)


def main():
    state.update()
    state.draw_overlays()

    if PyImGui.begin("Frame Viewer"):
        if PyImGui.collapsing_header("Controls"):
            if PyImGui.button("Refresh Now"):
                state.update(force=True)
            PyImGui.same_line(0, -1)
            state.auto_refresh = PyImGui.checkbox("Auto Refresh", state.auto_refresh)
            PyImGui.same_line(0, -1)
            if PyImGui.button("Clear Draw Toggles"):
                state.draw_enabled.clear()
            PyImGui.same_line(0, -1)
            if PyImGui.button("Close All Cards"):
                state.open_cards.clear()
            PyImGui.same_line(0, -1)
            if PyImGui.button("Generate Alias Index"):
                state.generate_alias_index()
            PyImGui.same_line(0, -1)
            if PyImGui.button("Reload Alias Index"):
                state.load_alias_index()

            state.show_only_visible = PyImGui.checkbox("Show Only Visible", state.show_only_visible)
            PyImGui.same_line(0, -1)
            state.show_only_created = PyImGui.checkbox("Show Only Created", state.show_only_created)
            state.show_alias_in_tree = PyImGui.checkbox("Show Alias In Tree", state.show_alias_in_tree)
            PyImGui.same_line(0, -1)
            state.show_runtime_path_in_tree = PyImGui.checkbox("Show Runtime Path In Tree", state.show_runtime_path_in_tree)

            state.max_nodes_drawn = PyImGui.input_int("Max Nodes Drawn", state.max_nodes_drawn)
            if state.max_nodes_drawn < 100:
                state.max_nodes_drawn = 100

        PyImGui.separator()
        
        if PyImGui.collapsing_header("Summary"):
            PyImGui.text(f"Status: {state.status}")
            PyImGui.text(f"Root Frame ID (native): {state.last_root_id}")
            PyImGui.text(f"Total Frames: {len(state.frames)}")
            PyImGui.text(f"Created: {state.count_created()}  Visible: {state.count_visible()}  Hashed: {state.count_hashed()}")
            PyImGui.text(f"Identified by Hash: {state.count_ident_hash()}  Identified by Path: {state.count_ident_path()}")
            PyImGui.text(f"Draw Enabled: {sum(1 for v in state.draw_enabled.values() if v)}")
            PyImGui.text_wrapped(f"Alias Index: {state.alias_generation_info}")

            if PyImGui.collapsing_header("Repeated Hashes"):
                repeats = state.repeated_hashes()
                if not repeats:
                    PyImGui.text("None")
                else:
                    for h, c in sorted(repeats.items()):
                        PyImGui.text(f"{h}: {c}")
                        
        PyImGui.text_colored("ID (Hash) + Created + Visible", state.color_identified_hash.to_tuple_normalized())
        PyImGui.text_colored("ID (NoHash) + Created + Visible", state.color_identified_path.to_tuple_normalized())
        PyImGui.text_colored("Hashed + UnID + Created + Visible", state.color_hashed_unidentified.to_tuple_normalized())
        PyImGui.text_colored("No Hash + UnID + Created + Visible", state.color_nohash_unidentified.to_tuple_normalized())
        PyImGui.text_colored("Hidden + ID", state.color_hidden_identified.to_tuple_normalized())
        PyImGui.text_colored("Hidden + UnID", state.color_hidden_unidentified.to_tuple_normalized())
        PyImGui.text_colored("Not Created + ID", state.color_not_created_identified.to_tuple_normalized())
        PyImGui.text_colored("Not Created + UnID", state.color_not_created_unidentified.to_tuple_normalized())

        PyImGui.separator()
        if PyImGui.begin_child("frame_tree_child", (0, 0), True, PyImGui.WindowFlags.HorizontalScrollbar):
            state._draw_counter = 0
            for root_id in state.root_ids:
                _draw_frame_node(root_id, 0)
            if state._draw_counter >= state.max_nodes_drawn:
                PyImGui.separator()
                PyImGui.text("Node draw limit reached. Increase 'Max Nodes Drawn' to show more.")
            PyImGui.end_child()

    PyImGui.end()
    _draw_open_cards()


if __name__ == "__main__":
    main()
