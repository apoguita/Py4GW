from enum import Enum, auto

class HealingScore(Enum):
    """
    Enum defining different healing-related conditions and priorities.
    Higher values indicate higher priority for healing.
    """
    # Party-wide damage conditions
    PARTY_DAMAGE_EMERGENCY = 80.0  # Critical party-wide damage
    PARTY_DAMAGE = 60.0            # Significant party-wide damage
    
    # Individual member damage conditions
    MEMBER_DAMAGED_EMERGENCY = 70.0  # Critical damage to a party member
    MEMBER_DAMAGED = 50.0           # Significant damage to a party member
    
    # Condition-based priorities
    MEMBER_CONDITIONED = 40.0       # Party member has harmful conditions

    
    def __float__(self) -> float:
        """Convert enum value to float for priority calculations."""
        return self.value 