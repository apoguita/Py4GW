from __future__ import annotations

import ast
import inspect
from pathlib import Path
import re
from typing import Iterable


class SearchTarget:
    def __init__(self, label: str, path: Path):
        self.label = label
        self.path = path

    @property
    def kind(self) -> str:
        if self.path.is_dir():
            return "Folder"
        if self.path.is_file():
            return "File"
        return "Missing"


class DiscoveryEntry:
    def __init__(
        self,
        source_label: str,
        source_path: str,
        group_name: str,
        group_display: str,
        entry_kind: str,
        name: str,
        display: str,
        qualname: str,
        signature: str,
        lineno: int,
        expose: bool,
        audience: str,
        purpose: str,
        user_description: str,
        notes: str,
        summary: str,
        file_path: str,
        call_owner: str,
        call_target: str,
        call_kind: str,
        code_template: str,
        metadata: dict[str, str] | None = None,
    ):
        self.source_label = source_label
        self.source_path = source_path
        self.group_name = group_name
        self.group_display = group_display
        self.entry_kind = entry_kind
        self.name = name
        self.display = display
        self.qualname = qualname
        self.signature = signature
        self.lineno = lineno
        self.expose = expose
        self.audience = audience
        self.purpose = purpose
        self.user_description = user_description
        self.notes = notes
        self.summary = summary
        self.file_path = file_path
        self.call_owner = call_owner
        self.call_target = call_target
        self.call_kind = call_kind
        self.code_template = code_template
        self.metadata = dict(metadata or {})


class DiscoveryGroup:
    def __init__(
        self,
        source_label: str,
        source_path: str,
        group_name: str,
        group_display: str,
        entries: list[DiscoveryEntry] | None = None,
    ):
        self.source_label = source_label
        self.source_path = source_path
        self.group_name = group_name
        self.group_display = group_display
        self.entries = list(entries or [])


class MetadataCatalogScanner:
    _meta_line_pattern = re.compile(r"^\s*([A-Za-z][A-Za-z0-9_ ]*):\s*(.*)$")

    def __init__(self, root_dir: Path, targets: list[SearchTarget] | None = None):
        self.root_dir = root_dir
        self.targets: list[SearchTarget] = list(targets or [])
        self.entries: list[DiscoveryEntry] = []
        self.errors: list[str] = []

    def add_target(self, raw_path: str, label: str = "") -> bool:
        text = raw_path.strip()
        if not text:
            return False

        candidate = Path(text)
        if not candidate.is_absolute():
            candidate = (self.root_dir / candidate).resolve()

        if not candidate.exists():
            self.errors.append(f"Path does not exist: {candidate}")
            return False

        if any(existing.path == candidate for existing in self.targets):
            self.errors.append(f"Target already added: {candidate}")
            return False

        resolved_label = label.strip() or candidate.name or str(candidate)
        self.targets.append(SearchTarget(label=resolved_label, path=candidate))
        self.targets.sort(key=lambda target: (target.label.lower(), str(target.path).lower()))
        return True

    def scan(self) -> None:
        self.entries = []
        self.errors = []

        for target in self.targets:
            for file_path in self._iter_python_files(target.path):
                self._scan_file(target, file_path)

        self.entries.sort(
            key=lambda entry: (
                entry.source_label.lower(),
                entry.group_display.lower(),
                entry.entry_kind.lower(),
                entry.display.lower(),
                entry.qualname.lower(),
            )
        )

    def get_groups(self, include_hidden: bool = False) -> list[DiscoveryGroup]:
        groups: dict[tuple[str, str], DiscoveryGroup] = {}

        for entry in self.entries:
            if not include_hidden and not entry.expose:
                continue

            key = (entry.source_label, entry.group_display)
            if key not in groups:
                groups[key] = DiscoveryGroup(
                    source_label=entry.source_label,
                    source_path=entry.source_path,
                    group_name=entry.group_name,
                    group_display=entry.group_display,
                )
            groups[key].entries.append(entry)

        ordered_groups = list(groups.values())
        ordered_groups.sort(key=lambda group: (group.source_label.lower(), group.group_display.lower()))
        return ordered_groups

    def _iter_python_files(self, path: Path) -> Iterable[Path]:
        if path.is_file():
            if path.suffix.lower() == ".py":
                yield path
            return

        for file_path in sorted(path.rglob("*.py")):
            yield file_path

    def _scan_file(self, target: SearchTarget, file_path: Path) -> None:
        try:
            source = file_path.read_text(encoding="utf-8")
            tree = ast.parse(source, filename=str(file_path))
        except Exception as exc:
            self.errors.append(f"Failed to parse {file_path}: {exc}")
            return

        self._visit_nodes(
            target=target,
            file_path=file_path,
            nodes=tree.body,
            class_stack=[],
            function_stack=[],
        )

    def _visit_nodes(
        self,
        target: SearchTarget,
        file_path: Path,
        nodes: list[ast.stmt],
        class_stack: list[ast.ClassDef],
        function_stack: list[ast.FunctionDef],
    ) -> None:
        for node in nodes:
            if isinstance(node, ast.ClassDef):
                self._maybe_add_entry(
                    target=target,
                    file_path=file_path,
                    node=node,
                    class_stack=class_stack,
                    function_stack=function_stack,
                )
                self._visit_nodes(
                    target=target,
                    file_path=file_path,
                    nodes=node.body,
                    class_stack=class_stack + [node],
                    function_stack=function_stack,
                )
            elif isinstance(node, ast.FunctionDef):
                self._maybe_add_entry(
                    target=target,
                    file_path=file_path,
                    node=node,
                    class_stack=class_stack,
                    function_stack=function_stack,
                )
                self._visit_nodes(
                    target=target,
                    file_path=file_path,
                    nodes=node.body,
                    class_stack=class_stack,
                    function_stack=function_stack + [node],
                )

    def _maybe_add_entry(
        self,
        target: SearchTarget,
        file_path: Path,
        node: ast.ClassDef | ast.FunctionDef,
        class_stack: list[ast.ClassDef],
        function_stack: list[ast.FunctionDef],
    ) -> None:
        docstring = ast.get_docstring(node, clean=False)
        if not docstring or "Meta:" not in docstring:
            return

        summary, metadata = self._parse_docstring(docstring)
        expose = metadata.get("Expose", "false").strip().lower() == "true"
        qualname_parts = [ancestor.name for ancestor in class_stack]
        qualname_parts.extend(ancestor.name for ancestor in function_stack)
        qualname_parts.append(node.name)
        qualname = ".".join(qualname_parts)

        group_name, group_display = self._resolve_group_identity(target, class_stack, node)
        entry_kind = self._resolve_entry_kind(target, class_stack, function_stack, node)
        display = metadata.get("Display", node.name)
        signature = f"class {node.name}" if isinstance(node, ast.ClassDef) else self._build_function_signature(node)
        call_owner, call_target, call_kind, code_template = self._build_codegen_reference(
            target=target,
            node=node,
            class_stack=class_stack,
            function_stack=function_stack,
        )

        self.entries.append(
            DiscoveryEntry(
                source_label=target.label,
                source_path=str(target.path),
                group_name=group_name,
                group_display=group_display,
                entry_kind=entry_kind,
                name=node.name,
                display=display,
                qualname=qualname,
                signature=signature,
                lineno=getattr(node, "lineno", 0),
                expose=expose,
                audience=metadata.get("Audience", ""),
                purpose=metadata.get("Purpose", ""),
                user_description=metadata.get("UserDescription", ""),
                notes=metadata.get("Notes", ""),
                summary=summary,
                file_path=str(file_path),
                call_owner=call_owner,
                call_target=call_target,
                call_kind=call_kind,
                code_template=code_template,
                metadata=metadata,
            )
        )

    def _resolve_group_identity(
        self,
        target: SearchTarget,
        class_stack: list[ast.ClassDef],
        node: ast.ClassDef | ast.FunctionDef,
    ) -> tuple[str, str]:
        if isinstance(node, ast.ClassDef) and not class_stack:
            metadata = self._parse_docstring(ast.get_docstring(node, clean=False) or "")[1]
            display = metadata.get("Display", node.name)
            return node.name, display

        if class_stack:
            group_class = class_stack[0]
            group_metadata = self._parse_docstring(ast.get_docstring(group_class, clean=False) or "")[1]
            return group_class.name, group_metadata.get("Display", group_class.name)

        return target.label, target.label

    def _resolve_entry_kind(
        self,
        target: SearchTarget,
        class_stack: list[ast.ClassDef],
        function_stack: list[ast.FunctionDef],
        node: ast.ClassDef | ast.FunctionDef,
    ) -> str:
        if isinstance(node, ast.ClassDef):
            if target.path.name == "BehaviorTree.py" and node.name.endswith("Node"):
                return "Node"
            if not class_stack:
                return "Group"
            return "Class"

        if function_stack:
            return "Nested Helper"
        if class_stack:
            return "Method"
        return "Function"

    def _build_codegen_reference(
        self,
        target: SearchTarget,
        node: ast.ClassDef | ast.FunctionDef,
        class_stack: list[ast.ClassDef],
        function_stack: list[ast.FunctionDef],
    ) -> tuple[str, str, str, str]:
        if function_stack:
            parent_name = ".".join(
                [ancestor.name for ancestor in class_stack] + [ancestor.name for ancestor in function_stack]
            )
            call_owner = parent_name
            call_target = f"{parent_name}.{node.name}" if parent_name else node.name
            return call_owner, call_target, "nested_helper", f"{call_target}(...)"

        if target.path.name == "BehaviorTree.py":
            if isinstance(node, ast.ClassDef) and node.name == "BehaviorTree":
                return "", "BehaviorTree", "tree_constructor", "BehaviorTree(root=...)"
            if isinstance(node, ast.ClassDef):
                if class_stack and class_stack[0].name == "BehaviorTree":
                    call_owner = "BehaviorTree"
                    call_target = f"BehaviorTree.{node.name}"
                    return call_owner, call_target, "nested_class_constructor", f"{call_target}(...)"
                return "", node.name, "class_constructor", f"{node.name}(...)"

            if class_stack and class_stack[0].name == "BehaviorTree":
                call_owner = "BehaviorTree"
                call_target = f"BehaviorTree.{node.name}"
                return call_owner, call_target, "class_method", f"{call_target}(...)"

        normalized_path = str(target.path).replace("\\", "/")
        if target.path.name == "BehaviourTrees.py" or "behaviourtrees_src" in normalized_path:
            if isinstance(node, ast.ClassDef):
                if node.name == "BT":
                    return "", "RoutinesBT", "catalog_root", "RoutinesBT"
                if not class_stack:
                    bt_group_name = self._strip_bt_prefix(node.name)
                    call_owner = "RoutinesBT"
                    call_target = f"RoutinesBT.{bt_group_name}"
                    return call_owner, call_target, "group", call_target

            if class_stack:
                group_root = class_stack[0].name
                bt_group_name = self._strip_bt_prefix(group_root)
                call_owner = f"RoutinesBT.{bt_group_name}"
                call_target = f"{call_owner}.{node.name}"
                return call_owner, call_target, "static_method", f"{call_target}(...)"

        if target.path.name == "BTNodes.py":
            if isinstance(node, ast.ClassDef):
                if node.name == "BTNodes":
                    return "", "BTNodes", "catalog_root", "BTNodes"
                if not class_stack:
                    call_owner = "BTNodes"
                    call_target = f"BTNodes.{node.name}"
                    return call_owner, call_target, "group", call_target

            if class_stack:
                owner_parts = [class_stack[0].name]
                for nested_class in class_stack[1:]:
                    owner_parts.append(nested_class.name)
                call_owner = ".".join(owner_parts)
                call_target = f"{call_owner}.{node.name}"
                return call_owner, call_target, "static_method", f"{call_target}(...)"

        if isinstance(node, ast.ClassDef):
            return "", node.name, "class_constructor", f"{node.name}(...)"

        call_owner = class_stack[0].name if class_stack else ""
        call_target = f"{call_owner}.{node.name}" if call_owner else node.name
        call_kind = "method" if call_owner else "function"
        return call_owner, call_target, call_kind, f"{call_target}(...)"

    def _strip_bt_prefix(self, name: str) -> str:
        if name.startswith("BT") and len(name) > 2:
            return name[2:]
        return name

    def _parse_docstring(self, docstring: str) -> tuple[str, dict[str, str]]:
        cleaned = inspect.cleandoc(docstring)
        if not cleaned:
            return "", {}

        lines = cleaned.splitlines()
        meta_index = -1
        for index, line in enumerate(lines):
            if line.strip() == "Meta:":
                meta_index = index
                break

        if meta_index == -1:
            return cleaned.strip(), {}

        summary_lines = [line.rstrip() for line in lines[:meta_index]]
        metadata: dict[str, str] = {}
        for line in lines[meta_index + 1 :]:
            if not line.strip():
                continue
            match = self._meta_line_pattern.match(line)
            if not match:
                continue
            metadata[match.group(1).strip()] = match.group(2).strip()

        summary = "\n".join(line for line in summary_lines if line.strip()).strip()
        return summary, metadata

    def _build_function_signature(self, node: ast.FunctionDef) -> str:
        positional = list(node.args.posonlyargs) + list(node.args.args)
        defaults = [None] * (len(positional) - len(node.args.defaults)) + list(node.args.defaults)
        parts: list[str] = []

        for arg, default in zip(positional, defaults):
            parts.append(self._format_arg(arg, default))

        if node.args.vararg is not None:
            parts.append("*" + self._format_arg(node.args.vararg, None, include_default=False))
        elif node.args.kwonlyargs:
            parts.append("*")

        for arg, default in zip(node.args.kwonlyargs, node.args.kw_defaults):
            parts.append(self._format_arg(arg, default))

        if node.args.kwarg is not None:
            parts.append("**" + self._format_arg(node.args.kwarg, None, include_default=False))

        signature = f"{node.name}({', '.join(parts)})"
        if node.returns is not None:
            try:
                signature += f" -> {ast.unparse(node.returns)}"
            except Exception:
                pass
        return signature

    def _format_arg(
        self,
        arg: ast.arg,
        default: ast.expr | None,
        include_default: bool = True,
    ) -> str:
        text = arg.arg
        if arg.annotation is not None:
            try:
                text += f": {ast.unparse(arg.annotation)}"
            except Exception:
                pass
        if include_default and default is not None:
            try:
                text += f" = {ast.unparse(default)}"
            except Exception:
                text += " = ..."
        return text
