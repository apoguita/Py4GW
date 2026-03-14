
from .Utils import Utils
import math

class VectorFields:
    """
    The VectorFields class simulates movement using repulsion and attraction forces based on agent arrays and custom positions.
    Additionally, custom repulsion and attraction positions can be provided.
    """

    def __init__(self, probe_position, custom_repulsion_radius=100, custom_attraction_radius=100, probe_radius=0.0):
        """
        Initialize the VectorFields object with player position and default settings.
        Args:
            probe_position (tuple): The player's current position (x, y).
        """
        self.probe_position = probe_position
        self.probe_radius = max(0.0, float(probe_radius))

        # Store settings for agent arrays and custom positions
        self.agent_arrays_settings = {}

        # Custom repulsion and attraction lists
        self.custom_repulsion_positions = []
        self.custom_attraction_positions = []

        # Radius for custom positions
        self.custom_repulsion_radius = custom_repulsion_radius
        self.custom_attraction_radius = custom_attraction_radius

    def add_agent_array(self, array_name, agent_array, radius, is_dangerous=True, body_radius=0.0, agent_radius_fn=None):
        """
        Add an agent array to be processed with the vector fields.
        Args:
            array_name (str): Name of the agent array (e.g., 'enemies', 'allies').
            agent_array (list): List of agent IDs to process.
            radius (int): Radius of effect for this array.
            is_dangerous (bool): Whether the array represents a dangerous (repulsion) or safe (attraction) set. Default is True.
        """
        self.agent_arrays_settings[array_name] = {
            'agent_array': agent_array,
            'radius': radius,
            'is_dangerous': is_dangerous,
            'body_radius': max(0.0, float(body_radius)),
            'agent_radius_fn': agent_radius_fn,
        }

    def add_custom_repulsion_position(self, position):
        """
        Add a custom repulsion position.
        Args:
            position (tuple): The position (x, y) to add to the repulsion list.
        """
        self.custom_repulsion_positions.append(position)

    def add_custom_attraction_position(self, position):
        """
        Add a custom attraction position.
        Args:
            position (tuple): The position (x, y) to add to the attraction list.
        """
        self.custom_attraction_positions.append(position)

    def set_probe_radius(self, probe_radius):
        """Set the probe/body radius used for edge-to-edge distance calculations."""
        self.probe_radius = max(0.0, float(probe_radius))

    def clear_custom_positions(self):
        """
        Clear all custom repulsion and attraction positions.
        """
        self.custom_repulsion_positions.clear()
        self.custom_attraction_positions.clear()

    def calculate_unit_vector(self, target_position):
        """
        Calculate the unit vector between the player and a target position.
        Args:
            target_position (tuple): The target's position (x, y).
        Returns:
            tuple: The unit vector (dx, dy) pointing from the player to the target.
        """
        # Create adjusted positions as new tuples
        pos_a = (self.probe_position[0] + 1, self.probe_position[1] + 1)
        pos_b = (target_position[0] - 1, target_position[1] - 1)

        distance = Utils.Distance(pos_a, pos_b)
        if distance == 0:
            return (0, 0)  # Avoid division by zero
        return ((pos_b[0] - pos_a[0]) / distance, (pos_b[1] - pos_a[1]) / distance)

    def _split_position_and_radius(self, value):
        """
        Backward-compatible custom position parser.
        Accepts:
            - (x, y)
            - (x, y, radius)
            - {"position": (x, y), "body_radius": r}
        """
        if isinstance(value, dict):
            position = value.get("position", (0.0, 0.0))
            radius = float(value.get("body_radius", 0.0))
            return position, max(0.0, radius)

        if isinstance(value, (tuple, list)):
            if len(value) >= 3:
                return (value[0], value[1]), max(0.0, float(value[2]))
            if len(value) >= 2:
                return (value[0], value[1]), 0.0

        return value, 0.0

    def _get_effective_distance(self, target_position, target_radius=0.0):
        """
        Distance between the probe body's edge and the target body's edge.
        Falls back to point distance when both radii are zero.
        """
        center_distance = Utils.Distance(self.probe_position, target_position)
        effective_distance = center_distance - self.probe_radius - max(0.0, float(target_radius))
        return max(0.0, effective_distance)



    def process_agent_array(self, agent_array, radius, is_dangerous, body_radius=0.0, agent_radius_fn=None):
        from Py4GWCoreLib import Agent
        """
        Process a given agent array and calculate its total vector (either repulsion or attraction).
        Args:
            agent_array (list): List of agent IDs.
            radius (int): Radius of effect for the agents.
            is_dangerous (bool): Whether the agents are repulsive (True) or attractive (False).
        Returns:
            tuple: The combined vector (dx, dy) from this agent array.
        """
        combined_vector = [0, 0]
        if radius == 0:
            return (0, 0)  # Ignore if radius is 0

        for agent_id in agent_array:
            pos_x, pos_y = Agent.GetXY(agent_id)
            target_position = (pos_x, pos_y)
            target_radius = body_radius
            if callable(agent_radius_fn):
                try:
                    target_radius = max(0.0, float(agent_radius_fn(agent_id)))
                except Exception:
                    target_radius = body_radius

            distance = self._get_effective_distance(target_position, target_radius)

            if distance <= radius:
                unit_vector = self.calculate_unit_vector(target_position)
                if is_dangerous:
                    # Repulsion: Subtract the vector
                    combined_vector[0] -= unit_vector[0]
                    combined_vector[1] -= unit_vector[1]
                else:
                    # Attraction: Add the vector
                    combined_vector[0] += unit_vector[0]
                    combined_vector[1] += unit_vector[1]

        return tuple(combined_vector)

    def process_custom_positions(self, positions, radius, is_dangerous):
        """
        Process custom repulsion or attraction positions and calculate their total vector.
        Args:
            positions (list): List of custom positions [(x, y), ...].
            radius (int): Radius of effect for these positions.
            is_dangerous (bool): Whether the positions are repulsive (True) or attractive (False).
        Returns:
            tuple: The combined vector (dx, dy) from the custom positions.
        """
        combined_vector = [0, 0]
        for position in positions:
            target_position, target_radius = self._split_position_and_radius(position)
            distance = self._get_effective_distance(target_position, target_radius)

            if distance <= radius:
                unit_vector = self.calculate_unit_vector(target_position)
                if is_dangerous:
                    # Repulsion: Subtract the vector
                    combined_vector[0] -= unit_vector[0]
                    combined_vector[1] -= unit_vector[1]
                else:
                    # Attraction: Add the vector
                    combined_vector[0] += unit_vector[0]
                    combined_vector[1] += unit_vector[1]

        return tuple(combined_vector)

    def compute_combined_vector(self):
        """
        Compute the overall vector for all agent arrays and custom positions.
        Returns:
            tuple: The final combined vector (dx, dy).
        """
        final_vector = [0, 0]

        # Process all agent arrays
        for array_name, settings in self.agent_arrays_settings.items():
            agent_vector = self.process_agent_array(
                settings['agent_array'],
                settings['radius'],
                settings['is_dangerous'],
                settings.get('body_radius', 0.0),
                settings.get('agent_radius_fn')
            )
            final_vector[0] += agent_vector[0]
            final_vector[1] += agent_vector[1]

        # Process custom repulsion positions
        repulsion_vector = self.process_custom_positions(self.custom_repulsion_positions, self.custom_repulsion_radius, True)
        final_vector[0] += repulsion_vector[0]
        final_vector[1] += repulsion_vector[1]

        # Process custom attraction positions
        attraction_vector = self.process_custom_positions(self.custom_attraction_positions, self.custom_attraction_radius, False)
        final_vector[0] += attraction_vector[0]
        final_vector[1] += attraction_vector[1]

        return tuple(final_vector)

    def generate_escape_vector(self, agent_arrays, custom_repulsion_positions=None, custom_attraction_positions=None):
        """
        Purpose: Generate an escape vector based on the input agent arrays and custom repulsion/attraction settings.
        Args:
            agent_arrays (list): A list of dictionaries representing different agent arrays and their parameters.
                                    Each dictionary should contain:
                                    - 'name' (str): Name of the agent array (e.g., 'enemies', 'allies').
                                    - 'array' (list): The agent IDs in the array.
                                    - 'radius' (int): The radius of effect for this array (0 to ignore).
                                    - 'is_dangerous' (bool): Whether this array represents repulsion (True) or attraction (False).
                                    - 'body_radius' (float, optional): Default body radius for every agent in the array.
                                    - 'agent_radius_fn' (callable, optional): Function(agent_id) -> radius.
            custom_repulsion_positions (list, optional): A list of custom positions (x, y) to act as repulsion sources. Default is None.
            custom_attraction_positions (list, optional): A list of custom positions (x, y) to act as attraction sources. Default is None.
        Returns:
            tuple: The final combined vector (dx, dy) based on all agent arrays and custom settings.
        """
        # Loop through the provided agent arrays and add them to the vector fields
        for agent_array in agent_arrays:
            name = agent_array['name']
            array = agent_array['array']
            radius = agent_array['radius']
            is_dangerous = agent_array['is_dangerous']
            body_radius = float(agent_array.get('body_radius', 0.0))
            agent_radius_fn = agent_array.get('agent_radius_fn')

            # Add each agent array to the vector field with its properties
            self.add_agent_array(name, array, radius, is_dangerous, body_radius=body_radius, agent_radius_fn=agent_radius_fn)

        # Add custom repulsion positions if provided
        if custom_repulsion_positions:
            for position in custom_repulsion_positions:
                self.add_custom_repulsion_position(position)

        # Add custom attraction positions if provided
        if custom_attraction_positions:
            for position in custom_attraction_positions:
                self.add_custom_attraction_position(position)

        # Compute the final escape vector by combining all repulsion/attraction vectors
        escape_vector = self.compute_combined_vector()

        return escape_vector

class BumperCarVectorFields:
    class Body:
        def __init__(self, position, radius, weight=1.0, body_id=None):
            self.position = (float(position[0]), float(position[1]))
            self.radius = max(0.0, float(radius))
            self.weight = max(0.0, float(weight))
            self.body_id = body_id

    def __init__(
        self,
        probe_position,
        target_position=None,
        probe_radius=0.0,
        probe_id=None,
        contact_strength=1.0,
        penetration_strength=1.0,
        max_step_size=0.0,
        contact_epsilon=0.0,
    ):
        """
        Resolve local body separation only.

        The solver treats touching radii as a collision and produces a short
        escape destination away from the combined pressure of every invading
        body. It intentionally does not encode follow/combat policy, role
        logic, or long-range target seeking.
        """
        self.probe_position = (float(probe_position[0]), float(probe_position[1]))
        self.probe_radius = max(0.0, float(probe_radius))
        self.probe_id = probe_id
        self.contact_strength = max(0.0, float(contact_strength))
        self.penetration_strength = max(0.0, float(penetration_strength))
        self.max_step_size = max(0.0, float(max_step_size))
        self.contact_epsilon = max(0.0, float(contact_epsilon))
        self._bodies: list[BumperCarVectorFields.Body] = []

    @staticmethod
    def _sub(a, b):
        return (a[0] - b[0], a[1] - b[1])

    @staticmethod
    def _add(a, b):
        return (a[0] + b[0], a[1] + b[1])

    @staticmethod
    def _scale(v, s):
        return (v[0] * s, v[1] * s)

    @staticmethod
    def _dot(a, b):
        return (a[0] * b[0]) + (a[1] * b[1])

    @staticmethod
    def _cross_z(a, b):
        return (a[0] * b[1]) - (a[1] * b[0])

    @staticmethod
    def _length(v):
        return math.hypot(v[0], v[1])

    @staticmethod
    def _normalize(v):
        length = math.hypot(v[0], v[1])
        if length <= 0.000001:
            return (0.0, 0.0)
        return (v[0] / length, v[1] / length)

    @staticmethod
    def _perpendicular(v):
        return (-v[1], v[0])

    @staticmethod
    def _clamp(value, minimum, maximum):
        return max(minimum, min(maximum, value))

    def set_probe_position(self, position):
        self.probe_position = (float(position[0]), float(position[1]))

    def set_probe_id(self, probe_id):
        self.probe_id = probe_id

    def set_probe_radius(self, probe_radius):
        self.probe_radius = max(0.0, float(probe_radius))

    def set_max_step_size(self, max_step_size):
        self.max_step_size = max(0.0, float(max_step_size))

    def add_body(self, position, radius, velocity=(0.0, 0.0), weight=1.0, body_id=None):
        self._bodies.append(self.Body(position, radius, weight, body_id))

    def clear_bodies(self):
        self._bodies.clear()

    def _stable_scalar(self, value):
        if value is None:
            return 0
        try:
            return int(value)
        except Exception:
            return sum(ord(ch) for ch in str(value))

    def _resolve_away_vector(self, body):
        delta = self._sub(self.probe_position, body.position)
        distance = self._length(delta)
        if distance > 0.000001:
            return self._normalize(delta)

        probe_scalar = self._stable_scalar(self.probe_id)
        body_scalar = self._stable_scalar(body.body_id)
        selector = 1.0 if ((probe_scalar + body_scalar) % 2 == 0) else -1.0
        return self._normalize((selector, float(((probe_scalar ^ body_scalar) % 3) - 1)))

    def _collision_response(self, body):
        combined_radius = self.probe_radius + body.radius + self.contact_epsilon
        center_delta = self._sub(body.position, self.probe_position)
        center_distance = self._length(center_delta)
        penetration = combined_radius - center_distance
        if penetration < 0.0:
            return (0.0, 0.0)

        away = self._resolve_away_vector(body)
        strength = (self.contact_strength + (penetration * self.penetration_strength)) * body.weight
        return self._scale(away, strength)

    def compute_vector(self):
        collision_vector = (0.0, 0.0)

        for body in self._bodies:
            collision_vector = self._add(
                collision_vector,
                self._collision_response(body)
            )

        return collision_vector

    def compute_direction(self):
        return self._normalize(self.compute_vector())

    def has_collisions(self):
        for body in self._bodies:
            combined_radius = self.probe_radius + body.radius + self.contact_epsilon
            if self._length(self._sub(body.position, self.probe_position)) <= combined_radius:
                return True
        return False

    def compute_step_distance(self, max_step_size=None):
        vector = self.compute_vector()
        magnitude = self._length(vector)
        if magnitude <= 0.000001:
            return 0.0

        step_cap = self.max_step_size if max_step_size is None else max(0.0, float(max_step_size))
        if step_cap <= 0.0:
            return magnitude
        return self._clamp(magnitude, 0.0, step_cap)

    def compute_next_position(self, max_step_size=None):
        direction = self.compute_direction()
        step_distance = self.compute_step_distance(max_step_size=max_step_size)
        return self._add(self.probe_position, self._scale(direction, step_distance))
