# Architecture

This page describes how ModularBot recipe JSON becomes FSM runtime behavior.

## Diagram 1: Block Load and Action Dispatch

```mermaid
flowchart TD
    A[modular_block_run] --> B[_load_block_data]
    B --> C[steps array]
    C --> D[register_repeated_steps]
    D --> E[modular_actions register_step]
    E --> F[action_registry STEP_HANDLERS]
    F --> G[actions movement targeting interaction party inventory]
    G --> H[Botting FSM states registered]
```

## Diagram 2: Runtime FSM Lifecycle

```mermaid
flowchart TD
    A[Recipe step object] --> B[register_step_title state]
    B --> C[handler dispatch]
    C --> D[states added via AddCustomState helpers]
    D --> E[wait_after_step]
    E --> F[FSM executes in runtime order]
    F --> G{anchor flag}
    G -->|yes| H[set runtime anchor to final emitted state]
    G -->|no| I[continue next expanded step]
    I --> J[repeat expansion handled by register_repeated_steps]
```

## Diagram 3: Combat-Engine Hook Integration

```mermaid
flowchart TD
    A[Step requests combat/loot/party operation] --> B[resolve_engine_for_bot]
    B --> C{Engine}
    C -- custom_behaviors --> D[CustomBehaviors party APIs]
    C -- hero_ai --> E[HeroAI shared-memory options]
    C -- none/shared --> F[Botting/native/shared command fallback]
    D --> G[apply_auto_combat_state / apply_auto_looting_state]
    E --> G
    F --> G
    G --> H[Optional multibox send + outbound wait]
    H --> I[Runtime state completion]
```

## Recovery and Anchor

Recovery routing details are documented here:
- [Anchor and Recovery Fallback](anchor-and-recovery.md)
