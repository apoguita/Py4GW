
from .Utils import Utils

class VectorFields:
    """
    The VectorFields class simulates movement using repulsion and attraction forces based on agent arrays and custom positions.
    Additionally, custom repulsion and attraction positions can be provided.
    """

    def __init__(self, probe_position, custom_repulsion_radius=100, custom_attraction_radius=100):
        """
        Initialize the VectorFields object with player position and default settings.
        Args:
            probe_position (tuple): The player's current position (x, y).
        """
        self.probe_position = probe_position

        # Store settings for agent arrays and custom positions
        self.agent_arrays_settings = {}

        # Custom repulsion and attraction lists
        self.custom_repulsion_positions = []
        self.custom_attraction_positions = []

        # Radius for custom positions
        self.custom_repulsion_radius = custom_repulsion_radius
        self.custom_attraction_radius = custom_attraction_radius

    def add_agent_array(self, array_name, agent_array, radius, is_dangerous=True):
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
            'is_dangerous': is_dangerous
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



    def process_agent_array(self, agent_array, radius, is_dangerous):
        import PyAgent
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
            agent_instance = PyAgent.PyAgent(agent_id)
            target_position = (agent_instance.x, agent_instance.y)
            distance = Utils.Distance(self.probe_position, target_position)

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
            distance = Utils.Distance(self.probe_position, position)

            if distance <= radius:
                unit_vector = self.calculate_unit_vector(position)
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
                settings['agent_array'], settings['radius'], settings['is_dangerous'])
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

            # Add each agent array to the vector field with its properties
            self.add_agent_array(name, array, radius, is_dangerous)

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
