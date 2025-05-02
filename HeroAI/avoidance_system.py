from Py4GWCoreLib import *
import math
import random

# Avoidance system constants
STUCK_DETECTION_RADIUS = 8      # Distance threshold to determine if character is stuck
STUCK_COUNTER_THRESHOLD = 3     # Number of consecutive checks to consider a character stuck
OBSTACLE_RADIUS = 100           # Radius around enemies considered as obstacles
AGENT_REPULSION_RADIUS = 150    # Radius of repulsion for enemies in vector field
PATH_STEP_SIZE = 150            # Distance between path points
PATH_POINT_REACHED_DISTANCE = 75  # Distance to consider a path point reached
TARGET_MOVED_THRESHOLD = 200    # Distance threshold to recalculate path if target moves
UPDATE_FREQUENCY = 25           # Milliseconds between updates (reduced from 25ms)
MAX_PATH_STEPS = 5              # Maximum number of intermediate points in path
BLEND_FACTOR = 0.3              # Mixing factor between avoidance and target direction

class AvoidanceSystem:
    """System to detect and handle movement obstruction by finding paths around obstacles"""
    
    def __init__(self):
        """Initialize the avoidance system"""
        self.is_active = False
        self.stuck_counter = 0
        self.last_position = (0, 0)
        self.target_id = 0
        self.path = []
        self.current_path_index = 0
        self.avoidance_cooldown = Timer()
        self.avoidance_cooldown.Start()
        
    def reset(self):
        """Reset the avoidance system state"""
        self.is_active = False
        self.stuck_counter = 0
        self.path = []
        self.current_path_index = 0
        
    def check_if_stuck(self, current_position):
        """Check if the character is stuck in the same position"""
        # If we're too close to the last known position
        if Utils.Distance(current_position, self.last_position) < STUCK_DETECTION_RADIUS:
            self.stuck_counter += 1
        else:
            self.stuck_counter = 0
            
        self.last_position = current_position
        
        # If stuck for consecutive frames
        return self.stuck_counter > STUCK_COUNTER_THRESHOLD
    
    def find_path_around_obstacles(self, start_pos, target_id):
        """Calculate a path to bypass obstacles"""
        if not Agent.IsValid(target_id) or not Agent.IsAlive(target_id):
            return False
            
        target_pos = Agent.GetXY(target_id)
        self.target_id = target_id
        
        # Get all potential obstacles (enemies around the player)
        obstacles = []
        enemies = AgentArray.GetEnemyArray()
        enemies = AgentArray.Filter.ByDistance(enemies, start_pos, Range.Spellcast.value)
        
        for enemy_id in enemies:
            if enemy_id != target_id:  # Don't consider the target as an obstacle
                enemy_pos = Agent.GetXY(enemy_id)
                # Create obstacle representation
                obstacles.append({
                    'position': enemy_pos,
                    'radius': OBSTACLE_RADIUS
                })
        
        # Create vector field for path calculation
        vector_field = Utils.VectorFields(start_pos)
        
        # Add target as attraction point
        vector_field.add_custom_attraction_position(target_pos)
        
        # Add obstacles as repulsion points
        for obstacle in obstacles:
            vector_field.add_custom_repulsion_position(obstacle['position'])
        
        # Configure and calculate path
        agent_arrays = []
        # Add different agent groups that influence movement
        for enemy_id in enemies:
            if enemy_id != target_id:
                agent_arrays.append({
                    'name': f'enemy_{enemy_id}',
                    'array': [enemy_id],
                    'radius': AGENT_REPULSION_RADIUS,
                    'is_dangerous': True
                })
        
        # Calculate avoidance vector
        escape_vector = vector_field.generate_escape_vector(agent_arrays)
        
        # Generate path based on avoidance vector
        path = self._generate_path(start_pos, target_pos, escape_vector, obstacles)
        
        if path and len(path) > 0:
            self.path = path
            self.current_path_index = 0
            self.is_active = True
            return True
        
        return False
    
    def _generate_path(self, start_pos, target_pos, escape_vector, obstacles):
        """Generate a path of waypoints based on the avoidance vector"""
        path = []
        current_pos = start_pos
        
        # Normalize the avoidance vector
        magnitude = math.sqrt(escape_vector[0]**2 + escape_vector[1]**2)
        if magnitude < 0.001:  # Avoid division by zero
            # No clear direction, try to move directly to target
            direction = (
                target_pos[0] - start_pos[0],
                target_pos[1] - start_pos[1]
            )
            magnitude = math.sqrt(direction[0]**2 + direction[1]**2)
            if magnitude < 0.001:
                return []
            
            normalized_dir = (
                direction[0] / magnitude,
                direction[1] / magnitude
            )
        else:
            normalized_dir = (
                escape_vector[0] / magnitude,
                escape_vector[1] / magnitude
            )
        
        # Create path following the avoidance vector
        for i in range(MAX_PATH_STEPS):
            # Calculate next path point
            next_pos = (
                current_pos[0] + normalized_dir[0] * PATH_STEP_SIZE,
                current_pos[1] + normalized_dir[1] * PATH_STEP_SIZE
            )
            
            # Check if this point brings us closer to the target
            if Utils.Distance(next_pos, target_pos) < Utils.Distance(current_pos, target_pos):
                path.append(next_pos)
                current_pos = next_pos
            else:
                # If not getting closer, adjust direction toward target
                direction_to_target = (
                    target_pos[0] - current_pos[0],
                    target_pos[1] - current_pos[1]
                )
                magnitude = math.sqrt(direction_to_target[0]**2 + direction_to_target[1]**2)
                if magnitude < 0.001:
                    break
                
                # Blend avoidance direction with target direction
                adjusted_dir = (
                    normalized_dir[0] * BLEND_FACTOR + direction_to_target[0] / magnitude * (1 - BLEND_FACTOR),
                    normalized_dir[1] * BLEND_FACTOR + direction_to_target[1] / magnitude * (1 - BLEND_FACTOR)
                )
                
                # Normalize adjusted direction
                magnitude = math.sqrt(adjusted_dir[0]**2 + adjusted_dir[1]**2)
                if magnitude < 0.001:
                    break
                
                normalized_dir = (
                    adjusted_dir[0] / magnitude,
                    adjusted_dir[1] / magnitude
                )
                
                next_pos = (
                    current_pos[0] + normalized_dir[0] * PATH_STEP_SIZE,
                    current_pos[1] + normalized_dir[1] * PATH_STEP_SIZE
                )
                
                path.append(next_pos)
                current_pos = next_pos
        
        # Add final target position
        path.append(target_pos)
        return path
    
    def follow_path(self):
        """Follow the calculated path to avoid obstacles"""
        if not self.is_active or not self.path or self.current_path_index >= len(self.path):
            return False
        
        # Get next path point
        next_point = self.path[self.current_path_index]
        
        # Move to this point
        ActionQueueManager().AddAction("ACTION", Player.Move, next_point[0], next_point[1])
        
        # Check if we've reached this point
        if Utils.Distance(Player.GetXY(), next_point) < PATH_POINT_REACHED_DISTANCE:
            self.current_path_index += 1
            
            # If we've reached the last point (the target)
            if self.current_path_index >= len(self.path):
                # Reset avoidance system and interact with target
                self.reset()
                if Agent.IsValid(self.target_id) and Agent.IsAlive(self.target_id):
                    ActionQueueManager().AddAction("ACTION", Player.ChangeTarget, self.target_id)
                    ActionQueueManager().AddAction("ACTION", Player.Interact, self.target_id)
                return False
            
            # Move to the next point immediately without waiting for next update
            # This creates more fluid movement
            if self.current_path_index < len(self.path):
                next_point = self.path[self.current_path_index]
                ActionQueueManager().AddAction("ACTION", Player.Move, next_point[0], next_point[1])
        
        return True
    
    def update(self, target_id):
        """Main update function to be called each frame"""
        # Limit check frequency
        if not self.avoidance_cooldown.HasElapsed(UPDATE_FREQUENCY):
            return
            
        self.avoidance_cooldown.Reset()
        
        current_pos = Player.GetXY()
        
        # If system is already active, follow path
        if self.is_active:
            # Check if target is still valid
            if not Agent.IsValid(self.target_id) or not Agent.IsAlive(self.target_id):
                # Target died or invalid, reset avoidance system
                self.reset()
                return
                
            # Check if we're already close enough to interact
            target_distance = Utils.Distance(current_pos, Agent.GetXY(self.target_id))
            if (Agent.IsMelee(Player.GetAgentID()) and target_distance <= Range.Adjacent.value) or \
               (not Agent.IsMelee(Player.GetAgentID()) and target_distance <= Range.Spellcast.value):
                # We're in range, interact and reset avoidance
                ActionQueueManager().AddAction("ACTION", Player.ChangeTarget, self.target_id)
                ActionQueueManager().AddAction("ACTION", Player.Interact, self.target_id)
                self.reset()
                return
                
            # Check if target moved too much
            target_pos = Agent.GetXY(self.target_id)
            if self.path and Utils.Distance(target_pos, self.path[-1]) > TARGET_MOVED_THRESHOLD:
                # Target moved too much, recalculate path
                self.find_path_around_obstacles(current_pos, self.target_id)
            else:
                # Follow existing path
                self.follow_path()
        else:
            # Check if character is stuck
            if self.check_if_stuck(current_pos):
                # Character is stuck, activate avoidance system
                self.find_path_around_obstacles(current_pos, target_id)