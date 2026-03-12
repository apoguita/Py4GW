from collections import defaultdict, deque
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, Iterator, List, Literal, Optional, Sequence, Tuple
import json
import time

import PyUIManager  # type: ignore

import PyImGui  # type: ignore

SelectionMode = Literal["all", "first", "nth"]
SearchScope = Literal["direct_children", "descendants"]
SortBy = Literal["top", "left", "right", "bottom", "area", "sibling_x", "sibling_y"]
SortOrder = Literal["asc", "desc"]


@dataclass(frozen=True)
class FramePositionRecord:
    top: int = 0
    left: int = 0
    bottom: int = 0
    right: int = 0
    content_top: int = 0
    content_left: int = 0
    content_bottom: int = 0
    content_right: int = 0
    unknown: int = 0
    scale_factor: float = 0.0
    viewport_width: float = 0.0
    viewport_height: float = 0.0
    screen_top: int = 0
    screen_left: int = 0
    screen_bottom: int = 0
    screen_right: int = 0
    top_on_screen: int = 0
    left_on_screen: int = 0
    bottom_on_screen: int = 0
    right_on_screen: int = 0
    width_on_screen: int = 0
    height_on_screen: int = 0
    viewport_scale_x: float = 0.0
    viewport_scale_y: float = 0.0

    @property
    def area_on_screen(self) -> int:
        return max(0, int(self.width_on_screen)) * max(0, int(self.height_on_screen))


@dataclass(frozen=True)
class FrameRelationRecord:
    parent_id: int = 0
    frame_hash_id: int = 0
    field67_0x124: int = 0
    field68_0x128: int = 0
    siblings: Tuple[int, ...] = ()


@dataclass
class FrameNodeRecord:
    frame_id: int
    parent_id: int
    frame_hash: int
    child_offset_id: int
    is_created: bool
    is_visible: bool
    visibility_flags: int
    type: int
    template_type: int
    frame_layout: int
    frame_state: int
    position: FramePositionRecord
    relation_parent_id: int
    relation_frame_hash_id: int
    siblings: Tuple[int, ...] = ()
    depth: Optional[int] = None
    root_id: Optional[int] = None
    nearest_hashed_ancestor_id: Optional[int] = None
    nearest_hashed_ancestor_hash: Optional[int] = None
    offset_path_from_hashed_ancestor: Tuple[int, ...] = ()
    sibling_rank_x: Optional[int] = None
    sibling_rank_y: Optional[int] = None

    @property
    def effective_hash(self) -> int:
        return self.frame_hash or self.relation_frame_hash_id


@dataclass(frozen=True)
class SnapshotDiagnostic:
    severity: Literal["info", "warning", "error"]
    code: str
    message: str
    frame_id: Optional[int] = None
    extra: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ChildResolverSpec:
    anchor_hash: int
    offset_path: Optional[List[int]] = None
    selection_mode: SelectionMode = "all"
    nth_index: Optional[int] = None
    search_scope: SearchScope = "descendants"
    max_depth_from_anchor: Optional[int] = None
    is_created: Optional[bool] = None
    is_visible: Optional[bool] = None
    type_in: Optional[List[int]] = None
    template_type_in: Optional[List[int]] = None
    frame_hash: Optional[int] = None
    child_offset_id: Optional[int] = None
    depth_from_anchor: Optional[int] = None
    child_count_min: Optional[int] = None
    child_count_max: Optional[int] = None
    parent_hash: Optional[int] = None
    sort_by: Optional[SortBy] = None
    sort_order: SortOrder = "asc"
    prefer_visible: bool = True
    prefer_created: bool = True
    screen_region_hint: Optional[Dict[str, int]] = None
    expected_rank_in_sorted: Optional[int] = None
    require_fast_path_match: bool = False
    fallback_to_search: bool = True

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ChildResolverSpec":
        return cls(**data)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class RankedFrameMatch:
    frame_id: int
    score: float
    rank: int
    reasons: List[str]
    node: FrameNodeRecord


@dataclass
class FrameSnapshot:
    nodes_by_id: Dict[int, FrameNodeRecord]
    children_by_parent_id: Dict[int, List[int]]
    parent_by_id: Dict[int, int]
    hash_to_id: Dict[int, int]
    root_ids: List[int]
    primary_root_id: Optional[int]
    build_timestamp_ms: Optional[int]
    frame_count: int
    diagnostics: List[SnapshotDiagnostic] = field(default_factory=list)

    def get_node(self, frame_id: int) -> Optional[FrameNodeRecord]:
        return self.nodes_by_id.get(frame_id)

    def children(self, frame_id: int) -> List[FrameNodeRecord]:
        return [self.nodes_by_id[cid] for cid in self.children_by_parent_id.get(frame_id, []) if cid in self.nodes_by_id]

    def descendants(self, frame_id: int, filters: Optional[Any] = None) -> List[FrameNodeRecord]:
        out: List[FrameNodeRecord] = []
        dq: deque[int] = deque(self.children_by_parent_id.get(frame_id, []))
        while dq:
            cid = dq.popleft()
            node = self.nodes_by_id.get(cid)
            if node is None:
                continue
            if _match_filter(node, filters):
                out.append(node)
            dq.extend(self.children_by_parent_id.get(cid, []))
        return out

    def iter_tree(self, root_id: Optional[int] = None, traversal: Literal["dfs", "bfs"] = "dfs") -> Iterator[FrameNodeRecord]:
        roots = [root_id] if root_id is not None else list(self.root_ids)
        seen: set[int] = set()
        if traversal == "bfs":
            dq: deque[int] = deque(roots)
            while dq:
                fid = dq.popleft()
                if fid in seen:
                    continue
                seen.add(fid)
                node = self.nodes_by_id.get(fid)
                if node is None:
                    continue
                yield node
                dq.extend(self.children_by_parent_id.get(fid, []))
            return
        stack = list(reversed(roots))
        while stack:
            fid = stack.pop()
            if fid in seen:
                continue
            seen.add(fid)
            node = self.nodes_by_id.get(fid)
            if node is None:
                continue
            yield node
            stack.extend(reversed(self.children_by_parent_id.get(fid, [])))

    def validate(self) -> List[SnapshotDiagnostic]:
        issues = list(self.diagnostics)
        for child_id, parent_id in self.parent_by_id.items():
            if child_id not in self.nodes_by_id:
                issues.append(SnapshotDiagnostic("error", "parent_index_missing_node", "Parent index references missing node", child_id))
            if parent_id != 0 and parent_id not in self.nodes_by_id:
                issues.append(SnapshotDiagnostic("warning", "missing_parent", "Node parent missing from snapshot", child_id, {"parent_id": parent_id}))
        for parent_id, child_ids in self.children_by_parent_id.items():
            for child_id in child_ids:
                node = self.nodes_by_id.get(child_id)
                if node is None:
                    issues.append(SnapshotDiagnostic("error", "children_index_missing_node", "Children index references missing node", child_id, {"parent_id": parent_id}))
                    continue
                if node.parent_id != parent_id:
                    issues.append(SnapshotDiagnostic("error", "parent_child_mismatch", "Child parent_id does not match index", child_id, {"index_parent_id": parent_id, "node_parent_id": node.parent_id}))
        return issues


@dataclass
class _ResolveDebugState:
    anchor_hash: int
    anchor_frame_id: Optional[int] = None
    fast_path_candidates: List[int] = field(default_factory=list)
    fast_path_valid_candidates: List[int] = field(default_factory=list)
    fallback_search_used: bool = False
    searched_candidate_count: int = 0


class FrameQueryEngine:
    SCORE_FAST_PATH = 100.0
    SCORE_TYPE_MATCH = 25.0
    SCORE_TEMPLATE_MATCH = 25.0
    SCORE_DEPTH_MATCH = 20.0
    SCORE_CHILD_OFFSET_MATCH = 10.0
    SCORE_VISIBLE_PREFERRED = 5.0
    SCORE_CREATED_PREFERRED = 5.0
    SCORE_EXPECTED_RANK_MATCH = 15.0
    SCORE_REGION_HINT = 10.0
    PENALTY_DEPTH_DISTANCE = 3.0
    PENALTY_RANK_DISTANCE = 2.0

    def __init__(
        self,
        snapshot: FrameSnapshot,
        hash_names: Optional[Dict[int, str]] = None,
        descriptors: Optional[Dict[str, ChildResolverSpec]] = None,
        legacy_aliases: Optional[Dict[str, str]] = None,
    ) -> None:
        self.snapshot = snapshot
        self.hash_names = hash_names or {}
        self.descriptors = descriptors or {}
        self.legacy_aliases = legacy_aliases or {}
        self._last_debug_state: Optional[_ResolveDebugState] = None

    def find_by_hash(self, frame_hash: int) -> Optional[FrameNodeRecord]:
        if not frame_hash:
            return None
        fid = self.snapshot.hash_to_id.get(frame_hash)
        return self.snapshot.get_node(fid) if fid is not None else None

    def find_children(self, parent_id: int, *, filters: Optional[Any] = None, sort: Optional[Tuple[SortBy, SortOrder]] = None) -> List[FrameNodeRecord]:
        nodes = [self.snapshot.nodes_by_id[cid] for cid in self.snapshot.children_by_parent_id.get(parent_id, []) if cid in self.snapshot.nodes_by_id]
        nodes = [n for n in nodes if _match_filter(n, filters)]
        return self._apply_sort(nodes, sort)

    def find_descendants(self, parent_id: int, *, filters: Optional[Any] = None, sort: Optional[Tuple[SortBy, SortOrder]] = None) -> List[FrameNodeRecord]:
        return self._apply_sort(self.snapshot.descendants(parent_id, filters=filters), sort)

    def resolve_offset_path(self, anchor_hash: int, offsets: List[int], *, validate: Optional[Any] = None) -> List[RankedFrameMatch]:
        anchor = self.find_by_hash(anchor_hash)
        if anchor is None:
            return []
        candidates = self._traverse_offset_path_branching(anchor.frame_id, offsets)
        valid = [n for n in candidates if _match_filter(n, validate)]
        spec = ChildResolverSpec(anchor_hash=anchor_hash, offset_path=list(offsets))
        return self._rank_candidates(anchor, valid, spec, {n.frame_id for n in valid})

    def resolve_under_hash(self, anchor_hash: int, query: ChildResolverSpec) -> List[RankedFrameMatch]:
        spec = query if isinstance(query, ChildResolverSpec) else ChildResolverSpec.from_dict(query)  # type: ignore[arg-type]
        if not spec.anchor_hash:
            spec.anchor_hash = anchor_hash
        anchor = self.find_by_hash(anchor_hash)
        self._last_debug_state = _ResolveDebugState(anchor_hash=anchor_hash)
        if anchor is None:
            return []
        self._last_debug_state.anchor_frame_id = anchor.frame_id

        fast_valid: List[FrameNodeRecord] = []
        if spec.offset_path:
            fast_candidates = self._traverse_offset_path_branching(anchor.frame_id, spec.offset_path)
            self._last_debug_state.fast_path_candidates = [n.frame_id for n in fast_candidates]
            fast_valid = [n for n in fast_candidates if self._matches_spec(anchor, n, spec)]
            self._last_debug_state.fast_path_valid_candidates = [n.frame_id for n in fast_valid]

        use_fallback = False
        if not fast_valid and spec.fallback_to_search:
            use_fallback = True
        if spec.require_fast_path_match and spec.offset_path and not fast_valid:
            use_fallback = False
        if fast_valid and spec.fallback_to_search and spec.selection_mode == "all":
            use_fallback = True

        search_candidates: List[FrameNodeRecord] = []
        if use_fallback:
            self._last_debug_state.fallback_search_used = True
            search_candidates = self._search_under_anchor(anchor, spec)
            self._last_debug_state.searched_candidate_count = len(search_candidates)

        merged: Dict[int, FrameNodeRecord] = {}
        for node in fast_valid:
            merged[node.frame_id] = node
        for node in search_candidates:
            merged[node.frame_id] = node

        ranked = self._rank_candidates(anchor, list(merged.values()), spec, {n.frame_id for n in fast_valid})
        return self._select_matches(ranked, spec)

    def explain_match(self, anchor_hash: int, query: ChildResolverSpec) -> Dict[str, Any]:
        matches = self.resolve_under_hash(anchor_hash, query)
        dbg = self._last_debug_state
        return {
            "anchor_hash": anchor_hash,
            "anchor_frame_id": dbg.anchor_frame_id if dbg else None,
            "query": query.to_dict(),
            "fast_path_candidates": dbg.fast_path_candidates if dbg else [],
            "fast_path_valid_candidates": dbg.fast_path_valid_candidates if dbg else [],
            "fallback_search_used": dbg.fallback_search_used if dbg else False,
            "searched_candidate_count": dbg.searched_candidate_count if dbg else 0,
            "matches": [{"frame_id": m.frame_id, "score": m.score, "rank": m.rank, "reasons": m.reasons} for m in matches],
        }

    def get_display_label(self, node: FrameNodeRecord, custom_alias: Optional[str] = None) -> str:
        if custom_alias:
            return custom_alias
        if node.effective_hash and node.effective_hash in self.hash_names:
            return self.hash_names[node.effective_hash]
        return f"Frame[{node.frame_id}]"

    def _apply_sort(self, nodes: List[FrameNodeRecord], sort: Optional[Tuple[SortBy, SortOrder]]) -> List[FrameNodeRecord]:
        if not sort:
            return nodes
        sort_by, sort_order = sort
        return sorted(nodes, key=lambda n: _sort_value(n, sort_by), reverse=(sort_order == "desc"))

    def _traverse_offset_path_branching(self, anchor_frame_id: int, offsets: Sequence[int]) -> List[FrameNodeRecord]:
        current_ids = [anchor_frame_id]
        for offset in offsets:
            next_ids: List[int] = []
            for pid in current_ids:
                for cid in self.snapshot.children_by_parent_id.get(pid, []):
                    node = self.snapshot.nodes_by_id.get(cid)
                    if node is not None and node.child_offset_id == offset:
                        next_ids.append(cid)
            if not next_ids:
                return []
            current_ids = next_ids
        return [self.snapshot.nodes_by_id[fid] for fid in current_ids if fid in self.snapshot.nodes_by_id]

    def _search_under_anchor(self, anchor: FrameNodeRecord, spec: ChildResolverSpec) -> List[FrameNodeRecord]:
        if spec.search_scope == "direct_children":
            candidates = self.find_children(anchor.frame_id)
        else:
            candidates = self.find_descendants(anchor.frame_id)
        return [n for n in candidates if self._matches_spec(anchor, n, spec)]

    def _matches_spec(self, anchor: FrameNodeRecord, node: FrameNodeRecord, spec: ChildResolverSpec) -> bool:
        if spec.search_scope == "direct_children" and node.parent_id != anchor.frame_id:
            return False
        if spec.search_scope != "direct_children" and node.frame_id == anchor.frame_id:
            return False
        depth_delta = _safe_depth_delta(anchor, node)
        if spec.max_depth_from_anchor is not None and depth_delta is not None and depth_delta > spec.max_depth_from_anchor:
            return False
        if spec.depth_from_anchor is not None and depth_delta != spec.depth_from_anchor:
            return False
        if spec.is_created is not None and node.is_created != spec.is_created:
            return False
        if spec.is_visible is not None and node.is_visible != spec.is_visible:
            return False
        if spec.type_in is not None and node.type not in spec.type_in:
            return False
        if spec.template_type_in is not None and node.template_type not in spec.template_type_in:
            return False
        if spec.frame_hash is not None and node.effective_hash != spec.frame_hash:
            return False
        if spec.child_offset_id is not None and node.child_offset_id != spec.child_offset_id:
            return False
        child_count = len(self.snapshot.children_by_parent_id.get(node.frame_id, []))
        if spec.child_count_min is not None and child_count < spec.child_count_min:
            return False
        if spec.child_count_max is not None and child_count > spec.child_count_max:
            return False
        if spec.parent_hash is not None:
            parent = self.snapshot.get_node(node.parent_id)
            if (parent.effective_hash if parent else 0) != spec.parent_hash:
                return False
        return True

    def _rank_candidates(self, anchor: FrameNodeRecord, candidates: List[FrameNodeRecord], spec: ChildResolverSpec, fast_path_ids: set[int]) -> List[RankedFrameMatch]:
        expected_order: Dict[int, int] = {}
        if spec.sort_by:
            sorted_for_rank = self._apply_sort(list(candidates), (spec.sort_by, spec.sort_order))
            expected_order = {n.frame_id: i for i, n in enumerate(sorted_for_rank)}

        scored: List[Tuple[float, float, FrameNodeRecord, List[str]]] = []
        for node in candidates:
            score = 0.0
            reasons: List[str] = []
            depth_delta = _safe_depth_delta(anchor, node)

            if node.frame_id in fast_path_ids:
                score += self.SCORE_FAST_PATH
                reasons.append("matched offset fast path")
            if spec.type_in is not None and node.type in spec.type_in:
                score += self.SCORE_TYPE_MATCH
                reasons.append("type matched")
            if spec.template_type_in is not None and node.template_type in spec.template_type_in:
                score += self.SCORE_TEMPLATE_MATCH
                reasons.append("template_type matched")
            if spec.depth_from_anchor is not None and depth_delta is not None:
                if depth_delta == spec.depth_from_anchor:
                    score += self.SCORE_DEPTH_MATCH
                    reasons.append("depth matched")
                else:
                    score -= abs(depth_delta - spec.depth_from_anchor) * self.PENALTY_DEPTH_DISTANCE
                    reasons.append("depth penalty")
            if spec.child_offset_id is not None and node.child_offset_id == spec.child_offset_id:
                score += self.SCORE_CHILD_OFFSET_MATCH
                reasons.append("child offset matched")
            if spec.prefer_visible and node.is_visible:
                score += self.SCORE_VISIBLE_PREFERRED
                reasons.append("visible preferred")
            if spec.prefer_created and node.is_created:
                score += self.SCORE_CREATED_PREFERRED
                reasons.append("created preferred")
            if spec.screen_region_hint and _inside_region(node.position, spec.screen_region_hint):
                score += self.SCORE_REGION_HINT
                reasons.append("in screen region")
            if spec.expected_rank_in_sorted is not None and spec.sort_by:
                actual_rank = expected_order.get(node.frame_id)
                if actual_rank is not None:
                    if actual_rank == spec.expected_rank_in_sorted:
                        score += self.SCORE_EXPECTED_RANK_MATCH
                        reasons.append("expected rank matched")
                    else:
                        score -= abs(actual_rank - spec.expected_rank_in_sorted) * self.PENALTY_RANK_DISTANCE
                        reasons.append("rank penalty")
            tie = _sort_value(node, spec.sort_by) if spec.sort_by else float(node.frame_id)
            scored.append((score, tie, node, reasons))

        reverse_tie = spec.sort_order == "desc"
        scored.sort(key=lambda t: (-t[0], -t[1] if reverse_tie else t[1], t[2].frame_id))
        return [RankedFrameMatch(frame_id=n.frame_id, score=s, rank=i, reasons=r, node=n) for i, (s, _t, n, r) in enumerate(scored)]

    def _select_matches(self, matches: List[RankedFrameMatch], spec: ChildResolverSpec) -> List[RankedFrameMatch]:
        if spec.selection_mode == "first":
            return matches[:1]
        if spec.selection_mode == "nth":
            if spec.nth_index is None:
                return []
            return [matches[spec.nth_index]] if 0 <= spec.nth_index < len(matches) else []
        return matches


def _match_filter(node: FrameNodeRecord, filters: Optional[Any]) -> bool:
    if filters is None:
        return True
    if callable(filters):
        return bool(filters(node))
    if isinstance(filters, dict):
        for key, value in filters.items():
            if key == "type_in":
                if node.type not in value:
                    return False
                continue
            if key == "template_type_in":
                if node.template_type not in value:
                    return False
                continue
            if key == "frame_hash":
                if node.effective_hash != value:
                    return False
                continue
            if getattr(node, key, None) != value:
                return False
    return True


def _safe_depth_delta(anchor: FrameNodeRecord, node: FrameNodeRecord) -> Optional[int]:
    if anchor.depth is None or node.depth is None:
        return None
    return node.depth - anchor.depth


def _sort_value(node: FrameNodeRecord, sort_by: Optional[SortBy]) -> float:
    if not sort_by:
        return float(node.frame_id)
    pos = node.position
    if sort_by == "top":
        return float(pos.top_on_screen)
    if sort_by == "left":
        return float(pos.left_on_screen)
    if sort_by == "right":
        return float(pos.right_on_screen)
    if sort_by == "bottom":
        return float(pos.bottom_on_screen)
    if sort_by == "area":
        return float(pos.area_on_screen)
    if sort_by == "sibling_x":
        return float(node.sibling_rank_x if node.sibling_rank_x is not None else 1_000_000)
    if sort_by == "sibling_y":
        return float(node.sibling_rank_y if node.sibling_rank_y is not None else 1_000_000)
    return float(node.frame_id)


def _inside_region(pos: FramePositionRecord, region: Dict[str, int]) -> bool:
    x0 = int(region.get("x0", -10_000_000))
    y0 = int(region.get("y0", -10_000_000))
    x1 = int(region.get("x1", 10_000_000))
    y1 = int(region.get("y1", 10_000_000))
    cx = (int(pos.left_on_screen) + int(pos.right_on_screen)) // 2
    cy = (int(pos.top_on_screen) + int(pos.bottom_on_screen)) // 2
    return x0 <= cx <= x1 and y0 <= cy <= y1


def _copy_position(src: Any) -> FramePositionRecord:
    if src is None:
        return FramePositionRecord()
    data: Dict[str, Any] = {}
    for key, field_info in FramePositionRecord.__dataclass_fields__.items():
        data[key] = getattr(src, key, field_info.default)
    return FramePositionRecord(**data)


def _copy_relation(src: Any) -> FrameRelationRecord:
    if src is None:
        return FrameRelationRecord()
    siblings = getattr(src, "siblings", []) or []
    try:
        siblings_tuple = tuple(int(x) for x in siblings)
    except Exception:
        siblings_tuple = ()
    return FrameRelationRecord(
        parent_id=int(getattr(src, "parent_id", 0) or 0),
        frame_hash_id=int(getattr(src, "frame_hash_id", 0) or 0),
        field67_0x124=int(getattr(src, "field67_0x124", 0) or 0),
        field68_0x128=int(getattr(src, "field68_0x128", 0) or 0),
        siblings=siblings_tuple,
    )


def _frame_node_from_uiframe(frame: Any) -> FrameNodeRecord:
    relation = _copy_relation(getattr(frame, "relation", None))
    return FrameNodeRecord(
        frame_id=int(getattr(frame, "frame_id", 0) or 0),
        parent_id=int(getattr(frame, "parent_id", 0) or 0),
        frame_hash=int(getattr(frame, "frame_hash", 0) or 0),
        child_offset_id=int(getattr(frame, "child_offset_id", 0) or 0),
        is_created=bool(getattr(frame, "is_created", False)),
        is_visible=bool(getattr(frame, "is_visible", False)),
        visibility_flags=int(getattr(frame, "visibility_flags", 0) or 0),
        type=int(getattr(frame, "type", 0) or 0),
        template_type=int(getattr(frame, "template_type", 0) or 0),
        frame_layout=int(getattr(frame, "frame_layout", 0) or 0),
        frame_state=int(getattr(frame, "frame_state", 0) or 0),
        position=_copy_position(getattr(frame, "position", None)),
        relation_parent_id=relation.parent_id,
        relation_frame_hash_id=relation.frame_hash_id,
        siblings=relation.siblings,
    )


def build_snapshot(*, refresh_context: bool = False, root_frame_id_hint: Optional[int] = None) -> FrameSnapshot:
    if PyUIManager is None:
        raise RuntimeError("PyUIManager module is not available in this runtime")

    nodes_by_id: Dict[int, FrameNodeRecord] = {}
    children_by_parent_id: Dict[int, List[int]] = defaultdict(list)
    parent_by_id: Dict[int, int] = {}
    hash_to_id: Dict[int, int] = {}
    diagnostics: List[SnapshotDiagnostic] = []

    for raw_fid in list(PyUIManager.UIManager.get_frame_array()):
        fid = int(raw_fid)
        try:
            ui_frame = PyUIManager.UIFrame(fid)
            if refresh_context and hasattr(ui_frame, "get_context"):
                ui_frame.get_context()
            node = _frame_node_from_uiframe(ui_frame)
        except Exception as exc:
            diagnostics.append(SnapshotDiagnostic("warning", "uiframe_read_failed", "Failed to read UIFrame during snapshot build", fid, {"error": str(exc)}))
            continue

        nodes_by_id[node.frame_id] = node
        parent_by_id[node.frame_id] = node.parent_id
        children_by_parent_id[node.parent_id].append(node.frame_id)

        h = node.effective_hash
        if h:
            if h in hash_to_id:
                diagnostics.append(SnapshotDiagnostic("error", "duplicate_hash", "Duplicate non-zero frame hash detected; keeping first", node.frame_id, {"hash": h, "kept_frame_id": hash_to_id[h]}))
            else:
                hash_to_id[h] = node.frame_id

    root_ids = sorted([fid for fid, n in nodes_by_id.items() if n.parent_id == 0 or n.parent_id not in nodes_by_id])

    if root_frame_id_hint is None:
        try:
            root_frame_id_hint = int(PyUIManager.UIManager.get_root_frame_id())
        except Exception:
            root_frame_id_hint = None

    primary_root_id = root_frame_id_hint if root_frame_id_hint in nodes_by_id else (root_ids[0] if root_ids else None)
    snapshot = FrameSnapshot(
        nodes_by_id=nodes_by_id,
        children_by_parent_id=dict(children_by_parent_id),
        parent_by_id=parent_by_id,
        hash_to_id=hash_to_id,
        root_ids=root_ids,
        primary_root_id=primary_root_id,
        build_timestamp_ms=int(time.time() * 1000),
        frame_count=len(nodes_by_id),
        diagnostics=diagnostics,
    )
    _compute_derived_fields(snapshot)
    return snapshot


def _compute_derived_fields(snapshot: FrameSnapshot) -> None:
    for _parent_id, child_ids in snapshot.children_by_parent_id.items():
        siblings = [snapshot.nodes_by_id[cid] for cid in child_ids if cid in snapshot.nodes_by_id]
        by_x = sorted(siblings, key=lambda n: (n.position.left_on_screen, n.frame_id))
        by_y = sorted(siblings, key=lambda n: (n.position.top_on_screen, n.frame_id))
        x_rank = {n.frame_id: i for i, n in enumerate(by_x)}
        y_rank = {n.frame_id: i for i, n in enumerate(by_y)}
        for n in siblings:
            n.sibling_rank_x = x_rank.get(n.frame_id)
            n.sibling_rank_y = y_rank.get(n.frame_id)

    visited: set[int] = set()
    roots = list(snapshot.root_ids)
    for root_id in roots:
        _traverse_assign(snapshot, root_id, visited)

    for fid in sorted(snapshot.nodes_by_id.keys()):
        if fid in visited:
            continue
        snapshot.diagnostics.append(SnapshotDiagnostic("error", "unvisited_component", "Unvisited component detected; possible cycle", fid))
        _traverse_assign(snapshot, fid, visited, force_root=True)


def _traverse_assign(snapshot: FrameSnapshot, root_id: int, visited: set[int], force_root: bool = False) -> None:
    root = snapshot.nodes_by_id.get(root_id)
    if root is None:
        return
    root_hash = root.effective_hash or None
    root_hashed_id = root.frame_id if root_hash else None
    dq: deque[Tuple[int, int, Optional[int], Optional[int], Tuple[int, ...], frozenset[int]]] = deque()
    dq.append((root_id, 0, root_hashed_id, root_hash, (), frozenset()))

    while dq:
        fid, depth, nearest_hid, nearest_hhash, off_path, lineage = dq.popleft()
        if fid in lineage:
            snapshot.diagnostics.append(SnapshotDiagnostic("error", "cycle_detected", "Cycle detected during traversal", fid))
            continue
        node = snapshot.nodes_by_id.get(fid)
        if node is None:
            continue
        if fid in visited and not force_root:
            continue
        visited.add(fid)

        node.depth = depth
        node.root_id = root_id
        if node.effective_hash:
            node.nearest_hashed_ancestor_id = node.frame_id
            node.nearest_hashed_ancestor_hash = node.effective_hash
            node.offset_path_from_hashed_ancestor = ()
            child_anchor_id = node.frame_id
            child_anchor_hash = node.effective_hash
            child_prefix: Tuple[int, ...] = ()
        else:
            node.nearest_hashed_ancestor_id = nearest_hid
            node.nearest_hashed_ancestor_hash = nearest_hhash
            node.offset_path_from_hashed_ancestor = off_path
            child_anchor_id = nearest_hid
            child_anchor_hash = nearest_hhash
            child_prefix = off_path

        new_lineage = set(lineage)
        new_lineage.add(fid)
        for cid in snapshot.children_by_parent_id.get(fid, []):
            child = snapshot.nodes_by_id.get(cid)
            if child is None:
                continue
            next_path = child_prefix + (child.child_offset_id,) if child_anchor_hash else ()
            dq.append((cid, depth + 1, child_anchor_id, child_anchor_hash, next_path, frozenset(new_lineage)))


def make_engine(
    snapshot: FrameSnapshot,
    hash_names: Optional[Dict[int, str]] = None,
    descriptors: Optional[Dict[str, ChildResolverSpec]] = None,
    legacy_aliases: Optional[Dict[str, str]] = None,
) -> FrameQueryEngine:
    return FrameQueryEngine(snapshot, hash_names=hash_names, descriptors=descriptors, legacy_aliases=legacy_aliases)


def load_hash_name_dict(path: str) -> Dict[int, str]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            raw = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}
    if not isinstance(raw, dict):
        return {}
    out: Dict[int, str] = {}
    for k, v in raw.items():
        if not isinstance(v, str):
            continue
        try:
            out[int(str(k))] = v
        except ValueError:
            continue
    return out


def save_hash_name_dict(path: str, mapping: Dict[int, str]) -> None:
    serializable = {str(int(k)): v for k, v in sorted(mapping.items(), key=lambda item: int(item[0]))}
    with open(path, "w", encoding="utf-8") as f:
        json.dump(serializable, f, indent=4)


def load_legacy_aliases(path: str) -> Dict[str, str]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            raw = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}
    if not isinstance(raw, dict):
        return {}
    return {str(k): str(v) for k, v in raw.items() if isinstance(v, str)}


def load_descriptors(path: str) -> Dict[str, ChildResolverSpec]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            raw = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}
    if not isinstance(raw, dict):
        return {}
    out: Dict[str, ChildResolverSpec] = {}
    for name, spec_data in raw.items():
        if not isinstance(name, str) or not isinstance(spec_data, dict):
            continue
        try:
            out[name] = ChildResolverSpec.from_dict(spec_data)
        except TypeError:
            continue
    return out


def save_descriptors(path: str, descriptors: Dict[str, ChildResolverSpec]) -> None:
    payload: Dict[str, Dict[str, Any]] = {}
    for name, spec in descriptors.items():
        payload[name] = spec.to_dict() if isinstance(spec, ChildResolverSpec) else dict(spec)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=4, sort_keys=True)


def snapshot_summary(snapshot: FrameSnapshot) -> Dict[str, Any]:
    return {
        "frame_count": snapshot.frame_count,
        "root_ids": list(snapshot.root_ids),
        "primary_root_id": snapshot.primary_root_id,
        "hash_count": len(snapshot.hash_to_id),
        "diagnostics": [asdict(d) for d in snapshot.diagnostics],
    }


def format_tree_lines(
    snapshot: FrameSnapshot,
    *,
    root_id: Optional[int] = None,
    max_depth: Optional[int] = None,
    hash_names: Optional[Dict[int, str]] = None,
) -> List[str]:
    hash_names = hash_names or {}
    lines: List[str] = []
    for node in snapshot.iter_tree(root_id=root_id):
        depth = node.depth or 0
        if max_depth is not None and depth > max_depth:
            continue
        name = hash_names.get(node.effective_hash, "") if node.effective_hash else ""
        line = (
            f"{'  ' * depth}- id={node.frame_id} parent={node.parent_id} "
            f"hash={node.effective_hash} off={node.child_offset_id} "
            f"vis={int(node.is_visible)} cr={int(node.is_created)}"
        )
        if name:
            line += f" name={name}"
        lines.append(line)
    return lines


class _EngineUIState:
    def __init__(self) -> None:
        self.window_name = "Runtime Frame Tree Engine"
        self.snapshot: Optional[FrameSnapshot] = None
        self.engine: Optional[FrameQueryEngine] = None
        self.hash_names: Dict[int, str] = {}
        self.descriptors: Dict[str, ChildResolverSpec] = {}
        self.legacy_aliases: Dict[str, str] = {}
        self.hash_names_path = "Py4GWCoreLib\\frame_hash_names.json"
        self.descriptors_path = "Py4GWCoreLib\\frame_child_descriptors.json"
        self.legacy_aliases_path = "Py4GWCoreLib\\frame_aliases.json"
        self.auto_rebuild = False
        self.auto_rebuild_ms = 1000
        self._last_rebuild_ms = 0
        self.status = "Idle"
        self.selected_frame_id: int = 0
        self.lookup_hash: int = 0
        self.lookup_offsets_text = ""
        self.lookup_results: List[RankedFrameMatch] = []
        self.lookup_message = ""

        self.resolver_name = "TempResolver"
        self.resolver_anchor_hash: int = 0
        self.resolver_offsets_text = ""
        self.resolver_scope_idx = 1  # descendants
        self.resolver_selection_idx = 0  # all
        self.resolver_nth_index = 0
        self.resolver_type_text = ""
        self.resolver_template_type_text = ""
        self.resolver_visible_mode = 0  # any/true/false
        self.resolver_created_mode = 0  # any/true/false
        self.resolver_sort_idx = 0  # none
        self.resolver_sort_desc = False
        self.resolver_results: List[RankedFrameMatch] = []
        self.resolver_debug: Dict[str, Any] = {}

    def _now_ms(self) -> int:
        return int(time.time() * 1000)

    def maybe_auto_rebuild(self) -> None:
        if not self.auto_rebuild:
            return
        now_ms = self._now_ms()
        if now_ms - self._last_rebuild_ms >= max(100, int(self.auto_rebuild_ms)):
            self.rebuild()

    def reload_mappings(self) -> None:
        self.hash_names = load_hash_name_dict(self.hash_names_path)
        self.descriptors = load_descriptors(self.descriptors_path)
        self.legacy_aliases = load_legacy_aliases(self.legacy_aliases_path)

    def rebuild(self) -> None:
        try:
            self.reload_mappings()
            self.snapshot = build_snapshot()
            self.engine = make_engine(
                self.snapshot,
                hash_names=self.hash_names,
                descriptors=self.descriptors,
                legacy_aliases=self.legacy_aliases,
            )
            self._last_rebuild_ms = self._now_ms()
            self.status = f"Built snapshot: {self.snapshot.frame_count} frames, {len(self.snapshot.hash_to_id)} hashes"
            if self.selected_frame_id and self.snapshot.get_node(self.selected_frame_id) is None:
                self.selected_frame_id = 0
        except Exception as exc:
            self.status = f"Rebuild failed: {exc}"
            self.snapshot = None
            self.engine = None


_ui_state = _EngineUIState()


def _parse_csv_ints(text: str) -> List[int]:
    out: List[int] = []
    for chunk in (text or "").replace(" ", "").split(","):
        if not chunk:
            continue
        try:
            out.append(int(chunk))
        except ValueError:
            continue
    return out


def _parse_optional_int_list(text: str) -> Optional[List[int]]:
    vals = _parse_csv_ints(text)
    return vals if vals else None


def _bool_mode_to_optional(mode: int) -> Optional[bool]:
    # 0=any, 1=true, 2=false
    if mode == 1:
        return True
    if mode == 2:
        return False
    return None


def _sort_choice_to_value(idx: int) -> Optional[SortBy]:
    mapping = [None, "top", "left", "right", "bottom", "area", "sibling_x", "sibling_y"]
    if 0 <= idx < len(mapping):
        return mapping[idx]  # type: ignore[return-value]
    return None


def _selection_choice_to_value(idx: int) -> SelectionMode:
    return ["all", "first", "nth"][max(0, min(2, idx))]  # type: ignore[return-value]


def _scope_choice_to_value(idx: int) -> SearchScope:
    return ["direct_children", "descendants"][max(0, min(1, idx))]  # type: ignore[return-value]


def _draw_frame_node_tree(snapshot: FrameSnapshot, engine: Optional[FrameQueryEngine], frame_id: int, state: _EngineUIState) -> None:
    node = snapshot.get_node(frame_id)
    if node is None:
        return
    h = node.effective_hash
    name = engine.hash_names.get(h, "") if (engine and h) else ""
    label = f"[{node.frame_id}] <{h}> off:{node.child_offset_id}"
    if name:
        label += f" {name}"

    children = snapshot.children_by_parent_id.get(frame_id, [])
    is_selected = state.selected_frame_id == frame_id
    if children:
        opened = PyImGui.tree_node(f"{label}##frame_{frame_id}")
        PyImGui.same_line(0, -1)
        if PyImGui.small_button(f"{'*' if is_selected else 'Select'}##sel_{frame_id}"):
            state.selected_frame_id = frame_id
        if opened:
            for cid in children:
                _draw_frame_node_tree(snapshot, engine, cid, state)
            PyImGui.tree_pop()
    else:
        PyImGui.bullet_text(label)
        PyImGui.same_line(0, -1)
        if PyImGui.small_button(f"{'*' if is_selected else 'Select'}##sel_{frame_id}"):
            state.selected_frame_id = frame_id


def _draw_selected_frame_panel(state: _EngineUIState) -> None:
    if not state.snapshot or not state.selected_frame_id:
        PyImGui.text("No frame selected")
        return
    node = state.snapshot.get_node(state.selected_frame_id)
    if node is None:
        PyImGui.text("Selected frame no longer exists in snapshot")
        return

    PyImGui.text(f"Frame ID: {node.frame_id}")
    PyImGui.text(f"Parent ID: {node.parent_id}")
    PyImGui.text(f"Hash: {node.effective_hash}")
    PyImGui.text(f"Child Offset: {node.child_offset_id}")
    PyImGui.text(f"Visible: {node.is_visible}  Created: {node.is_created}")
    PyImGui.text(f"Type: {node.type}  Template: {node.template_type}  Layout: {node.frame_layout}")
    PyImGui.text(f"Depth: {node.depth}  Root: {node.root_id}")
    PyImGui.text(f"Nearest Anchor Hash: {node.nearest_hashed_ancestor_hash}")
    PyImGui.text(f"Offset Path From Anchor: {list(node.offset_path_from_hashed_ancestor)}")
    pos = node.position
    PyImGui.text(f"Screen Rect: L{pos.left_on_screen} T{pos.top_on_screen} R{pos.right_on_screen} B{pos.bottom_on_screen}")


def _draw_snapshot_tab(state: _EngineUIState) -> None:
    if PyImGui.button("Rebuild Snapshot"):
        state.rebuild()
    PyImGui.same_line(0, -1)
    if PyImGui.button("Reload Mappings"):
        try:
            state.reload_mappings()
            if state.snapshot:
                state.engine = make_engine(state.snapshot, hash_names=state.hash_names, descriptors=state.descriptors, legacy_aliases=state.legacy_aliases)
            state.status = "Mappings reloaded"
        except Exception as exc:
            state.status = f"Reload mappings failed: {exc}"

    state.auto_rebuild = PyImGui.checkbox("Auto rebuild", state.auto_rebuild)
    state.auto_rebuild_ms = PyImGui.input_int("Auto rebuild ms", state.auto_rebuild_ms)
    if state.auto_rebuild_ms < 100:
        state.auto_rebuild_ms = 100

    state.hash_names_path = PyImGui.input_text("Hash names JSON", state.hash_names_path)
    state.descriptors_path = PyImGui.input_text("Descriptors JSON", state.descriptors_path)
    state.legacy_aliases_path = PyImGui.input_text("Legacy aliases JSON", state.legacy_aliases_path)
    PyImGui.separator()
    PyImGui.text_wrapped(state.status)

    if state.snapshot:
        summary = snapshot_summary(state.snapshot)
        PyImGui.text(f"Frames: {summary['frame_count']}")
        PyImGui.text(f"Roots: {len(summary['root_ids'])}  Primary root: {summary['primary_root_id']}")
        PyImGui.text(f"Hashed frames: {summary['hash_count']}")
        PyImGui.text(f"Diagnostics: {len(summary['diagnostics'])}")
        if PyImGui.collapsing_header("Diagnostics"):
            for d in state.snapshot.validate():
                PyImGui.text(f"[{d.severity}] {d.code} frame={d.frame_id} {d.message}")


def _draw_tree_tab(state: _EngineUIState) -> None:
    if not state.snapshot:
        PyImGui.text("Build a snapshot first")
        return
    if PyImGui.begin_child("RuntimeFrameTreeLeft", (700, 500), True):
        for root_id in state.snapshot.root_ids:
            _draw_frame_node_tree(state.snapshot, state.engine, root_id, state)
        PyImGui.end_child()
    PyImGui.same_line(0, -1)
    if PyImGui.begin_child("RuntimeFrameTreeRight", (500, 500), True):
        _draw_selected_frame_panel(state)
        PyImGui.end_child()


def _draw_lookup_tab(state: _EngineUIState) -> None:
    if not state.engine:
        PyImGui.text("Build a snapshot first")
        return

    state.lookup_hash = PyImGui.input_int("Lookup hash", state.lookup_hash)
    if PyImGui.button("Find by Hash"):
        node = state.engine.find_by_hash(state.lookup_hash)
        if node:
            state.selected_frame_id = node.frame_id
            state.lookup_message = f"Found frame_id={node.frame_id}"
        else:
            state.lookup_message = "Hash not found"
    PyImGui.same_line(0, -1)
    if PyImGui.button("Use Selected Hash") and state.snapshot and state.selected_frame_id:
        node = state.snapshot.get_node(state.selected_frame_id)
        if node:
            state.lookup_hash = node.effective_hash

    PyImGui.text_wrapped(state.lookup_message)
    PyImGui.separator()

    state.lookup_offsets_text = PyImGui.input_text("Offset path CSV", state.lookup_offsets_text)
    if PyImGui.button("Resolve Offset Path"):
        offsets = _parse_csv_ints(state.lookup_offsets_text)
        state.lookup_results = state.engine.resolve_offset_path(state.lookup_hash, offsets)
    if PyImGui.collapsing_header("Offset Path Results"):
        for m in state.lookup_results:
            PyImGui.text(f"rank={m.rank} score={m.score:.1f} frame={m.frame_id} reasons={', '.join(m.reasons)}")
            PyImGui.same_line(0, -1)
            if PyImGui.small_button(f"Select##lookup_{m.frame_id}"):
                state.selected_frame_id = m.frame_id


def _build_resolver_spec_from_ui(state: _EngineUIState) -> ChildResolverSpec:
    sort_by = _sort_choice_to_value(state.resolver_sort_idx)
    return ChildResolverSpec(
        anchor_hash=state.resolver_anchor_hash,
        offset_path=_parse_optional_int_list(state.resolver_offsets_text),
        selection_mode=_selection_choice_to_value(state.resolver_selection_idx),
        nth_index=state.resolver_nth_index if _selection_choice_to_value(state.resolver_selection_idx) == "nth" else None,
        search_scope=_scope_choice_to_value(state.resolver_scope_idx),
        is_visible=_bool_mode_to_optional(state.resolver_visible_mode),
        is_created=_bool_mode_to_optional(state.resolver_created_mode),
        type_in=_parse_optional_int_list(state.resolver_type_text),
        template_type_in=_parse_optional_int_list(state.resolver_template_type_text),
        sort_by=sort_by,
        sort_order="desc" if state.resolver_sort_desc else "asc",
    )


def _draw_resolver_tab(state: _EngineUIState) -> None:
    if not state.engine:
        PyImGui.text("Build a snapshot first")
        return
    if state.selected_frame_id and state.snapshot:
        node = state.snapshot.get_node(state.selected_frame_id)
        if node and PyImGui.button("Use Selected As Anchor"):
            state.resolver_anchor_hash = node.effective_hash

    state.resolver_anchor_hash = PyImGui.input_int("Anchor hash", state.resolver_anchor_hash)
    state.resolver_name = PyImGui.input_text("Resolver name", state.resolver_name)
    state.resolver_offsets_text = PyImGui.input_text("Offset path CSV", state.resolver_offsets_text)
    state.resolver_type_text = PyImGui.input_text("Type filter CSV", state.resolver_type_text)
    state.resolver_template_type_text = PyImGui.input_text("Template filter CSV", state.resolver_template_type_text)
    state.resolver_nth_index = PyImGui.input_int("Nth index", state.resolver_nth_index)
    if state.resolver_nth_index < 0:
        state.resolver_nth_index = 0

    scope_labels = ["direct_children", "descendants"]
    sel_labels = ["all", "first", "nth"]
    sort_labels = ["none", "top", "left", "right", "bottom", "area", "sibling_x", "sibling_y"]
    vis_labels = ["any", "true", "false"]
    cre_labels = ["any", "true", "false"]

    state.resolver_scope_idx = PyImGui.combo("Search scope", state.resolver_scope_idx, scope_labels)
    state.resolver_selection_idx = PyImGui.combo("Selection", state.resolver_selection_idx, sel_labels)
    state.resolver_sort_idx = PyImGui.combo("Sort by", state.resolver_sort_idx, sort_labels)
    state.resolver_visible_mode = PyImGui.combo("Visible", state.resolver_visible_mode, vis_labels)
    state.resolver_created_mode = PyImGui.combo("Created", state.resolver_created_mode, cre_labels)
    state.resolver_sort_desc = PyImGui.checkbox("Sort descending", state.resolver_sort_desc)

    if PyImGui.button("Run Resolver"):
        spec = _build_resolver_spec_from_ui(state)
        state.resolver_results = state.engine.resolve_under_hash(spec.anchor_hash, spec)
        state.resolver_debug = state.engine.explain_match(spec.anchor_hash, spec)

    PyImGui.same_line(0, -1)
    if PyImGui.button("Save Resolver Descriptor"):
        try:
            spec = _build_resolver_spec_from_ui(state)
            state.descriptors[state.resolver_name] = spec
            save_descriptors(state.descriptors_path, state.descriptors)
            state.status = f"Saved descriptor '{state.resolver_name}'"
        except Exception as exc:
            state.status = f"Save descriptor failed: {exc}"

    if PyImGui.collapsing_header("Resolver Results"):
        for m in state.resolver_results:
            PyImGui.text(f"rank={m.rank} score={m.score:.1f} frame={m.frame_id} hash={m.node.effective_hash}")
            PyImGui.same_line(0, -1)
            if PyImGui.small_button(f"Select##resolver_{m.frame_id}"):
                state.selected_frame_id = m.frame_id
        if state.resolver_debug:
            PyImGui.separator()
            PyImGui.text(f"Fast path candidates: {state.resolver_debug.get('fast_path_candidates', [])}")
            PyImGui.text(f"Fast path valid: {state.resolver_debug.get('fast_path_valid_candidates', [])}")
            PyImGui.text(f"Fallback used: {state.resolver_debug.get('fallback_search_used', False)}")


def draw_ui() -> None:
    if PyImGui is None:
        return
    state = _ui_state
    state.maybe_auto_rebuild()

    flags = getattr(PyImGui.WindowFlags, "AlwaysAutoResize", 0)
    if PyImGui.begin(state.window_name, flags):
        if PyImGui.begin_tab_bar("RuntimeFrameTreeEngineTabs"):
            if PyImGui.begin_tab_item("Snapshot"):
                _draw_snapshot_tab(state)
                PyImGui.end_tab_item()
            if PyImGui.begin_tab_item("Tree"):
                _draw_tree_tab(state)
                PyImGui.end_tab_item()
            if PyImGui.begin_tab_item("Lookup"):
                _draw_lookup_tab(state)
                PyImGui.end_tab_item()
            if PyImGui.begin_tab_item("Resolver"):
                _draw_resolver_tab(state)
                PyImGui.end_tab_item()
            PyImGui.end_tab_bar()
    PyImGui.end()


def main() -> None:
    draw_ui()


if __name__ == "__main__":
    if PyImGui is not None:
        main()
    else:
        try:
            snap = build_snapshot()
            print(json.dumps(snapshot_summary(snap), indent=2))
        except Exception as exc:
            print(f"RuntimeFrameTreeEngine error: {exc}")
