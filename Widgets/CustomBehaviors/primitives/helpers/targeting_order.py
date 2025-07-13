from enum import Enum

# Create an enumeration
class TargetingOrder(Enum):

    AGENT_QUANTITY_WITHIN_RANGE_ASC = 1 # how much other agents are at given range of the agent
    AGENT_QUANTITY_WITHIN_RANGE_DESC = 2 # how much other agents are at given range of the agent

    ENEMIES_QUANTITY_WITHIN_RANGE_DESC = 4 # how much other ennemies are at given range of the agent, so only possible when targeting allies

    HP_ASC = 10
    HP_DESC = 11

    ENERGY_ASC = 15
    ENERGY_DESC = 16

    DISTANCE_ASC = 20
    DISTANCE_DESC = 21

    CASTER_THEN_MELEE = 30
    MELEE_THEN_CASTER = 31


