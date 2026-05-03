from enum import Enum


class HeroAIStatus(Enum):
    WAITING_MAP = 'PAUSED: Waiting for explorable map'
    PLAYER_DEAD = 'PAUSED: Player dead'
    PLAYER_KNOCKED_DOWN = 'PAUSED: Player knocked down'
    DISABLED = 'PAUSED: Headless HeroAI disabled'
    COMBAT_TICK = 'COMBAT: Tick'
    OOC_TICK = 'COMBAT: OOC Tick'


class PlannerStatus(Enum):
    PAUSED_ON_COMBAT = 'PAUSED: HeroAI owns combat'
    PAUSED_ON_LOOTING = 'PAUSED: HeroAI owns looting'
    IDLE = 'PLANNER: Idle'
    TICK = 'PLANNER: Tick'
    OWNER_HEROAI = 'OWNER: HeroAI'
    OWNER_PLANNER = 'OWNER: Planner'
