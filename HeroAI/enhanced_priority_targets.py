from Py4GWCoreLib import *
import math
import random
from .priority_targets import PriorityTargets
from .avoidance_system import AvoidanceSystem

# Enhanced priority targeting constants
COMBAT_UPDATE_FREQUENCY = 25  # Milliseconds between combat updates

class EnhancedPriorityTargets(PriorityTargets):
    """Enhanced priority targeting system with obstacle avoidance capabilities"""
    
    def __init__(self):
        """Initialize the enhanced priority targeting system"""
        super().__init__()
        self.avoidance_system = AvoidanceSystem()
        self.combat_timer = Timer()
        self.combat_timer.Start()
        
    def attack_priority_target(self, distance=Range.Earshot.value):
        """Attack a priority target with avoidance if needed"""
        character_name = self.get_character_name()
        
        # Check if priority targeting is enabled for this character
        if not self.is_enabled(character_name):
            return False
            
        # Ensure the character exists in our dictionary
        if character_name not in self.character_targets:
            self.character_targets[character_name] = []
            
        # If no priority targets for this character, return False
        if not self.character_targets.get(character_name, []):
            return False
            
        # Find nearest priority target
        target_id = self.find_nearest_priority_target(distance)
        if target_id == 0:
            self.avoidance_system.reset()
            return False
            
        # If not in avoidance mode, check if we need it
        if not self.avoidance_system.is_active:
            # Normal attack routine
            ActionQueueManager().AddAction("ACTION", Player.ChangeTarget, target_id)
            
            # Check if we're in melee range and not attacking
            if Agent.IsMelee(Player.GetAgentID()):
                if Utils.Distance(Player.GetXY(), Agent.GetXY(target_id)) > Range.Adjacent.value:
                    # Need to move closer
                    self.avoidance_system.find_path_around_obstacles(Player.GetXY(), target_id)
                else:
                    # In range, just attack
                    ActionQueueManager().AddAction("ACTION", Player.Interact, target_id)
            else:
                # Ranged class, just attack if in spellcast range
                if Utils.Distance(Player.GetXY(), Agent.GetXY(target_id)) <= Range.Spellcast.value:
                    ActionQueueManager().AddAction("ACTION", Player.Interact, target_id)
                else:
                    # Need to move closer for ranged
                    self.avoidance_system.find_path_around_obstacles(Player.GetXY(), target_id)
        else:
            # Already in avoidance mode, update it
            self.avoidance_system.update(target_id)
            
        return True
    
    def update(self):
        """Update function to be called every frame"""
        # Only run combat checks every 250ms
        if not self.combat_timer.HasElapsed(COMBAT_UPDATE_FREQUENCY):
            return
            
        self.combat_timer.Reset()
        
        character_name = self.get_character_name()
        
        # If in combat and priority targeting is enabled for this character
        if self.is_enabled(character_name) and Player.GetTargetID() != 0:
            # Check if current target is a priority target
            if self.is_priority_target(Player.GetTargetID()):
                # Already targeting priority target
                if Agent.IsMelee(Player.GetAgentID()):
                    # For melee, check if we're stuck
                    if not Agent.IsAttacking(Player.GetAgentID()) and Agent.IsAlive(Player.GetTargetID()):
                        if Utils.Distance(Player.GetXY(), Agent.GetXY(Player.GetTargetID())) > Range.Adjacent.value:
                            # Can't reach target, activate avoidance
                            if not self.avoidance_system.is_active:
                                self.avoidance_system.find_path_around_obstacles(Player.GetXY(), Player.GetTargetID())
            else:
                # Not targeting priority target, check if there is one
                self.attack_priority_target()