class LockKeyHelper:
    """
    Centralized helper class for generating lock keys used in party coordination.
    Lock keys prevent multiple party members from targeting the same agent with similar skills.
    """

    @staticmethod
    def hex_removal(agent_id: int) -> str:
        return f"Hex_Removal_{agent_id}"

    @staticmethod
    def condition_removal(agent_id: int) -> str:
        return f"Condition_Removal_{agent_id}"

    @staticmethod
    def resurrection(agent_id: int) -> str:
        return f"Resurrection_{agent_id}"