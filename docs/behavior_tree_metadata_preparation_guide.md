# BehaviorTree Metadata Preparation Guide

This document records the conventions and decisions used to prepare
`Py4GWCoreLib/py4gwcorelib_src/BehaviorTree.py` as a discovery source for the
future wizard/configurator system.

The goal of this preparation work was not to redesign the runtime. The goal was
to shape the existing class so tooling can inspect it reliably with less guesswork.

## Scope

This session focused on `BehaviorTree.py` only.

What was in scope:
- naming consistency
- explicit structural metadata
- disciplined internal runtime naming
- docstring format for human help plus machine-readable metadata
- keeping the existing tree rendering support intact

What was not in scope:
- redesigning the behavior tree runtime
- changing execution semantics
- building the configurator itself
- defining the helper-layer metadata system in full

## Outcome

`BehaviorTree.py` is now suitable to serve as the base discovery layer for the
system.

It now provides:
- canonical node identity through `node_type`
- explicit structural family through `node_category`
- consistent default naming
- clearer distinction between configuration fields and runtime-only fields
- node docstrings with a predictable `Meta:` block

The key late-session clarification is that discovery is now metadata-gated:

- metadata is mandatory for discovery
- no metadata means ignore
- low-level runtime internals do not need to be scanned unless they explicitly opt in

## Core Decisions

### 1. Canonical naming uses the class name

The chosen convention is intentionally simple:

- class name is the canonical identity
- `node_type` matches the class name
- default `name` matches the class name

Example:

- class: `SequenceNode`
- `node_type`: `SequenceNode`
- default `name`: `SequenceNode`

This avoids drift between Python identity, metadata identity, and default display naming.

Custom instance names are still allowed when a tree author wants a more descriptive label.

Example:

- class: `SequenceNode`
- `node_type`: `SequenceNode`
- `name`: `Starting common sequence`

## 2. Structural family is explicit

The runtime already had clear node families, but they had to be inferred from code.
That is now declared directly through `node_category`.

Current categories used in `BehaviorTree.py`:
- `leaf`
- `composite`
- `decorator`
- `repeater`
- `router`
- `wait`

This gives tooling a stable structural vocabulary without changing node behavior.

## 3. Internal runtime state should look internal

Runtime bookkeeping should be visually distinguishable from authored/configuration data.

Rule:
- runtime-only and lifecycle state uses a leading underscore
- authored/configuration fields remain public
- stable metadata fields remain public

Examples of runtime/internal fields:
- `_current_child_index`
- `_current_repeat_count`
- `_start_time_ms`
- `_last_check_time_ms`
- `_run_start_time_ms`
- `_active_tree`
- `_selected_key`
- `_subtree`

Examples of authored/configuration fields:
- `child`
- `children`
- `timeout_ms`
- `duration_ms`
- `condition_fn`
- `selector_fn`
- `cases`

Examples of stable metadata fields:
- `name`
- `node_type`
- `node_category`
- `icon`
- `color`

## 4. Tree drawing support stays in the class

`BehaviorTree.Node` includes self-rendering support for tree/debug inspection.
Because of that, these fields remain valid parts of the class:

- `icon`
- `color`
- draw-related helpers

These are not treated as accidental UI leakage. They are part of the existing
tree-inspection feature and were intentionally retained.

## Node Docstring Format

The node docstring format has two layers:

1. Human-readable description
2. Structured `Meta:` block

This gives us readable code for developers and a predictable parsing surface for tools.

### Required shape

```python
"""
Free human-readable explanation of what the node does.
This section is intentionally flexible and written for humans.

Meta:
  Expose: true
  Audience: beginner
  Display: Sequence Node
  Purpose: Execute several child nodes from first to last.
  UserDescription: Use this when steps must happen in order.
  Notes: Stops on first failure. Resumes from the running child on the next tick.
"""
```

### Parsing rules

- Only the `Meta:` block is intended for machine parsing.
- Metadata lines should use `Key: Value`.
- Keep metadata values single-line.
- Unknown keys should be ignored safely by tools.
- The human-readable section must remain readable even if the metadata parser is never used.
- If a class or function has no `Meta:` block, discovery should ignore it instead of inferring meaning from implementation details.

## Recommended Meaning Of Current Meta Keys

- `Expose`
  - whether the node should be visible to authoring/discovery tools

- `Audience`
  - rough intended experience level, such as `beginner`, `intermediate`, or `advanced`

- `Display`
  - user-facing label for UI presentation

- `Purpose`
  - short explanation of what the node does

- `UserDescription`
  - instruction-like wording intended for end users

- `Notes`
  - important behavior details, caveats, or constraints

## Relationship Between Code Metadata And Docstring Metadata

Not all metadata belongs in docstrings.

Code should remain the source of truth for structural/runtime identity:
- `node_type`
- `node_category`
- constructor parameters
- child relationships
- runtime bookkeeping

Docstrings should be used for:
- presentation hints
- guidance text
- discovery help
- user-facing explanation

This split keeps the system maintainable:
- structural meaning lives in code
- explanatory meaning lives in docstrings

## What Was Solved In This Session

The following issues were addressed in `BehaviorTree.py`:

1. `node_type` naming was normalized
- all built-in nodes now use the class-name form consistently

2. Class name, `node_type`, and default `name` were unified
- this removed ambiguity between implementation identity and metadata identity

3. Structural terminology was made explicit
- `node_category` is now present and assigned on built-in nodes

4. Internal runtime field naming was normalized
- internal lifecycle fields now use a consistent private style

5. Private/internal naming discipline was improved
- runtime-only state is clearer and easier for discovery tooling to ignore

6. Node docstrings now support a structured metadata section
- each built-in node can carry both human help text and parseable metadata

## Guidance For Future Edits

When adding or updating a node in `BehaviorTree.py`:

1. Keep the class name explicit.
2. Keep `node_type` equal to the class name.
3. Keep the default `name` equal to the class name unless there is a very specific reason not to.
4. Set `node_category` explicitly.
5. Keep runtime-only fields private.
6. Keep the node docstring in the two-part format:
   - human-readable section
   - `Meta:` block
7. Avoid duplicating structural truth in the docstring if code already defines it clearly.

## Why This Matters For The Configurator

The future configurator cannot rely on a hand-maintained catalog in a library
that changes constantly.

Preparing `BehaviorTree.py` this way reduces guesswork for discovery:
- node identity is explicit
- structural family is explicit
- runtime-only state is easier to filter out
- user-facing help can be parsed from docstrings

This is the foundation layer. Helper discovery and higher-level authoring
surfaces will build on top of it.

## Current Session Status

The preparation outcome for this layer is now:

- the built-in node class surface has a stable parseable contract
- structural truth remains in code through class names, `node_type`, and `node_category`
- docstrings provide the discovery/presentation layer through the shared `Meta:` format
- metadata is now the intended discovery boundary, so low-level internals without metadata are out of scope for parser consumption
