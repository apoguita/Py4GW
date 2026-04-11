# ModularBot Docs

This documentation set is the single source of truth for ModularBot recipe authoring, action behavior, and contributor onboarding.

## What ModularBot Is

ModularBot executes JSON recipe blocks (missions/quests/routes/farms/dungeons/vanquishes/bounties) by expanding and dispatching step actions to subsystem handlers (`movement`, `interaction`, `targeting`, `party`, `inventory`).

Recipe files live under:
- `Sources/modular_bot/missions`
- `Sources/modular_bot/quests`
- `Sources/modular_bot/routes`
- `Sources/modular_bot/farms`
- `Sources/modular_bot/dungeons`
- `Sources/modular_bot/vanquishes`
- `Sources/modular_bot/bounties`

## Start Here

1. Read [Architecture](architecture.md) for data flow and runtime lifecycle.
2. Read [Anchor and Recovery Fallback](anchor-and-recovery.md) for recovery jump behavior and anchor precedence.
3. Read [Action Index](actions/index.md) then jump to subsystem pages.
4. Read [Selectors and Target Enums](selectors-and-target-enums.md) before writing selector-based steps.
5. Read [Contributing](contributing.md) for tester/coder-assistant tutorials and action-extension workflow.

## Quick Links

- Action reference: [actions/index.md](actions/index.md)
- Movement: [actions/movement.md](actions/movement.md)
- Interaction: [actions/interaction.md](actions/interaction.md)
- Targeting: [actions/targeting.md](actions/targeting.md)
- Party: [actions/party.md](actions/party.md)
- Inventory: [actions/inventory.md](actions/inventory.md)
- Architecture diagrams: [architecture.md](architecture.md)
- Anchor and recovery fallback: [anchor-and-recovery.md](anchor-and-recovery.md)
- Selector/registry reference: [selectors-and-target-enums.md](selectors-and-target-enums.md)
- Contributor tutorials: [contributing.md](contributing.md)
